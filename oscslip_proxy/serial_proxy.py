import serial
from sliplib import SlipStream
from time import sleep
from pythonosc.udp_client import UDPClient
from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage
from queue import Queue, Empty


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
    def __init__(self, portT, bd=115200, to=None, osc_receivers=[], verbose=True):
        print("[OSC] forwarding to:")
        for recv in osc_receivers:
            print(recv)
        self.port, self.baudrate, self.timeout = portT, bd, to
        self.stopEvent = False
        self.osc_clients = [UDPClient(
            addr, port) for (addr, port) in osc_receivers]
        self.out_message_queue = Queue()
        self.verbose = verbose

    def forward_outbound_messages(self, ser):
        while not self.out_message_queue.empty():
            try:
                data = self.out_message_queue.get_nowait()
                self.slipDecoder.send_msg(data)
            except Empty:
                break

    def serve_autoreconnect(self):
        try:
            self.serve()
        except serial.serialutil.SerialException:
            print('[Serial] Disconnected: retrying in 3s...')
            sleep(3)
            self.serve_autoreconnect()

    def serve(self):
        print(
            f'[Serial] opening port {self.port} (baud: {self.baudrate}, timeout: {self.timeout})')
        with serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout) as ser:
            self.slipDecoder = SlipStream(ser, 1)
            print('Started... ctrl-C to exit')
            try:
                # read
                for msg in self.slipDecoder:
                    msg = self.get_osc_message(msg)
                    if (msg is not None):
                        print(msg.params)
                        if (self.verbose):
                            print('<', end='')
                            print_osc(msg)
                        for c in self.osc_clients:
                            c.send(msg)
                    self.forward_outbound_messages(ser)
            except KeyboardInterrupt:
                print('\nexiting...')

    def get_osc_message(self, dgram):
        if OscBundle.dgram_is_bundle(dgram):
            msg = OscBundle(dgram)
        elif OscMessage.dgram_is_message(dgram):
            msg = OscMessage(dgram)
        else:
            print(f'WARNING: unrecognized dgram {dgram}')
            return None
        return msg

