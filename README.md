# Movella DOT Quaternion Data Streaming

A Python-based tool to connect to Movella DOT sensors via Bluetooth Low Energy (BLE) and stream quaternion data in real-time. Built using `bleak` for BLE communication and `numpy` for data parsing.

## Features

- **BLE Connectivity**: Connect to Movella DOT sensors using their MAC address.
- **Real-Time Data Streaming**: Stream Extended Quaternion data (40-byte payloads) from the sensor.
- **Multi-Sensor Support**: Connect to and stream data from multiple Movella DOT sensors simultaneously.
- **Auto-Discovery**: Automatically find Movella DOT devices in range.
- **Firmware 3.0.0 Support**: Compatible with the latest Movella DOT firmware.
- **Data Parsing**: Parse raw BLE packets into structured quaternion data.
- **Logging**: Detailed logs for debugging and monitoring.

## Prerequisites

- Python 3.8+
- [Bleak](https://github.com/hbldh/bleak) BLE library
- [NumPy](https://numpy.org/) for data parsing
- Matplotlib for visualization (optional)
- Movella DOT sensor with firmware 3.0.0

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/movella-dot-quaternion.git
   cd movella-dot-quaternion

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate

3. Install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate

## Device Scanner

Use the scanner to find Movella DOT devices in range:
```python src/utils/scanner.py [options]```

Options:
 - ```-t, --timeout SECONDS```: Scan duration in seconds (default: 5.0)
 - ```-i, --interactive```: Run in interactive mode to select devices

## Multi-Sensor Usage
Connect to and stream data from multiple Movella DOT sensors:
```python src/multi_main.py [options]```

Options:
 - ```-t, --timeout SECONDS```: Scan duration in seconds (default: 5.0)
 - ```-d, --duration SECONDS```: Streaming duration in seconds (default: 10.0)
 - ```-a, --addresses [ADDR1 ADDR2 ...]```: Specify Bluetooth addresses of sensors
 - ```--json```: Output data in JSON format
 - ```--output FILENAME```: Output JSON to a file (default: sensor_readings.json)
 - ```--pretty```: Format JSON with indentation

## Real-Time Visualization
Visualize sensor orientation in real-time:
```python src/realtime_visualization.py [options]```

Options:
 - ```-t, --timeout SECONDS```: Scan duration in seconds (default: 5.0)
 - ```-d, --duration SECONDS```: Streaming duration in seconds (default: 10.0)
 - ```-a, --addresses [ADDR1 ADDR2 ...]```: Specify Bluetooth addresses of sensors
 - ```--json```: Output data in JSON format
 - ```--output FILENAME```: Output JSON to a file (default: sensor_readings.json)
