import asyncio
import logging
import struct
from typing import Optional, Callable
from bleak import BleakClient

from movella.types import QuaternionData
from movella.parser import parse_quaternion_data
from utils.callbacks import default_single_sensor_callback

# UUIDs for Movella DOT
CONTROL_CHARACTERISTIC_UUID = "15172001-4947-11e9-8646-d663bd873d93"
MEDIUM_PAYLOAD_CHARACTERISTIC_UUID = "15172003-4947-11e9-8646-d663bd873d93"
LONG_PAYLOAD_CHARACTERISTIC_UUID = "15172002-4947-11e9-8646-d663bd873d93"

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
    
    def notification_callback(self, sender, data: bytes) -> None:
        """
        Callback for BLE notifications that parses and processes quaternion data
        
        Args:
            sender: BLE characteristic that sent the data
            data: Raw bytes received from the BLE device
        """
        # Process the data based on the payload type
        if len(data) >= 44:  # Long payload (Custom Mode 5)
            self.process_custom_mode_data(data)
        else:  # Medium payload (original quaternion data)
            parsed_data = parse_quaternion_data(data)
            if parsed_data is not None:
                self.callback(parsed_data)
    
    def process_custom_mode_data(self, data: bytes) -> None:
        """
        Process Custom Mode 5 data (timestamp, quaternion, acceleration, angular velocity)
        
        Args:
            data: Raw bytes received from the BLE device
        """
        if len(data) >= 44:
            try:
                # Create data object first - but don't rely on the init to set properties
                quat_data = QuaternionData()
                
                # Timestamp (4 bytes)
                quat_data.timestamp = int.from_bytes(data[0:4], byteorder='little')
                
                # Quaternion (16 bytes): w, x, y, z as float
                quat_data.quat_w = struct.unpack('<f', data[4:8])[0]
                quat_data.quat_x = struct.unpack('<f', data[8:12])[0]
                quat_data.quat_y = struct.unpack('<f', data[12:16])[0]
                quat_data.quat_z = struct.unpack('<f', data[16:20])[0]
                
                # Acceleration (12 bytes): x, y, z as float
                acc_x = struct.unpack('<f', data[20:24])[0]
                acc_y = struct.unpack('<f', data[24:28])[0]
                acc_z = struct.unpack('<f', data[28:32])[0]
                quat_data.acceleration = (acc_x, acc_y, acc_z)
                
                # Angular velocity (12 bytes): x, y, z as float
                gyr_x = struct.unpack('<f', data[32:36])[0]
                gyr_y = struct.unpack('<f', data[36:40])[0]
                gyr_z = struct.unpack('<f', data[40:44])[0]
                quat_data.angular_velocity = (gyr_x, gyr_y, gyr_z)
                
                # Free acceleration - initialized to zeros
                quat_data.free_acc_x = 0.0
                quat_data.free_acc_y = 0.0
                quat_data.free_acc_z = 0.0
                
                # Call the user's callback
                self.callback(quat_data)
                
            except Exception as e:
                logging.error(f"Error processing custom mode data: {e}")
    
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
        """
        Start streaming quaternion, acceleration, and angular velocity data
        for the specified duration using Custom Mode 5
        
        Args:
            duration_seconds: Duration of streaming in seconds
        """
        if not self.client or not self.client.is_connected:
            logging.error("Not connected to device")
            return
        
        try:
            # Stopping any ongoing measurement first
            stop_command = bytearray([0x01, 0x00, 0x00])
            await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
            await asyncio.sleep(0.5)

            # Subscribe to long payload characteristic for Custom Mode 5
            await self.client.start_notify(LONG_PAYLOAD_CHARACTERISTIC_UUID, self.notification_callback)
            logging.info("Successfully subscribed to long payload notifications")
            await asyncio.sleep(0.1)
            
            # Set measurement mode to Custom Mode 5 (value 26) for Timestamp, Quaternion, Acceleration, Angular velocity
            custom_mode_command = bytearray([0x01, 0x01, 0x1A])  # 0x1A = 26 in decimal
            await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, custom_mode_command, response=True)
            logging.info("Set measurement mode to Custom Mode 5")
            
            logging.info(f"Streaming motion data for {duration_seconds} seconds...")
            await asyncio.sleep(duration_seconds)
            
            # Stop measurement before disconnecting
            await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
            logging.info("Stopped measurement")
            
            # Unsubscribe from notifications
            await self.client.stop_notify(LONG_PAYLOAD_CHARACTERISTIC_UUID)
            
        except Exception as e:
            logging.error(f"Error during data streaming: {e}")
            
            # Try to stop measurement even if there was an error
            try:
                if self.client and self.client.is_connected:
                    stop_command = bytearray([0x01, 0x00, 0x00])
                    await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
                    await self.client.stop_notify(LONG_PAYLOAD_CHARACTERISTIC_UUID)
            except Exception:
                pass  # Ignore errors during cleanup