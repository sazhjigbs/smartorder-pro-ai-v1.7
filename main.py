from fastapi import FastAPI
import os, psutil, json

app = FastAPI(title="SMARTORDER PRO AI v1.8-FINAL")

@app.get("/health")
def health():
    return {"ok": True, "ver": "1.8-final", "cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent}

@app.get("/")
def index():
    return {"msg": "SMARTORDER PRO AI v1.8 is running!"}
