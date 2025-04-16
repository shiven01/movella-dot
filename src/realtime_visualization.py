import asyncio
import queue
import threading
import time
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.animation import FuncAnimation

# Import from Movella DOT package
from movella.multi.multi_client import MultiMovellaDotClient
from movella.types import QuaternionData
from utils.logging_config import setup_logging
from utils.scanner import scan_for_movella_devices

# Logging Setuop
setup_logging(log_file_name="movella_visualization.log")

# Global data queue for passing quaternion data between threads
data_queue = queue.Queue()
recording_data = []  # For saving data to a JSON file if requested

def quaternion_to_rotation_matrix(q):
    """Convert quaternion to rotation matrix."""
    w, x, y, z = q
    
    # Create rotation matrix from quaternion
    rotation_matrix = np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - w*z), 2*(x*z + w*y)],
        [2*(x*y + w*z), 1 - 2*(x*x + z*z), 2*(y*z - w*x)],
        [2*(x*z - w*y), 2*(y*z + w*x), 1 - 2*(x*x + y*y)]
    ])
    
    return rotation_matrix

def create_cuboid(size=(1, 0.6, 0.2)):
    """Create a cuboid with the given size."""
    dx, dy, dz = size[0]/2, size[1]/2, size[2]/2
    
    # Define the vertices
    vertices = np.array([
        [-dx, -dy, -dz],  # 0
        [dx, -dy, -dz],   # 1
        [dx, dy, -dz],    # 2
        [-dx, dy, -dz],   # 3
        [-dx, -dy, dz],   # 4
        [dx, -dy, dz],    # 5
        [dx, dy, dz],     # 6
        [-dx, dy, dz]     # 7
    ])
    
    # Define the faces (each face is defined by the indices of its vertices)
    faces = [
        [0, 1, 2, 3],  # Bottom face (-z)
        [4, 5, 6, 7],  # Top face (+z)
        [0, 1, 5, 4],  # Front face (-y)
        [2, 3, 7, 6],  # Back face (+y)
        [0, 3, 7, 4],  # Left face (-x)
        [1, 2, 6, 5]   # Right face (+x)
    ]
    
    # Define the edges (for drawing lines)
    edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],  # Bottom face edges
        [4, 5], [5, 6], [6, 7], [7, 4],  # Top face edges
        [0, 4], [1, 5], [2, 6], [3, 7]   # Connecting edges
    ]
    
    # Define colors for each face
    face_colors = ['r', 'g', 'b', 'y', 'c', 'm']
    
    return vertices, faces, edges, face_colors

class VisualizationManager:
    """Manages the 3D visualization of quaternion data"""
    
    def __init__(self):
        self.current_quaternion = [1.0, 0.0, 0.0, 0.0]  # Default identity quaternion
        self.current_timestamp = 0
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.vertices, self.faces, self.edges, self.face_colors = create_cuboid()
        
        # Initialize animation
        self.animation = FuncAnimation(
            self.fig,
            self.update_frame,
            interval=50,  # Update every 50ms (20 FPS)
            blit=False
        )
    
    def update_frame(self, frame):
        """Update function for animation - gets the latest quaternion from the queue"""
        # Try to get the latest quaternion data from the queue
        try:
            # Non-blocking to avoid freezing the animation
            # Get all available data and use the most recent
            latest_data = None
            while not data_queue.empty():
                latest_data = data_queue.get_nowait()
            
            if latest_data:
                self.current_quaternion = latest_data['quaternion']
                self.current_timestamp = latest_data['timestamp']
        except queue.Empty:
            pass  # No new data, use the previous quaternion
        
        # Update the visualization with the current quaternion
        self.ax.clear()
        
        # Set axis limits and labels
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.set_zlim(-2, 2)
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        # Keep axis equal to maintain cuboid proportions
        self.ax.set_box_aspect([1, 1, 1])
        
        # Convert quaternion to rotation matrix
        R = quaternion_to_rotation_matrix(self.current_quaternion)
        
        # Apply rotation to vertices
        rotated_vertices = np.array([np.dot(R, v) for v in self.vertices])
        
        # Plot each face
        for i, face_indices in enumerate(self.faces):
            # Get vertices for this face
            face_vertices = [rotated_vertices[j] for j in face_indices]
            
            # Create 3D polygon
            poly = Poly3DCollection([face_vertices], alpha=0.7)
            poly.set_facecolor(self.face_colors[i])
            self.ax.add_collection3d(poly)
        
        # Plot edges
        for edge in self.edges:
            x = [rotated_vertices[edge[0]][0], rotated_vertices[edge[1]][0]]
            y = [rotated_vertices[edge[0]][1], rotated_vertices[edge[1]][1]]
            z = [rotated_vertices[edge[0]][2], rotated_vertices[edge[1]][2]]
            self.ax.plot(x, y, z, 'k-', linewidth=1)
        
        # Add timestamp as title
        self.ax.set_title(f'Timestamp: {self.current_timestamp}')
        
        return self.ax
    
    def show(self):
        """Show the visualization window"""
        plt.tight_layout()
        plt.show()

