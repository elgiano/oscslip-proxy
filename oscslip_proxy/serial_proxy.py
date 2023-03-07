import serial
from sliplib import SlipStream
from pythonosc.udp_client import UDPClient
from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage


def print_osc(msg):
    if msg.__class__ == OscBundle:
        print('[')
        for m in msg:
            print('-', end=' ')
            print_osc(m)
        print(']')
    elif msg.__class__ == OscMessage:
        print(msg.address, msg.params)


class SerialOSCProxy():
    def __init__(self, port, bd=115200, to=None, osc_receivers=[], verbose=True):
        print("[OSC] forwarding to:")
        for recv in osc_receivers:
            print(recv)
        self.port, self.baudrate, self.timeout = port, bd, to
        self.osc_clients = [
            UDPClient(addr, port) for (addr, port) in osc_receivers
        ]
        self.serial = None
        self.slipCodec = None
        self.verbose = verbose

    def open_serial(self):
        print(
            f'[Serial] opening port {self.port} (baud: {self.baudrate}, timeout: {self.timeout})')
        self.serial = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.slipCodec = SlipStream(self.serial, 1)

    def close_serial(self):
        if self.serial is not None:
            self.serial.close()

    def serve(self):
        if self.serial is None:
            print("[Serial] no serial connection.")
            return
        print('Started... ctrl-C to exit')
        for msg in self.slipCodec:
            msg = self.get_osc_message(msg)
            if (msg is not None):
                if (self.verbose):
                    print('<', end='')
                    print_osc(msg)
                for c in self.osc_clients:
                    c.send(msg)

    def get_osc_message(self, dgram):
        if OscBundle.dgram_is_bundle(dgram):
            msg = OscBundle(dgram)
        elif OscMessage.dgram_is_message(dgram):
            msg = OscMessage(dgram)
        else:
            print(f'WARNING: unrecognized dgram {dgram}')
            return None
        return msg

