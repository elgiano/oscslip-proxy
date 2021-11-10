import socketserver
from typing import List, Tuple
import threading
from pythonosc.osc_server import _is_valid_request
from pythonosc.dispatcher import Dispatcher
from queue import Queue, Full


class _UDPQueuer(socketserver.BaseRequestHandler):
    """Just append datagrams to a queue, then call handlers"""

    def handle(self) -> None:
        try:
            self.server.queue.put(self.request[0])
        except Full:
            print('WARNING: out queue full')
        self.server.dispatcher.call_handlers_for_packet(
            self.request[0], self.client_address)


class QueueingOSCUDPServer(socketserver.UDPServer):
    """
        OSC server that adds incoming messages to a Queue.
        The queue is meant to be consumed by SerialServer to forward OSC via serial
    """

    def __init__(self, server_address: Tuple[str, int], queue: Queue, dispatcher: Dispatcher, bind_and_activate=True) -> None:
        super().__init__(server_address, _UDPQueuer, bind_and_activate)
        self.queue = queue
        self._dispatcher = dispatcher

    def verify_request(self, request: List[bytes], client_address: Tuple[str, int]) -> bool:
        return _is_valid_request(request)

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher


class OSCServerThread(threading.Thread):
    def __init__(self, port, msg_queue, verbose=True):
        super(OSCServerThread, self).__init__()
        self.port = port
        dispatcher = Dispatcher()
        if verbose:
            dispatcher.set_default_handler(self.print_message)
        self.server = QueueingOSCUDPServer(
            ('127.0.0.1', port), msg_queue, dispatcher)

    def run(self):
        print(f'[OSC] listening to port {self.port}')
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def print_message(self, path, *data):
        print('>', path, data)
