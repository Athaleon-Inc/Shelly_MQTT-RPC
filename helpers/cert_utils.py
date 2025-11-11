"""Certificate utilities for converting and handling certificates/keys"""
import base64
import os
from typing import List


def cert_to_pem_string(cert_path: str) -> str:
    """
    Read a certificate or key file and return its payload string stripped of
    PEM header/footer markers. The resulting string contains only the base64
    body, suitable for Shelly RPC uploads.
    
    Args:
        cert_path: Path to the certificate or key file
        
    Returns:
        String containing the concatenated base64 body of the PEM content
        
    Raises:
        FileNotFoundError: If the certificate file doesn't exist
        ValueError: If no PEM payload could be extracted
    """
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificate file not found: {cert_path}")
    
    with open(cert_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    payload = strip_pem_boundaries(content)
    
    if not payload:
        raise ValueError(f"Certificate file contains no PEM data: {cert_path}")
    
    return payload


def strip_pem_boundaries(content: str) -> str:
    """
    Remove PEM BEGIN/END markers and whitespace, returning only the base64 body.
    Supports multiple concatenated PEM blocks (e.g., certificate chains).
    
    Args:
        content: Raw PEM string, potentially containing multiple blocks
        
    Returns:
        Concatenated base64 payload string without markers or whitespace
    """
    blocks: List[str] = []
    collecting = False
    current: List[str] = []
    
    for line in content.splitlines():
        stripped = line.strip()
        
        if not stripped:
            continue
        
        if stripped.startswith("-----BEGIN "):
            collecting = True
            current = []
            continue
        
        if stripped.startswith("-----END "):
            if collecting and current:
                blocks.append("".join(current))
            collecting = False
            current = []
            continue
        
        if collecting:
            current.append(stripped)
    
    if collecting:
        raise ValueError("Incomplete PEM content: missing END marker")
    
    return "".join(blocks)


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


def read_pem_file(cert_path: str) -> str:
    """
    Read a PEM file (certificate or key) and return its full textual contents
    without stripping headers, footers, or whitespace.
    
    Args:
        cert_path: Path to the certificate or key file
        
    Returns:
        Raw PEM text as read from disk
    """
    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificate file not found: {cert_path}")
    
    with open(cert_path, 'r', encoding='utf-8') as f:
        return f.read()

