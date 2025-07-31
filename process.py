import socket
import threading
import time
from utils import LamportClock, log_event

class Process:
    def __init__(self, process_id, port, peers):
        self.process_id = process_id
        self.port = port
        self.peers = peers
        self.clock = LamportClock()
        self.state = {"counter": 0, "status": "ON"}
        self.snapshot = None
        self.received_markers = set()
        self.running = True

    def start(self):
        threading.Thread(target=self._run_server, daemon=True).start()
        threading.Thread(target=self._generate_events, daemon=True).start()

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("localhost", self.port))
            server.listen()
            while self.running:
                conn, _ = server.accept()
                threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()

    def _handle_connection(self, conn):
        with conn:
            data = conn.recv(1024).decode()
            if data.startswith("MARKER"):
                self._handle_marker(data)
            else:
                self._handle_message(data)

    def _handle_message(self, data):
        sender_id, timestamp = map(int, data.split(","))
        self.clock.update(timestamp)
        self.clock.increment()
        log_event(f"Process {self.process_id} received message from {sender_id} with timestamp {timestamp}. Clock: {self.clock.time}")

    def _handle_marker(self, data):
        sender_id = int(data.split(",")[1])
        if self.snapshot is None:
            self.snapshot = self.state.copy()
            log_event(f"Process {self.process_id} recorded snapshot: {self.snapshot}")
        self.received_markers.add(sender_id)
        if len(self.received_markers) == len(self.peers):
            log_event(f"Process {self.process_id} completed snapshot collection.")

    def _generate_events(self):
        while self.running:
            time.sleep(2)
            self.clock.increment()
            self.state["counter"] += 1
            log_event(f"Process {self.process_id} generated internal event. Clock: {self.clock.time}")
            self._send_message()

    def _send_message(self):
        self.clock.increment()
        for peer_port in self.peers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("localhost", peer_port))
                sock.sendall(f"{self.process_id},{self.clock.time}".encode())
        log_event(f"Process {self.process_id} sent message. Clock: {self.clock.time}")

    def initiate_snapshot(self):
        self.snapshot = self.state.copy()
        log_event(f"Process {self.process_id} initiated snapshot: {self.snapshot}")
        for peer_port in self.peers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("localhost", peer_port))
                sock.sendall(f"MARKER,{self.process_id}".encode())
