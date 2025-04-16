import numpy as np

class ArmSegment:
    """Represents a segment of an arm (e.g., upper arm, lower arm)"""
    
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
    """Represents an arm with upper and lower segments joined at one joint"""
    
    def __init__(self):
        # Create upper arm segment
        self.upper_arm = ArmSegment("upper_arm", length=1.0, start_point=np.array([0, 0, 0]))
        
        # Create lower arm segment - start point will be updated based on upper arm
        self.lower_arm = ArmSegment("lower_arm", length=1.0, start_point=np.array([0, 0, 1.0]))
        
        # Initialize quaternions
        self.upper_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        self.lower_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        self.relative_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
    
    def update_from_sensors(self, upper_quat, lower_quat):
        """Update arm model with new sensor quaternions"""
        # Store original quaternions
        self.upper_quaternion = upper_quat
        self.lower_quaternion = lower_quat
        
        # Calculate relative quaternion (rotation of lower arm relative to upper arm)
        self.relative_quaternion = self.multiply_inverse_quaternion(
            self.upper_quaternion, self.lower_quaternion)
        
        # Update upper arm with its quaternion
        self.upper_arm.update_orientation(self.upper_quaternion)
        
        # Get upper arm end point, which is lower arm start point
        _, end_point = self.upper_arm.get_transformed_points()
        
        # Update lower arm start point and orientation
        self.lower_arm.start_point = end_point
        self.lower_arm.update_orientation(self.lower_quaternion)
    
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