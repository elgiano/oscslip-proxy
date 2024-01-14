from .serial_proxy import SerialOSCProxy
from .osc_server import OSCServerThread
from serial.serialutil import SerialException
from time import sleep
import argparse


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--osc_port', type=int, default=58000,
                        help="osc port listening for outbound messages")
    parser.add_argument('-s', '--serial_port', type=str, default='/dev/ttyACM0',
                        help="serial port")
    parser.add_argument('-b', '--baudrate', type=int, default=115200,
                        help="baudrate")
    parser.add_argument('-t', '--timeout', type=int, default=None,
                        help="timeout")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="print messages")
    parser.add_argument('receiver_ports', type=int, nargs='*', default=[57120],
                        help="osc receivers (57120)")
    return parser.parse_args()


def main():
    args = get_arguments()
    recv = [('127.0.0.1', p) for p in args.receiver_ports]
    print("[OSC] forwarding serial-osc to:")
    for r in recv:
        print(r)
    serial = SerialOSCProxy(args.serial_port, args.baudrate,
                            args.timeout, recv, args.verbose)
    osc_server = OSCServerThread(args.osc_port, serial, args.verbose)
    osc_server.start()
    while True:
        try:
            serial.open_serial()
            serial.receive()
        except SerialException:
            serial.close_serial()
            print('[Serial] Disconnected: retrying in 3s...')
            try:
                sleep(3)
            except KeyboardInterrupt:
                break
        except KeyboardInterrupt:
            break

    print('\nexiting...')
    osc_server.stop()
    serial.close_serial()


if __name__ == "__main__":
    main()
