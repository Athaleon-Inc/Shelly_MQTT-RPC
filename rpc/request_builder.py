"""RPC request builders for Shelly device commands"""
from typing import Dict, Any, Optional, List


class RPCRequestBuilder:
    """Builder for Shelly RPC request payloads"""
    
    @staticmethod
    def build_rpc_payload(msg_id: int, src: str, method: str, 
                         params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build a basic RPC payload structure.
        
        Args:
            msg_id: Message ID for tracking responses
            src: Source identifier (e.g., 'sunio_app')
            method: RPC method name
            params: Optional parameters dictionary
            
        Returns:
            RPC payload dictionary
        """
        payload = {
            "id": msg_id,
            "src": src,
            "method": method
        }
        
        if params is not None:
            payload["params"] = params
        
        return payload
    
    @staticmethod
    def build_status_request(msg_id: int, src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a status request (Shelly.GetStatus).
        
        Args:
            msg_id: Message ID
            src: Source identifier
            
        Returns:
            RPC payload for status request
        """
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.GetStatus")
    
    @staticmethod
    def build_device_info_request(msg_id: int, src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a device info request (Shelly.GetDeviceInfo).
        
        Args:
            msg_id: Message ID
            src: Source identifier
            
        Returns:
            RPC payload for device info request
        """
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.GetDeviceInfo")
    
    @staticmethod
    def build_reboot_request(msg_id: int, src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a reboot request (Shelly.Reboot).
        
        Args:
            msg_id: Message ID
            src: Source identifier
            
        Returns:
            RPC payload for reboot request
        """
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.Reboot")
    
    @staticmethod
    def build_mqtt_config_update(msg_id: int, config_dict: Dict[str, Any], 
                                src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build an MQTT configuration update request (MQTT.SetConfig).
        
        Args:
            msg_id: Message ID
            config_dict: MQTT configuration dictionary
            src: Source identifier
            
        Returns:
            RPC payload for MQTT config update
        """
        params = {
            "config": config_dict
        }
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "MQTT.SetConfig", params)
    
    @staticmethod
    def build_get_mqtt_config_request(msg_id: int, src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build an MQTT configuration get request (MQTT.GetConfig).
        
        Args:
            msg_id: Message ID
            src: Source identifier
            
        Returns:
            RPC payload for getting MQTT config
        """
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "MQTT.GetConfig")
    
    @staticmethod
    def build_put_user_ca(msg_id: int, cert_data: str, append: bool = False,
                         src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a user CA certificate upload request (Shelly.PutUserCA).
        
        Args:
            msg_id: Message ID
            cert_data: Certificate data (PEM format string)
            append: Whether to append to existing certificate
            src: Source identifier
            
        Returns:
            RPC payload for CA certificate upload
        """
        params = {
            "data": cert_data,
            "append": append
        }
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.PutUserCA", params)
    
    @staticmethod
    def build_put_tls_client_cert(msg_id: int, cert_data: str, append: bool = False,
                                 src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a TLS client certificate upload request (Shelly.PutTLSClientCert).
        
        Args:
            msg_id: Message ID
            cert_data: Certificate data (PEM format string)
            append: Whether to append to existing certificate
            src: Source identifier
            
        Returns:
            RPC payload for client certificate upload
        """
        params = {
            "data": cert_data,
            "append": append
        }
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.PutTLSClientCert", params)
    
    @staticmethod
    def build_put_tls_client_key(msg_id: int, key_data: str, append: bool = False,
                                src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a TLS client key upload request (Shelly.PutTLSClientKey).
        
        Args:
            msg_id: Message ID
            key_data: Key data (PEM format string)
            append: Whether to append to existing key
            src: Source identifier
            
        Returns:
            RPC payload for client key upload
        """
        params = {
            "data": key_data,
            "append": append
        }
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.PutTLSClientKey", params)
    
    @staticmethod
    def build_chunked_upload_requests(msg_id_start: int, method: str, 
                                    chunks: List[Dict[str, Any]], 
                                    src: str = "sunio_app") -> List[Dict[str, Any]]:
        """
        Build multiple RPC requests for chunked data upload.
        
        Args:
            msg_id_start: Starting message ID
            method: RPC method name (e.g., 'Shelly.PutUserCA')
            chunks: List of chunk dictionaries from chunker
            src: Source identifier
            
        Returns:
            List of RPC payloads for chunked upload
        """
        payloads = []
        
        for i, chunk_info in enumerate(chunks):
            msg_id = msg_id_start + i
            params = {
                "data": chunk_info['chunk'],
                "append": chunk_info['append']
            }
            payload = RPCRequestBuilder.build_rpc_payload(msg_id, src, method, params)
            payloads.append(payload)
        
        return payloads
    
    @staticmethod
    def build_reset_config_request(msg_id: int, src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a factory reset request (Shelly.FactoryReset).
        
        Args:
            msg_id: Message ID
            src: Source identifier
            
        Returns:
            RPC payload for factory reset
        """
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.FactoryReset")
    
    @staticmethod
    def build_update_request(msg_id: int, stage: str = "stable", 
                           src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a firmware update request (Shelly.Update).
        
        Args:
            msg_id: Message ID
            stage: Update stage ('stable' or 'beta')
            src: Source identifier
            
        Returns:
            RPC payload for firmware update
        """
        params = {
            "stage": stage
        }
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.Update", params)
    
    @staticmethod
    def build_check_for_update_request(msg_id: int, src: str = "sunio_app") -> Dict[str, Any]:
        """
        Build a check for update request (Shelly.CheckForUpdate).
        
        Args:
            msg_id: Message ID
            src: Source identifier
            
        Returns:
            RPC payload for checking updates
        """
        return RPCRequestBuilder.build_rpc_payload(msg_id, src, "Shelly.CheckForUpdate")

