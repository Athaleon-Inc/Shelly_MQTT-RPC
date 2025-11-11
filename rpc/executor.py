"""RPC executor for managing the complete RPC workflow"""
from typing import Dict, Any, Optional, List
import logging
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import json

from core.session import Session
from mqtt.client import MQTTClient
from mqtt.publisher import RPCPublisher
from rpc.request_builder import RPCRequestBuilder
from rpc.response_handler import RPCResponseHandler, RPCResponse
from helpers.cert_utils import read_pem_file
from helpers.chunker import chunk_data, get_chunk_info
from helpers.rpc_command_saver import save_rpc_command


class RPCExecutor:
    """Execute RPC commands with full workflow: build, save, display, confirm, send, receive"""
    
    def __init__(self, mqtt_client: MQTTClient, response_handler: RPCResponseHandler,
                 config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize RPC executor.
        
        Args:
            mqtt_client: MQTT client instance
            response_handler: Response handler instance
            config: Application configuration
            logger: Logger instance
        """
        self.mqtt_client = mqtt_client
        self.response_handler = response_handler
        self.config = config
        self.logger = logger or logging.getLogger("shelly_mqtt_rpc.executor")
        self.publisher = RPCPublisher(mqtt_client, logger)
        self.console = Console()
        
        # Message ID counter
        self._next_msg_id = 1
    
    def get_next_msg_id(self) -> int:
        """Get next message ID"""
        msg_id = self._next_msg_id
        self._next_msg_id += 1
        return msg_id
    
    def execute_rpc(self, session: Session, method: str, params: Optional[Dict[str, Any]] = None,
                   auto_confirm: bool = False, timeout: float = 30.0) -> Optional[RPCResponse]:
        """
        Execute a single RPC command.
        
        Args:
            session: Session instance
            method: RPC method name
            params: Optional parameters
            auto_confirm: If True, skip user confirmation
            timeout: Response timeout in seconds
            
        Returns:
            RPCResponse if successful, None otherwise
        """
        # Get configuration
        src = self.config.get('rpc', {}).get('default_src', 'sunio_app')
        msg_id = self.get_next_msg_id()
        
        # Build payload
        payload = RPCRequestBuilder.build_rpc_payload(msg_id, src, method, params)
        
        # Save command
        save_path = save_rpc_command(session.name, method, payload)
        self.logger.debug(f"Saved RPC command to: {save_path}")
        
        # Display payload
        self._display_payload(payload, f"RPC Command: {method}")
        
        # Confirm
        if not auto_confirm:
            if not self._confirm_send():
                self.console.print("[yellow]Command cancelled by user[/yellow]")
                return None
        
        # Register for response
        self.response_handler.register_request(msg_id)
        
        # Subscribe to response topic (src field indicates where response will come from)
        response_topic = f"{src}/rpc"
        self.mqtt_client.subscribe(response_topic, self.response_handler.handle_message)
        
        # Publish
        published_id = self.publisher.publish_rpc(session.mqtt_prefix, payload)
        
        if published_id is None:
            self.console.print("[red]Failed to publish RPC command[/red]")
            self.response_handler.cancel_request(msg_id)
            return None
        
        self.console.print(f"[green]Command sent successfully (ID: {msg_id})[/green]")
        self.console.print(f"[cyan]Waiting for response (timeout: {timeout}s)...[/cyan]")
        
        # Wait for response
        response = self.response_handler.wait_for_response(msg_id, timeout)
        
        if response is None:
            self.console.print("[red]Timeout: No response received[/red]")
            return None
        
        # Display response
        self._display_response(response)
        
        return response
    
    def execute_cert_upload(self, session: Session, cert_path: str, method: str,
                          auto_confirm: bool = False, timeout: float = 30.0) -> List[Optional[RPCResponse]]:
        """
        Execute certificate upload with automatic chunking if needed.
        
        Args:
            session: Session instance
            cert_path: Path to certificate file
            method: RPC method (e.g., 'Shelly.PutUserCA')
            auto_confirm: If True, skip user confirmation
            timeout: Response timeout in seconds per chunk
            
        Returns:
            List of RPCResponse objects (one per chunk)
        """
        # Read certificate preserving full PEM content
        try:
            cert_data = read_pem_file(cert_path)
        except (FileNotFoundError, UnicodeDecodeError) as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return []
        
        if not cert_data.strip():
            self.console.print(f"[red]Error: Certificate file is empty: {cert_path}[/red]")
            return []
        
        # Get chunk size from config
        chunk_size = self.config.get('rpc', {}).get('chunk_size', 2048)
        
        # Check if chunking is needed
        chunk_info = get_chunk_info(cert_data, chunk_size)
        
        self.console.print(Panel(
            f"Certificate size: {chunk_info['total_size']} bytes\n"
            f"Chunks needed: {chunk_info['chunk_count']}\n"
            f"Needs chunking: {chunk_info['needs_chunking']}",
            title="Certificate Upload Info"
        ))
        
        # Chunk data
        chunks = chunk_data(cert_data, chunk_size)
        
        # Build payloads
        src = self.config.get('rpc', {}).get('default_src', 'sunio_app')
        msg_id_start = self.get_next_msg_id()
        payloads = RPCRequestBuilder.build_chunked_upload_requests(
            msg_id_start, method, chunks, src
        )
        
        # Save commands
        save_path = save_rpc_command(session.name, method, payloads)
        self.logger.debug(f"Saved {len(payloads)} RPC commands to: {save_path}")
        
        # Display payloads
        for i, payload in enumerate(payloads):
            self._display_payload(payload, f"Chunk {i+1}/{len(payloads)}")
        
        # Confirm
        if not auto_confirm:
            if not self._confirm_send():
                self.console.print("[yellow]Upload cancelled by user[/yellow]")
                return []

        # Issue delete command before uploading new data, matching shelly-cert behavior
        self.console.print(
            "[cyan]Deleting existing certificate/key on device...[/cyan]"
        )
        delete_response = self.execute_rpc(
            session,
            method,
            params={"data": None},
            auto_confirm=True,
            timeout=timeout
        )
        delete_failed = (
            delete_response is None
            or (
                hasattr(delete_response, "success")
                and not delete_response.success
            )
        )
        if delete_failed:
            self.console.print(
                "[red]Pre-upload deletion failed. Aborting upload.[/red]"
            )
            return []
        
        # Subscribe to response topic
        response_topic = f"{src}/rpc"
        self.mqtt_client.subscribe(response_topic, self.response_handler.handle_message)
        
        # Execute each chunk
        responses = []
        for i, payload in enumerate(payloads):
            msg_id = payload['id']
            
            self.console.print(f"\n[cyan]Sending chunk {i+1}/{len(payloads)} (ID: {msg_id})...[/cyan]")
            
            # Register for response
            self.response_handler.register_request(msg_id)
            
            # Publish
            published_id = self.publisher.publish_rpc(session.mqtt_prefix, payload)
            
            if published_id is None:
                self.console.print(f"[red]Failed to publish chunk {i+1}[/red]")
                self.response_handler.cancel_request(msg_id)
                responses.append(None)
                continue
            
            # Wait for response
            response = self.response_handler.wait_for_response(msg_id, timeout)
            
            if response is None:
                self.console.print(f"[red]Timeout for chunk {i+1}[/red]")
                responses.append(None)
                continue
            
            if not response.success:
                self.console.print(f"[red]Chunk {i+1} failed: {response.error}[/red]")
                self._display_response(response)
                responses.append(response)
                # Stop on error
                break
            
            self.console.print(f"[green]Chunk {i+1} uploaded successfully[/green]")
            self._display_response(response)
            responses.append(response)
        
        # Display final result
        success_count = sum(1 for r in responses if r and r.success)
        self.console.print(Panel(
            f"Total chunks: {len(payloads)}\n"
            f"Successful: {success_count}\n"
            f"Failed: {len(payloads) - success_count}",
            title="Upload Summary",
            style="green" if success_count == len(payloads) else "red"
        ))
        
        return responses
    
    def execute_mqtt_config_update(self, session: Session, mqtt_config: Dict[str, Any],
                                  auto_confirm: bool = False, timeout: float = 30.0) -> Optional[RPCResponse]:
        """
        Execute MQTT configuration update.
        
        Args:
            session: Session instance
            mqtt_config: MQTT configuration dictionary
            auto_confirm: If True, skip user confirmation
            timeout: Response timeout in seconds
            
        Returns:
            RPCResponse if successful, None otherwise
        """
        return self.execute_rpc(session, "MQTT.SetConfig", 
                              params={"config": mqtt_config}, 
                              auto_confirm=auto_confirm, timeout=timeout)
    
    def _display_payload(self, payload: Dict[str, Any], title: str = "RPC Payload"):
        """Display RPC payload in formatted JSON"""
        json_str = json.dumps(payload, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        self.console.print(Panel(syntax, title=title))
    
    def _display_response(self, response: RPCResponse):
        """Display RPC response"""
        if response.success:
            result_str = json.dumps(response.result, indent=2) if response.result else "No result data"
            syntax = Syntax(result_str, "json", theme="monokai", line_numbers=False)
            self.console.print(Panel(
                syntax,
                title=f"[green]Response (ID: {response.msg_id}) - Success[/green]",
                border_style="green"
            ))
        else:
            error_str = json.dumps(response.error, indent=2) if response.error else "Unknown error"
            syntax = Syntax(error_str, "json", theme="monokai", line_numbers=False)
            self.console.print(Panel(
                syntax,
                title=f"[red]Response (ID: {response.msg_id}) - Error[/red]",
                border_style="red"
            ))
    
    def _confirm_send(self) -> bool:
        """Ask user to confirm sending the command"""
        response = self.console.input("\n[yellow]Send this command? (yes/no): [/yellow]")
        return response.lower() in ['yes', 'y']

