import serial
from oscslip_proxy.slipDecoder import SlipDecoder
from time import sleep
from pythonosc.udp_client import UDPClient
from pythonosc.osc_bundle import OscBundle
from pythonosc.osc_message import OscMessage
from queue import Queue, Empty


class SerialOSCProxy():
    def __init__(self, portT, bd=115200, to=None, osc_receivers=[], verbose=True):
        self.port, self.baudrate, self.timeout = portT, bd, to
        self.stopEvent = False
        self.slipDecoder = SlipDecoder()
        self.osc_clients = [UDPClient(
            addr, port) for (addr, port) in osc_receivers]
        self.out_message_queue = Queue()
        self.verbose = verbose

    def forward_outbound_messages(self, ser):
        while not self.out_message_queue.empty():
            try:
                data = self.out_message_queue.get_nowait()
                packet = self.slipDecoder.encodeToSLIP(data)
                ser.write(packet)
            except Empty:
                break

    def forward_incoming_messages(self, ser):
        res = self.slipDecoder.decodeFromSLIP(
            ser.read(16))  # 16 bytes
        if res:
            msg = self.get_osc_message(bytes(res))
            if msg is not None:
                for c in self.osc_clients:
                    c.send(msg)

    def handshake(self, ser):
        sleep(1)
        # first clear anything on the incoming port
        ser.timeout = 0
        while ser.read():
            pass
        ser.timeout = self.timeout
        # now give the handshake!
        sleep(1)
        ser.write(b'|')
        sleep(1)

    def serve(self):
        print(
            f'[Serial] opening port {self.port} (baud: {self.baudrate}, timeout: {self.timeout})')
        with serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout) as ser:
            self.handshake(ser)
            print('Started... ctrl-C to exit')
            while True:
                try:
                    if self.stopEvent:
                        print('\nexiting...')
                        break
                    self.forward_incoming_messages(ser)
                    self.forward_outbound_messages(ser)
                except KeyboardInterrupt:
                    self.stopEvent = True

    def get_osc_message(self, dgram):
        if OscBundle.dgram_is_bundle(dgram):
            msg = OscBundle(dgram)
        elif OscMessage.dgram_is_message(dgram):
            msg = OscMessage(dgram)
        else:
            print(f'WARNING: unrecognized dgram {dgram}')
            return None
        if self.verbose:
            print('<', end=' ')
            self.print_osc(msg)
        return msg

    def print_osc(self, msg):
        if msg.__class__ == OscBundle:
            print('[')
            for m in msg:
                print('-', end=' ')
                self.print_osc(m)
            print(']')
        elif msg.__class__ == OscMessage:
            print(msg.address, msg.params)
