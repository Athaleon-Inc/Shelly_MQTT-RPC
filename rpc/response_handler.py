"""RPC response handler for processing device responses"""
from typing import Dict, Any, Optional, Callable
import logging
import time
import threading


class RPCResponse:
    """Container for RPC response data"""
    
    def __init__(self, msg_id: int, success: bool, result: Any = None, 
                 error: Optional[Dict[str, Any]] = None, raw: Optional[Dict[str, Any]] = None):
        self.msg_id = msg_id
        self.success = success
        self.result = result
        self.error = error
        self.raw = raw
        self.timestamp = time.time()
    
    def __repr__(self):
        if self.success:
            return f"RPCResponse(id={self.msg_id}, success=True, result={self.result})"
        else:
            return f"RPCResponse(id={self.msg_id}, success=False, error={self.error})"


class RPCResponseHandler:
    """Handles RPC responses from Shelly devices"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize response handler.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("shelly_mqtt_rpc.response")
        
        # Response tracking
        self.pending_responses: Dict[int, threading.Event] = {}
        self.responses: Dict[int, RPCResponse] = {}
        self.response_callbacks: Dict[int, Callable] = {}
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def register_request(self, msg_id: int, callback: Optional[Callable] = None):
        """
        Register a request for response tracking.
        
        Args:
            msg_id: Message ID to track
            callback: Optional callback function to call when response arrives
        """
        with self.lock:
            self.pending_responses[msg_id] = threading.Event()
            if callback:
                self.response_callbacks[msg_id] = callback
        
        self.logger.debug(f"Registered request ID: {msg_id}")
    
    def handle_message(self, topic: str, payload: Dict[str, Any]):
        """
        Handle an incoming MQTT message as a potential RPC response.
        
        Args:
            topic: MQTT topic
            payload: Message payload dictionary
        """
        # Check if this is an RPC response
        if 'id' not in payload:
            self.logger.debug(f"Message on topic '{topic}' is not an RPC response (no 'id' field)")
            return
        
        msg_id = payload.get('id')
        
        # Check if we're expecting this response
        if msg_id not in self.pending_responses:
            self.logger.debug(f"Received unexpected response with ID: {msg_id}")
            return
        
        # Parse response
        response = self._parse_response(payload)
        
        with self.lock:
            self.responses[msg_id] = response
            self.pending_responses[msg_id].set()
            
            # Call callback if registered
            if msg_id in self.response_callbacks:
                callback = self.response_callbacks[msg_id]
                try:
                    callback(response)
                except Exception as e:
                    self.logger.error(f"Error in response callback for ID {msg_id}: {e}")
        
        self.logger.info(f"Received RPC response for ID {msg_id}: success={response.success}")
    
    def _parse_response(self, payload: Dict[str, Any]) -> RPCResponse:
        """
        Parse an RPC response payload.
        
        Args:
            payload: Response payload dictionary
            
        Returns:
            RPCResponse object
        """
        msg_id = payload.get('id', 0)
        
        # Check for error
        if 'error' in payload:
            error = payload['error']
            return RPCResponse(
                msg_id=msg_id,
                success=False,
                error=error,
                raw=payload
            )
        
        # Success response
        result = payload.get('result', payload.get('src'))
        return RPCResponse(
            msg_id=msg_id,
            success=True,
            result=result,
            raw=payload
        )
    
    def wait_for_response(self, msg_id: int, timeout: float = 30.0) -> Optional[RPCResponse]:
        """
        Wait for a response to a specific request.
        
        Args:
            msg_id: Message ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            RPCResponse if received, None if timeout
        """
        if msg_id not in self.pending_responses:
            self.logger.warning(f"Request ID {msg_id} not registered")
            return None
        
        # Wait for response
        event = self.pending_responses[msg_id]
        received = event.wait(timeout)
        
        if not received:
            self.logger.warning(f"Timeout waiting for response to ID {msg_id}")
            with self.lock:
                # Cleanup
                del self.pending_responses[msg_id]
                if msg_id in self.response_callbacks:
                    del self.response_callbacks[msg_id]
            return None
        
        # Get response
        with self.lock:
            response = self.responses.get(msg_id)
            # Cleanup
            del self.pending_responses[msg_id]
            if msg_id in self.response_callbacks:
                del self.response_callbacks[msg_id]
            if msg_id in self.responses:
                del self.responses[msg_id]
        
        return response
    
    def cancel_request(self, msg_id: int):
        """
        Cancel waiting for a request response.
        
        Args:
            msg_id: Message ID to cancel
        """
        with self.lock:
            if msg_id in self.pending_responses:
                del self.pending_responses[msg_id]
            if msg_id in self.response_callbacks:
                del self.response_callbacks[msg_id]
            if msg_id in self.responses:
                del self.responses[msg_id]
        
        self.logger.debug(f"Cancelled request ID: {msg_id}")

