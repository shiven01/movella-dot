import json
import time
import logging
from typing import Dict, List, Optional, TextIO, Union, Callable
from pathlib import Path
from movella.types import QuaternionData

class JsonStreamWriter:
    """
    Class to handle streaming output of sensor data in JSON format
    """
    def __init__(self, output_file: Optional[str] = None, pretty_print: bool = False):
        """
        Initialize JSON stream writer
        
        Args:
            output_file: Optional file path to write JSON output
            pretty_print: Whether to format JSON with indentation
        """
        self.output_file = output_file
        self.file_handle: Optional[TextIO] = None
        self.pretty_print = pretty_print
        self.data_buffer: List[Dict] = []
        
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(exist_ok=True, parents=True)
            self.file_handle = open(output_file, 'w')
            # Start a JSON array
            self.file_handle.write('[\n')
        
    def write_data(self, data_dict: Dict) -> None:
        """
        Write a data dictionary as JSON
        
        Args:
            data_dict: Dictionary with sensor data
        """
        # Add timestamp if not present
        if 'timestamp' not in data_dict:
            data_dict['timestamp'] = int(time.time() * 1000)
            
        json_str = json.dumps(data_dict, indent=2 if self.pretty_print else None)
        
        # Print to console
        print(json_str)
        
        # Write to file if configured
        if self.file_handle:
            if self.data_buffer:  # Not the first entry
                self.file_handle.write(',\n')
            self.file_handle.write(json_str)
            self.file_handle.flush()
            
        self.data_buffer.append(data_dict)
    
    def close(self) -> None:
        """Close the JSON stream and finalize the file"""
        if self.file_handle:
            self.file_handle.write('\n]')
            self.file_handle.close()
            self.file_handle = None
            logging.info(f"JSON data written to {self.output_file}")
            
    def get_buffer(self) -> List[Dict]:
        """Get the current data buffer"""
        return self.data_buffer

def create_single_sensor_callback(json_writer: JsonStreamWriter) -> Callable[[QuaternionData], None]:
    """
    Create a callback function for single sensor that writes to a JSON stream
    
    Args:
        json_writer: JsonStreamWriter instance to use for output
        
    Returns:
        Callback function to use with MovellaDotClient
    """
    def callback(quat_data: QuaternionData) -> None:
        json_writer.write_data(quat_data.to_dict())
    return callback

def create_multi_sensor_callback(json_writer: JsonStreamWriter) -> Callable[[str, QuaternionData], None]:
    """
    Create a callback function for multiple sensors that writes to a JSON stream
    
    Args:
        json_writer: JsonStreamWriter instance to use for output
        
    Returns:
        Callback function to use with MultiMovellaDotClient
    """
    def callback(sensor_id: str, quat_data: QuaternionData) -> None:
        data_dict = quat_data.to_dict()
        data_dict['sensor_id'] = sensor_id
        json_writer.write_data(data_dict)
    return callback