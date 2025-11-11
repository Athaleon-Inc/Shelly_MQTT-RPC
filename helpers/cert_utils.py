"""Certificate utilities for converting and handling certificates/keys"""
import base64
import os
from typing import Optional


def cert_to_pem_string(cert_path: str) -> str:
    """
    Read a certificate or key file and return it as a PEM format string.
    Preserves newlines and formatting.
    
    Args:
        cert_path: Path to the certificate or key file
        
    Returns:
        PEM formatted string with newlines preserved
        
    Raises:
        FileNotFoundError: If the certificate file doesn't exist
    """
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificate file not found: {cert_path}")
    
    with open(cert_path, 'r') as f:
        content = f.read()
    
    # Ensure the content ends with a newline if it doesn't already
    if not content.endswith('\n'):
        content += '\n'
    
    return content


def pem_to_base64(pem_string: str) -> str:
    """
    Convert a PEM formatted string to base64 encoding.
    This can be used if RPC methods require base64 instead of plain PEM.
    
    Args:
        pem_string: PEM formatted certificate or key string
        
    Returns:
        Base64 encoded string
    """
    # Encode the PEM string to bytes, then to base64
    pem_bytes = pem_string.encode('utf-8')
    base64_bytes = base64.b64encode(pem_bytes)
    return base64_bytes.decode('utf-8')


def base64_to_pem(base64_string: str) -> str:
    """
    Convert a base64 encoded string back to PEM format.
    
    Args:
        base64_string: Base64 encoded certificate or key
        
    Returns:
        PEM formatted string
    """
    base64_bytes = base64_string.encode('utf-8')
    pem_bytes = base64.b64decode(base64_bytes)
    return pem_bytes.decode('utf-8')


def validate_pem_format(content: str) -> bool:
    """
    Validate that the content appears to be in PEM format.
    
    Args:
        content: String content to validate
        
    Returns:
        True if content appears to be valid PEM format
    """
    pem_markers = [
        '-----BEGIN CERTIFICATE-----',
        '-----BEGIN RSA PRIVATE KEY-----',
        '-----BEGIN PRIVATE KEY-----',
        '-----BEGIN EC PRIVATE KEY-----',
        '-----BEGIN PUBLIC KEY-----'
    ]
    
    return any(marker in content for marker in pem_markers)


def get_cert_size(cert_path: str) -> int:
    """
    Get the size of a certificate file in bytes.
    
    Args:
        cert_path: Path to the certificate file
        
    Returns:
        Size in bytes
    """
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificate file not found: {cert_path}")
    
    return os.path.getsize(cert_path)

