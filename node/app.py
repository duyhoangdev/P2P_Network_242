import streamlit as st
import os

import requests


from client import login, publish_file, fetch_file, SERVER_HOST, SERVER_PORT
from peer import start_peer_server, PieceDownloader
from file_handler import merge_pieces_into_file, check_local_pieces
import socket
import threading

st.set_page_config(page_title="P2P File Sharing", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "peer_id" not in st.session_state:
    st.session_state.peer_id = f"node-{socket.gethostname()}-{os.getpid()}"
if "port" not in st.session_state:
    st.session_state.port = 65435
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
            st.session_state.current_file = file.name
            st.session_state.info_hash = info_hash
            st.success(f"Published {file.name} with {len(pieces)} pieces")

    with tab2:
        file_name = st.text_input("Enter file name to fetch")
        if st.button("Fetch"):
            peers = fetch_file(st.session_state.token, file_name, st.session_state.info_hash or "",
                               st.session_state.peer_id, ip, st.session_state.port)
            if peers:
                st.write("Available peers:", peers)
                threads = []
                for i, peer in enumerate(peers, 1):
                    downloader = PieceDownloader(peer["ip"], peer["port"], file_name, i)
                    threads.append(downloader)
                    downloader.start()
                for t in threads:
                    t.join()
                pieces = check_local_pieces(file_name)
                if pieces:
                    merge_pieces_into_file(pieces, file_name)
                    st.success(f"Downloaded and merged {file_name}")
            else:
                st.error("No peers found")


if st.session_state.token:
    main_page()
else:
    login_page()