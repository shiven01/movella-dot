"""
Enhanced arm model for Movella DOT visualization.

This module contains classes for representing a three-segment arm model
with shoulder, elbow, and wrist joints using quaternion-based orientation.
"""

import numpy as np

class ArmSegment:
    """Represents a segment of an arm (e.g., upper arm, forearm, hand)"""
    
    def __init__(self, name, length=1.0, start_point=np.array([0, 0, 0])):
        self.name = name
        self.length = length
        self.start_point = start_point
        self.end_point = start_point + np.array([0, 0, length])
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion (w, x, y, z)
    
    def update_orientation(self, quaternion):
        """Update segment orientation with new quaternion"""
        self.quaternion = quaternion
        
    def get_transformed_points(self):
        """Get the start and end points with quaternion rotation applied"""
        # Vector representing the segment in local coordinates
        local_vector = np.array([0, 0, self.length])
        
        # Apply rotation to the vector using quaternion
        rotated_vector = self.rotate_vector_by_quaternion(local_vector, self.quaternion)
        
        # Calculate end point based on start point and rotated vector
        end_point = self.start_point + rotated_vector
        
        return self.start_point, end_point
    
    @staticmethod
    def rotate_vector_by_quaternion(v, q):
        """Rotate a vector v by quaternion q"""
        # Convert quaternion to (w, x, y, z) format
        w, x, y, z = q
        
        # Quaternion rotation formula: v' = q * v * q^-1
        # This is equivalent to the formula below which is computationally more efficient
        
        # Compute the vector part of the quaternion rotation
        t = 2.0 * (y * v[2] - z * v[1])
        u = 2.0 * (z * v[0] - x * v[2])
        s = 2.0 * (x * v[1] - y * v[0])
        
        # Apply the rotation
        rotated_v = np.array([
            v[0] + w * t + y * s - z * u,
            v[1] + w * u + z * t - x * s,
            v[2] + w * s + x * u - y * t
        ])
        
        return rotated_v

class ArmModel:
    """Represents a complete arm with three segments and two joints (shoulder, elbow, and wrist)"""
    
    def __init__(self):
        # Create upper arm segment (shoulder to elbow)
        self.upper_arm = ArmSegment("upper_arm", length=0.8, start_point=np.array([0, 0, 0]))
        
        # Create forearm segment (elbow to wrist)
        self.forearm = ArmSegment("forearm", length=0.7, start_point=np.array([0, 0, 0.8]))
        
        # Create hand segment (wrist to fingertips)
        self.hand = ArmSegment("hand", length=0.4, start_point=np.array([0, 0, 1.5]))
        
        # Initialize quaternions
        self.upper_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        self.forearm_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        self.hand_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        
        # Relative quaternions (for joint angles)
        self.elbow_relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        self.wrist_relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
    
    def update_from_sensors(self, upper_quat, forearm_quat, hand_quat):
        """Update arm model with new sensor quaternions for all three segments"""
        # Store original quaternions
        self.upper_quaternion = upper_quat
        self.forearm_quaternion = forearm_quat
        self.hand_quaternion = hand_quat
        
        # Calculate relative quaternion for elbow (rotation of forearm relative to upper arm)
        self.elbow_relative_quaternion = self.multiply_inverse_quaternion(
            self.upper_quaternion, self.forearm_quaternion)
        
        # Calculate relative quaternion for wrist (rotation of hand relative to forearm)
        self.wrist_relative_quaternion = self.multiply_inverse_quaternion(
            self.forearm_quaternion, self.hand_quaternion)
        
        # Update upper arm with its quaternion
        self.upper_arm.update_orientation(self.upper_quaternion)
        
        # Get upper arm end point, which is forearm start point
        _, elbow_point = self.upper_arm.get_transformed_points()
        
        # Update forearm start point and orientation
        self.forearm.start_point = elbow_point
        self.forearm.update_orientation(self.forearm_quaternion)
        
        # Get forearm end point, which is hand start point
        _, wrist_point = self.forearm.get_transformed_points()
        
        # Update hand start point and orientation
        self.hand.start_point = wrist_point
        self.hand.update_orientation(self.hand_quaternion)
    
    @staticmethod
    def multiply_inverse_quaternion(q1, q2):
        """Calculate q1^-1 * q2 (rotation of q2 relative to q1)"""
        # Quaternion inverse: q^-1 = conjugate(q) / |q|^2
        # For unit quaternions, q^-1 = conjugate(q) = [w, -x, -y, -z]
        q1_inv = np.array([q1[0], -q1[1], -q1[2], -q1[3]])
        
        # Quaternion multiplication: q1 * q2
        w1, x1, y1, z1 = q1_inv
        w2, x2, y2, z2 = q2
        
        result = np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,  # w component
            w1*x2 + x1*w2 + y1*z2 - z1*y2,  # x component
            w1*y2 - x1*z2 + y1*w2 + z1*x2,  # y component
            w1*z2 + x1*y2 - y1*x2 + z1*w2   # z component
        ])
        
        # Normalize the result
        norm = np.sqrt(np.sum(result**2))
        if norm > 0:
            result = result / norm
            
        return result