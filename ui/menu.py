"""Main menu for the console application"""
from typing import Optional, Dict, Any
import logging
from rich.console import Console

from core.session import Session
from ui.panels import UIPanels
from ui.prompts import UIPrompts
from ui.session_menu import SessionMenu


class MainMenu:
    """Main menu for the application"""
    
    def __init__(self, config: Dict[str, Any], mqtt_client, rpc_executor, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize main menu.
        
        Args:
            config: Application configuration
            mqtt_client: MQTT client instance
            rpc_executor: RPC executor instance
            logger: Logger instance
        """
        self.config = config
        self.mqtt_client = mqtt_client
        self.rpc_executor = rpc_executor
        self.logger = logger or logging.getLogger("shelly_mqtt_rpc.menu")
        
        self.console = Console()
        self.panels = UIPanels(self.console)
        self.prompts = UIPrompts()
        
        self.current_session: Optional[Session] = None
        self.running = True
    
    def show(self):
        """Display main menu"""
        self.panels.clear_screen()
        self.panels.show_banner()
        
        # Show current session if any
        if self.current_session:
            self.panels.show_session_info(self.current_session)
            self.console.print()
        
        # Show MQTT status
        mqtt_config = self.config.get('mqtt', {})
        self.panels.show_mqtt_status(self.mqtt_client.is_connected(), mqtt_config)
        
        # Show TLS configuration warning if needed
        if mqtt_config.get('use_tls') and not getattr(self.mqtt_client, 'tls_configured', False):
            self.console.print("[yellow]⚠ TLS not configured - update MQTT settings in configs/config.json[/yellow]")
        
        self.console.print()
        
        # Menu options
        self.console.print("[bold cyan]Main Menu:[/bold cyan]")
        self.console.print("  1. Create new session")
        self.console.print("  2. Load existing session")
        self.console.print("  3. View session configuration")
        self.console.print("  4. Connect to MQTT broker")
        self.console.print("  5. Disconnect from MQTT broker")
        
        if self.current_session and self.mqtt_client.is_connected():
            self.console.print("  6. RPC Operations (Session menu)")
        else:
            self.console.print("  6. RPC Operations [dim](requires session & MQTT connection)[/dim]")
        
        self.console.print("  0. Exit")
        self.console.print()
    
    def run(self):
        """Run the main menu loop"""
        while self.running:
            try:
                self.show()
                
                choice = self.prompts.prompt_text("Select option", required=True)
                
                if choice == "1":
                    self._create_session()
                elif choice == "2":
                    self._load_session()
                elif choice == "3":
                    self._view_session_config()
                elif choice == "4":
                    self._connect_mqtt()
                elif choice == "5":
                    self._disconnect_mqtt()
                elif choice == "6":
                    self._open_session_menu()
                elif choice == "0":
                    self._exit()
                else:
                    self.panels.show_error("Invalid option")
                    self.prompts.prompt_text("\nPress Enter to continue")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use option 0 to exit[/yellow]")
                self.prompts.prompt_text("\nPress Enter to continue")
            except Exception as e:
                self.logger.error(f"Error in main menu: {e}", exc_info=True)
                self.panels.show_error(f"An error occurred: {e}")
                self.prompts.prompt_text("\nPress Enter to continue")
    
    def _create_session(self):
        """Create a new session"""
        self.console.print("\n[bold cyan]Create New Session[/bold cyan]\n")
        
        try:
            # Get existing session names
            existing = Session.list_sessions()
            
            # Prompt for session details
            name = self.prompts.prompt_session_name(existing)
            device_id = self.prompts.prompt_device_id()
            
            # Generate default MQTT prefix
            prefix_template = self.config.get('session', {}).get('default_mqtt_prefix_template', 
                                                                'shellypro4pm-{device_id}')
            default_prefix = prefix_template.format(device_id=device_id)
            mqtt_prefix = self.prompts.prompt_mqtt_prefix(default_prefix)
            
            notes = self.prompts.prompt_notes()
            
            # Create session
            session = Session(name=name, device_id=device_id, mqtt_prefix=mqtt_prefix)
            session.notes = notes
            session.create()
            
            self.current_session = session
            self.panels.show_success(f"Session '{name}' created successfully!")
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}", exc_info=True)
            self.panels.show_error(f"Failed to create session: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _load_session(self):
        """Load an existing session"""
        self.console.print("\n[bold cyan]Load Session[/bold cyan]\n")
        
        try:
            # List available sessions
            sessions = Session.list_sessions()
            
            if not sessions:
                self.panels.show_info("No sessions available. Create a new session first.")
                self.prompts.prompt_text("\nPress Enter to continue")
                return
            
            self.panels.show_sessions_list(sessions)
            self.console.print()
            
            # Prompt for session selection
            choice = self.prompts.prompt_choice("Select session name", sessions)
            
            if choice in sessions:
                self.current_session = Session.load(choice)
                self.panels.show_success(f"Session '{choice}' loaded successfully!")
            else:
                self.panels.show_error("Invalid session name")
            
        except Exception as e:
            self.logger.error(f"Error loading session: {e}", exc_info=True)
            self.panels.show_error(f"Failed to load session: {e}")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _view_session_config(self):
        """View current session configuration"""
        self.console.print("\n[bold cyan]Session Configuration[/bold cyan]\n")
        
        if not self.current_session:
            self.panels.show_warning("No session loaded. Load or create a session first.")
        else:
            self.panels.show_session_info(self.current_session)
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _connect_mqtt(self):
        """Connect to MQTT broker"""
        self.console.print("\n[bold cyan]Connect to MQTT Broker[/bold cyan]\n")
        
        if self.mqtt_client.is_connected():
            self.panels.show_info("Already connected to MQTT broker")
        else:
            self.console.print("Connecting to MQTT broker...")
            success = self.mqtt_client.connect()
            
            if success:
                # Wait a moment for connection
                import time
                time.sleep(1)
                
                if self.mqtt_client.is_connected():
                    self.panels.show_success("Connected to MQTT broker successfully!")
                else:
                    self.panels.show_warning("Connection initiated, waiting for confirmation...")
            else:
                self.panels.show_error("Failed to connect to MQTT broker. Check configuration and logs.")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        self.console.print("\n[bold cyan]Disconnect from MQTT Broker[/bold cyan]\n")
        
        if not self.mqtt_client.is_connected():
            self.panels.show_info("Not connected to MQTT broker")
        else:
            self.mqtt_client.disconnect()
            self.panels.show_success("Disconnected from MQTT broker")
        
        self.prompts.prompt_text("\nPress Enter to continue")
    
    def _open_session_menu(self):
        """Open session-specific RPC operations menu"""
        if not self.current_session:
            self.panels.show_warning("No session loaded. Load or create a session first.")
            self.prompts.prompt_text("\nPress Enter to continue")
            return
        
        if not self.mqtt_client.is_connected():
            self.panels.show_warning("Not connected to MQTT broker. Connect first.")
            self.prompts.prompt_text("\nPress Enter to continue")
            return
        
        # Open session menu
        session_menu = SessionMenu(
            self.current_session,
            self.mqtt_client,
            self.rpc_executor,
            self.config,
            self.logger
        )
        session_menu.run()
    
    def _exit(self):
        """Exit the application"""
        if self.prompts.prompt_yes_no("Are you sure you want to exit?", default=False):
            self.console.print("\n[cyan]Shutting down...[/cyan]")
            
            # Disconnect MQTT if connected
            if self.mqtt_client.is_connected():
                self.mqtt_client.disconnect()
            
            self.running = False
            self.console.print("[green]Goodbye![/green]\n")

