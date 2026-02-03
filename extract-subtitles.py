from moviepy import VideoFileClip
import whisper
import json
import os
import sys

VIDEO_PATH = "Beautiful Recitation of Surah Infitar (سورة الانفطار_).mp4"

# Whisper Settings
WHISPER_MODEL = "large-v3"  # Options: tiny, base, small, medium, large, large-v3
LANGUAGE = "ar"            
TASK = "transcribe"          

# Output Files
OUTPUT_TXT = "subtitles.txt"      
OUTPUT_SRT = "subtitles.srt"      
OUTPUT_JSON = "subtitles.json"    

SUBTITLE_DELAY = 1.2



def format_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_audio_from_video(video_path):
    
    video = VideoFileClip(video_path)
    audio_file = "temp_audio.wav"
    
    
    video.audio.write_audiofile(
        audio_file, 
        codec='pcm_s16le',
        logger=None
    )
    
    video.close()
    print(f"Audio extracted: {audio_file}")
    
    return audio_file


def transcribe_with_whisper(audio_file, language, task):
    """Transcribe audio using Whisper AI"""
    print(f"\n Loading Whisper AI model: {WHISPER_MODEL}")
    print("   (First time may take a while to download the model)")
    
    model = whisper.load_model(WHISPER_MODEL)
    print(" Model loaded successfully!")
    
    print(f"\n Transcribing audio...")
    print(f"   Language: {language}")
    print(f"   Task: {task}")
    print("   This may take several minutes...")
    
    result = model.transcribe(
        audio_file,
        language=language,
        task=task,
        initial_prompt="A clear English translation of Quranic recitation.",
        no_speech_threshold=0.6,
        condition_on_previous_text=False,
        verbose=False
    )
    
    print(f"Transcription complete!")
    print(f"   Detected {len(result['segments'])} subtitle segments")
    
    return result


def save_txt_format(subtitles, filename):
    """Save subtitles in custom TXT format (start | end | text)"""
    print(f"\n Saving TXT format: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Auto-generated Subtitles\n")
        f.write("# Format: start_time | end_time | text\n")
        f.write("# You can edit this file before adding to video\n\n")
        
        for sub in subtitles:
            f.write(f"{sub['start']:.2f} | {sub['end']:.2f} | {sub['text']}\n")
    
    print(f"Saved: {filename}")


def save_srt_format(subtitles, filename):
    """Save subtitles in SRT format"""
    print(f"\nSaving SRT format: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(sub['start'])} --> {format_srt_time(sub['end'])}\n")
            f.write(f"{sub['text']}\n\n")
    
    print(f"Saved: {filename}")


def save_json_format(subtitles, filename):
    """Save subtitles in JSON format (backup with all data)"""
    print(f"\n Saving JSON format: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(subtitles, f, indent=2, ensure_ascii=False)
    
    print(f" Saved: {filename}")


def preview_subtitles(subtitles, count=5):
    """Show preview of first few subtitles"""
    print("\n" + "="*70)
    print(f"SUBTITLE PREVIEW (First {count} of {len(subtitles)})")
    print("="*70)
    
    for i, sub in enumerate(subtitles[:count], 1):
        print(f"\n{i}. [{sub['start']:.1f}s - {sub['end']:.1f}s] ({sub['duration']:.1f}s)")
        print(f"   {sub['text']}")
    
    if len(subtitles) > count:
        print(f"\n... and {len(subtitles) - count} more subtitles")
    
    print("="*70)


def main():
    # Check if video exists
    if not os.path.exists(VIDEO_PATH):
        print(f"\n Error: Video file not found!")
        print(f"   Looking for: {VIDEO_PATH}")
        print(f"   In directory: {os.getcwd()}")
        return
    
    print(f"\nVideo found: {VIDEO_PATH}")
    
    try:
        # Step 1: Extract audio
        audio_file = extract_audio_from_video(VIDEO_PATH)
        
        # Step 2: Transcribe with Whisper
        result = transcribe_with_whisper(audio_file, LANGUAGE, TASK)
        
        # Step 3: Process subtitles
        print(f"\n Processing {len(result['segments'])} segments...")
        
        subtitles = []
        for segment in result['segments']:
            subtitles.append({
                'text': segment['text'].strip(),
                'start': round(segment['start'] + SUBTITLE_DELAY, 2),  
                'end': round(segment['end'] + SUBTITLE_DELAY, 2),      
                'duration': round(segment['end'] - segment['start'], 2)
            })
        
        # Step 4: Preview
        preview_subtitles(subtitles)
        
        # Step 5: Save in multiple formats
        print("\nSaving subtitle files...")
        save_txt_format(subtitles, OUTPUT_TXT)
        save_srt_format(subtitles, OUTPUT_SRT)
        save_json_format(subtitles, OUTPUT_JSON)
        
        # Cleanup
        print(f"\nCleaning up temporary files...")
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Removed: {audio_file}")
        
        # Success message
        print("SUCCESS! Subtitles extracted and saved!")
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup on any exit
        if os.path.exists("temp_audio.wav"):
            try:
                os.remove("temp_audio.wav")
            except:
                pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)