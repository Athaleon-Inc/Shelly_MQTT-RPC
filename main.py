"""
Shelly MQTT-RPC Manager
Main entry point for the application
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config_loader import ConfigLoader
from core.logger import LoggerSetup
from mqtt.client import MQTTClient
from rpc.response_handler import RPCResponseHandler
from rpc.executor import RPCExecutor
from ui.menu import MainMenu
from helpers.rpc_command_saver import clear_temp_rpc_commands


def main():
    """Main application entry point"""
    
    # Load configuration
    try:
        config_loader = ConfigLoader("configs/config.json")
        config = config_loader.load()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Setup logging
    app_config = config.get('application', {})
    log_level = app_config.get('log_level', 'INFO')
    log_file = app_config.get('log_file', 'logs/shelly_mqtt_rpc.log')
    
    logger = LoggerSetup.setup(log_level=log_level, log_file=log_file)
    logger.info("=" * 60)
    logger.info("Shelly MQTT-RPC Manager Starting")
    logger.info("=" * 60)
    
    # Clear temporary RPC commands from previous run
    try:
        clear_temp_rpc_commands()
        logger.info("Cleared temporary RPC command files")
    except Exception as e:
        logger.warning(f"Failed to clear temp RPC commands: {e}")
    
    # Initialize MQTT client (don't connect yet)
    mqtt_config = config.get('mqtt', {})
    mqtt_client = MQTTClient(mqtt_config, logger)
    logger.info("MQTT client initialized")
    
    # Initialize RPC response handler
    response_handler = RPCResponseHandler(logger)
    logger.info("RPC response handler initialized")
    
    # Initialize RPC executor
    rpc_executor = RPCExecutor(mqtt_client, response_handler, config, logger)
    logger.info("RPC executor initialized")
    
    # Create main menu
    main_menu = MainMenu(config, mqtt_client, rpc_executor, logger)
    
    try:
        # Run main menu loop
        logger.info("Starting main menu")
        main_menu.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nShutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main application: {e}", exc_info=True)
        print(f"\n\nFatal error: {e}")
        print("Check logs for details.")
    finally:
        # Cleanup
        logger.info("Performing cleanup")
        
        # Disconnect MQTT if connected
        if mqtt_client.is_connected():
            logger.info("Disconnecting from MQTT broker")
            mqtt_client.disconnect()
        
        logger.info("Application shutdown complete")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()

