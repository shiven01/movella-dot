"""
Utility functions for body visualization with five sensors.

This module provides utility functions for the five-segment body visualization,
such as sensor calibration.
"""

import asyncio
import numpy as np
import logging
import threading

logger = logging.getLogger("BodyUtils")

def calibrate_sensors(multi_client):
    """
    Perform calibration to define the initial position for all five body segments
    Returns the calibration quaternions
    """
    logger.info("CALIBRATION: Please stand in T-pose for 3 seconds...")
    
    # Initialize calibration storage
    calibration_data = {
        "torso": None,
        "left_arm": None,
        "right_arm": None,
        "left_leg": None,
        "right_leg": None
    }
    
    # Create a calibration event
    calibration_complete = threading.Event()
    
    # Define a calibration callback
    def calibration_callback(sensor_id, quat_data):
        # Store the quaternion data
        if sensor_id in calibration_data:
            calibration_data[sensor_id] = quat_data.quaternion
            
            # Check if we have data from all five sensors
            if all(calibration_data.values()):
                calibration_complete.set()
    
    # Set the callback
    original_callback = multi_client.callback
    multi_client.callback = calibration_callback
    
    # Stream data briefly to get calibration values
    asyncio.run(multi_client.start_streaming_all(duration_seconds=0.5))
    
    # Wait for calibration data or timeout
    if not calibration_complete.wait(timeout=5.0):
        logger.warning("Calibration timed out, using identity quaternions")
        calibration_data = {
            "torso": np.array([1.0, 0.0, 0.0, 0.0]),
            "left_arm": np.array([1.0, 0.0, 0.0, 0.0]),
            "right_arm": np.array([1.0, 0.0, 0.0, 0.0]),
            "left_leg": np.array([1.0, 0.0, 0.0, 0.0]),
            "right_leg": np.array([1.0, 0.0, 0.0, 0.0])
        }
    
    # Restore original callback
    multi_client.callback = original_callback
    
    logger.info("Calibration complete!")
    return calibration_data

def inverse_quaternion(q):
    """
    Calculate the inverse of a quaternion
    
    Args:
        q: Quaternion [w, x, y, z]
        
    Returns:
        Inverse quaternion
    """
    # For unit quaternions, the inverse is the conjugate
    return np.array([q[0], -q[1], -q[2], -q[3]])

def get_joint_angle(ref_quat, segment_quat):
    """
    Calculate the angle between two quaternions
    
    Args:
        ref_quat: Reference quaternion (e.g., torso)
        segment_quat: Segment quaternion (e.g., arm)
        
    Returns:
        Angle in degrees
    """
    # Calculate the relative quaternion
    inv_ref = inverse_quaternion(ref_quat)
    rel_quat = quaternion_multiply(inv_ref, segment_quat)
    
    # Convert to angle
    angle_rad = 2 * np.arccos(np.clip(rel_quat[0], -1.0, 1.0))
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def quaternion_multiply(q1, q2):
    """
    Multiply two quaternions
    
    Args:
        q1: First quaternion [w, x, y, z]
        q2: Second quaternion [w, x, y, z]
        
    Returns:
        Product quaternion
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    
    return np.array([w, x, y, z])