"""Session management for Shelly MQTT-RPC Manager"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class Session:
    """Represents a Shelly device session with configuration and certificates"""
    
    def __init__(self, name: str, device_id: str = "", mqtt_prefix: str = "", 
                 sessions_dir: str = "sessions"):
        self.name = name
        self.device_id = device_id
        self.mqtt_prefix = mqtt_prefix
        self.sessions_dir = sessions_dir
        
        # Paths
        self.session_dir = os.path.join(sessions_dir, name)
        self.config_path = os.path.join(self.session_dir, "config.json")
        self.cert_dir = os.path.join(self.session_dir, "certs")
        
        # Metadata
        self.created_at: Optional[str] = None
        self.last_used: Optional[str] = None
        self.notes: str = ""
    
    def create(self) -> 'Session':
        """Create a new session with directory structure"""
        # Create session directory
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Create certs directory
        os.makedirs(self.cert_dir, exist_ok=True)
        self._ensure_cert_placeholders()
        
        # Set timestamps
        self.created_at = datetime.now().isoformat()
        self.last_used = self.created_at
        
        # Save configuration
        self.save()
        
        return self
    
    @classmethod
    def load(cls, name: str, sessions_dir: str = "sessions") -> 'Session':
        """Load an existing session from disk"""
        session = cls(name=name, sessions_dir=sessions_dir)
        
        if not os.path.exists(session.config_path):
            raise FileNotFoundError(f"Session '{name}' not found at {session.config_path}")
        
        with open(session.config_path, 'r') as f:
            config = json.load(f)
        
        # Load session data
        session.device_id = config.get('device_id', '')
        session.mqtt_prefix = config.get('mqtt_prefix', '')
        session.created_at = config.get('created_at')
        session.last_used = config.get('last_used')
        session.notes = config.get('notes', '')
        
        # Update last used timestamp
        session.last_used = datetime.now().isoformat()
        session.save()
        
        return session

    def _ensure_cert_placeholders(self):
        """Create placeholder certificate files for new sessions."""
        placeholders = {
            'ca_cert': "# Paste the CA certificate chain here\n",
            'client_cert': "# Paste the client certificate here\n",
            'client_key': "# Paste the client private key here\n"
        }

        for key, path in self.get_cert_paths().items():
            if not os.path.exists(path):
                with open(path, 'w') as cert_file:
                    cert_file.write(placeholders[key])
    
    def save(self):
        """Save session configuration to disk"""
        config = {
            'name': self.name,
            'device_id': self.device_id,
            'mqtt_prefix': self.mqtt_prefix,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'notes': self.notes,
            'cert_dir': self.cert_dir
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_cert_paths(self) -> Dict[str, str]:
        """Get paths to certificate files"""
        return {
            'ca_cert': os.path.join(self.cert_dir, 'ca.crt'),
            'client_cert': os.path.join(self.cert_dir, 'client.crt'),
            'client_key': os.path.join(self.cert_dir, 'client.key')
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get session configuration as dictionary"""
        return {
            'name': self.name,
            'device_id': self.device_id,
            'mqtt_prefix': self.mqtt_prefix,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'notes': self.notes,
            'session_dir': self.session_dir,
            'cert_dir': self.cert_dir
        }
    
    def update(self, **kwargs):
        """Update session properties"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
    
    @staticmethod
    def list_sessions(sessions_dir: str = "sessions") -> List[str]:
        """List all available session names"""
        if not os.path.exists(sessions_dir):
            return []
        
        sessions = []
        for item in os.listdir(sessions_dir):
            session_path = os.path.join(sessions_dir, item)
            config_path = os.path.join(session_path, "config.json")
            if os.path.isdir(session_path) and os.path.exists(config_path):
                sessions.append(item)
        
        return sorted(sessions)
    
    @staticmethod
    def session_exists(name: str, sessions_dir: str = "sessions") -> bool:
        """Check if a session exists"""
        config_path = os.path.join(sessions_dir, name, "config.json")
        return os.path.exists(config_path)
    
    def delete(self):
        """Delete this session and all its files"""
        import shutil
        if os.path.exists(self.session_dir):
            shutil.rmtree(self.session_dir)
    
    def __repr__(self):
        return f"Session(name='{self.name}', device_id='{self.device_id}', mqtt_prefix='{self.mqtt_prefix}')"

