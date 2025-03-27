import os

import requests
import socket
import json
from file_handler import calculate_piece_hash, calculate_info_hash, split_file_into_pieces

SERVER_HOST = "localhost"
SERVER_PORT = 8000

def create_torrent_file(file_path, tracker_url):
    pieces = split_file_into_pieces(file_path)
    piece_hashes = [calculate_piece_hash(open(p, "rb").read()) for p in pieces]
    file_info = {
        "announce": tracker_url,
        "info": {
            "name": os.path.basename(file_path),
            "piece_length": 524288,
            "pieces": piece_hashes,
            "length": os.path.getsize(file_path)
        }
    }
    info_hash = calculate_info_hash(file_info["info"])
    torrent_data = {
        "announce": tracker_url,
        "info": file_info["info"],
        "info_hash": info_hash
    }
    torrent_file_path = f"{file_path}.torrent"
    with open(torrent_file_path, "w") as f:
        json.dump(torrent_data, f)
    return torrent_file_path, info_hash
def login(username, password):
    response = requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/login",
                            data={"username": username, "password": password})
    return response.json()["access_token"] if response.status_code == 200 else None

def publish_file(token, file_path, peer_id, ip, port):
    pieces = split_file_into_pieces(file_path)
    piece_hashes = [calculate_piece_hash(open(p, "rb").read()) for p in pieces]
    file_info = {
        "name": os.path.basename(file_path),
        "size": os.path.getsize(file_path),
        "piece_length": 524288,
        "piece_hashes": piece_hashes
    }
    info_hash = calculate_info_hash(file_info)
    file_info["info_hash"] = info_hash
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/publish", json=file_info, headers=headers)
    announce(token, info_hash, peer_id, ip, port, 0, 0, file_info["size"], "started")
    return info_hash, pieces

def announce(token, info_hash, peer_id, ip, port, uploaded, downloaded, left, event=None):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "info_hash": info_hash,
        "peer_id": peer_id,
        "ip": ip,
        "port": port,
        "uploaded": uploaded,
        "downloaded": downloaded,
        "left": left,
        "event": event
    }
    response = requests.get(f"http://{SERVER_HOST}:{SERVER_PORT}/announce", params=params, headers=headers)
    print("Tracker response:", response.json())
    return response.json()["peers"] if response.status_code == 200 else []

def fetch_file(token, file_name, info_hash, peer_id, ip, port):
    peers = announce(token, info_hash, peer_id, ip, port, 0, 0, 0)  # Simplified left value
    return peers