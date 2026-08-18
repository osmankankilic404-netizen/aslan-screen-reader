# Piper TTS Otomatik Türkçe Ses Sürücüsü
import os, urllib.request

VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx"
JSON_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx.json"

class SynthDriver:
    name = "piper"
    description = "Piper TTS (Türkçe)"
