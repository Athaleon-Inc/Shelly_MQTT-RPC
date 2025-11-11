"""RPC command saving utilities for storing generated commands"""
import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Union


def clear_temp_rpc_commands(temp_dir: str = "temp/rpc_commands"):
    """
    Clear all temporary RPC command files.
    Should be called on application startup.
    
    Args:
        temp_dir: Directory containing temporary RPC command files
    """
    if os.path.exists(temp_dir):
        # Remove all files in the directory
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    else:
        # Create the directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)


def save_rpc_command(session_name: str, method_name: str, 
                     payloads: Union[Dict[str, Any], List[Dict[str, Any]]], 
                     temp_dir: str = "temp/rpc_commands") -> str:
    """
    Save RPC command payload(s) to a JSON file.
    
    Args:
        session_name: Name of the session
        method_name: RPC method name (e.g., 'Shelly.PutUserCA')
        payloads: Single payload dict or list of payload dicts (for chunked commands)
        temp_dir: Directory to save command files
        
    Returns:
        Path to the saved file
    """
    # Ensure temp directory exists
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize method name for filename
    safe_method_name = method_name.replace('.', '_').replace('/', '_')
    filename = f"{session_name}_{safe_method_name}_{timestamp}.json"
    filepath = os.path.join(temp_dir, filename)
    
    # Prepare data structure
    if isinstance(payloads, dict):
        payloads = [payloads]  # Convert single payload to list
    
    data = {
        'session': session_name,
        'method': method_name,
        'timestamp': datetime.now().isoformat(),
        'payload_count': len(payloads),
        'payloads': payloads
    }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def load_rpc_command(filepath: str) -> Dict[str, Any]:
    """
    Load RPC command from a saved file.
    
    Args:
        filepath: Path to the RPC command file
        
    Returns:
        Dictionary containing the command data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"RPC command file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)


def list_rpc_commands(session_name: str = None, temp_dir: str = "temp/rpc_commands") -> List[str]:
    """
    List all saved RPC command files, optionally filtered by session.
    
    Args:
        session_name: Optional session name to filter by
        temp_dir: Directory containing RPC command files
        
    Returns:
        List of file paths
    """
    if not os.path.exists(temp_dir):
        return []
    
    files = []
    for filename in os.listdir(temp_dir):
        if filename.endswith('.json'):
            if session_name is None or filename.startswith(f"{session_name}_"):
                files.append(os.path.join(temp_dir, filename))
    
    return sorted(files, reverse=True)  # Most recent first


def get_rpc_command_summary(filepath: str) -> Dict[str, Any]:
    """
    Get a summary of an RPC command file without loading full payloads.
    
    Args:
        filepath: Path to the RPC command file
        
    Returns:
        Dictionary with command summary
    """
    data = load_rpc_command(filepath)
    
    return {
        'filepath': filepath,
        'session': data.get('session'),
        'method': data.get('method'),
        'timestamp': data.get('timestamp'),
        'payload_count': data.get('payload_count'),
        'filename': os.path.basename(filepath)
    }

