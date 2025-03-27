import json

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
# from . import models, schemas, crud, auth, database
from tracker import models, schemas, crud, auth, database


from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

models.Base.metadata.create_all(bind=database.engine)

@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.create_user(db, user)
    token = auth.create_access_token(data={"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# @app.post("/publish", response_model=schemas.FileCreate)
# def publish_file(file: schemas.FileCreate, db: Session = Depends(database.get_db),
#                 current_user: models.User = Depends(auth.get_current_user)):
#     db_file = crud.get_file_by_info_hash(db, file.info_hash)
#     if db_file:
#         try:
#             db_file.piece_hashes = json.loads(db_file.piece_hashes)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=500, detail="Invalid JSON format in piece_hashes")
#         return db_file
#     return crud.create_file(db, file)
@app.post("/publish", response_model=schemas.FileCreate)
def publish_file(file: schemas.FileCreate, db: Session = Depends(database.get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    try:
        db_torrent = crud.get_torrent_by_info_hash(db, file.info_hash)
        if db_torrent:
            return schemas.FileCreate(
                name=db_torrent.name,
                size=db_torrent.total_size,
                info_hash=db_torrent.info_hash,
                piece_length=db_torrent.piece_length,
                piece_hashes=json.loads(db_torrent.piece_hashes)
            )
        return crud.create_torrent(db, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
@app.get("/announce", response_model=schemas.AnnounceResponse)
def announce(
    announce: schemas.AnnounceRequest = Depends(),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        # Lấy torrent theo info_hash
        torrent = crud.get_torrent_by_info_hash(db, announce.info_hash)
        if not torrent:
            raise HTTPException(status_code=404, detail="Torrent not found")

        # Tạo hoặc cập nhật peer
        peer = crud.create_or_update_peer(
            db,
            current_user.id,
            announce.peer_id,
            announce.ip,
            announce.port
        )

        # Xử lý sự kiện
        if announce.event == "started":
            crud.update_peer_status(db, peer.id, torrent.id, "active", announce)
        elif announce.event == "completed":
            crud.update_peer_status(db, peer.id, torrent.id, "seeding", announce)
        elif announce.event == "stopped":
            crud.update_peer_status(db, peer.id, torrent.id, "stopped", announce)

        # Lấy danh sách peers
        peers = crud.get_peers_for_torrent(db, torrent.id)

        # Trả về response
        return schemas.AnnounceResponse(
            peers=peers,
            tracker_id="your-tracker-id",
            interval=1800
        )
    except HTTPException as e:
        raise e  # Ném lại HTTPException nếu có
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
@app.get("/test")
def test():
    return {"message": "Test successful"}