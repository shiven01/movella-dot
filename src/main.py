import asyncio
import logging
from pathlib import Path

from movella.client import MovellaDotClient
from movella.types import QuaternionData

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
    if quat_data.status > 0:
        print(f"Status flags: 0x{quat_data.status:04x}")
    
    # Readability Divider
    print("-" * 50)

async def main():
    setup_logging()
    
    address = "60AAC426-059B-BBAA-23A3-4CBF4A9B886F"
    client = MovellaDotClient(address, process_quaternion)
    
    logging.info(f"Connecting to Movella DOT at {address}...")
    connected = await client.connect()
    
    if connected:
        logging.info("Connected successfully to Movella DOT")
        
        try:
            await client.start_quaternion_stream(10.0)
        finally:
            await client.disconnect()
            logging.info("Disconnected from Movella DOT")
    else:
        logging.error("Failed to connect to Movella DOT")

if __name__ == "__main__":
    asyncio.run(main())