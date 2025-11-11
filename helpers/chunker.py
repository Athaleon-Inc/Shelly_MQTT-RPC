"""Data chunking utilities for splitting large payloads"""
from typing import List, Dict, Any, Union


def _ensure_bytes(data: Union[str, bytes]) -> bytes:
    """
    Convert incoming data (str or bytes) to raw bytes without loss.
    
    Args:
        data: Data as string or bytes
        
    Returns:
        Raw bytes representation
    """
    if isinstance(data, bytes):
        return data
    # UTF-8 maintains PEM/base64 data while supporting text inputs
    return data.encode('utf-8')


def chunk_data(data: Union[str, bytes], max_size: int) -> List[Dict[str, Any]]:
    """
    Divide large data into manageable chunks.
    
    Args:
        data: The data string to chunk
        max_size: Maximum size per chunk in bytes
        
    Returns:
        List of chunk dictionaries containing:
        - chunk: The data chunk
        - index: 0-based chunk index
        - total: Total number of chunks
        - is_first: True if this is the first chunk
        - is_last: True if this is the last chunk
        - append: False for first chunk, True for subsequent chunks
    """
    if data in (None, b"", ""):
        return []
    
    # If data fits in one chunk, return it as a single chunk
    data_bytes = _ensure_bytes(data)
    data_size = len(data_bytes)
    if data_size <= max_size:
        return [{
            'chunk': data_bytes.decode('latin-1'),
            'index': 0,
            'total': 1,
            'is_first': True,
            'is_last': True,
            'append': False,
            'size': data_size
        }]
    
    # Split data into chunks
    chunks: List[Dict[str, Any]] = []
    offset = 0
    chunk_index = 0
    
    while offset < len(data_bytes):
        # Get the next chunk
        chunk_bytes = data_bytes[offset:offset + max_size]
        chunk_str = chunk_bytes.decode('latin-1')
        
        chunks.append({
            'chunk': chunk_str,
            'index': chunk_index,
            'size': len(chunk_bytes)
        })
        
        offset += len(chunk_bytes)
        chunk_index += 1
    
    # Add metadata to chunks
    total_chunks = len(chunks)
    for i, chunk_info in enumerate(chunks):
        chunk_info['total'] = total_chunks
        chunk_info['is_first'] = (i == 0)
        chunk_info['is_last'] = (i == total_chunks - 1)
        chunk_info['append'] = (i > 0)  # First chunk should not append, rest should
    
    return chunks


def calculate_chunk_count(data: Union[str, bytes], max_size: int) -> int:
    """
    Calculate how many chunks will be needed for the data.
    
    Args:
        data: The data string to chunk
        max_size: Maximum size per chunk in bytes
        
    Returns:
        Number of chunks needed
    """
    if data in (None, b"", ""):
        return 0
    
    data_size = len(_ensure_bytes(data))
    if data_size <= max_size:
        return 1
    
    return (data_size + max_size - 1) // max_size  # Ceiling division


def get_chunk_info(data: Union[str, bytes], max_size: int) -> Dict[str, Any]:
    """
    Get information about chunking requirements without actually chunking.
    
    Args:
        data: The data string to analyze
        max_size: Maximum size per chunk in bytes
        
    Returns:
        Dictionary with chunking information:
        - total_size: Total size in bytes
        - chunk_count: Number of chunks needed
        - needs_chunking: True if chunking is required
        - avg_chunk_size: Average chunk size
    """
    if data in (None, b"", ""):
        return {
            'total_size': 0,
            'chunk_count': 0,
            'needs_chunking': False,
            'avg_chunk_size': 0
        }
    
    total_size = len(_ensure_bytes(data))
    chunk_count = calculate_chunk_count(data, max_size)
    
    return {
        'total_size': total_size,
        'chunk_count': chunk_count,
        'needs_chunking': chunk_count > 1,
        'avg_chunk_size': total_size // chunk_count if chunk_count > 0 else 0
    }

