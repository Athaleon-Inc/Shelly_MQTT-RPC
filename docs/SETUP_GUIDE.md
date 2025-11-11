# Setup Guide

## First Time Setup

### 1. Configure MQTT Broker Settings

Edit `configs/config.json` and update the MQTT settings:

```json
{
  "mqtt": {
    "host": "your-mqtt-broker.com",    // Your MQTT broker hostname
    "port": 8883,                       // MQTT broker port (8883 for TLS, 1883 for plain)
    "use_tls": true,                    // Enable/disable TLS
    "ca_cert": "",                      // Path to CA certificate (optional)
    "client_cert": "",                  // Path to client certificate (optional)
    "client_key": "",                   // Path to client key (optional)
    "username": "your_username",        // MQTT username (if required)
    "password": "your_password",        // MQTT password (if required)
    "client_id": "shelly_manager",      // MQTT client ID
    "skip_cert_cn_check": true,         // Skip certificate CN verification
    "response_timeout": 30              // Response timeout in seconds
  }
}
```

### 2. Certificate Configuration (Optional)

If your MQTT broker requires client certificates:

1. Place your certificates in `configs/certs/`:
   - `ca.crt` - CA certificate
   - `client.crt` - Client certificate
   - `client.key` - Client private key

2. Update `config.json` with certificate paths:
   ```json
   "ca_cert": "configs/certs/ca.crt",
   "client_cert": "configs/certs/client.crt",
   "client_key": "configs/certs/client.key"
   ```

**Note:** If you leave certificate paths empty, the application will still work but will use the system's default CA bundle.

### 3. Run the Application

```bash
./run.sh
```

The first run will:
- Create a virtual environment
- Install dependencies
- Start the application

### 4. Create Your First Session

1. Select "1. Create new session"
2. Enter a session name (e.g., "my_shelly_device")
3. Enter device ID (e.g., "abc123")
4. Confirm or customize the MQTT prefix
5. Add optional notes

### 5. Connect to MQTT Broker

1. Select "4. Connect to MQTT broker"
2. Wait for connection confirmation
3. If connection fails, check logs at `logs/shelly_mqtt_rpc.log`

### 6. Execute RPC Commands

1. Ensure you have a session loaded and MQTT connected
2. Select "6. RPC Operations"
3. Choose the operation you want to perform
4. Review the generated RPC command
5. Confirm to send
6. View the device response

## Common Configuration Scenarios

### Scenario 1: Public MQTT Broker (No TLS)

```json
{
  "mqtt": {
    "host": "mqtt.example.com",
    "port": 1883,
    "use_tls": false,
    "ca_cert": "",
    "client_cert": "",
    "client_key": "",
    "username": "myuser",
    "password": "mypassword",
    "client_id": "shelly_manager"
  }
}
```

### Scenario 2: TLS with System CA Bundle

```json
{
  "mqtt": {
    "host": "mqtt.example.com",
    "port": 8883,
    "use_tls": true,
    "ca_cert": "",              // Empty = use system CA bundle
    "client_cert": "",          // No client authentication
    "client_key": "",
    "username": "myuser",
    "password": "mypassword",
    "client_id": "shelly_manager",
    "skip_cert_cn_check": false
  }
}
```

### Scenario 3: TLS with Client Certificates (Most Secure)

```json
{
  "mqtt": {
    "host": "mqtt.example.com",
    "port": 8883,
    "use_tls": true,
    "ca_cert": "configs/certs/ca.crt",
    "client_cert": "configs/certs/client.crt",
    "client_key": "configs/certs/client.key",
    "username": "",             // May not be needed with cert auth
    "password": "",
    "client_id": "shelly_manager",
    "skip_cert_cn_check": true
  }
}
```

## Uploading Certificates to Shelly Devices

When uploading certificates to your Shelly device:

1. Place device certificates in the session's cert directory:
   - `sessions/{session_name}/certs/ca.crt`
   - `sessions/{session_name}/certs/client.crt`
   - `sessions/{session_name}/certs/client.key`

2. Use the RPC Operations menu:
   - "5. Upload CA certificate" → Uploads the CA cert
   - "6. Upload client certificate" → Uploads client cert
   - "7. Upload client key" → Uploads client private key

3. The application will automatically chunk large files if needed

4. After uploading certificates, update the device's MQTT configuration using "4. Update MQTT configuration"

## Troubleshooting

### Error: "TLS not configured"

**Solution:** Update `configs/config.json` with valid MQTT broker settings. If not using TLS, set `"use_tls": false`.

### Error: "Failed to connect to MQTT broker"

**Possible causes:**
1. Incorrect host or port
2. Firewall blocking connection
3. Invalid credentials
4. Certificate issues

**Solution:** Check `logs/shelly_mqtt_rpc.log` for detailed error messages.

### Error: "Timeout: No response received"

**Possible causes:**
1. Device not connected to MQTT broker
2. Wrong MQTT prefix
3. Device offline

**Solution:** 
- Verify device is online
- Check MQTT prefix matches device configuration
- Increase `response_timeout` in config

### Error: "FileNotFoundError" for certificates

**Solution:** 
- Verify certificate paths in `config.json` are correct
- Check that certificate files exist
- Use absolute paths if relative paths don't work

## Advanced Configuration

### Adjusting Chunk Size

If you're experiencing issues with large certificate uploads, adjust the chunk size:

```json
{
  "rpc": {
    "chunk_size": 1024    // Smaller chunks for slower connections
  }
}
```

### Logging Configuration

Adjust logging verbosity:

```json
{
  "application": {
    "log_level": "DEBUG",    // Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_file": "logs/shelly_mqtt_rpc.log"
  }
}
```

### Custom MQTT Prefix Template

Change the default session MQTT prefix pattern:

```json
{
  "session": {
    "default_mqtt_prefix_template": "shellypro4pm-{device_id}"
  }
}
```

Variables available:
- `{device_id}` - Device ID entered during session creation

## Getting Help

1. Check the logs: `logs/shelly_mqtt_rpc.log`
2. Review this guide and README.md
3. Verify your MQTT broker is accessible
4. Test MQTT connection with another tool (e.g., mosquitto_pub/sub)

## Security Best Practices

1. **Protect your config file** - It contains credentials
2. **Use TLS** - Always use TLS in production
3. **Secure certificates** - Set proper file permissions (600 or 400)
4. **Regular updates** - Keep certificates up to date
5. **Use client certificates** - More secure than username/password
6. **Restrict access** - Limit who can access the sessions directory