def process_quaternion_for_viz(sensor_id: str, quat_data: QuaternionData) -> None:
    """Process quaternion data and add it to the queue for visualization"""
    # Extract the quaternion data
    data = {
        'sensor_id': sensor_id,
        'timestamp': quat_data.timestamp,
        'quaternion': quat_data.quaternion,
        'acceleration': quat_data.acceleration,
        'angular_velocity': quat_data.angular_velocity,
        'free_acceleration': quat_data.free_acceleration,
    }
    
    # Add to queue for visualization
    data_queue.put(data)
    
    # Record data if we're saving to a file
    recording_data.append({
        'timestamp': quat_data.timestamp,
        'quaternion': {
            'w': quat_data.quat_w,
            'x': quat_data.quat_x,
            'y': quat_data.quat_y,
            'z': quat_data.quat_z
        },
        'free_acceleration': {
            'x': quat_data.free_acc_x,
            'y': quat_data.free_acc_y,
            'z': quat_data.free_acc_z
        },
        'acceleration': {
            'x': quat_data.acceleration[0],
            'y': quat_data.acceleration[1],
            'z': quat_data.acceleration[2]
        },
        'angular_velocity': {
            'x': quat_data.angular_velocity[0],
            'y': quat_data.angular_velocity[1],
            'z': quat_data.angular_velocity[2]
        },
        'quaternion_norm': sum(q*q for q in quat_data.quaternion),
        'status': getattr(quat_data, 'status', 0),
        'sensor_id': sensor_id
    })
    
    # Also log the data for debugging
    logging.debug(f"Received data from {sensor_id}: {quat_data.quaternion}")

async def sensor_data_collection(addresses: List[str], duration: float, save_output: Optional[str] = None):
    """Collect data from sensors for the specified duration"""
    # Create multi-sensor client with our visualization callback
    multi_client = MultiMovellaDotClient(process_quaternion_for_viz)
    
    # Add sensors
    for i, address in enumerate(addresses):
        multi_client.add_sensor(address, f"Sensor-{i+1}")
    
    # Connect to all sensors
    connection_status = await multi_client.connect_all()
    
    # Check if at least one sensor connected successfully
    if not any(connection_status.values()):
        logging.error("Failed to connect to any Movella DOT sensors.")
        return
    
    # Log connection status for each sensor
    for address, status in connection_status.items():
        if status:
            logging.info(f"Connected successfully to {address}")
        else:
            logging.error(f"Failed to connect to {address}")
    
    try:
        # Start streaming from all connected sensors
        logging.info(f"Streaming quaternion data for {duration} seconds...")
        await multi_client.start_streaming_all(duration)
    finally:
        # Always ensure we disconnect from all sensors
        await multi_client.disconnect_all()
        logging.info("Disconnected from all sensors")
        
        # Save collected data if requested
        if save_output and recording_data:
            output_path = Path(save_output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(recording_data, f, indent=2)
            
            logging.info(f"Saved {len(recording_data)} data points to {output_path}")

def run_sensor_collection(addresses, duration, save_output):
    """Run the sensor data collection in a separate thread"""
    asyncio.run(sensor_data_collection(addresses, duration, save_output))

def main():
    parser = argparse.ArgumentParser(description="Visualize Movella DOT orientation in real-time")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, 
                        help="Scan duration in seconds")
    parser.add_argument("-d", "--duration", type=float, default=60.0,
                        help="Duration to stream data in seconds")
    parser.add_argument("-a", "--addresses", nargs='+', 
                        help="Bluetooth addresses of specific Movella DOT devices")
    parser.add_argument("--json", action="store_true",
                        help="Save data to JSON file")
    parser.add_argument("-o", "--output", type=str, default="sensor_readings.json",
                        help="Output JSON file path")
    args = parser.parse_args()
    
    # Determine sensor addresses - either from arguments or by scanning
    if args.addresses:
        addresses = args.addresses
    else:
        # Need to scan for devices
        devices = asyncio.run(scan_for_movella_devices(args.timeout))
        
        if not devices:
            logging.error("No Movella DOT devices found. Make sure sensors are powered on.")
            return
            
        print(f"Found {len(devices)} Movella DOT devices:")
        for i, device in enumerate(devices):
            print(f"{i+1}. {device['name']} [{device['address']}]")
        
        addresses = [device['address'] for device in devices]
    
    # Create and show the visualization
    viz_manager = VisualizationManager()
    
    # Determine if we should save output
    save_output = args.output if args.json else None
    
    # Start sensor collection in a separate thread
    sensor_thread = threading.Thread(
        target=run_sensor_collection,
        args=(addresses, args.duration, save_output),
        daemon=True  # Daemon thread will exit when main thread exits
    )
    sensor_thread.start()
    
    # Show visualization (this blocks until window is closed)
    viz_manager.show()
    
    # Wait for sensor thread to complete
    sensor_thread.join(timeout=1.0)

if __name__ == "__main__":
    main()