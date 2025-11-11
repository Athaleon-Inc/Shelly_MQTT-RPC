"""MQTT publisher utilities for RPC commands"""
from typing import Dict, Any, Optional
import logging
from mqtt.client import MQTTClient


class RPCPublisher:
    """Handles publishing RPC commands to Shelly devices via MQTT"""
    
    def __init__(self, mqtt_client: MQTTClient, logger: Optional[logging.Logger] = None):
        """
        Initialize RPC publisher.
        
        Args:
            mqtt_client: MQTT client instance
            logger: Logger instance
        """
        self.mqtt_client = mqtt_client
        self.logger = logger or logging.getLogger("shelly_mqtt_rpc.publisher")
    
    def publish_rpc(self, mqtt_prefix: str, payload: Dict[str, Any], qos: int = 1) -> Optional[int]:
        """
        Publish an RPC command to a Shelly device.
        
        Args:
            mqtt_prefix: MQTT prefix for the device (e.g., 'shellypro4pm-deviceid')
            payload: RPC payload dictionary
            qos: Quality of Service level
            
        Returns:
            Message ID from the payload if successful, None otherwise
        """
        # Construct RPC topic
        topic = f"{mqtt_prefix}/rpc"
        
        # Log the RPC call
        method = payload.get('method', 'unknown')
        msg_id = payload.get('id', 0)
        self.logger.info(f"Publishing RPC command: {method} (ID: {msg_id}) to {topic}")
        
        # Publish message
        success = self.mqtt_client.publish(topic, payload, qos=qos)
        
        if success:
            return msg_id
        else:
            self.logger.error(f"Failed to publish RPC command to {topic}")
            return None
    
    def publish_multiple_rpc(self, mqtt_prefix: str, payloads: list[Dict[str, Any]], 
                           qos: int = 1, delay: float = 0.1) -> list[Optional[int]]:
        """
        Publish multiple RPC commands sequentially (useful for chunked uploads).
        
        Args:
            mqtt_prefix: MQTT prefix for the device
            payloads: List of RPC payload dictionaries
            qos: Quality of Service level
            delay: Delay between messages in seconds
            
        Returns:
            List of message IDs (or None for failed publishes)
        """
        import time
        
        message_ids = []
        
        for i, payload in enumerate(payloads):
            msg_id = self.publish_rpc(mqtt_prefix, payload, qos)
            message_ids.append(msg_id)
            
            # Add delay between messages (except for the last one)
            if i < len(payloads) - 1 and delay > 0:
                time.sleep(delay)
        
        return message_ids

