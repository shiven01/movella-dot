import asyncio
import logging
from typing import Dict, List, Callable, Optional, Tuple

from movella.client import MovellaDotClient
from movella.types import QuaternionData
from utils.callbacks import default_multi_sensor_callback

class MultiMovellaDotClient:
    """
    Class to manage multiple Movella DOT sensors simultaneously
    """
    def __init__(self, 
                 callback: Optional[Callable[[str, QuaternionData], None]] = None):
        """
        Initialize MultiMovellaDotClient
        
        Args:
            callback: Function to call when quaternion data is received from any sensor.
                      First parameter is the sensor's address, second is the quaternion data.
        """
        self.sensors: Dict[str, MovellaDotClient] = {}
        self.user_callback = callback or self._default_callback
    
    def _create_sensor_callback(self, sensor_id: str) -> Callable[[QuaternionData], None]:
        """
        Creates a callback for a specific sensor that adds the sensor ID
        to the user's callback
        
        Args:
            sensor_id: ID of the sensor for this callback
            
        Returns:
            Callback function that adds sensor ID to user callback
        """
        def sensor_callback(data: QuaternionData) -> None:
            self.user_callback(sensor_id, data)
        return sensor_callback
    
    def add_sensor(self, address: str, sensor_name: Optional[str] = None) -> None:
        """
        Add a Movella DOT sensor to be managed
        
        Args:
            address: Bluetooth address of the Movella DOT device
            sensor_name: Optional name for the sensor (for easier identification)
        """
        sensor_id = sensor_name or address
        callback = self._create_sensor_callback(sensor_id)
        self.sensors[address] = MovellaDotClient(address, callback)
        logging.info(f"Added sensor {sensor_id} with address {address}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all added sensors
        
        Returns:
            Dictionary mapping sensor addresses to connection status (True/False)
        """
        connection_tasks = []
        for address, client in self.sensors.items():
            connection_tasks.append(client.connect())
        
        # Connect to all sensors concurrently
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        # Map results to sensor addresses
        connection_status = {}
        for i, (address, _) in enumerate(self.sensors.items()):
            if isinstance(results[i], Exception):
                logging.error(f"Error connecting to {address}: {results[i]}")
                connection_status[address] = False
            else:
                connection_status[address] = results[i]
                
        return connection_status
    
    async def disconnect_all(self) -> None:
        """Disconnect from all sensors"""
        disconnect_tasks = []
        for client in self.sensors.values():
            disconnect_tasks.append(client.disconnect())
        
        # Disconnect from all sensors concurrently
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        logging.info("Disconnected from all sensors")
    
    async def start_streaming_all(self, duration_seconds: float = 5.0) -> None:
        """
        Start quaternion streaming from all connected sensors
        
        Args:
            duration_seconds: Duration of streaming in seconds
        """
        stream_tasks = []
        for client in self.sensors.values():
            stream_tasks.append(client.start_quaternion_stream(duration_seconds))
        
        # Start streaming from all sensors concurrently
        await asyncio.gather(*stream_tasks, return_exceptions=True)