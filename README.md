# oscslip-proxy
Run an OSC server for bidirectional SLIP encoded OSC communication over a serial transport.

## Installation
```
pip install oscslip-proxy
```

## Requirements
```
pip install -r requirements.txt
```
- [python-osc](https://github.com/attwad/python-osc)
- [pyserial](https://github.com/pyserial/pyserial)
- [sliplib](https://github.com/rhjdjong/SlipLib)

## Usage
```
$ ./oscslip-proxy.py -h

usage: oscslip-proxy [-h] [-p OSC_PORT] [-s SERIAL_PORT] [-b BAUDRATE] [-t TIMEOUT] [-v] [receiver_ports ...]

positional arguments:
  receiver_ports        osc receivers (57120)

options:
  -h, --help            show this help message and exit
  -p OSC_PORT, --osc_port OSC_PORT
                        osc port listening for outbound messages
  -s SERIAL_PORT, --serial_port SERIAL_PORT
                        serial port
  -b BAUDRATE, --baudrate BAUDRATE
                        baudrate
  -t TIMEOUT, --timeout TIMEOUT
                        timeout
  -v, --verbose         print messages
```
