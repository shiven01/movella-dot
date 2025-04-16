import queue
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import threading
import asyncio
import logging
from pathlib import Path

# Import the shared data queue
from shared.resources import data_queue

# Import from our new modules
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

# Global queue for passing quaternion data between threads
data_queue = queue.Queue()

class ArmVisualizer:
    """Handles 3D visualization of the arm model"""
    
    def __init__(self):
        # Create a 3D figure
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Initialize the arm model
        self.arm_model = ArmModel()
        
        # Initialize animation properties
        self.ani = None
        self.last_update_time = 0
        
        # Line objects for visualization
        self.upper_arm_line = None
        self.lower_arm_line = None
        self.joint_point = None
        
        # Initialize the visualization
        self._init_visualization()
    
    def _init_visualization(self):
        """Initialize the visualization elements"""
        # Get initial points from the arm model
        upper_start, upper_end = self.arm_model.upper_arm.get_transformed_points()
        lower_start, lower_end = self.arm_model.lower_arm.get_transformed_points()
        
        # Create lines for upper and lower arm segments
        self.upper_arm_line, = self.ax.plot([upper_start[0], upper_end[0]],
                                          [upper_start[1], upper_end[1]],
                                          [upper_start[2], upper_end[2]],
                                          'b-', linewidth=4, label='Upper Arm')
        
        self.lower_arm_line, = self.ax.plot([lower_start[0], lower_end[0]],
                                          [lower_start[1], lower_end[1]],
                                          [lower_start[2], lower_end[2]],
                                          'r-', linewidth=4, label='Lower Arm')
        
        # Add a point to represent the joint
        self.joint_point, = self.ax.plot([upper_end[0]], [upper_end[1]], [upper_end[2]],
                                       'go', markersize=10, label='Joint')
        
        # Set axis properties
        self.ax.set_xlim([-2, 2])
        self.ax.set_ylim([-2, 2])
        self.ax.set_zlim([-0.5, 2.5])
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Arm Joint Visualization')
        
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
                # Extract quaternions
                upper_quat = latest_data['upper_arm']
                lower_quat = latest_data['lower_arm']
                
                # Update the arm model
                self.arm_model.update_from_sensors(upper_quat, lower_quat)
                
                # Update visualization
                upper_start, upper_end = self.arm_model.upper_arm.get_transformed_points()
                lower_start, lower_end = self.arm_model.lower_arm.get_transformed_points()
                
                # Update line data
                self.upper_arm_line.set_data_3d([upper_start[0], upper_end[0]],
                                              [upper_start[1], upper_end[1]],
                                              [upper_start[2], upper_end[2]])
                
                self.lower_arm_line.set_data_3d([lower_start[0], lower_end[0]],
                                              [lower_start[1], lower_end[1]],
                                              [lower_start[2], lower_end[2]])
                
                # Update joint point
                self.joint_point.set_data_3d([upper_end[0]], [upper_end[1]], [upper_end[2]])
                
                # Calculate and display joint angle
                angle_degrees = self.calculate_joint_angle()
                self.ax.set_title(f'Arm Joint Visualization - Joint Angle: {angle_degrees:.1f}°')
        
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
        
        # Return all artists that need to be redrawn
        return [self.upper_arm_line, self.lower_arm_line, self.joint_point]
    
    def calculate_joint_angle(self):
        """Calculate the angle of the joint in degrees"""
        # For a simple angle calculation, we'll use the relative quaternion
        # Convert to axis-angle representation
        rel_quat = self.arm_model.relative_quaternion
        
        # Calculate the angle from the quaternion
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
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Visualize arm joint using Movella DOT sensors")
    parser.add_argument("-u", "--upper", help="Bluetooth address of upper arm sensor")
    parser.add_argument("-l", "--lower", help="Bluetooth address of lower arm sensor")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Scan timeout in seconds")
    parser.add_argument("-d", "--duration", type=float, default=60.0, help="Streaming duration in seconds")
    args = parser.parse_args()
    
    # Determine sensor addresses
    upper_address = args.upper
    lower_address = args.lower
    
    # If addresses not provided, scan for devices
    if not upper_address or not lower_address:
        logger.info("Scanning for Movella DOT devices...")
        devices = asyncio.run(scan_for_movella_devices(args.timeout))
        
        if len(devices) < 2:
            logger.error(f"Found only {len(devices)} devices, need at least 2 for arm visualization.")
            return
        
        # Use the first two devices found
        upper_address = devices[0]['address']
        lower_address = devices[1]['address']
        
        logger.info(f"Using sensor {upper_address} for upper arm")
        logger.info(f"Using sensor {lower_address} for lower arm")
    
    # Create and show the visualization
    viz = ArmVisualizer()
    
    # Start sensor collection in a separate thread
    sensor_thread = threading.Thread(
        target=run_sensor_collection,
        args=(upper_address, lower_address, args.duration),
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