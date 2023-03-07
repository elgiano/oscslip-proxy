import threading
import socketserver
from typing import List, Tuple
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import _is_valid_request


class _UDPForwardBytes(socketserver.BaseRequestHandler):
    """Forward datagrams to server as bytes, then call handlers"""

    def handle(self) -> None:
        try:
            self.server.forward_bytes(self.request[0])
        except Exception:
            print('Error sending message from osc to serial')
        self.server.dispatcher.call_handlers_for_packet(
            self.request[0], self.client_address)


class SlipOSCUDPServer(socketserver.UDPServer):
    """OSC server that forwards all incoming messages to serial"""

    def __init__(self, server_address: Tuple[str, int], slipSerial,
                 dispatcher: Dispatcher, bind_and_activate=True) -> None:
        super().__init__(server_address, _UDPForwardBytes, bind_and_activate)
        self.slipSerial = slipSerial
        self._dispatcher = dispatcher

    def forward_bytes(self, data):
        self.slipSerial.send_msg(data)

    def verify_request(self, request: List[bytes],
                       client_address: Tuple[str, int]) -> bool:
        return _is_valid_request(request)

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher


class OSCServerThread(threading.Thread):
    def __init__(self, port, slipSerial, verbose=True):
        super().__init__()
        self.server = SlipOSCUDPServer(('127.0.0.1', port), slipSerial, Dispatcher())
        if verbose:
            self.server.dispatcher.set_default_handler(self.print_msg)

    def run(self):
        print(f'[OSC] listening to port {self.server.server_address[1]}')
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def print_msg(self, path, *data):
        print('>', path, data)
