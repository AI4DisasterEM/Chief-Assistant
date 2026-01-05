"""Voice Transcription for CHIEF Notes"""
import os
import json
import boto3
import tempfile
import requests
from datetime import datetime
from openai import OpenAI


def get_secret(secret_id):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_id)
    return json.loads(response['SecretString'])


def get_s3_client():
    return boto3.client('s3', region_name='us-east-1')


class VoiceTranscriber:
    def __init__(self):
        creds = get_secret('chief/openai-api-key')
        self.client = OpenAI(api_key=creds['api_key'])
        self.s3 = get_s3_client()
        
        # Get bucket name
        s3_config = get_secret('chief/s3-config')
        self.bucket = s3_config['bucket_name']
    
    def transcribe_file(self, audio_path):
        """Transcribe an audio file using Whisper"""
        with open(audio_path, 'rb') as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return response
    
    def transcribe_url(self, audio_url):
        """Download and transcribe audio from URL"""
        # Download audio to temp file
        response = requests.get(audio_url)
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        try:
            transcript = self.transcribe_file(tmp_path)
            return transcript
        finally:
            os.unlink(tmp_path)
    
    def transcribe_s3(self, s3_key):
        """Transcribe audio from S3"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            self.s3.download_file(self.bucket, s3_key, tmp.name)
            tmp_path = tmp.name
        
        try:
            transcript = self.transcribe_file(tmp_path)
            return transcript
        finally:
            os.unlink(tmp_path)
    
    def save_audio_to_s3(self, audio_data, filename=None):
        """Save audio to S3 and return the key"""
        if not filename:
            filename = f"audio/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp3"
        
        self.s3.put_object(
            Bucket=self.bucket,
            Key=filename,
            Body=audio_data
        )
        
        return filename
    
    def transcribe_and_process(self, audio_source, source_type='file'):
        """Transcribe audio and extract action items"""
        from .note_manager import NoteSession
        
        # Transcribe based on source type
        if source_type == 'file':
            transcript = self.transcribe_file(audio_source)
        elif source_type == 'url':
            transcript = self.transcribe_url(audio_source)
        elif source_type == 's3':
            transcript = self.transcribe_s3(audio_source)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # Create note session and add transcript
        notes = NoteSession()
        session_id = notes.start_session("Voice Note", workspace="operations")
        actions, msg = notes.add_entry(session_id, transcript, input_type="voice")
        summary, _ = notes.end_session(session_id)
        
        return {
            'session_id': session_id,
            'transcript': transcript,
            'actions': actions,
            'summary': summary
        }


def handle_twilio_voice_message(media_url, from_number):
    """Handle incoming voice/audio message from Twilio"""
    transcriber = VoiceTranscriber()
    
    # Transcribe the audio
    transcript = transcriber.transcribe_url(media_url)
    
    # Process as a note
    result = transcriber.transcribe_and_process(media_url, source_type='url')
    
    return result
