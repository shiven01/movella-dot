"""
3D visualization for a realistic three-segment arm model.

This module visualizes a complete arm with upper arm, forearm, and hand segments
tracked by three Movella DOT sensors.
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

# Import from our arm modules
from arm.model import ArmSegment, ArmModel
from arm.utils import calibrate_sensors
from arm.sensor import process_quaternion_for_arm_viz, run_sensor_collection

# Import from existing Movella modules
from movella.multi.multi_client import MultiMovellaDotClient
from movella.types import QuaternionData
from utils.scanner import scan_for_movella_devices

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArmViz")

class ArmVisualizer:
    """Handles 3D visualization of the three-segment arm model"""
    
    def __init__(self):
        # Create a 3D figure
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Initialize the arm model
        self.arm_model = ArmModel()
        
        # Initialize animation properties
        self.ani = None
        self.last_update_time = 0
        
        # Line objects for visualization
        self.upper_arm_line = None
        self.forearm_line = None
        self.hand_line = None
        self.elbow_point = None
        self.wrist_point = None
        
        # Initialize the visualization
        self._init_visualization()
    
    def _init_visualization(self):
        """Initialize the visualization elements"""
        # Get initial points from the arm model
        upper_start, elbow_point = self.arm_model.upper_arm.get_transformed_points()
        forearm_start, wrist_point = self.arm_model.forearm.get_transformed_points()
        hand_start, hand_end = self.arm_model.hand.get_transformed_points()
        
        # Create lines for arm segments
        self.upper_arm_line, = self.ax.plot([upper_start[0], elbow_point[0]],
                                          [upper_start[1], elbow_point[1]],
                                          [upper_start[2], elbow_point[2]],
                                          'b-', linewidth=4, label='Upper Arm')
        
        self.forearm_line, = self.ax.plot([forearm_start[0], wrist_point[0]],
                                        [forearm_start[1], wrist_point[1]],
                                        [forearm_start[2], wrist_point[2]],
                                        'r-', linewidth=4, label='Forearm')
                                        
        self.hand_line, = self.ax.plot([hand_start[0], hand_end[0]],
                                      [hand_start[1], hand_end[1]],
                                      [hand_start[2], hand_end[2]],
                                      'g-', linewidth=4, label='Hand')
        
        # Add points to represent the joints
        self.elbow_point, = self.ax.plot([elbow_point[0]], [elbow_point[1]], [elbow_point[2]],
                                       'ro', markersize=8, label='Elbow')
                                       
        self.wrist_point, = self.ax.plot([wrist_point[0]], [wrist_point[1]], [wrist_point[2]],
                                       'go', markersize=8, label='Wrist')
        
        # Set axis properties
        self.ax.set_xlim([-2, 2])
        self.ax.set_ylim([-2, 2])
        self.ax.set_zlim([-0.5, 2.5])
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Three-Segment Arm Visualization')
        
        # Add a legend
        self.ax.legend()
        
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
                # Extract quaternions for all three segments
                upper_quat = latest_data['upper_arm']
                forearm_quat = latest_data['forearm']
                hand_quat = latest_data['hand']
                
                # Update the arm model with all three quaternions
                self.arm_model.update_from_sensors(upper_quat, forearm_quat, hand_quat)
                
                # Update visualization
                upper_start, elbow_point = self.arm_model.upper_arm.get_transformed_points()
                forearm_start, wrist_point = self.arm_model.forearm.get_transformed_points()
                hand_start, hand_end = self.arm_model.hand.get_transformed_points()
                
                # Update line data
                self.upper_arm_line.set_data_3d([upper_start[0], elbow_point[0]],
                                              [upper_start[1], elbow_point[1]],
                                              [upper_start[2], elbow_point[2]])
                
                self.forearm_line.set_data_3d([forearm_start[0], wrist_point[0]],
                                            [forearm_start[1], wrist_point[1]],
                                            [forearm_start[2], wrist_point[2]])
                                            
                self.hand_line.set_data_3d([hand_start[0], hand_end[0]],
                                         [hand_start[1], hand_end[1]],
                                         [hand_start[2], hand_end[2]])
                
                # Update joint points
                self.elbow_point.set_data_3d([elbow_point[0]], [elbow_point[1]], [elbow_point[2]])
                self.wrist_point.set_data_3d([wrist_point[0]], [wrist_point[1]], [wrist_point[2]])
                
                # Calculate and display joint angles
                elbow_angle = self.calculate_joint_angle(self.arm_model.elbow_relative_quaternion)
                wrist_angle = self.calculate_joint_angle(self.arm_model.wrist_relative_quaternion)
                
                self.ax.set_title(f'Arm Visualization - Elbow: {elbow_angle:.1f}° | Wrist: {wrist_angle:.1f}°')
        
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
        
        # Return all artists that need to be redrawn
        return [self.upper_arm_line, self.forearm_line, self.hand_line,
                self.elbow_point, self.wrist_point]
    
    def calculate_joint_angle(self, rel_quat):
        """Calculate the angle of a joint in degrees from a relative quaternion"""
        # For a unit quaternion [w, x, y, z], the angle is 2*arccos(w)
        angle_rad = 2 * np.arccos(np.clip(rel_quat[0], -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
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
    """Main function to run the arm visualization"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Visualize complete arm using three Movella DOT sensors")
    parser.add_argument("-u", "--upper", help="Bluetooth address of upper arm sensor")
    parser.add_argument("-f", "--forearm", help="Bluetooth address of forearm sensor")
    parser.add_argument("-h", "--hand", help="Bluetooth address of hand sensor", dest="hand_sensor")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Scan timeout in seconds")
    parser.add_argument("-d", "--duration", type=float, default=60.0, help="Streaming duration in seconds")
    args = parser.parse_args()
    
    # Determine sensor addresses
    upper_address = args.upper
    forearm_address = args.forearm
    hand_address = args.hand_sensor
    
    # If addresses not provided, scan for devices
    if not (upper_address and forearm_address and hand_address):
        logger.info("Scanning for Movella DOT devices...")
        devices = asyncio.run(scan_for_movella_devices(args.timeout))
        
        if len(devices) < 3:
            logger.error(f"Found only {len(devices)} devices, need at least 3 for complete arm visualization.")
            return
        
        # Use the first three devices found
        upper_address = devices[0]['address']
        forearm_address = devices[1]['address']
        hand_address = devices[2]['address']
        
        logger.info(f"Using sensor {upper_address} for upper arm")
        logger.info(f"Using sensor {forearm_address} for forearm")
        logger.info(f"Using sensor {hand_address} for hand")
    
    # Create and show the visualization
    viz = ArmVisualizer()
    
    # Start sensor collection in a separate thread
    sensor_thread = threading.Thread(
        target=run_sensor_collection,
        args=(upper_address, forearm_address, hand_address, args.duration),
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