from typing import Optional
from movella.types import QuaternionData

def default_single_sensor_callback(data: QuaternionData) -> None:
    """Default callback that prints quaternion data without sensor ID"""
    print(f"Quaternion: {data.quaternion}")
    print(f"Timestamp: {data.timestamp}")
    print(f"Acceleration: {data.acceleration}")
    print(f"Angular Velocity: {data.angular_velocity}")

def default_multi_sensor_callback(sensor_id: str, data: QuaternionData) -> None:
    """Default callback that prints quaternion data with sensor ID"""
    print(f"Sensor {sensor_id}:")
    default_single_sensor_callback(data)