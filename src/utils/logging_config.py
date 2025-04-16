import logging
from pathlib import Path

def setup_logging(log_file_name: str = "movella_sensor.log", console_level: int = logging.INFO):
    """
    Set up logging configuration with file and console output
    
    Args:
        log_file_name: Name of the log file
        console_level: Logging level for console output
    """
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / log_file_name
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file,
        filemode='a'
    )

    console = logging.StreamHandler()
    console.setLevel(console_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    # Reduce verbosity of bleak library
    logging.getLogger('bleak').setLevel(logging.WARNING)
    
    return logging.getLogger('')