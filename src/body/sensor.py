"""
Sensor handler for five Movella DOT sensors for realistic body tracking.

This module handles sensor data collection and processing for torso, arms, and legs tracking.
"""

import threading
import asyncio
import numpy as np
import logging

from movella.multi.multi_client import MultiMovellaDotClient
from movella.types import QuaternionData
from shared.resources import data_queue

logger = logging.getLogger("BodySensor")

def process_quaternion_for_body_viz(sensor_id: str, quat_data: QuaternionData) -> None:
    """Process quaternion data and add it to the queue for visualization"""
    
    # Extract the quaternion data (w, x, y, z)
    quat = quat_data.quaternion
    
    # Identify which body segment this sensor is for
    if sensor_id == "torso":
        body_segment = "torso"
    elif sensor_id == "left_arm":
        body_segment = "left_arm"
    elif sensor_id == "right_arm":
        body_segment = "right_arm"
    elif sensor_id == "left_leg":
        body_segment = "left_leg"
    elif sensor_id == "right_leg":
        body_segment = "right_leg"
    else:
        # Skip if not a recognized sensor
        logger.warning(f"Received data from unknown sensor: {sensor_id}")
        return
    
    # Store the quaternion data
    if not hasattr(process_quaternion_for_body_viz, 'latest_data'):
        # Initialize the latest data storage on first call
        process_quaternion_for_body_viz.latest_data = {}
    
    # Update the data for this segment
    process_quaternion_for_body_viz.latest_data[body_segment] = np.array(quat)
    
    # Only add to visualization queue if we have all five sensors' data
    if all(segment in process_quaternion_for_body_viz.latest_data for segment in
          ['torso', 'left_arm', 'right_arm', 'left_leg', 'right_leg']):
        # Add a copy of the current data to queue
        data_queue.put(process_quaternion_for_body_viz.latest_data.copy())
    
    # Log the data
    logger.debug(f"Received {body_segment} quaternion: {quat}")

async def sensor_data_collection(torso_address: str, left_arm_address: str, 
                                right_arm_address: str, left_leg_address: str,
                                right_leg_address: str, duration: float):
    """Collect data from five sensors for the specified duration"""
    # Create multi-sensor client with our visualization callback
    multi_client = MultiMovellaDotClient(process_quaternion_for_body_viz)
    
    # Add sensors with specific names for identification
    multi_client.add_sensor(torso_address, "torso")
    multi_client.add_sensor(left_arm_address, "left_arm")
    multi_client.add_sensor(right_arm_address, "right_arm")
    multi_client.add_sensor(left_leg_address, "left_leg")
    multi_client.add_sensor(right_leg_address, "right_leg")
    
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

def run_sensor_collection(torso_address, left_arm_address, right_arm_address, 
                         left_leg_address, right_leg_address, duration):
    """Run the sensor data collection in a separate thread"""
    asyncio.run(sensor_data_collection(
        torso_address, left_arm_address, right_arm_address, 
        left_leg_address, right_leg_address, duration))