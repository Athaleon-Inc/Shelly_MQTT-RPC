"""Rich panels for styled console output"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing import Dict, Any, Optional
from datetime import datetime

from core.session import Session


class UIPanels:
    """Collection of UI panels for displaying information"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def show_banner(self):
        """Display application banner"""
        banner = Text()
        banner.append("╔═══════════════════════════════════════╗\n", style="bold cyan")
        banner.append("║   Shelly MQTT-RPC Manager             ║\n", style="bold cyan")
        banner.append("║   Device Configuration & Management   ║\n", style="bold cyan")
        banner.append("╚═══════════════════════════════════════╝", style="bold cyan")
        
        self.console.print(banner)
        self.console.print()
    
    def show_session_info(self, session: Session):
        """Display session information panel"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Session Name", session.name)
        table.add_row("Device ID", session.device_id or "[dim]Not set[/dim]")
        table.add_row("MQTT Prefix", session.mqtt_prefix or "[dim]Not set[/dim]")
        table.add_row("Session Dir", session.session_dir)
        table.add_row("Cert Dir", session.cert_dir)
        
        if session.created_at:
            created = datetime.fromisoformat(session.created_at).strftime("%Y-%m-%d %H:%M:%S")
            table.add_row("Created", created)
        
        if session.last_used:
            used = datetime.fromisoformat(session.last_used).strftime("%Y-%m-%d %H:%M:%S")
            table.add_row("Last Used", used)
        
        if session.notes:
            table.add_row("Notes", session.notes)
        
        self.console.print(Panel(table, title="[bold]Session Information[/bold]", border_style="blue"))
    
    def show_mqtt_status(self, connected: bool, config: Dict[str, Any]):
        """Display MQTT connection status panel"""
        status_text = "[green]Connected[/green]" if connected else "[red]Disconnected[/red]"
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Status", status_text)
        table.add_row("Broker", f"{config.get('host')}:{config.get('port')}")
        table.add_row("Client ID", config.get('client_id', 'N/A'))
        table.add_row("TLS", "Enabled" if config.get('use_tls') else "Disabled")
        
        self.console.print(Panel(table, title="[bold]MQTT Status[/bold]", border_style="cyan"))
    
    def show_error(self, message: str, title: str = "Error"):
        """Display error message"""
        self.console.print(Panel(
            f"[red]{message}[/red]",
            title=f"[bold red]{title}[/bold red]",
            border_style="red"
        ))
    
    def show_success(self, message: str, title: str = "Success"):
        """Display success message"""
        self.console.print(Panel(
            f"[green]{message}[/green]",
            title=f"[bold green]{title}[/bold green]",
            border_style="green"
        ))
    
    def show_info(self, message: str, title: str = "Information"):
        """Display info message"""
        self.console.print(Panel(
            f"[cyan]{message}[/cyan]",
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan"
        ))
    
    def show_warning(self, message: str, title: str = "Warning"):
        """Display warning message"""
        self.console.print(Panel(
            f"[yellow]{message}[/yellow]",
            title=f"[bold yellow]{title}[/bold yellow]",
            border_style="yellow"
        ))
    
    def show_sessions_list(self, sessions: list):
        """Display list of available sessions"""
        if not sessions:
            self.show_info("No sessions found. Create a new session to get started.")
            return
        
        table = Table(title="Available Sessions", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="white")
        
        for i, session_name in enumerate(sessions, 1):
            table.add_row(str(i), session_name, "[green]Ready[/green]")
        
        self.console.print(table)
    
    def clear_screen(self):
        """Clear the console screen"""
        self.console.clear()

