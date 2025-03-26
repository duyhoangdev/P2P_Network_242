import json

from sqlalchemy.orm import Session
from . import models, schemas, auth
from .models import PeerStatus

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_file(db: Session, file: schemas.FileCreate):
    # Convert Pydantic model to dictionary using model_dump()
    file_data = file.model_dump()

    # Convert piece_hashes list to a JSON string
    file_data['piece_hashes'] = json.dumps(file_data['piece_hashes'])

    # Create a new models.File instance from the dictionary
    db_file = models.File(**file_data)

    # Add to database, commit, and refresh
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file
def get_file_by_info_hash(db: Session, info_hash: str):
    return db.query(models.File).filter(models.File.info_hash == info_hash).first()

def create_or_update_peer(db: Session, user_id: int, peer_id: str, ip: str, port: int):
    peer = db.query(models.Peer).filter(models.Peer.peer_id == peer_id).first()
    if not peer:
        peer = models.Peer(user_id=user_id, peer_id=peer_id, ip=ip, port=port)
        db.add(peer)
    else:
        peer.ip = ip
        peer.port = port
    db.commit()
    db.refresh(peer)
    return peer

def update_peer_file(db: Session, peer_id: int, file_id: int, announce: schemas.AnnounceRequest):
    peer_file = db.query(models.PeerFile).filter(models.PeerFile.peer_id == peer_id, models.PeerFile.file_id == file_id).first()
    if not peer_file:
        # Sử dụng enum thay vì chuỗi
        status = PeerStatus.SEEDING if announce.event == "completed" else PeerStatus.LEECHING
        peer_file = models.PeerFile(
            peer_id=peer_id,
            file_id=file_id,
            status=status,
            uploaded=announce.uploaded,
            downloaded=announce.downloaded,
            left=announce.left
        )
        db.add(peer_file)
    else:
        if announce.event == "completed":
            peer_file.status = PeerStatus.SEEDING
        # Nếu muốn cập nhật trạng thái cho trường hợp khác, bạn có thể thêm else nữa
        peer_file.uploaded = announce.uploaded
        peer_file.downloaded = announce.downloaded
        peer_file.left = announce.left
    db.commit()
    return peer_file

def get_peers_for_file(db: Session, file_id: int):
    peer_files = db.query(models.PeerFile).filter(models.PeerFile.file_id == file_id).all()
    peers = [db.query(models.Peer).filter(models.Peer.id == pf.peer_id).first() for pf in peer_files]
    return [{"peer_id": p.peer_id, "ip": p.ip, "port": p.port} for p in peers if p]