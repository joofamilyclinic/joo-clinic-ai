from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import requests
import datetime
import os

app = Flask(__name__)

ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "https://hooks.zapier.com/hooks/catch/your-zap-id/")

@app.route("/", methods=["GET"])
def home():
    return "✅ Joo Family Clinic Webhook is running."

@app.route("/webhook/voice", methods=["POST"])
def voice_webhook():
    response = VoiceResponse()
    gather = Gather(num_digits=1, action="/webhook/language", method="POST", timeout=5)
    gather.say("Welcome to Joo Family Clinic. For English, press 1. For Korean, press 2. For Spanish, press 3.", language="en-US")
    response.append(gather)
    response.redirect("/webhook/voice")
    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/language", methods=["POST"])
def language_handler():
    digit = request.form.get("Digits", "")
    response = VoiceResponse()

    if digit == "1":
        response.say("You selected English. Please leave a message after the beep.", language="en-US")
    elif digit == "2":
        response.say("\ud55c\uad6d\uc5b4\ub97c \uc120\ud0dd\ud558\uc154\uc694. \ube44 \uc18d\uc758 \uc18c\ub9ac \ud6c4\uc5d0 \uba54\uc2dc\uc9c0\ub97c \ub0a8\uaca8 \uc8fc\uc138\uc694.", language="ko-KR")
    elif digit == "3":
        response.say("Seleccion\u00f3 espa\u00f1ol. Por favor deje un mensaje despu\u00e9s del tono.", language="es-MX")
    else:
        response.say("Invalid selection. Goodbye.", language="en-US")
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    response.record(
        timeout=10,
        max_length=60,
        action="/webhook/recording_done",
        play_beep=True,
        transcribe=True,
        transcribe_callback="/webhook/transcription_done"
    )
    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/recording_done", methods=["POST"])
def recording_done():
    recording_url = request.form.get("RecordingUrl")
    caller = request.form.get("From")
    timestamp = datetime.datetime.utcnow().isoformat()

    try:
        requests.post(ZAPIER_WEBHOOK_URL, json={
            "caller": caller,
            "recording_url": recording_url,
            "timestamp": timestamp
        })
    except Exception as e:
        print("Zapier error:", str(e))

    response = VoiceResponse()
    response.say("Thank you. Your message has been received.", language="en-US")
    response.hangup()
    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/transcription_done", methods=["POST"])
def transcription_done():
    transcription_text = request.form.get("TranscriptionText")
    recording_url = request.form.get("RecordingUrl")
    caller = request.form.get("From")
    timestamp = datetime.datetime.utcnow().isoformat()

    try:
        requests.post(ZAPIER_WEBHOOK_URL, json={
            "caller": caller,
            "recording_url": recording_url,
            "transcription": transcription_text,
            "timestamp": timestamp
        })
    except Exception as e:
        print("Zapier error:", str(e))

    return Response("OK", mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

