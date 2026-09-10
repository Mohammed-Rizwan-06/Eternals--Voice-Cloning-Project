from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter()


@router.post("/voice/incoming")
async def incoming_call(request: Request):
    form = await request.form()

    call_sid = form.get("CallSid")
    from_number = form.get("From")

    print(
        f"CALL RECEIVED | "
        f"CallSid={call_sid} | "
        f"From={from_number}"
    )

    response = VoiceResponse()

    start = response.start()

    start.stream(
        url="wss://dilation-walk-carload.ngrok-free.dev/media-stream",
        track="inbound_track"
    )

    response.say(
        "Welcome to VoxShield. Your call has been received."
    )

    return Response(
        content=str(response),
        media_type="application/xml",
    )