import numpy as np
import logging
from typing import Optional

from movella.types import QuaternionData

def parse_quaternion_data(bytes_: bytes) -> Optional[QuaternionData]:
    """
    Parse quaternion data from bytes.
    
    Extended Quaternion Format (36 bytes):
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
        logging.warning(f"Unsupported data length: {len(bytes_)}. Expected 40 bytes.")
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
            logging.warning(f"Quaternion not normalized: {quat_data.quaternion}")
        
        return quat_data
        
    except Exception as e:
        logging.error(f"Error parsing quaternion data: {e}")
        return None