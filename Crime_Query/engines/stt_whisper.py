import whisper

def transcribe_whisper(audio_file_path: str, model_name: str = "base"): # type: ignore
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_file_path)
    return result["text"]

