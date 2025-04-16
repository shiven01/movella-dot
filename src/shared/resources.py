import queue

# Global queue for passing quaternion data between threads
data_queue = queue.Queue()

# Other potential shared resources
latest_sensor_data = {}