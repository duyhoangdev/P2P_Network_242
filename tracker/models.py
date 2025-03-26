from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from .database import Base
import enum

class PeerStatus(enum.Enum):
    SEEDING = "SEEDING"
    LEECHING = "LEECHING"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    info_hash = Column(String, unique=True, index=True)
    name = Column(String)
    size = Column(Integer)
    piece_length = Column(Integer)
    piece_hashes = Column(String)  # JSON string chứa danh sách hash của các piece

class Peer(Base):
    __tablename__ = "peers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    peer_id = Column(String, unique=True, index=True)
    ip = Column(String)
    port = Column(Integer)

class PeerFile(Base):
    __tablename__ = "peer_files"
    id = Column(Integer, primary_key=True, index=True)
    peer_id = Column(Integer, ForeignKey("peers.id"))
    file_id = Column(Integer, ForeignKey("files.id"))
    status = Column(Enum(PeerStatus))
    uploaded = Column(Integer, default=0)
    downloaded = Column(Integer, default=0)
    left = Column(Integer)