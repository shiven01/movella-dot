import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Tuple

from bleak import BleakScanner

from movella.types import QuaternionData
from movella.multi.multi_client import MultiMovellaDotClient

def setup_logging():
    log_file = Path(__file__).parent.parent / "logs" / "movella_multi_sensor.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a'
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger('bleak').setLevel(logging.WARNING)

def process_quaternion(sensor_id: str, quat_data: QuaternionData) -> None:
    """
    Process and display quaternion data with sensor identification
    
    Args:
        sensor_id: Identifier for the sensor that provided the data
        quat_data: Quaternion data from the Movella DOT
    """
    w, x, y, z = quat_data.quaternion
    ax, ay, az = quat_data.free_acceleration

    data_lines = [
        f"Sensor: {sensor_id}",
        f"Timestamp: {quat_data.timestamp}",
        f"Sensor: {sensor_id}",
        f"Quaternion (w,x,y,z): ({w:.4f}, {x:.4f}, {y:.4f}, {z:.4f})",
        f"Free acceleration (m/s²): ({ax:.2f}, {ay:.2f}, {az:.2f})"
    ]
    
    print("-" * 50)
    data_message = "\n".join(data_lines)
    logging.info(f"Quaternion Data:\n{data_message}")
    print(data_message)

async def scan_for_movella_devices(timeout: float = 5.0) -> List[Tuple[str, str]]:
    """
    Scan for Movella DOT devices
    
    Args:
        timeout: Scan duration in seconds
        
    Returns:
        List of tuples (address, name) for found Movella DOT devices
    """
    print(f"Scanning for Movella DOT devices for {timeout} seconds...")
    devices = await BleakScanner.discover(timeout=timeout)
    
    movella_devices = []
    for device in devices:
        if device.name and "Movella" in device.name:
            movella_devices.append((device.address, device.name))
    
    return movella_devices

async def main():
    parser = argparse.ArgumentParser(description="Connect to multiple Movella DOT sensors")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, 
                        help="Scan duration in seconds")
    parser.add_argument("-d", "--duration", type=float, default=10.0,
                        help="Duration to stream data in seconds")
    parser.add_argument("-a", "--addresses", nargs='+', 
                        help="Bluetooth addresses of specific Movella DOT devices")
    args = parser.parse_args()
    
    setup_logging()
    
    # Create multi-sensor client
    multi_client = MultiMovellaDotClient(process_quaternion)
    
    # Either use provided addresses or scan for devices
    if args.addresses:
        for i, address in enumerate(args.addresses):
            multi_client.add_sensor(address, f"Sensor-{i+1}")
    else:
        movella_devices = await scan_for_movella_devices(args.timeout)
        
        if not movella_devices:
            logging.error("No Movella DOT devices found. Make sure sensors are powered on.")
            return
            
        print(f"Found {len(movella_devices)} Movella DOT devices:")
        for i, (address, name) in enumerate(movella_devices):
            print(f"{i+1}. {name} [{address}]")
            multi_client.add_sensor(address, f"Sensor-{i+1}")
    
    # Connect to all sensors
    connection_status = await multi_client.connect_all()
    
    # Check if at least one sensor connected successfully
    if not any(connection_status.values()):
        logging.error("Failed to connect to any Movella DOT sensors.")
        return
    
    # Log connection status for each sensor
    for address, status in connection_status.items():
        if status:
            logging.info(f"Connected successfully to {address}")
        else:
            logging.error(f"Failed to connect to {address}")
    
    try:
        # Start streaming from all connected sensors
        logging.info(f"Streaming quaternion data for {args.duration} seconds...")
        await multi_client.start_streaming_all(args.duration)
    finally:
        # Always ensure we disconnect from all sensors
        await multi_client.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())