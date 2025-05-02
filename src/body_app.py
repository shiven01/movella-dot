#!/usr/bin/env python3
"""
Movella DOT Five-Segment Body Visualization Application

This script serves as the main entry point for the body visualization application,
which connects to five Movella DOT sensors and visualizes a complete body with
torso, arms, and legs in 3D.
"""

import logging
import sys
import argparse
import asyncio

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BodyApp")

def main():
    """
    Main entry point for the application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Visualize full body using five Movella DOT sensors")
    parser.add_argument("-t", "--torso", help="Bluetooth address of torso sensor")
    parser.add_argument("-la", "--left_arm", help="Bluetooth address of left arm sensor")
    parser.add_argument("-ra", "--right_arm", help="Bluetooth address of right arm sensor")
    parser.add_argument("-ll", "--left_leg", help="Bluetooth address of left leg sensor")
    parser.add_argument("-rl", "--right_leg", help="Bluetooth address of right leg sensor")
    parser.add_argument("-d", "--duration", type=float, default=60.0, help="Streaming duration in seconds")
    parser.add_argument("--timeout", type=float, default=5.0, help="Scan timeout in seconds")
    parser.add_argument("--interactive", action="store_true", help="Use interactive scanner to select devices")
    args = parser.parse_args()
    
    try:
        # Import the visualization module
        from body.visualizer import main as visualizer_main
        
        # Import interactive scanner if needed
        if args.interactive:
            from utils.scanner import interactive_scan
            logger.info("Starting interactive device scanner...")
            selected_devices = asyncio.run(interactive_scan(args.timeout))
            
            if len(selected_devices) < 5:
                logger.error(f"Selected only {len(selected_devices)} devices, need 5 for body tracking.")
                return 1
                
            # Override command line arguments with selected devices
            args.torso = selected_devices[0]
            args.left_arm = selected_devices[1]
            args.right_arm = selected_devices[2]
            args.left_leg = selected_devices[3]
            args.right_leg = selected_devices[4]
            
            logger.info("Selected devices:")
            logger.info(f"Torso sensor: {args.torso}")
            logger.info(f"Left arm sensor: {args.left_arm}")
            logger.info(f"Right arm sensor: {args.right_arm}")
            logger.info(f"Left leg sensor: {args.left_leg}")
            logger.info(f"Right leg sensor: {args.right_leg}")
        
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