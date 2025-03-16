import asyncio
import logging
from typing import Optional, Callable
from bleak import BleakClient

from movella.types import QuaternionData
from movella.parser import parse_quaternion_data

# UUIDs for Movella DOT
CONTROL_CHARACTERISTIC_UUID = "15172001-4947-11e9-8646-d663bd873d93"
MEDIUM_PAYLOAD_CHARACTERISTIC_UUID = "15172003-4947-11e9-8646-d663bd873d93"

class MovellaDotClient:
    def __init__(self, address: str, callback: Optional[Callable[[QuaternionData], None]] = None):
        """
        Initialize MovellaDotClient
        
        Args:
            address: Bluetooth address of the Movella DOT device
            callback: Function to call when quaternion data is received
        """
        self.address = address
        self.client: Optional[BleakClient] = None
        self.callback = callback or self._default_callback
    
    def _default_callback(self, data: QuaternionData) -> None:
        """Default callback that prints the quaternion data"""
        print(f"Quaternion: {data.quaternion}")
    
    def notification_callback(self, sender, data: bytes) -> None:
        """
        Callback for BLE notifications that parses and processes quaternion data
        
        Args:
            sender: BLE characteristic that sent the data
            data: Raw bytes received from the BLE device
        """
        parsed_data = parse_quaternion_data(data)
        if parsed_data is not None:
            self.callback(parsed_data)
    
    async def connect(self) -> bool:
        try:
            self.client = BleakClient(self.address)
            await self.client.connect()
            logging.info(f"Connection status: {self.client.is_connected}")
            
            services = self.client.services
            for service in services:
                logging.debug(f"Service: {service.uuid}")
                for char in service.characteristics:
                    logging.debug(f"  Characteristic: {char.uuid}, Properties: {char.properties}")
                    
            return self.client.is_connected
            
        except Exception as e:
            logging.error(f"Connection error: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self.client and self.client.is_connected:
            await self.client.disconnect()
    
    async def start_quaternion_stream(self, duration_seconds: float = 5.0) -> None:
        if not self.client or not self.client.is_connected:
            logging.error("Not connected to device")
            return
        
        try:
            # Stopping any ongoing measurement first
            stop_command = bytearray([0x01, 0x00, 0x00])
            await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
            await asyncio.sleep(0.5)

            # Subscribe to quaternion data notifications
            await self.client.start_notify(MEDIUM_PAYLOAD_CHARACTERISTIC_UUID, self.notification_callback)
            logging.info("Successfully subscribed to quaternion data notifications")
            await asyncio.sleep(0.1)
            
            # Set measurement mode to Extended (Quaternion) - 0x02
            control_command = bytearray([0x01, 0x01, 0x02])
            await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, control_command, response=True)
            logging.info("Set measurement mode to Extended (Quaternion)")
            
            logging.info(f"Streaming quaternion data for {duration_seconds} seconds...")
            await asyncio.sleep(duration_seconds)
            
            # Stop measurement before disconnecting
            await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
            logging.info("Stopped measurement")
            
            # Unsubscribe from notifications
            await self.client.stop_notify(MEDIUM_PAYLOAD_CHARACTERISTIC_UUID)
            
        except Exception as e:
            logging.error(f"Error during quaternion streaming: {e}")
            
            # Try to stop measurement even if there was an error
            try:
                if self.client and self.client.is_connected:
                    stop_command = bytearray([0x01, 0x00, 0x00])
                    await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
                    await self.client.stop_notify(MEDIUM_PAYLOAD_CHARACTERISTIC_UUID)
            except Exception:
                pass  # Ignore errors during cleanup