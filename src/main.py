import asyncio
import logging
import argparse
from pathlib import Path

from movella.client import MovellaDotClient
from movella.types import QuaternionData
from utils.json_output import JsonStreamWriter, create_single_sensor_callback

def setup_logging():
    log_file = Path(__file__).parent.parent / "logs" / "movella_quaternion.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def process_quaternion(quat_data: QuaternionData) -> None:
    """
    Process and display quaternion data
    
    Args:
        quat_data: Quaternion data from the Movella DOT
    """
    w, x, y, z = quat_data.quaternion
    print(f"Quaternion (w,x,y,z): ({w:.4f}, {x:.4f}, {y:.4f}, {z:.4f})")
    
    norm = sum(q*q for q in quat_data.quaternion)
    print(f"Quaternion norm: {norm:.4f}")
    
    ax, ay, az = quat_data.free_acceleration
    print(f"Free acceleration (m/s²): ({ax:.2f}, {ay:.2f}, {az:.2f})")
    
    # Display status if non-zero
    if hasattr(quat_data, "status") and quat_data.status > 0:
        print(f"Status flags: 0x{quat_data.status:04x}")
    
    # Readability Divider
    print("-" * 50)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Connect to Movella DOT sensor and stream quaternion data")
    parser.add_argument("--json", action="store_true", help="Output data in JSON format")
    parser.add_argument("--output", type=str, help="Output JSON to a file")
    parser.add_argument("--pretty", action="store_true", help="Format JSON with indentation")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration to stream data in seconds")
    parser.add_argument("--address", type=str, default="60AAC426-059B-BBAA-23A3-4CBF4A9B886F", 
                        help="Bluetooth address of the Movella DOT device")
    args = parser.parse_args()
    
    setup_logging()
    
    address = args.address
    json_writer = None
    client = None
    connected = False
    
    try:
        if args.json:
            # Use JSON output
            json_writer = JsonStreamWriter(args.output, args.pretty)
            callback = create_single_sensor_callback(json_writer)
        else:
            # Use default text output
            callback = process_quaternion
        
        client = MovellaDotClient(address, callback)
        
        logging.info(f"Connecting to Movella DOT at {address}...")
        connected = await client.connect()
        
        if connected:
            logging.info("Connected successfully to Movella DOT")
            
            await client.start_quaternion_stream(args.duration)
        else:
            logging.error("Failed to connect to Movella DOT")
            
    finally:
        # Clean up resources
        if client and connected:
            await client.disconnect()
            logging.info("Disconnected from Movella DOT")
            
        if json_writer:
            json_writer.close()

if __name__ == "__main__":
    asyncio.run(main())