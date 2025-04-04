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
    
    @quaternion.setter
    def quaternion(self, quat: Tuple[float, float, float, float]):
        """Sets quaternion components from a tuple (w, x, y, z)"""
        self.quat_w, self.quat_x, self.quat_y, self.quat_z = quat
    
    @property
    def free_acceleration(self) -> Tuple[float, float, float]:
        """Returns the free acceleration as a tuple (x, y, z)"""
        return (self.free_acc_x, self.free_acc_y, self.free_acc_z)
    
    @free_acceleration.setter
    def free_acceleration(self, acc: Tuple[float, float, float]):
        """Sets free acceleration components from a tuple (x, y, z)"""
        self.free_acc_x, self.free_acc_y, self.free_acc_z = acc
    
    def is_quaternion_normalized(self, tolerance: float = 0.1) -> bool:
        """Check if quaternion is normalized (w²+x²+y²+z² ≈ 1)"""
        norm = sum(q*q for q in self.quaternion)
        return abs(norm - 1.0) <= tolerance
    
    def to_dict(self) -> dict:
        """
        Convert this data to a dictionary suitable for JSON serialization
        
        Returns:
            Dictionary with all data components
        """
        w, x, y, z = self.quaternion
        ax, ay, az = self.free_acceleration
        acc_x, acc_y, acc_z = self.acceleration
        gyr_x, gyr_y, gyr_z = self.angular_velocity
        
        # Calculate quaternion norm
        quat_norm = sum(q*q for q in self.quaternion)
        
        return {
            "timestamp": self.timestamp,
            "quaternion": {
                "w": w,
                "x": x,
                "y": y,
                "z": z
            },
            "free_acceleration": {
                "x": ax,
                "y": ay,
                "z": az
            },
            "acceleration": {
                "x": acc_x,
                "y": acc_y,
                "z": acc_z
            },
            "angular_velocity": {
                "x": gyr_x,
                "y": gyr_y,
                "z": gyr_z
            },
            "quaternion_norm": quat_norm,
            "status": getattr(self, "status", 0)
        }