import asyncio
import argparse
from bleak import BleakScanner

async def scan_for_devices(timeout: float = 5.0):
    """
    Scan for BLE devices
    
    Args:
        timeout: Scan duration in seconds
    """
    print(f"Scanning for BLE devices for {timeout} seconds...")
    devices = await BleakScanner.discover(timeout=timeout)
    
    print(f"\nFound {len(devices)} devices:")
    print("-" * 70)
    
    # Filter for Movella devices if any are found
    movella_devices = []
    
    for i, device in enumerate(devices):
        is_movella = "Movella" in (device.name or "")
        device_info = f"{i+1}. {device.name or 'Unknown'} [{device.address}]"
        
        if is_movella:
            device_info += " (Movella DOT)"
            movella_devices.append(device)
        
        print(device_info)
    
    print("-" * 70)
    
    if movella_devices:
        print(f"\nFound {len(movella_devices)} Movella DOT devices:")
        for i, device in enumerate(movella_devices):
            print(f"{i+1}. {device.name} [{device.address}]")
    else:
        print("\nNo Movella DOT devices found. Make sure your sensors are powered on.")

def main():
    parser = argparse.ArgumentParser(description="Scan for BLE devices, particularly Movella DOT sensors")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Scan duration in seconds")
    args = parser.parse_args()
    
    asyncio.run(scan_for_devices(args.timeout))

if __name__ == "__main__":
    main()