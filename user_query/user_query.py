import os
import json
import argparse
import datetime
import sounddevice as sd
import scipy.io.wavfile as wav
from google.cloud import texttospeech
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
import random
import uuid
import simpleaudio as sa
import numpy as np

# === CONFIG ===
SERVICE_ACCOUNT_PATH = os.getenv("GCP_T5_SVC_ACC_KEY" ,"./tachyon5-svc-key.json")
PROJECT_ID = os.getenv("GCP_PROJECT", "genuine-space-465418-e3")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_PATH

vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-2.5-flash", generation_config=GenerationConfig(response_mime_type="application/json"))

tts_client = texttospeech.TextToSpeechClient()

lang_code_map = {
    "Hindi": "hi-IN", "Tamil": "ta-IN", "Telugu": "te-IN",
    "Kannada": "kn-IN", "Malayalam": "ml-IN", "Bengali": "bn-IN",
    "Marathi": "mr-IN", "Gujarati": "gu-IN", "English": "en-US"
}

def fetch_firestore_data(username: str):
    """
    Generate a sample dataset for the given username.
    Returns exactly 10 records dated randomly within the past 3 months.
    """
    base = datetime.datetime.utcnow()
    results = []
    for _ in range(10):
        days_ago = random.randint(0, 89)
        ts = (base - datetime.timedelta(days=days_ago)).isoformat()
        docid = str(uuid.uuid4())
        metadata = {
            "documentId": docid,
            "username": username,
            "timestamp": ts,
            "gstNumber": f"{random.randint(100000000000,999999999999)}",
            "additionalInfo": {"store_type": random.choice(["Pharmacy","Grocery","Clothing"])},
            "tags": random.sample(["food","health","electronics","home"], 2)
        }
        item = {
            "document_id": docid,
            "item_name": random.choice(["dolo-650","paracetamol","syrup"]),
            "item_type": "medicine",
            "quantity": random.randint(1,20),
            "price": round(random.uniform(10,200),2),
            "validity": f"{random.randint(10,60)} days"
        }
        results.append({"documentId": docid, "metadata": metadata, "item": item})
    results.sort(key=lambda x: x["metadata"]["timestamp"], reverse=True)
    return results

def record_audio(filename="input.wav", duration=7, fs=16000):
    print("Recording for 7 sec... Please talk")
    rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()
    wav.write(filename, fs, rec)
    print("Recording complete.")

def detect_lang_and_translate(audio_path, username):
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    part = Part.from_data(data=audio_data, mime_type="audio/wav")
    prompt = f"""
This prompt is for: {username}
Please detect the spoken language, transcribe the speech, and translate it into English.
Respond ONLY in valid JSON:
{{"language": "...", "transcription": "...", "translation": "..."}}
"""
    resp = model.generate_content([prompt, part])
    text = resp.text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        clean = text.strip("```").strip()
        return json.loads(clean)

def gemini_search(query, cache, username):
    prompt = f"""
This prompt is for: {username}
Search the following Firestore database content and return only the relevant information as JSON.

Database:
{json.dumps(cache)}

User Query: "{query}"
"""
    resp = model.generate_content(prompt)
    return resp.text.strip()

def summarize_response(json_data, username):
    prompt = f"""
This prompt is for: {username}
Summarize the following JSON in English in a short and friendly way:

{json_data}
"""
    resp = model.generate_content(prompt)
    return resp.text.strip()

def translate_to_local(text, lang, username):
    prompt = f"""
This prompt is for: {username}
Translate the following into {lang}. Do not add any extra info. Just raw text.

{text}
"""
    resp = model.generate_content(prompt)
    return resp.text.strip()

def speak(text, lang_code):
    synth_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
    response = tts_client.synthesize_speech(
        input=synth_input,
        voice=voice,
        audio_config=audio_config
    )

    audio_bytes = response.audio_content
    # Convert bytes to numpy array for simpleaudio
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
    wave_obj = sa.WaveObject(audio_array, num_channels=1, bytes_per_sample=2, sample_rate=16000)
    play_obj = wave_obj.play()
    play_obj.wait_done()

def process_query(name, type, query=None ):
    data = fetch_firestore_data(name)
    if not data:
        print(f"No recent records found for user '{name}'.")
        return

    if type == "voice":
        record_audio()
        res = detect_lang_and_translate("input.wav", name)
        if not res:
            print("Could not parse audio. Exiting.")
            return
        lang = res["language"]
        query_en = res["translation"]
    else:
        if not query:
            print("Error: Provide --query when using text mode.")
            return
        query_en = query
        detect_prompt = f"""
This prompt is for: {name}
Detect the language of the following query and respond ONLY with the language name:

{query_en}
"""
        lang = model.generate_content(detect_prompt).text.strip()

    print(f"\n[Detected Language: {lang}]\nQuery: {query_en}")

    search_json = gemini_search(query_en, data, name)
    print("\nSearch Response length:\n", len(search_json))

    summary = summarize_response(search_json, name)
    translated = translate_to_local(summary, lang, name)

    print("\nFinal Response:\n", translated)
    if type == "voice":
        speak(translated, lang_code_map.get(lang, "en-US"))
    else:
        return translated
