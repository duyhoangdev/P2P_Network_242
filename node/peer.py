import os
import socket
import threading
import json

stop_event = threading.Event()

def send_piece(conn, file_path):
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            conn.sendall(chunk)

def handle_peer_request(conn, addr):
    try:
        data = conn.recv(4096).decode()
        command = json.loads(data)
        if command["action"] == "request_piece":
            piece_path = f"{command['file_name']}_piece{command['piece_index']}"
            if os.path.exists(piece_path):
                send_piece(conn, piece_path)
    finally:
        conn.close()

def start_peer_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen()
    server.settimeout(1)
    while not stop_event.is_set():
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_peer_request, args=(conn, addr)).start()
        except socket.timeout:
            continue
    server.close()

class PieceDownloader(threading.Thread):
    def __init__(self, ip, port, file_name, piece_index):
        super().__init__()
        self.ip = ip
        self.port = port
        self.file_name = file_name
        self.piece_index = piece_index

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.ip, self.port))
            sock.sendall(json.dumps({
                "action": "request_piece",
                "file_name": self.file_name,
                "piece_index": self.piece_index
            }).encode())
            with open(f"{self.file_name}_piece{self.piece_index}", "wb") as f:
                while chunk := sock.recv(4096):
                    f.write(chunk)
            print(f"Downloaded piece {self.piece_index} of {self.file_name}")
        finally:
            sock.close()