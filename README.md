# Shelly MQTT-RPC Manager

A comprehensive Python application for managing Shelly device configurations through MQTT-backed RPC calls. This tool is designed for advanced configuration tasks that are not available through Shelly's cloud APIs, such as certificate rotation, MQTT TLS credential management, and remote deployments.

## Features

- **Session Management**: Create and manage multiple device configurations with isolated certificate directories
- **MQTT Integration**: Secure MQTT communication with TLS support
- **RPC Operations**: Execute various Shelly RPC commands including:
  - Device status and information retrieval
  - MQTT configuration updates
  - Certificate management (CA, client cert, client key)
  - Device reboot
  - Firmware update checks
- **Automatic Chunking**: Large certificates are automatically split into manageable chunks for MQTT transmission
- **Command Persistence**: All RPC commands are saved before sending for review and auditing
- **Interactive Console UI**: User-friendly terminal interface with rich formatting
- **Response Tracking**: Correlate RPC requests with device responses

## Project Structure

```
Shelly_MQTT-RPC/
├── configs/              # Configuration files and root certificates
│   ├── config.json       # Main application configuration
│   └── certs/            # Root certificate directory
├── sessions/             # Session-specific folders
│   └── {session_name}/
│       ├── config.json   # Session metadata
│       └── certs/        # Session certificates
├── core/                 # Core functionality
│   ├── config_loader.py  # Configuration loading and validation
│   ├── logger.py         # Logging setup with Rich
│   └── session.py        # Session management
├── helpers/              # Utility functions
│   ├── cert_utils.py     # Certificate conversion utilities
│   ├── chunker.py        # Data chunking for large payloads
│   └── rpc_command_saver.py  # RPC command persistence
├── mqtt/                 # MQTT client and publishing
│   ├── client.py         # MQTT client with TLS support
│   └── publisher.py      # RPC publishing utilities
├── rpc/                  # RPC system
│   ├── request_builder.py    # RPC payload builders
│   ├── response_handler.py   # Response tracking and parsing
│   └── executor.py       # RPC execution workflow
├── ui/                   # Console user interface
│   ├── panels.py         # Rich panels for display
│   ├── prompts.py        # Input prompts with validation
│   ├── menu.py           # Main menu
│   └── session_menu.py   # Session-specific RPC operations menu
├── temp/                 # Temporary files
│   └── rpc_commands/     # RPC command JSON files (cleared on startup)
├── main.py               # Application entry point
├── run.sh                # Startup script
└── requirements.txt      # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository

2. Make the run script executable:
   ```bash
   chmod +x run.sh
   ```

3. Run the application (the script will create a virtual environment and install dependencies):
   ```bash
   ./run.sh
   ```

Alternatively, manual setup:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Configuration

### Main Configuration (configs/config.json)

```json
{
  "mqtt": {
    "host": "mqtt.example.com",
    "port": 8883,
    "use_tls": true,
    "ca_cert": "configs/certs/ca.crt",
    "client_cert": "configs/certs/client.crt",
    "client_key": "configs/certs/client.key",
    "username": "",
    "password": "",
    "client_id": "shelly_manager",
    "skip_cert_cn_check": true,
    "response_timeout": 30
  },
  "rpc": {
    "chunk_size": 2048,
    "default_src": "sunio_app"
  },
  "session": {
    "default_mqtt_prefix_template": "shellypro4pm-{device_id}"
  },
  "application": {
    "log_level": "INFO",
    "log_file": "logs/shelly_mqtt_rpc.log",
    "console_theme": "monokai"
  }
}
```

### Session Configuration

Each session is stored in `sessions/{session_name}/config.json`:

```json
{
  "name": "device_name",
  "device_id": "deviceid123",
  "mqtt_prefix": "shellypro4pm-deviceid123",
  "created_at": "2025-11-11T12:00:00",
  "last_used": "2025-11-11T12:30:00",
  "notes": "Production device",
  "cert_dir": "sessions/device_name/certs"
}
```

## Usage

### Starting the Application

```bash
./run.sh
```

### Creating a Session

1. Select "Create new session" from the main menu
2. Enter session name (alphanumeric, hyphens, underscores)
3. Enter device ID
4. Confirm or customize MQTT prefix
5. Add optional notes

### Connecting to MQTT Broker

1. Select "Connect to MQTT broker" from the main menu
2. Wait for connection confirmation

### Executing RPC Commands

1. Load a session
2. Connect to MQTT broker
3. Select "RPC Operations"
4. Choose desired operation
5. Review generated RPC payload
6. Confirm to send
7. View device response

### Certificate Upload Workflow

When uploading certificates:

1. The application reads the certificate file
2. Header/footer PEM markers (`-----BEGIN/END ...-----`) are stripped automatically, leaving only the base64 payload expected by Shelly RPC
2. Checks size against configured chunk limit
3. Automatically splits into chunks if needed
4. Displays all chunks for review
5. Sends chunks sequentially on confirmation
6. Each chunk uses `append: false` for first, `append: true` for subsequent chunks

#### Manual Verification Checklist

- Export the desired certificate chain in PEM format (one or more concatenated certificates).
- Use the application to upload the file to a test Shelly device; confirm the previewed payload omits the PEM boundary lines.
- After upload, verify on the device (e.g., via Shelly web UI or `Shelly.GetStatus`) that the certificate was stored and is valid.
- If the upload fails, inspect the saved JSON command in `temp/rpc_commands/` to confirm the payload only contains base64 characters and rerun with adjusted chunk size if needed.

## RPC Methods Supported

- `Shelly.GetStatus` - Get device status
- `Shelly.GetDeviceInfo` - Get device information
- `Shelly.Reboot` - Reboot device
- `Shelly.CheckForUpdate` - Check for firmware updates
- `MQTT.GetConfig` - Get MQTT configuration
- `MQTT.SetConfig` - Update MQTT configuration
- `Shelly.PutUserCA` - Upload CA certificate
- `Shelly.PutTLSClientCert` - Upload client certificate
- `Shelly.PutTLSClientKey` - Upload client key

## RPC Command Storage

All RPC commands are saved to `temp/rpc_commands/` before sending:

- Filename format: `{session}_{method}_{timestamp}.json`
- Contains all payload(s) including chunked variants
- Cleared automatically on application startup
- Useful for debugging and audit trails

## Logging

Logs are written to:
- Console: INFO level and above with rich formatting
- File: All levels to `logs/shelly_mqtt_rpc.log` with rotation

## Troubleshooting

### Connection Issues

- Verify MQTT broker settings in `configs/config.json`
- Check TLS certificates are valid and accessible
- Review logs for detailed error messages

### Certificate Upload Failures

- Ensure certificate files are in PEM format
- Check file permissions
- Verify chunk size is appropriate for your MQTT broker

### Response Timeouts

- Increase `response_timeout` in config
- Check device is online and connected to MQTT broker
- Verify MQTT topic subscriptions match the `src` field

## Development

### Adding New RPC Methods

1. Add method builder in `rpc/request_builder.py`
2. Add menu option in `ui/session_menu.py`
3. Implement handler method in `ui/session_menu.py`

### Custom Certificate Handling

Modify `helpers/cert_utils.py` for different certificate formats or encoding requirements.

## Security Notes

- Keep `configs/config.json` secure (contains MQTT credentials)
- Store certificates with appropriate file permissions
- Use TLS for MQTT connections in production
- Review RPC payloads before sending to devices

## License

[Specify your license here]

## Credits

Developed for managing Shelly devices in advanced deployment scenarios where cloud APIs are insufficient.

