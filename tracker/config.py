import os
# class Config:
#     SQLALCHEMY_DATABASE_URI = "postgresql://postgres:12345@localhost:5432/p2p"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SECRET_KEY = "b9a8d1a2f5b6484f96e7a9c3babc5e64ff3e6a29d3f4e7c1e8b7a6f2c4d5e8f7"
class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://avnadmin:AVNS_iFffmdh8OuBUzvvrjJZ@pg-6a52d21-jimminhmai03-5622.e.aivencloud.com:27582/defaultdb?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "b9a8d1a2f5b6484f96e7a9c3babc5e64ff3e6a29d3f4e7c1e8b7a6f2c4d5e8f7"
