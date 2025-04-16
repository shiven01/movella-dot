import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Tuple

from bleak import BleakScanner

from movella.types import QuaternionData
from movella.multi.multi_client import MultiMovellaDotClient
from utils.json_output import JsonStreamWriter, create_multi_sensor_callback
from utils.logging_config import setup_logging
from utils.scanner import scan_for_movella_devices

def process_quaternion(sensor_id: str, quat_data: QuaternionData) -> None:
    """
    Process and display quaternion data with sensor identification
    
    Args:
        sensor_id: Identifier for the sensor that provided the data
        quat_data: Quaternion data from the Movella DOT
    """
    w, x, y, z = quat_data.quaternion
    ax, ay, az = quat_data.free_acceleration
    gx, gy, gz = quat_data.angular_velocity

    data_lines = [
        f"Sensor: {sensor_id}",
        f"Timestamp: {quat_data.timestamp}",
        f"Quaternion (w,x,y,z): ({w:.4f}, {x:.4f}, {y:.4f}, {z:.4f})",
        f"Free acceleration (m/s²): ({ax:.2f}, {ay:.2f}, {az:.2f})",
        f"Angular Velocity (dps): ({gx:.2f}, {gy:.2f}, {gz:.2f})"
    ]
    
    print("-" * 50)
    data_message = "\n".join(data_lines)
    logging.info(f"Quaternion Data:\n{data_message}")
    print(data_message)

async def main():
    parser = argparse.ArgumentParser(description="Connect to multiple Movella DOT sensors")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, 
                        help="Scan duration in seconds")
    parser.add_argument("-d", "--duration", type=float, default=10.0,
                        help="Duration to stream data in seconds")
    parser.add_argument("-a", "--addresses", nargs='+', 
                        help="Bluetooth addresses of specific Movella DOT devices")
    parser.add_argument("--json", action="store_true", help="Output data in JSON format")
    parser.add_argument("--output", type=str, help="Output JSON to a file")
    parser.add_argument("--pretty", action="store_true", help="Format JSON with indentation")
    args = parser.parse_args()
    
    setup_logging(log_file_name="movella_multi_sensor.log")
    
    json_writer = None
    multi_client = None
    
    try:
        # Create appropriate callback based on output format
        if args.json:
            # Use JSON output
            json_writer = JsonStreamWriter(args.output, args.pretty)
            callback = create_multi_sensor_callback(json_writer)
        else:
            # Use default text output
            callback = process_quaternion
        
        # Create multi-sensor client
        multi_client = MultiMovellaDotClient(callback)
        
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
        
        # Start streaming from all connected sensors
        logging.info(f"Streaming quaternion data for {args.duration} seconds...")
        await multi_client.start_streaming_all(args.duration)
        
    finally:
        # Always ensure we disconnect from all sensors
        if multi_client:
            await multi_client.disconnect_all()
            
        # Close JSON writer if used
        if json_writer:
            json_writer.close()

if __name__ == "__main__":
    asyncio.run(main())