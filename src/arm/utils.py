import asyncio
import numpy as np
from asyncio.log import logger
import threading

def calibrate_sensors(multi_client):
    """
    Perform a simple calibration to define the initial position
    Returns the calibration quaternions
    """
    logger.info("CALIBRATION: Please hold the arm straight for 3 seconds...")
    
    # Initialize calibration storage
    calibration_data = {
        "upper_arm": None,
        "lower_arm": None
    }
    
    # Create a calibration event
    calibration_complete = threading.Event()
    
    # Define a calibration callback
    def calibration_callback(sensor_id, quat_data):
        # Store the quaternion data
        if sensor_id in calibration_data:
            calibration_data[sensor_id] = quat_data.quaternion
            
            # Check if we have data from both sensors
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
            "upper_arm": np.array([1.0, 0.0, 0.0, 0.0]),
            "lower_arm": np.array([1.0, 0.0, 0.0, 0.0])
        }
    
    # Restore original callback
    multi_client.callback = original_callback
    
    logger.info("Calibration complete!")
    return calibration_data