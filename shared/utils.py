import hashlib

def calculate_hash(data):
    return hashlib.sha1(data).hexdigest()