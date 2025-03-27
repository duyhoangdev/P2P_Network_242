from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class FileCreate(BaseModel):
    name: str
    size: int
    piece_length: int
    piece_hashes: List[str]
    info_hash: str

class AnnounceRequest(BaseModel):
    info_hash: str
    peer_id: str
    ip: str
    port: int
    uploaded: int
    downloaded: int
    left: int
    event: Optional[str] = None

class PeerInfo(BaseModel):
    peer_id: str
    ip: str
    port: int

class AnnounceResponse(BaseModel):
    peers: List[PeerInfo]
    tracker_id: str
    interval: int