"""Session-specific RPC operations menu"""
from typing import Optional, Dict, Any
import logging
import os
from rich.console import Console

from core.session import Session
from ui.panels import UIPanels
from ui.prompts import UIPrompts


class SessionMenu:
    """Menu for RPC operations on a specific session"""
    
    def __init__(self, session: Session, mqtt_client, rpc_executor, 
                 config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize session menu.
        
        Args:
            session: Session instance
            mqtt_client: MQTT client instance
            rpc_executor: RPC executor instance
            config: Application configuration
            logger: Logger instance
        """
        self.session = session
        self.mqtt_client = mqtt_client
        self.rpc_executor = rpc_executor
        self.config = config
        self.logger = logger or logging.getLogger("shelly_mqtt_rpc.session_menu")
        
        self.console = Console()
        self.panels = UIPanels(self.console)
        self.prompts = UIPrompts()
        
        self.running = True
    
    def show(self):
        """Display session menu"""
        self.panels.clear_screen()
        self.console.print(f"[bold cyan]Session: {self.session.name}[/bold cyan]")
        self.console.print(f"[dim]Device: {self.session.device_id} | Prefix: {self.session.mqtt_prefix}[/dim]\n")
        
        self.console.print("[bold cyan]RPC Operations:[/bold cyan]")
        self.console.print("  1. Get device status (Shelly.GetStatus)")
        self.console.print("  2. Get device info (Shelly.GetDeviceInfo)")
        self.console.print("  3. Get MQTT configuration (MQTT.GetConfig)")
        self.console.print("  4. Update MQTT configuration (MQTT.SetConfig)")
        self.console.print("  5. Upload CA certificate (Shelly.PutUserCA)")
        self.console.print("  6. Upload client certificate (Shelly.PutTLSClientCert)")
        self.console.print("  7. Upload client key (Shelly.PutTLSClientKey)")
        self.console.print("  8. Reboot device (Shelly.Reboot)")
        self.console.print("  9. Check for updates (Shelly.CheckForUpdate)")
        self.console.print("  0. Back to main menu")
        self.console.print()
    
    def run(self):
        """Run the session menu loop"""
        while self.running:
            try:
                self.show()
                
                choice = self.prompts.prompt_text("Select operation", required=True)
                
                if choice == "1":
                    self._get_status()
                elif choice == "2":
                    self._get_device_info()
                elif choice == "3":
                    self._get_mqtt_config()
                elif choice == "4":
                    self._update_mqtt_config()
                elif choice == "5":
                    self._upload_ca_cert()
                elif choice == "6":
                    self._upload_client_cert()
                elif choice == "7":
                    self._upload_client_key()
                elif choice == "8":
                    self._reboot_device()
                elif choice == "9":
                    self._check_for_updates()
                elif choice == "0":
                    self.running = False
                else:
                    self.panels.show_error("Invalid option")
                    self.prompts.prompt_text("\nPress Enter to continue")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use option 0 to go back[/yellow]")
                self.prompts.prompt_text("\nPress Enter to continue")
            except Exception as e:
                self.logger.error(f"Error in session menu: {e}", exc_info=True)
                self.panels.show_error(f"An error occurred: {e}")
                self.prompts.prompt_text("\nPress Enter to continue")
    
    def _get_status(self):
        """Get device status"""
        self.console.print("\n[bold cyan]Get Device Status[/bold cyan]\n")
        
        try:
            response = self.rpc_executor.execute_rpc(
                self.session,
                "Shelly.GetStatus",
                auto_confirm=False
            )
            
            if response and response.success:
                self.panels.show_success("Status retrieved successfully")
            elif response:
                self.panels.show_error(f"Failed to get status: {response.error}")
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _get_device_info(self):
        """Get device information"""
        self.console.print("\n[bold cyan]Get Device Information[/bold cyan]\n")
        
        try:
            response = self.rpc_executor.execute_rpc(
                self.session,
                "Shelly.GetDeviceInfo",
                auto_confirm=False
            )
            
            if response and response.success:
                self.panels.show_success("Device info retrieved successfully")
            elif response:
                self.panels.show_error(f"Failed to get device info: {response.error}")
            
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _get_mqtt_config(self):
        """Get MQTT configuration"""
        self.console.print("\n[bold cyan]Get MQTT Configuration[/bold cyan]\n")
        
        try:
            response = self.rpc_executor.execute_rpc(
                self.session,
                "MQTT.GetConfig",
                auto_confirm=False
            )
            
            if response and response.success:
                self.panels.show_success("MQTT config retrieved successfully")
            elif response:
                self.panels.show_error(f"Failed to get MQTT config: {response.error}")
            
        except Exception as e:
            self.logger.error(f"Error getting MQTT config: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _update_mqtt_config(self):
        """Update MQTT configuration"""
        self.console.print("\n[bold cyan]Update MQTT Configuration[/bold cyan]\n")
        
        try:
            # Prompt for MQTT settings
            self.console.print("Enter new MQTT configuration:")
            
            enable = self.prompts.prompt_yes_no("Enable MQTT", default=True)
            server = self.prompts.prompt_text("Server (e.g., mqtts://mqtt.example.com:8883)", required=True)
            client_id = self.prompts.prompt_text("Client ID", required=True)
            user = self.prompts.prompt_text("Username", default="")
            password = self.prompts.prompt_text("Password", default="")
            ssl_ca = self.prompts.prompt_choice("SSL CA", ["*", "ca.pem", "user_ca.pem"], default="*")
            use_client_cert = self.prompts.prompt_yes_no("Use client certificate", default=True)
            skip_cert_cn_check = self.prompts.prompt_yes_no("Skip certificate CN check", default=True)
            
            # Build config
            mqtt_config = {
                "enable": enable,
                "server": server,
                "client_id": client_id,
                "user": user,
                "pass": password,
                "ssl_ca": ssl_ca,
                "use_client_cert": use_client_cert,
                "skip_cert_cn_check": skip_cert_cn_check
            }
            
            # Execute
            response = self.rpc_executor.execute_mqtt_config_update(
                self.session,
                mqtt_config,
                auto_confirm=False
            )
            
            if response and response.success:
                self.panels.show_success("MQTT configuration updated successfully")
            elif response:
                self.panels.show_error(f"Failed to update MQTT config: {response.error}")
            
        except Exception as e:
            self.logger.error(f"Error updating MQTT config: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _upload_ca_cert(self):
        """Upload CA certificate"""
        self.console.print("\n[bold cyan]Upload CA Certificate[/bold cyan]\n")
        
        try:
            # Get default path
            default_path = os.path.join(self.session.cert_dir, "ca.crt")
            
            cert_path = self.prompts.prompt_file_path(
                f"CA certificate path [{default_path}]: ",
                must_exist=True
            )
            
            if not cert_path:
                cert_path = default_path
            
            # Execute upload
            responses = self.rpc_executor.execute_cert_upload(
                self.session,
                cert_path,
                "Shelly.PutUserCA",
                auto_confirm=False
            )
            
            if responses and all(r and r.success for r in responses):
                self.panels.show_success("CA certificate uploaded successfully")
            elif responses:
                self.panels.show_error("CA certificate upload completed with errors")
            
        except Exception as e:
            self.logger.error(f"Error uploading CA cert: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _upload_client_cert(self):
        """Upload client certificate"""
        self.console.print("\n[bold cyan]Upload Client Certificate[/bold cyan]\n")
        
        try:
            # Get default path
            default_path = os.path.join(self.session.cert_dir, "client.crt")
            
            cert_path = self.prompts.prompt_file_path(
                f"Client certificate path [{default_path}]: ",
                must_exist=True
            )
            
            if not cert_path:
                cert_path = default_path
            
            # Execute upload
            responses = self.rpc_executor.execute_cert_upload(
                self.session,
                cert_path,
                "Shelly.PutTLSClientCert",
                auto_confirm=False
            )
            
            if responses and all(r and r.success for r in responses):
                self.panels.show_success("Client certificate uploaded successfully")
            elif responses:
                self.panels.show_error("Client certificate upload completed with errors")
            
        except Exception as e:
            self.logger.error(f"Error uploading client cert: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _upload_client_key(self):
        """Upload client key"""
        self.console.print("\n[bold cyan]Upload Client Key[/bold cyan]\n")
        
        try:
            # Get default path
            default_path = os.path.join(self.session.cert_dir, "client.key")
            
            key_path = self.prompts.prompt_file_path(
                f"Client key path [{default_path}]: ",
                must_exist=True
            )
            
            if not key_path:
                key_path = default_path
            
            # Execute upload
            responses = self.rpc_executor.execute_cert_upload(
                self.session,
                key_path,
                "Shelly.PutTLSClientKey",
                auto_confirm=False
            )
            
            if responses and all(r and r.success for r in responses):
                self.panels.show_success("Client key uploaded successfully")
            elif responses:
                self.panels.show_error("Client key upload completed with errors")
            
        except Exception as e:
            self.logger.error(f"Error uploading client key: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _reboot_device(self):
        """Reboot device"""
        self.console.print("\n[bold cyan]Reboot Device[/bold cyan]\n")
        
        if not self.prompts.prompt_yes_no("Are you sure you want to reboot the device?", default=False):
            self.console.print("[yellow]Reboot cancelled[/yellow]")
            self.prompts.prompt_text("\nPress Enter to continue")
            return
        
        try:
            response = self.rpc_executor.execute_rpc(
                self.session,
                "Shelly.Reboot",
                auto_confirm=True  # Already confirmed above
            )
            
            if response and response.success:
                self.panels.show_success("Reboot command sent successfully")
            elif response:
                self.panels.show_error(f"Failed to reboot: {response.error}")
            
        except Exception as e:
            self.logger.error(f"Error rebooting device: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _check_for_updates(self):
        """Check for firmware updates"""
        self.console.print("\n[bold cyan]Check for Updates[/bold cyan]\n")
        
        try:
            response = self.rpc_executor.execute_rpc(
                self.session,
                "Shelly.CheckForUpdate",
                auto_confirm=False
            )
            
            if response and response.success:
                self.panels.show_success("Update check completed successfully")
            elif response:
                self.panels.show_error(f"Failed to check for updates: {response.error}")
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)
            self.panels.show_error(f"Error: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")

