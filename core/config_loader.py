"""Configuration loader for Shelly MQTT-RPC Manager"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Loads and validates the main configuration file"""
    
    def __init__(self, config_path: str = "configs/config.json"):
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = json.load(f)
        
        self._validate()
        return self._config
    
    def _validate(self):
        """Validate required configuration fields"""
        if not self._config:
            raise ValueError("Configuration not loaded")
        
        # Validate MQTT settings
        mqtt = self._config.get('mqtt', {})
        required_mqtt = ['host', 'port', 'use_tls']
        for field in required_mqtt:
            if field not in mqtt:
                raise ValueError(f"Missing required MQTT field: {field}")
        
        # Validate RPC settings
        rpc = self._config.get('rpc', {})
        if 'chunk_size' not in rpc:
            raise ValueError("Missing required RPC field: chunk_size")
        
        # Validate session settings
        session = self._config.get('session', {})
        if 'default_mqtt_prefix_template' not in session:
            raise ValueError("Missing required session field: default_mqtt_prefix_template")
        
        # Validate application settings
        app = self._config.get('application', {})
        if 'log_level' not in app:
            raise ValueError("Missing required application field: log_level")
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation"""
        if not self._config:
            self.load()
        
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """Get MQTT configuration section"""
        return self.get('mqtt', default={})
    
    def get_rpc_config(self) -> Dict[str, Any]:
        """Get RPC configuration section"""
        return self.get('rpc', default={})
    
    def get_rpc_call_delay(self, default: float = 0.0) -> float:
        """Get configured delay between RPC calls in seconds"""
        return self.get('rpc', 'call_delay_seconds', default=default)
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get session configuration section"""
        return self.get('session', default={})
    
    def get_application_config(self) -> Dict[str, Any]:
        """Get application configuration section"""
        return self.get('application', default={})
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration"""
        if not self._config:
            self.load()
        return self._config

