from fastapi import FastAPI

from backend.telephony.routes import router as telephony_router
from backend.telephony.websocket import router as websocket_router


app = FastAPI(title="VoxShield Backend")

app.include_router(telephony_router)
app.include_router(websocket_router)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "voxshield-backend"
    }