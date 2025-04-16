import asyncio
import argparse
import logging
from typing import List, Dict, Optional, Tuple
from bleak import BleakScanner

logger = logging.getLogger(__name__)

async def scan_for_devices(timeout: float = 5.0, filter_name: Optional[str] = None):
    """
    Scan for BLE devices with optional name filtering
    
    Args:
        timeout: Scan duration in seconds
        filter_name: Optional substring to filter device names
        
    Returns:
        List of discovered devices
    """
    print(f"Scanning for BLE devices for {timeout} seconds...")
    devices = await BleakScanner.discover(timeout=timeout)
    
    # Filter devices if requested
    if filter_name:
        filtered_devices = [d for d in devices if d.name and filter_name in d.name]
    else:
        filtered_devices = devices
    
    # Print results in a formatted way
    print_scan_results(devices)
    
    # Return all devices or filtered ones based on the filter_name parameter
    return filtered_devices if filter_name else devices

def print_scan_results(devices):
    """Print discovered devices in a formatted way"""
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
    
    return movella_devices

async def scan_for_movella_devices(timeout: float = 5.0) -> List[Dict]:
    """
    Scan specifically for Movella DOT devices
    
    Args:
        timeout: Scan duration in seconds
        
    Returns:
        List of dictionaries with device information
    """
    print(f"Scanning for Movella DOT devices for {timeout} seconds...")
    devices = await scan_for_devices(timeout)
    
    # Extract Movella devices
    movella_devices = []
    for device in devices:
        if device.name and "Movella" in device.name:
            movella_devices.append({
                'address': device.address,
                'name': device.name
            })
    
    if not movella_devices:
        logger.warning("No Movella DOT devices found")
    else:
        logger.info(f"Found {len(movella_devices)} Movella DOT devices")
        for i, device in enumerate(movella_devices):
            logger.info(f"{i+1}. {device['name']} [{device['address']}]")
    
    return movella_devices

async def interactive_scan(timeout: float = 5.0) -> List[str]:
    """
    Interactive scanner that lets user choose devices
    
    Args:
        timeout: Scan duration in seconds
        
    Returns:
        List of selected device addresses
    """
    devices = await scan_for_devices(timeout)
    
    movella_devices = [d for d in devices if d.name and "Movella" in d.name]
    
    if not movella_devices:
        print("\nNo Movella DOT devices found. Showing all devices instead.")
        selectable_devices = devices
    else:
        print(f"\nFound {len(movella_devices)} Movella DOT devices:")
        for i, device in enumerate(movella_devices):
            print(f"{i+1}. {device.name} [{device.address}]")
        selectable_devices = movella_devices
    
    if not selectable_devices:
        print("No devices found.")
        return []
    
    selected_indices = input("\nEnter device numbers to use (comma separated, or 'all'): ")
    
    if selected_indices.lower() == 'all':
        return [device.address for device in selectable_devices]
    
    try:
        indices = [int(idx.strip()) - 1 for idx in selected_indices.split(',')]
        selected_addresses = []
        
        for idx in indices:
            if 0 <= idx < len(selectable_devices):
                selected_addresses.append(selectable_devices[idx].address)
            else:
                print(f"Invalid index: {idx + 1}")
        
        return selected_addresses
    except ValueError:
        print("Invalid input. Please enter comma-separated numbers.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Scan for BLE devices, particularly Movella DOT sensors")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Scan duration in seconds")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode to select devices")
    parser.add_argument("-m", "--movella-only", action="store_true", help="Show only Movella devices")
    args = parser.parse_args()
    
    if args.interactive:
        selected = asyncio.run(interactive_scan(args.timeout))
        if selected:
            print(f"\nSelected devices: {selected}")
    elif args.movella_only:
        movella_devices = asyncio.run(scan_for_movella_devices(args.timeout))
        if movella_devices:
            print(f"\nFound {len(movella_devices)} Movella DOT devices:")
            for i, device in enumerate(movella_devices):
                print(f"{i+1}. {device['name']} [{device['address']}]")
    else:
        asyncio.run(scan_for_devices(args.timeout))

if __name__ == "__main__":
    main()