"""
3D visualization for a realistic five-segment body model.

This module visualizes a complete body with torso, arms, and legs
tracked by five Movella DOT sensors.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import threading
import asyncio
import logging
import argparse
from pathlib import Path

# Import the shared data queue
from shared.resources import data_queue

# Import from our body modules
from body.model import BodySegment, BodyModel
from body.sensor import process_quaternion_for_body_viz, run_sensor_collection

# Import from existing Movella modules
from movella.multi.multi_client import MultiMovellaDotClient
from movella.types import QuaternionData
from utils.scanner import scan_for_movella_devices

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BodyViz")

class BodyVisualizer:
    """Handles 3D visualization of the five-segment body model"""
    
    def __init__(self):
        # Create a 3D figure
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Initialize the body model
        self.body_model = BodyModel()
        
        # Initialize animation properties
        self.ani = None
        self.last_update_time = 0
        
        # Line objects for visualization
        self.torso_line = None
        self.left_arm_line = None
        self.right_arm_line = None
        self.left_leg_line = None
        self.right_leg_line = None
        
        # Joint point objects for visualization
        self.left_shoulder_point = None
        self.right_shoulder_point = None
        self.left_hip_point = None
        self.right_hip_point = None
        
        # Initialize the visualization
        self._init_visualization()
    
    def _init_visualization(self):
        """Initialize the visualization elements"""
        # Get initial points from the body model
        torso_start, torso_end = self.body_model.torso.get_transformed_points()
        left_arm_start, left_arm_end = self.body_model.left_arm.get_transformed_points()
        right_arm_start, right_arm_end = self.body_model.right_arm.get_transformed_points()
        left_leg_start, left_leg_end = self.body_model.left_leg.get_transformed_points()
        right_leg_start, right_leg_end = self.body_model.right_leg.get_transformed_points()
        
        # Create lines for body segments
        self.torso_line, = self.ax.plot([torso_start[0], torso_end[0]],
                                        [torso_start[1], torso_end[1]],
                                        [torso_start[2], torso_end[2]],
                                        'g-', linewidth=4, label='Torso')
        
        self.left_arm_line, = self.ax.plot([left_arm_start[0], left_arm_end[0]],
                                          [left_arm_start[1], left_arm_end[1]],
                                          [left_arm_start[2], left_arm_end[2]],
                                          'b-', linewidth=4, label='Left Arm')
        
        self.right_arm_line, = self.ax.plot([right_arm_start[0], right_arm_end[0]],
                                           [right_arm_start[1], right_arm_end[1]],
                                           [right_arm_start[2], right_arm_end[2]],
                                           'b-', linewidth=4, label='Right Arm')
        
        self.left_leg_line, = self.ax.plot([left_leg_start[0], left_leg_end[0]],
                                          [left_leg_start[1], left_leg_end[1]],
                                          [left_leg_start[2], left_leg_end[2]],
                                          'r-', linewidth=4, label='Left Leg')
        
        self.right_leg_line, = self.ax.plot([right_leg_start[0], right_leg_end[0]],
                                           [right_leg_start[1], right_leg_end[1]],
                                           [right_leg_start[2], right_leg_end[2]],
                                           'r-', linewidth=4, label='Right Leg')
        
        # Add points to represent the joints
        self.left_shoulder_point, = self.ax.plot([left_arm_start[0]], [left_arm_start[1]], [left_arm_start[2]],
                                              'bo', markersize=8, label='Left Shoulder')
        
        self.right_shoulder_point, = self.ax.plot([right_arm_start[0]], [right_arm_start[1]], [right_arm_start[2]],
                                               'bo', markersize=8, label='Right Shoulder')
        
        self.left_hip_point, = self.ax.plot([left_leg_start[0]], [left_leg_start[1]], [left_leg_start[2]],
                                          'ro', markersize=8, label='Left Hip')
        
        self.right_hip_point, = self.ax.plot([right_leg_start[0]], [right_leg_start[1]], [right_leg_start[2]],
                                           'ro', markersize=8, label='Right Hip')
        
        # Set axis properties
        self.ax.set_xlim([-1, 1])
        self.ax.set_ylim([-1, 1])
        self.ax.set_zlim([-0.5, 2])
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Full Body Visualization')
        
        # Add a legend
        self.ax.legend(loc='upper left')
        
        # Equal aspect ratio
        self.ax.set_box_aspect([1, 1, 1])
    
    def update_frame(self, frame):
        """Update function for animation - gets the latest quaternion from the queue"""
        try:
            # Non-blocking to avoid freezing the animation
            # Get all available data and use the most recent
            latest_data = None
            while not data_queue.empty():
                latest_data = data_queue.get_nowait()
            
            if latest_data:
                # Extract quaternions for all five segments
                torso_quat = latest_data['torso']
                left_arm_quat = latest_data['left_arm']
                right_arm_quat = latest_data['right_arm']
                left_leg_quat = latest_data['left_leg']
                right_leg_quat = latest_data['right_leg']
                
                # Update the body model with all five quaternions
                self.body_model.update_from_sensors(
                    torso_quat, left_arm_quat, right_arm_quat, left_leg_quat, right_leg_quat)
                
                # Update visualization for torso
                torso_start, torso_end = self.body_model.torso.get_transformed_points()
                self.torso_line.set_data_3d([torso_start[0], torso_end[0]],
                                          [torso_start[1], torso_end[1]],
                                          [torso_start[2], torso_end[2]])
                
                # Update visualization for left arm
                left_arm_start, left_arm_end = self.body_model.left_arm.get_transformed_points()
                self.left_arm_line.set_data_3d([left_arm_start[0], left_arm_end[0]],
                                             [left_arm_start[1], left_arm_end[1]],
                                             [left_arm_start[2], left_arm_end[2]])
                
                # Update visualization for right arm
                right_arm_start, right_arm_end = self.body_model.right_arm.get_transformed_points()
                self.right_arm_line.set_data_3d([right_arm_start[0], right_arm_end[0]],
                                              [right_arm_start[1], right_arm_end[1]],
                                              [right_arm_start[2], right_arm_end[2]])
                
                # Update visualization for left leg
                left_leg_start, left_leg_end = self.body_model.left_leg.get_transformed_points()
                self.left_leg_line.set_data_3d([left_leg_start[0], left_leg_end[0]],
                                             [left_leg_start[1], left_leg_end[1]],
                                             [left_leg_start[2], left_leg_end[2]])
                
                # Update visualization for right leg
                right_leg_start, right_leg_end = self.body_model.right_leg.get_transformed_points()
                self.right_leg_line.set_data_3d([right_leg_start[0], right_leg_end[0]],
                                              [right_leg_start[1], right_leg_end[1]],
                                              [right_leg_start[2], right_leg_end[2]])
                
                # Update joint visualizations
                self.left_shoulder_point.set_data_3d([left_arm_start[0]], [left_arm_start[1]], [left_arm_start[2]])
                self.right_shoulder_point.set_data_3d([right_arm_start[0]], [right_arm_start[1]], [right_arm_start[2]])
                self.left_hip_point.set_data_3d([left_leg_start[0]], [left_leg_start[1]], [left_leg_start[2]])
                self.right_hip_point.set_data_3d([right_leg_start[0]], [right_leg_start[1]], [right_leg_start[2]])
                
                # Calculate and display joint angles
                joint_angles = self.body_model.get_joint_angles()
                
                self.ax.set_title(
                    f'Full Body Visualization - '
                    f'L.Shoulder: {joint_angles["left_shoulder"]:.1f}° | '
                    f'R.Shoulder: {joint_angles["right_shoulder"]:.1f}° | '
                    f'L.Hip: {joint_angles["left_hip"]:.1f}° | '
                    f'R.Hip: {joint_angles["right_hip"]:.1f}°'
                )
        
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
        
        # Return all artists that need to be redrawn
        return [self.torso_line, self.left_arm_line, self.right_arm_line,
                self.left_leg_line, self.right_leg_line,
                self.left_shoulder_point, self.right_shoulder_point,
                self.left_hip_point, self.right_hip_point]
    
    def show(self):
        """Show the visualization window"""
        # Create animation
        self.ani = FuncAnimation(
            self.fig,
            self.update_frame,
            interval=50,  # Update every 50ms (20 FPS)
            blit=True
        )
        
        # Show the plot
        plt.tight_layout()
        plt.show()

def main():
    """Main function to run the body visualization"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Visualize full body using five Movella DOT sensors")
    parser.add_argument("-t", "--torso", help="Bluetooth address of torso sensor")
    parser.add_argument("-la", "--left_arm", help="Bluetooth address of left arm sensor")
    parser.add_argument("-ra", "--right_arm", help="Bluetooth address of right arm sensor")
    parser.add_argument("-ll", "--left_leg", help="Bluetooth address of left leg sensor")
    parser.add_argument("-rl", "--right_leg", help="Bluetooth address of right leg sensor")
    parser.add_argument("-d", "--duration", type=float, default=60.0, help="Streaming duration in seconds")
    parser.add_argument("--timeout", type=float, default=5.0, help="Scan timeout in seconds")
    args = parser.parse_args()
    
    # Determine sensor addresses
    torso_address = args.torso
    left_arm_address = args.left_arm
    right_arm_address = args.right_arm
    left_leg_address = args.left_leg
    right_leg_address = args.right_leg
    
    # If addresses not provided, scan for devices
    if not all([torso_address, left_arm_address, right_arm_address, left_leg_address, right_leg_address]):
        logger.info("Scanning for Movella DOT devices...")
        devices = asyncio.run(scan_for_movella_devices(args.timeout))
        
        if len(devices) < 5:
            logger.error(f"Found only {len(devices)} devices, need 5 for complete body visualization.")
            return
        
        # Use the first five devices found
        torso_address = devices[0]['address']
        left_arm_address = devices[1]['address']
        right_arm_address = devices[2]['address']
        left_leg_address = devices[3]['address']
        right_leg_address = devices[4]['address']
        
        logger.info(f"Using sensor {torso_address} for torso")
        logger.info(f"Using sensor {left_arm_address} for left arm")
        logger.info(f"Using sensor {right_arm_address} for right arm")
        logger.info(f"Using sensor {left_leg_address} for left leg")
        logger.info(f"Using sensor {right_leg_address} for right leg")
    
    # Create and show the visualization
    viz = BodyVisualizer()
    
    # Start sensor collection in a separate thread
    sensor_thread = threading.Thread(
        target=run_sensor_collection,
        args=(torso_address, left_arm_address, right_arm_address, 
              left_leg_address, right_leg_address, args.duration),
        daemon=True  # Daemon thread will exit when main thread exits
    )
    sensor_thread.start()
    
    # Show visualization (this blocks until window is closed)
    logger.info("Starting visualization. Close the window or press Ctrl+C to exit.")
    viz.show()
    
    # Wait for sensor thread to complete
    sensor_thread.join(timeout=1.0)

if __name__ == "__main__":
    main()