#!/usr/bin/env python3
"""
Movella DOT Three-Segment Arm Visualization Application

This script serves as the main entry point for the enhanced arm visualization application,
which connects to three Movella DOT sensors and visualizes a complete arm with
shoulder, elbow, and wrist joints in 3D.
"""

import logging
import sys
import argparse

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArmApp")

def main():
    """
    Main entry point for the application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Visualize complete arm using three Movella DOT sensors")
    parser.add_argument("-u", "--upper", help="Bluetooth address of upper arm sensor")
    parser.add_argument("-f", "--forearm", help="Bluetooth address of forearm sensor")
    parser.add_argument("-h", "--hand", help="Bluetooth address of hand sensor", dest="hand_sensor")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Scan timeout in seconds")
    parser.add_argument("-d", "--duration", type=float, default=60.0, help="Streaming duration in seconds")
    args = parser.parse_args()
    
    try:
        # Import the visualization module
        from arm.visualizer import main as visualizer_main
        
        # Run the visualizer
        visualizer_main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Error running application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())