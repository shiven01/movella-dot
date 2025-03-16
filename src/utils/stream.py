import numpy as np
import asyncio
from bleak import BleakClient
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='movella_debug.log'
)

# UUIDs for Movella DOT
CONTROL_CHARACTERISTIC_UUID = "15172001-4947-11e9-8646-d663bd873d93"  # 0x2001
MEDIUM_PAYLOAD_CHARACTERISTIC_UUID = "15172003-4947-11e9-8646-d663bd873d93"  # 0x2003

def notification_callback(sender, data):
    parsed_data = parse_quaternion_data(data)
    if parsed_data is not None:
        print(parsed_data)

def parse_quaternion_data(bytes_) -> np.ndarray:
    # Complete (Quaternion) Format:
    # - Timestamp (4 bytes)
    # - Quaternion (16 bytes: w, x, y, z as floats)
    # - Free acceleration (12 bytes: x, y, z as floats)
    
    if len(bytes_) == 36:  # Extended Quaternion
        logging.debug(f"Extended Quaternion Data Segment")
        data_segments = np.dtype([
            ('timestamp', np.uint32),
            ('quat_w', np.float32),
            ('quat_x', np.float32),
            ('quat_y', np.float32),
            ('quat_z', np.float32),
            ('free_acc_x', np.float32),
            ('free_acc_y', np.float32),
            ('free_acc_z', np.float32),
            ('status', np.uint16),
            ('clip_acc', np.uint8),
            ('clip_gyro', np.uint8)
        ])

        try:
            formatted_data = np.frombuffer(bytes_, dtype=data_segments)
            
            # Validate quaternion is normalized (w²+x²+y²+z² ≈ 1)
            quat = [formatted_data['quat_w'][0], formatted_data['quat_x'][0], 
                    formatted_data['quat_y'][0], formatted_data['quat_z'][0]]
            norm = sum(q*q for q in quat)
            if abs(norm - 1.0) > 0.1:  # Allow some error
                logging.warning(f"Quaternion not normalized: {norm}")
            
            return formatted_data
        except Exception as e:
            logging.error(f"Error parsing data: {e}")
            return None

    elif len(bytes_) == 40:  # Custom Mode 1
        logging.debug(f"Custom Mode 1 Data Segment")
        data_segments = np.dtype([
            ('timestamp', np.uint32),
            ('euler_x', np.float32),
            ('euler_y', np.float32),
            ('euler_z', np.float32),
            ('free_acc_x', np.float32),
            ('free_acc_y', np.float32),
            ('free_acc_z', np.float32),
            ('ang_vel_x', np.float32),
            ('ang_vel_y', np.float32),
            ('ang_vel_z', np.float32)
        ])

        try:
            formatted_data = np.frombuffer(bytes_, dtype=data_segments)
            return formatted_data
        except Exception as e:
            logging.error(f"Error parsing data: {e}")
            return None

    else:
        logging.warning(f"Unknown data format with length: {len(bytes_)}")
        return None

async def main():
    address = "60AAC426-059B-BBAA-23A3-4CBF4A9B886F"  # Movella DOT address

    logging.info(f"Attempting to connect to device: {address}")
    try:
        async with BleakClient(address) as client:
            print(f"Client connection: {client.is_connected}")

            services = client.services
            for service in services:
                logging.info(f"Service: {service.uuid}")
                for char in service.characteristics:
                    logging.info(f"  Characteristic: {char.uuid}, Properties: {char.properties}")

            try:
                await client.start_notify(MEDIUM_PAYLOAD_CHARACTERISTIC_UUID, notification_callback)
                logging.info("Succesfully subscribed to notifications")
            except Exception as e:
                logging.error(f"Failed to subscribe to nofications: {e}")
                return
            
            # Setting the measurement mode to Extended (Quaternion) - 0x02
            control_command = bytearray([0x01, 0x01, 0x02])
            await client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, control_command, response=True)
            
            print("Streaming quaternion data for 10 seconds...")
            await asyncio.sleep(10.0)
            
            # Stop measurement before disconnecting
            stop_command = bytearray([0x01, 0x00, 0x00])
            await client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, stop_command, response=True)
            print("Stopped measurement")
    except Exception as e:
        logging.info(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())