import streamlit as st
import os

import requests
import struct
from collections import defaultdict
from client import login, publish_file, fetch_file, SERVER_HOST, SERVER_PORT, announce
from peer import start_peer_server, PieceDownloader
from file_handler import merge_pieces_into_file, check_local_pieces
import socket
import threading

st.set_page_config(page_title="P2P File Sharing", layout="wide")
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Hệ thống tự chọn một cổng trống
        return s.getsockname()[1]

if "token" not in st.session_state:
    st.session_state.token = None
if "peer_id" not in st.session_state:
    st.session_state.peer_id = f"node-{socket.gethostname()}-{os.getpid()}"
if "port" not in st.session_state:
    st.session_state.port = get_free_port()  # Dùng cổng động thay vì 65435
    threading.Thread(target=start_peer_server, args=(st.session_state.port,), daemon=True).start()


def login_page():
    st.title("Login / Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        token = login(username, password)
        if token:
            st.session_state.token = token
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials")
    if st.button("Register"):
        response = requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/register",
                                 json={"username": username, "password": password})
        if response.status_code == 200:
            st.success("Registered successfully! Please login.")
        else:
            st.error("Registration failed")

def generate_magnet_link(info_hash):
    return f"magnet:?xt=urn:btih:{info_hash}"




def get_available_pieces(peer, info_hash, peer_id):
    """
    Lấy danh sách các piece mà peer sở hữu bằng cách kết nối và nhận bitfield.

    Args:
        peer (dict): Thông tin peer từ tracker, chứa "ip" và "port".
        info_hash (str): Chuỗi định danh của torrent.
        peer_id (str): Định danh của client.

    Returns:
        list: Danh sách các chỉ số piece mà peer có.
    """
    # Thiết lập kết nối đến peer
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((peer["ip"], peer["port"]))

        # Gửi handshake theo giao thức BitTorrent
        handshake = (b'\x13BitTorrent protocol' + b'\x00' * 8 +
                     info_hash.encode() + peer_id.encode())
        sock.sendall(handshake)

        # Nhận handshake từ peer
        peer_handshake = sock.recv(68)  # Handshake có độ dài cố định 68 byte
        if peer_handshake[28:48] != info_hash.encode():
            raise ValueError("Handshake không khớp info_hash")

        # Nhận thông điệp bitfield
        len_prefix = sock.recv(4)  # Độ dài thông điệp
        message_len = struct.unpack(">I", len_prefix)[0]
        message_id = sock.recv(1)  # ID của thông điệp
        if message_id == b'\x05':  # ID 5 là bitfield
            bitfield = sock.recv(message_len - 1)
            # Phân tích bitfield thành danh sách piece
            available_pieces = []
            for i in range(len(bitfield) * 8):  # Mỗi byte có 8 bit
                if (bitfield[i // 8] & (1 << (7 - i % 8))) != 0:
                    available_pieces.append(i)
            return available_pieces
        else:
            return []  # Peer không gửi bitfield ngay lập tức
    except Exception as e:
        print(f"Lỗi khi kết nối tới peer {peer['ip']}:{peer['port']}: {e}")
        return []
    finally:
        sock.close()


def fetch_file(token, file_name, info_hash, peer_id, ip, port):
    peers = announce(token, info_hash, peer_id, ip, port, 0, 0, 0)
    if not peers:
        st.error("No peers found")
        return None

    piece_availability = defaultdict(list)
    for peer in peers:
        available_pieces = get_available_pieces(peer, info_hash, peer_id)  # Thêm peer_id
        for piece_idx in available_pieces:
            piece_availability[piece_idx].append(peer)

    rarity = {piece_idx: len(peers_list) for piece_idx, peers_list in piece_availability.items()}
    sorted_pieces = sorted(piece_availability.keys(), key=lambda p: rarity[p])

    requested_pieces = set()
    threads = []
    for piece_idx in sorted_pieces:
        if piece_idx not in requested_pieces:
            peer = piece_availability[piece_idx][0]
            downloader = PieceDownloader(peer["ip"], peer["port"], file_name, piece_idx)
            threads.append(downloader)
            requested_pieces.add(piece_idx)
            downloader.start()

    for t in threads:
        t.join()

    pieces = check_local_pieces(file_name)
    if pieces:
        merge_pieces_into_file(pieces, file_name)
        st.success(f"Đã tải và ghép xong file {file_name}")
    else:
        st.error("Không thể tải đủ các piece để ghép file")

    return peers


def main_page():
    st.title("P2P File Sharing")
    ip = socket.gethostbyname(socket.gethostname())

    tab1, tab2 = st.tabs(["Publish File", "Fetch File"])

    with tab1:
        file = st.file_uploader("Choose a file to publish")
        if file and st.button("Publish"):
            with open(file.name, "wb") as f:
                f.write(file.read())
            info_hash, pieces = publish_file(st.session_state.token, file.name, st.session_state.peer_id, ip,
                                             st.session_state.port)
            st.session_state.current_file = file.name  # Still useful for tracking the current file locally
            st.session_state.info_hash = info_hash  # Optional, for local reference
            st.success(f"Published {file.name} with {len(pieces)} pieces")
            # Generate and display the magnet link
            magnet_link = generate_magnet_link(info_hash)
            st.write(f"Share this magnet link: {magnet_link}")

    with tab2:
        magnet_link = st.text_input("Enter magnet link to fetch")
        if st.button("Fetch"):
            import urllib.parse
            # Parse the magnet link
            try:
                parsed = urllib.parse.urlparse(magnet_link)
                query_params = urllib.parse.parse_qs(parsed.query)
                xt = query_params.get("xt", [""])[0]
                if not xt.startswith("urn:btih:"):
                    st.error("Invalid magnet link: missing info_hash")
                    return
                info_hash = xt[9:]  # Extract info_hash after "urn:btih:"
                # Optionally extract file name from 'dn' (display name) parameter
                file_name = query_params.get("dn", ["unknown"])[0]

                # Fetch the file using the extracted info_hash
                peers = fetch_file(
                    st.session_state.token,
                    file_name,
                    info_hash,
                    st.session_state.peer_id,
                    ip,
                    st.session_state.port
                )
                if peers:
                    st.write("Available peers:", peers)
                    # Existing download logic
                    total_pieces = len(check_local_pieces(file_name)) or 1
                    progress_bar = st.progress(0)
                    threads = []
                    for i, peer in enumerate(peers, 1):
                        downloader = PieceDownloader(peer["ip"], peer["port"], file_name, i)
                        threads.append(downloader)
                        downloader.start()
                    completed = 0
                    for t in threads:
                        t.join()
                        completed += 1
                        progress_bar.progress(completed / total_pieces)
                    pieces = check_local_pieces(file_name)
                    if pieces:
                        merge_pieces_into_file(pieces, file_name)
                        st.success(f"Downloaded and merged {file_name}")
                    else:
                        st.error("No pieces downloaded.")
                else:
                    st.error("No peers found")
            except Exception as e:
                st.error(f"Error parsing magnet link: {e}")

if st.session_state.token:
    main_page()
else:
    login_page()