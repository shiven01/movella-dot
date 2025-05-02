"""
Enhanced body model for Movella DOT visualization.

This module contains classes for representing a multi-segment body model
with joints for torso, arms, and legs using quaternion-based orientation.
"""

import numpy as np

class BodySegment:
    """Represents a segment of a body (e.g., torso, upper arm, thigh)"""
    
    def __init__(self, name, length=1.0, start_point=np.array([0, 0, 0]), color='b'):
        """
        Initialize a body segment
        
        Args:
            name: Name of this segment
            length: Length of the segment
            start_point: 3D coordinates of the start point
            color: Color to use when visualizing this segment
        """
        self.name = name
        self.length = length
        self.start_point = start_point
        self.end_point = start_point + np.array([0, 0, length])
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion (w, x, y, z)
        self.color = color
    
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

class BodyModel:
    """Represents a complete body with torso, arms, and legs using 5 sensors"""
    
    def __init__(self):
        # Dimensions are approximate and can be adjusted
        # Torso (vertical, from hip to shoulder)
        self.torso = BodySegment("torso", length=0.7, start_point=np.array([0, 0, 0]), color='g')
        
        # Arms (from shoulder to wrist)
        shoulder_height = self.torso.length
        shoulder_width = 0.35  # Half-width from center to shoulder
        
        # Left arm segments
        self.left_arm = BodySegment(
            "left_arm", 
            length=0.6, 
            start_point=np.array([-shoulder_width, 0, shoulder_height]), 
            color='b'
        )
        
        # Right arm segments
        self.right_arm = BodySegment(
            "right_arm", 
            length=0.6, 
            start_point=np.array([shoulder_width, 0, shoulder_height]), 
            color='b'
        )
        
        # Legs (from hip to ankle)
        hip_width = 0.2  # Half-width from center to hip
        
        # Left leg segment
        self.left_leg = BodySegment(
            "left_leg", 
            length=0.8, 
            start_point=np.array([-hip_width, 0, 0]), 
            color='r'
        )
        
        # Right leg segment
        self.right_leg = BodySegment(
            "right_leg", 
            length=0.8, 
            start_point=np.array([hip_width, 0, 0]), 
            color='r'
        )
        
        # Initialize quaternions for all segments
        self.torso_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        self.left_arm_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.right_arm_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.left_leg_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.right_leg_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        
        # Relative quaternions (for joint angles)
        self.left_shoulder_relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.right_shoulder_relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.left_hip_relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.right_hip_relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
    
    def update_from_sensors(self, torso_quat, left_arm_quat, right_arm_quat, left_leg_quat, right_leg_quat):
        """Update body model with new sensor quaternions for all five segments"""
        # Store original quaternions
        self.torso_quaternion = torso_quat
        self.left_arm_quaternion = left_arm_quat
        self.right_arm_quaternion = right_arm_quat
        self.left_leg_quaternion = left_leg_quat
        self.right_leg_quaternion = right_leg_quat
        
        # Calculate relative quaternion for left shoulder
        self.left_shoulder_relative_quaternion = self.multiply_inverse_quaternion(
            self.torso_quaternion, self.left_arm_quaternion)
        
        # Calculate relative quaternion for right shoulder
        self.right_shoulder_relative_quaternion = self.multiply_inverse_quaternion(
            self.torso_quaternion, self.right_arm_quaternion)
        
        # Calculate relative quaternion for left hip
        self.left_hip_relative_quaternion = self.multiply_inverse_quaternion(
            self.torso_quaternion, self.left_leg_quaternion)
        
        # Calculate relative quaternion for right hip
        self.right_hip_relative_quaternion = self.multiply_inverse_quaternion(
            self.torso_quaternion, self.right_leg_quaternion)
        
        # Update torso with its quaternion
        self.torso.update_orientation(self.torso_quaternion)
        
        # Get torso endpoints
        torso_start, torso_end = self.torso.get_transformed_points()
        
        # Update all limbs based on torso orientation
        # The torso rotation affects the start points of all limbs
        
        # Calculate the rotated shoulder points
        left_shoulder_local = np.array([-0.35, 0, self.torso.length])
        right_shoulder_local = np.array([0.35, 0, self.torso.length])
        
        left_shoulder_global = torso_start + self.torso.rotate_vector_by_quaternion(
            left_shoulder_local, self.torso_quaternion)
        right_shoulder_global = torso_start + self.torso.rotate_vector_by_quaternion(
            right_shoulder_local, self.torso_quaternion)
        
        # Calculate the rotated hip points
        left_hip_local = np.array([-0.2, 0, 0])
        right_hip_local = np.array([0.2, 0, 0])
        
        left_hip_global = torso_start + self.torso.rotate_vector_by_quaternion(
            left_hip_local, self.torso_quaternion)
        right_hip_global = torso_start + self.torso.rotate_vector_by_quaternion(
            right_hip_local, self.torso_quaternion)
        
        # Update limb start points and orientations
        self.left_arm.start_point = left_shoulder_global
        self.left_arm.update_orientation(self.left_arm_quaternion)
        
        self.right_arm.start_point = right_shoulder_global
        self.right_arm.update_orientation(self.right_arm_quaternion)
        
        self.left_leg.start_point = left_hip_global
        self.left_leg.update_orientation(self.left_leg_quaternion)
        
        self.right_leg.start_point = right_hip_global
        self.right_leg.update_orientation(self.right_leg_quaternion)
    
    def get_joint_angles(self):
        """Calculate and return all joint angles in degrees"""
        left_shoulder_angle = self.calculate_angle_from_quaternion(self.left_shoulder_relative_quaternion)
        right_shoulder_angle = self.calculate_angle_from_quaternion(self.right_shoulder_relative_quaternion)
        left_hip_angle = self.calculate_angle_from_quaternion(self.left_hip_relative_quaternion)
        right_hip_angle = self.calculate_angle_from_quaternion(self.right_hip_relative_quaternion)
        
        return {
            'left_shoulder': left_shoulder_angle,
            'right_shoulder': right_shoulder_angle,
            'left_hip': left_hip_angle,
            'right_hip': right_hip_angle
        }
    
    @staticmethod
    def calculate_angle_from_quaternion(quaternion):
        """Calculate angle in degrees from a quaternion"""
        # For a unit quaternion [w, x, y, z], the angle is 2*arccos(w)
        w = quaternion[0]
        angle_rad = 2 * np.arccos(np.clip(w, -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        
        return angle_deg
    
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