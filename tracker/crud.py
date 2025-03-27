import json

from fastapi import HTTPException
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


def create_file(db: Session, torrent_id: int, name: str, size: int, offset: int):
    db_file = models.File(torrent_id=torrent_id, name=name, size=size, offset=offset)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file
def create_torrent(db: Session, file: schemas.FileCreate):
    file_data = file.model_dump()
    # Chuyển đổi piece_hashes sang JSON string
    file_data['piece_hashes'] = json.dumps(file_data['piece_hashes'])

    db_torrent = models.Torrent(
        info_hash=file_data['info_hash'],
        name=file_data['name'],
        total_size=file_data['size'],
        piece_length=file_data['piece_length'],
        piece_hashes=file_data['piece_hashes']
    )
    db.add(db_torrent)
    db.commit()
    db.refresh(db_torrent)
    return db_torrent


def get_torrent_by_info_hash(db: Session, info_hash: str):
    return db.query(models.Torrent).filter(models.Torrent.info_hash == info_hash).first()

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


def update_peer_status(db: Session, peer_id: int, torrent_id: int, new_status: str, announce: schemas.AnnounceRequest):
    # Lấy tất cả file của torrent
    files = db.query(models.File).filter(models.File.torrent_id == torrent_id).all()
    if not files:
        raise HTTPException(status_code=404, detail="No files found for this torrent")

    for file in files:
        peer_file = db.query(models.PeerFile).filter(
            models.PeerFile.peer_id == peer_id,
            models.PeerFile.file_id == file.id
        ).first()
        if not peer_file:
            # Tạo mới PeerFile nếu chưa có
            status = PeerStatus.LEECHING if new_status == "active" else PeerStatus.STOPPED
            peer_file = models.PeerFile(
                peer_id=peer_id,
                file_id=file.id,
                status=status,
                uploaded=announce.uploaded,
                downloaded=announce.downloaded,
                left=announce.left
            )
            db.add(peer_file)
        else:
            # Cập nhật trạng thái
            try:
                peer_file.status = models.PeerStatus(new_status.upper())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status value")
        db.commit()
        db.refresh(peer_file)
    return peer_file
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

def get_peers_for_torrent(db: Session, torrent_id: int):
    # Giả sử cần liên kết peers với torrent qua bảng trung gian mới
    # Đây chỉ là ví dụ, bạn cần điều chỉnh theo thiết kế thực tế
    files = db.query(models.File).filter(models.File.torrent_id == torrent_id).all()
    file_ids = [f.id for f in files]
    peer_files = db.query(models.PeerFile).filter(models.PeerFile.file_id.in_(file_ids)).all()
    peers = [db.query(models.Peer).filter(models.Peer.id == pf.peer_id).first() for pf in peer_files]
    return [{"peer_id": p.peer_id, "ip": p.ip, "port": p.port} for p in peers if p]
def get_peers_for_file(db: Session, file_id: int):
    peer_files = db.query(models.PeerFile).filter(models.PeerFile.file_id == file_id).all()
    peers = [db.query(models.Peer).filter(models.Peer.id == pf.peer_id).first() for pf in peer_files]
    return [{"peer_id": p.peer_id, "ip": p.ip, "port": p.port} for p in peers if p]