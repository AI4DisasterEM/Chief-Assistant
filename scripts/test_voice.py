"""Test Voice Transcription for Notes"""
import sys
import os
sys.path.insert(0, '.')

from src.notes.voice_transcription import VoiceTranscriber

def main():
    print("CHIEF Voice Transcription Test")
    print("=" * 40)
    
    transcriber = VoiceTranscriber()
    
    # Check if test audio file exists
    test_file = "test_audio.mp3"
    
    if os.path.exists(test_file):
        print(f"\n1. Transcribing {test_file}...")
        transcript = transcriber.transcribe_file(test_file)
        print(f"   Transcript: {transcript[:200]}...")
        
        print("\n2. Processing as note with action extraction...")
        result = transcriber.transcribe_and_process(test_file, source_type='file')
        
        print(f"\n   Session ID: {result['session_id']}")
        print(f"\n   Full Transcript:\n   {result['transcript']}")
        print(f"\n   Actions Found: {len(result['actions'])}")
        for action in result['actions']:
            print(f"   - {action.get('task', action.get('description', 'Unknown'))}")
        print(f"\n   Summary:\n   {result['summary']}")
    else:
        print(f"\n   No test audio file found.")
        print(f"\n   To test, place an audio file named 'test_audio.mp3' in:")
        print(f"   {os.getcwd()}")
        print(f"\n   Or record a voice memo on your phone and transfer it.")
        
        # Show that the transcriber is ready
        print("\n   Transcriber initialized successfully!")
        print("   Ready to transcribe when audio is provided.")
    
    print("\n✅ Voice transcription module ready!")

if __name__ == "__main__":
    main()
