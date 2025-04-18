"""
Sensor handler for three Movella DOT sensors for realistic arm tracking.

This module handles sensor data collection and processing for shoulder, elbow, and wrist tracking.
"""

import threading
import asyncio
import numpy as np
import logging

from movella.multi.multi_client import MultiMovellaDotClient
from movella.types import QuaternionData
from shared.resources import data_queue

logger = logging.getLogger("ArmSensor")

def process_quaternion_for_arm_viz(sensor_id: str, quat_data: QuaternionData) -> None:
    """Process quaternion data and add it to the queue for visualization"""
    
    # Extract the quaternion data (w, x, y, z)
    quat = quat_data.quaternion
    
    # Identify which arm segment this sensor is for
    if sensor_id == "upper_arm":
        arm_segment = "upper_arm"
    elif sensor_id == "forearm":
        arm_segment = "forearm"
    elif sensor_id == "hand":
        arm_segment = "hand"
    else:
        # Skip if not a recognized sensor
        logger.warning(f"Received data from unknown sensor: {sensor_id}")
        return
    
    # Store the quaternion data
    if not hasattr(process_quaternion_for_arm_viz, 'latest_data'):
        # Initialize the latest data storage on first call
        process_quaternion_for_arm_viz.latest_data = {}
    
    # Update the data for this segment
    process_quaternion_for_arm_viz.latest_data[arm_segment] = np.array(quat)
    
    # Only add to visualization queue if we have all three sensors' data
    if ('upper_arm' in process_quaternion_for_arm_viz.latest_data and 
        'forearm' in process_quaternion_for_arm_viz.latest_data and
        'hand' in process_quaternion_for_arm_viz.latest_data):
        # Add a copy of the current data to queue
        data_queue.put(process_quaternion_for_arm_viz.latest_data.copy())
    
    # Log the data
    logger.debug(f"Received {arm_segment} quaternion: {quat}")

async def sensor_data_collection(upper_address: str, forearm_address: str, hand_address: str, duration: float):
    """Collect data from three sensors for the specified duration"""
    # Create multi-sensor client with our visualization callback
    multi_client = MultiMovellaDotClient(process_quaternion_for_arm_viz)
    
    # Add sensors with specific names for identification
    multi_client.add_sensor(upper_address, "upper_arm")
    multi_client.add_sensor(forearm_address, "forearm")
    multi_client.add_sensor(hand_address, "hand")
    
    # Connect to all sensors
    logger.info("Connecting to sensors...")
    connection_status = await multi_client.connect_all()
    
    # Check if at least one sensor connected successfully
    if not any(connection_status.values()):
        logger.error("Failed to connect to any sensors!")
        return
    
    # Log connection status for each sensor
    for addr, status in connection_status.items():
        logger.info(f"Sensor {addr}: {'Connected' if status else 'Connection failed'}")
    
    # Start streaming from all connected sensors
    logger.info(f"Starting quaternion streaming for {duration} seconds...")
    await multi_client.start_streaming_all(duration_seconds=duration)
    
    # Always ensure we disconnect from all sensors
    logger.info("Disconnecting from sensors...")
    await multi_client.disconnect_all()

def run_sensor_collection(upper_address, forearm_address, hand_address, duration):
    """Run the sensor data collection in a separate thread"""
    asyncio.run(sensor_data_collection(upper_address, forearm_address, hand_address, duration))