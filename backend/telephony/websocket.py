import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()

    print("MEDIA STREAM CONNECTED")

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            event = data.get("event")

            if event == "connected":
                print("STREAM EVENT: connected")

            elif event == "start":
                start = data.get("start", {})

                print(
                    "STREAM STARTED | "
                    f"StreamSid={start.get('streamSid')} | "
                    f"CallSid={start.get('callSid')} | "
                    f"Tracks={start.get('tracks')}"
                )

                print(
                    "AUDIO FORMAT | "
                    f"{start.get('mediaFormat')}"
                )

            elif event == "media":
                media = data.get("media", {})

                print(
                    "AUDIO RECEIVED | "
                    f"track={media.get('track')} | "
                    f"chunk={media.get('chunk')} | "
                    f"timestamp={media.get('timestamp')} ms"
                )

            elif event == "stop":
                print("MEDIA STREAM STOPPED")
                break

    except WebSocketDisconnect:
        print("MEDIA STREAM DISCONNECTED")