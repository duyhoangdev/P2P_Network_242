import os
import hashlib
import json

def calculate_piece_hash(piece_data):
    return hashlib.sha1(piece_data).hexdigest()

def calculate_info_hash(file_info):
    return hashlib.sha1(json.dumps(file_info).encode()).hexdigest()

def split_file_into_pieces(file_path, piece_length=524288):  # 512KB
    pieces = []
    with open(file_path, "rb") as f:
        counter = 1
        while True:
            piece_data = f.read(piece_length)
            if not piece_data:
                break
            piece_path = f"{file_path}_piece{counter}"
            with open(piece_path, "wb") as pf:
                pf.write(piece_data)
            pieces.append(piece_path)
            counter += 1
    return pieces

def merge_pieces_into_file(pieces, output_path):
    with open(output_path, "wb") as f:
        for piece in sorted(pieces, key=lambda x: int(x.split("_piece")[-1])):
            with open(piece, "rb") as pf:
                f.write(pf.read())
    print(f"File merged: {output_path}")

def check_local_pieces(file_name):
    return [f for f in os.listdir(".") if f.startswith(file_name + "_piece")]