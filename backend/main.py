from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
os.makedirs("output", exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output files at /output/*
app.mount(
    "/output",
    StaticFiles(directory="output"),
    name="output",
)

# Import routers (excluding history)
from backend.api import run, status, result, download
app.include_router(run.router)
app.include_router(status.router)
app.include_router(result.router)
# app.include_router(history.router)  # DISABLED: Not used in project
app.include_router(download.router)
