"""MQTT client for Shelly MQTT-RPC Manager"""
import ssl
import paho.mqtt.client as mqtt
from typing import Callable, Optional, Dict, Any
import logging
import json


class MQTTClient:
    """MQTT client wrapper with TLS support and message routing"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize MQTT client with configuration.
        
        Args:
            config: MQTT configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger("shelly_mqtt_rpc.mqtt")
        
        # Client setup
        self.client_id = config.get('client_id', 'shelly_manager')
        self.client = mqtt.Client(client_id=self.client_id)
        
        # Connection state
        self.connected = False
        self.subscribed_topics = []
        
        # Message handlers
        self.message_callbacks: Dict[str, Callable] = {}
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Setup authentication
        username = config.get('username', '')
        password = config.get('password', '')
        if username or password:
            self.client.username_pw_set(username, password)
        
        # Setup TLS if enabled
        self.tls_configured = False
        if config.get('use_tls', False):
            try:
                self._setup_tls()
                self.tls_configured = True
            except Exception as e:
                self.logger.warning(f"TLS configuration failed: {e}")
                self.logger.info("Application will start, but MQTT connection will not work until TLS is configured")
    
    def _setup_tls(self):
        """Configure TLS/SSL settings"""
        import os
        
        tls_config = {}
        
        # CA certificate
        ca_cert = self.config.get('ca_cert')
        if ca_cert and os.path.exists(ca_cert):
            tls_config['ca_certs'] = ca_cert
            self.logger.debug(f"Using CA certificate: {ca_cert}")
        elif ca_cert:
            self.logger.warning(f"CA certificate not found: {ca_cert} - will use default CA bundle")
        
        # Client certificate and key
        client_cert = self.config.get('client_cert')
        client_key = self.config.get('client_key')
        
        # Only add client cert/key if BOTH files exist
        if client_cert and client_key:
            if os.path.exists(client_cert) and os.path.exists(client_key):
                tls_config['certfile'] = client_cert
                tls_config['keyfile'] = client_key
                self.logger.debug(f"Using client certificate: {client_cert}")
            else:
                if not os.path.exists(client_cert):
                    self.logger.warning(f"Client certificate not found: {client_cert}")
                if not os.path.exists(client_key):
                    self.logger.warning(f"Client key not found: {client_key}")
                self.logger.info("TLS will be configured without client certificate authentication")
        
        # Certificate verification
        if self.config.get('skip_cert_cn_check', False):
            tls_config['cert_reqs'] = ssl.CERT_NONE
        else:
            tls_config['cert_reqs'] = ssl.CERT_REQUIRED
        
        tls_config['tls_version'] = ssl.PROTOCOL_TLS
        
        self.client.tls_set(**tls_config)
        if self.config.get('skip_cert_cn_check', False):
            self.client.tls_insecure_set(True)
        self.logger.info("TLS configured successfully")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to MQTT broker: {self.config.get('host')}:{self.config.get('port')}")
            
            # Resubscribe to topics after reconnection
            for topic in self.subscribed_topics:
                self.client.subscribe(topic)
                self.logger.debug(f"Resubscribed to topic: {topic}")
        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_messages.get(rc, f"Connection refused - code {rc}")
            self.logger.error(f"Failed to connect: {error_msg}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected disconnect from MQTT broker (code: {rc})")
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        self.logger.debug(f"Message received on topic '{topic}': {payload[:100]}")
        
        # Try to parse as JSON
        try:
            payload_dict = json.loads(payload)
        except json.JSONDecodeError:
            payload_dict = {'raw': payload}
        
        # Route message to registered callbacks
        for pattern, callback in self.message_callbacks.items():
            if self._topic_matches(pattern, topic):
                try:
                    callback(topic, payload_dict)
                except Exception as e:
                    self.logger.error(f"Error in message callback for topic '{topic}': {e}")
    
    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if a topic matches a pattern (supports wildcards)"""
        # Simple wildcard matching
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) != len(topic_parts):
            # Check for # wildcard (multi-level)
            if '#' in pattern_parts:
                hash_index = pattern_parts.index('#')
                # Everything before # must match
                return pattern_parts[:hash_index] == topic_parts[:hash_index]
            return False
        
        for p, t in zip(pattern_parts, topic_parts):
            if p == '+':  # Single-level wildcard
                continue
            if p == '#':  # Multi-level wildcard
                return True
            if p != t:
                return False
        
        return True
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection initiated successfully
        """
        try:
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 1883)
            keepalive = self.config.get('keepalive', 60)
            
            self.logger.info(f"Connecting to MQTT broker {host}:{port}...")
            self.client.connect(host, port, keepalive)
            self.client.loop_start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.logger.info("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
    
    def subscribe(self, topic: str, callback: Optional[Callable] = None):
        """
        Subscribe to a topic.
        
        Args:
            topic: MQTT topic to subscribe to (supports wildcards)
            callback: Optional callback function for messages on this topic
        """
        if topic not in self.subscribed_topics:
            self.subscribed_topics.append(topic)
        
        if callback:
            self.register_callback(topic, callback)
        
        if self.connected:
            self.client.subscribe(topic)
            self.logger.info(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str):
        """
        Unsubscribe from a topic.
        
        Args:
            topic: MQTT topic to unsubscribe from
        """
        if topic in self.subscribed_topics:
            self.subscribed_topics.remove(topic)
        
        if topic in self.message_callbacks:
            del self.message_callbacks[topic]
        
        if self.connected:
            self.client.unsubscribe(topic)
            self.logger.info(f"Unsubscribed from topic: {topic}")
    
    def register_callback(self, topic_pattern: str, callback: Callable):
        """
        Register a callback for messages matching a topic pattern.
        
        Args:
            topic_pattern: Topic pattern (can include wildcards)
            callback: Callback function(topic, payload_dict)
        """
        self.message_callbacks[topic_pattern] = callback
        self.logger.debug(f"Registered callback for topic pattern: {topic_pattern}")
    
    def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        """
        Publish a message to a topic.
        
        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON-encoded if dict)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain the message
            
        Returns:
            True if publish was successful
        """
        if not self.connected:
            self.logger.error("Cannot publish: not connected to MQTT broker")
            return False
        
        # Convert payload to JSON if it's a dict
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        
        try:
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published to topic '{topic}': {payload[:100]}")
                return True
            else:
                self.logger.error(f"Failed to publish to topic '{topic}': {result.rc}")
                return False
        except Exception as e:
            self.logger.error(f"Error publishing to topic '{topic}': {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker"""
        return self.connected

