# Cursor Rules – Shelly MQTT-RPC Manager

## Project Purpose
- Manage Shelly device configuration through MQTT-backed RPC calls when cloud APIs lack required controls.
- Automate certificate rotation and advanced local-only configuration changes (e.g., MQTT TLS credentials, remote deployments).
- Centralize session-aware access to device-specific assets such as certificate bundles and MQTT prefixes.

## High-Level Structure
- `core/` handles logging, configuration bootstrap, and a `Session` domain model for lifecycle tasks (create/load, persist metadata, manage per-session certificate directories).
- `configs/` stores `config.json`, a root certificates directory, and session sub-folders containing device-specific assets.
- `helpers/` provides certificate conversion utilities (Base64 ↔ text for RPC payloads), payload chunking, and helpers for manipulating session objects.
- `mqtt/` encapsulates MQTT client setup, broker connectivity, and message routing based on configuration (`host`, `port`, TLS flags, CA/client certs, credentials, client ID).
- `rpc/` defines request/response handling, method-specific helpers (status, reset, MQTT settings update, certificate upload), and aligns MQTT topics with `{MQTT_PREFIX}/rpc`.

## Runtime & Tooling Expectations
- `run.sh` is the canonical entry point: create/refresh the virtual environment, install `requirements.txt`, activate the venv, and launch the console app.
- Keep `requirements.txt` in sync with Python dependencies (e.g., `prompt_toolkit`, `rich`, MQTT libraries); update it whenever code introduces new imports.
- Tests and ad-hoc scripts must be executed with the virtual environment activated (either via `run.sh` or a companion test runner script) to ensure consistent interpreter state.

## Console UI Guidelines
- Build the terminal experience with `prompt_toolkit` for structured input workflows and `rich` for styled output panels/log streams.
- Centralize TUI coordination (menus, refresh loops, key bindings) in a dedicated module under `core/` or `ui/` to keep it reusable and isolated from transport logic.
- Provide menu actions for session creation, session loading, configuration inspection, MQTT connection status, and RPC operations (with periodic refresh support).
- Design RPC response handlers to surface machine-readable data that the TUI can render without embedding formatting in transport code.

## RPC Messaging Requirements
- Every Shelly RPC payload is JSON containing `id`, `src`, `method`, and optional `params`.
- Persist the `id` to match asynchronous responses from the broker.
- Example certificate update:

Topic: {MQTT_PREFIX}/rpc
```json
{
  "id": 1,
  "src": "sunio_app",
  "method": "Shelly.PutUserCA",
  "params": {
    "data": "BASE64_ENCODED_CA_CERT"
  }
}
```

- Example reboot command:

Topic: {MQTT_PREFIX}/rpc
```json
{
  "id": 5,
  "src": "sunio_app",
  "method": "Shelly.Reboot"
}
```

- Examplple update MQTT connection setting

Topic: {MQTT_PREFIX}/rpc
```json
{
  "id": 301,
  "src": "sunio_app",
  "method": "MQTT.SetConfig",
  "params": {
    "config": {
      "enable": true,
      "server": "mqtts://mqtt.sunio.cz:8883",
      "client_id": "shelly_main_meter_domov_253",
      "user": "tvoje_uživatelské_jméno",
      "pass": "tvoje_heslo",
      "ssl_ca": "*",
      "use_client_cert": true,
      "skip_cert_cn_check": true
    }
  }
}
```
```