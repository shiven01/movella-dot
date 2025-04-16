import logging
import sys

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArmApp")

def main():
    """
    Main entry point for the application.
    """
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