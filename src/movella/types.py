from dataclasses import dataclass
from typing import Tuple

@dataclass
class QuaternionData:
    def __init__(self, 
                 timestamp: int = 0,
                 quaternion: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
                 free_acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 angular_velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
                ):
        self.timestamp = timestamp
        self.quaternion = quaternion
        self.free_acceleration = free_acceleration
        self.acceleration = acceleration
        self.angular_velocity = angular_velocity
    
    @property
    def quaternion(self) -> Tuple[float, float, float, float]:
        """Returns the quaternion as a tuple (w, x, y, z)"""
        return (self.quat_w, self.quat_x, self.quat_y, self.quat_z)
    
    @property
    def free_acceleration(self) -> Tuple[float, float, float]:
        """Returns the free acceleration as a tuple (x, y, z)"""
        return (self.free_acc_x, self.free_acc_y, self.free_acc_z)
    
    def is_quaternion_normalized(self, tolerance: float = 0.1) -> bool:
        """Check if quaternion is normalized (w²+x²+y²+z² ≈ 1)"""
        norm = sum(q*q for q in self.quaternion)
        return abs(norm - 1.0) <= tolerance