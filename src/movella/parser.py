# src/movella/parser.py
import numpy as np
import logging
import struct
from typing import Optional, Tuple

from movella.types import QuaternionData

logger = logging.getLogger(__name__)

def parse_quaternion_data(bytes_: bytes) -> Optional[QuaternionData]:
    """
    Parse quaternion data from bytes.
    
    Extended Quaternion Format (40 bytes):
    - Timestamp (4 bytes)
    - Quaternion (16 bytes: w, x, y, z as floats)
    - Free acceleration (12 bytes: x, y, z as floats)
    - Status (2 bytes)
    - Clipping Count Accelerometer (1 byte)
    - Clipping Count Gyroscope (1 byte)
    
    Returns:
        QuaternionData object or None if parsing fails
    """
    if len(bytes_) != 40:
        logger.warning(f"Unsupported data length: {len(bytes_)}. Expected 40 bytes.")
        return None
    
    try:
        # Mapping binary data to structured array
        dtype = np.dtype([
            ('timestamp', np.uint32),
            ('quat_w', np.float32), ('quat_x', np.float32), ('quat_y', np.float32), ('quat_z', np.float32),
            ('free_acc_x', np.float32), ('free_acc_y', np.float32), ('free_acc_z', np.float32),
            ('status', np.uint16),
            ('clip_acc', np.uint8), ('clip_gyro', np.uint8),
            ('reserved', np.uint8, 4)
        ])
        
        data = np.frombuffer(bytes_, dtype=dtype)[0]
        
        # Converting numpy array to Quaternion data structure
        quat_data = QuaternionData(
            timestamp=data['timestamp'],
            quat_w=data['quat_w'],
            quat_x=data['quat_x'],
            quat_y=data['quat_y'],
            quat_z=data['quat_z'],
            free_acc_x=data['free_acc_x'],
            free_acc_y=data['free_acc_y'],
            free_acc_z=data['free_acc_z'],
            status=data['status'],
            clip_acc=data['clip_acc'],
            clip_gyro=data['clip_gyro']
        )
        
        if not quat_data.is_quaternion_normalized():
            logger.warning(f"Quaternion not normalized: {quat_data.quaternion}")
        
        return quat_data
        
    except Exception as e:
        logger.error(f"Error parsing quaternion data: {e}")
        return None

def parse_custom_mode_data(data: bytes) -> Optional[QuaternionData]:
    """
    Parse Custom Mode 5 data (timestamp, quaternion, acceleration, angular velocity)
    
    Args:
        data: Raw bytes received from the BLE device
        
    Returns:
        QuaternionData object or None if parsing fails
    """
    if len(data) < 44:
        logger.warning(f"Insufficient data length for Custom Mode 5: {len(data)}. Expected at least 44 bytes.")
        return None
    
    try:
        # Create data object
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
        
        # Check quaternion normalization
        if not quat_data.is_quaternion_normalized():
            logger.warning(f"Quaternion not normalized: {quat_data.quaternion}")
        
        return quat_data
        
    except Exception as e:
        logger.error(f"Error processing custom mode data: {e}")
        return None