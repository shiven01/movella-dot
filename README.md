# Movella DOT Quaternion Data Streaming

A Python-based tool to connect to Movella DOT sensors via Bluetooth Low Energy (BLE) and stream quaternion data in real-time. Built using `bleak` for BLE communication and `numpy` for data parsing.

## Features

- **BLE Connectivity**: Connect to Movella DOT sensors using their MAC address.
- **Real-Time Data Streaming**: Stream Extended Quaternion data (40-byte payloads) from the sensor.
- **Firmware 3.0.0 Support**: Compatible with the latest Movella DOT firmware.
- **Data Parsing**: Parse raw BLE packets into structured quaternion data.
- **Logging**: Detailed logs for debugging and monitoring.

## Prerequisites

- Python 3.8+
- [Bleak](https://github.com/hbldh/bleak) BLE library
- [NumPy](https://numpy.org/) for data parsing
- Movella DOT sensor with firmware 3.0.0

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/movella-dot-quaternion.git
   cd movella-dot-quaternion
