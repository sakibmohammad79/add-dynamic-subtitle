

from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import json
import os
import sys
import arabic_reshaper
from bidi.algorithm import get_display


VIDEO_PATH = "Beautiful Recitation of Surah Infitar (سورة الانفطار_).mp4"
SUBTITLE_FILE = "subtitles.txt"  
OUTPUT_VIDEO = "output_with_subtitles.mp4"


# Subtitle Styling
FONT_SIZE = 30
FONT_COLOR = 'white'
STROKE_COLOR = 'black'
STROKE_WIDTH = 1.5
SUBTITLE_WIDTH_RATIO = 0.85
SUBTITLE_POSITION_FROM_BOTTOM = 90

# Font Path fron pc
FONT_PATH = r'C:\Windows\Fonts\Arial.ttf'

# Video Export Settings
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'
PRESET = 'medium'  # Options: ultrafast, fast, medium, slow, slower
THREADS = 4


def read_txt_subtitles(filename):
    """Read subtitles from TXT format (start | end | text)"""
    print(f"\nReading TXT format: {filename}")
    
    subtitles = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            
          
            if not line or line.startswith('#'):
                continue
            
            try:
                parts = [p.strip() for p in line.split('|')]
                
                if len(parts) < 3:
                    print(f"Line {line_num}: Skipping (invalid format)")
                    continue
                
                subtitles.append({
                    'start': float(parts[0]),
                    'end': float(parts[1]),
                    'text': parts[2]
                })
                
            except Exception as e:
                print(f"Line {line_num}: Error - {e}")
    
    return subtitles


def read_srt_subtitles(filename):
    """Read subtitles from SRT format"""
    print(f"\nReading SRT format: {filename}")
    
    subtitles = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            
            if len(lines) < 3:
                continue
            
            try:
                # Parse timing line (format: 00:00:00,000 --> 00:00:00,000)
                timing_line = lines[1]
                start_str, end_str = timing_line.split(' --> ')
                
                # Convert to seconds
                start = srt_time_to_seconds(start_str)
                end = srt_time_to_seconds(end_str)
                
                # Text is everything after timing
                text = '\n'.join(lines[2:])
                
                subtitles.append({
                    'start': start,
                    'end': end,
                    'text': text
                })
                
            except Exception as e:
                continue
    
    return subtitles


def srt_time_to_seconds(time_str):
    """Convert SRT time format to seconds"""
    # Format: HH:MM:SS,mmm
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    return hours * 3600 + minutes * 60 + seconds


def read_json_subtitles(filename):
    """Read subtitles from JSON format"""
    print(f"\nReading JSON format: {filename}")
    
    with open(filename, 'r', encoding='utf-8') as f:
        subtitles = json.load(f)
    
    return subtitles


def auto_detect_and_read_subtitles(filename):
    """Automatically detect format and read subtitles"""
    
    if not os.path.exists(filename):
        print(f"Error: Subtitle file not found: {filename}")
        return None
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.txt':
        return read_txt_subtitles(filename)
    elif ext == '.srt':
        return read_srt_subtitles(filename)
    elif ext == '.json':
        return read_json_subtitles(filename)
    else:
        print(f"Unknown format, trying TXT format...")
        return read_txt_subtitles(filename)




def add_subtitles_to_video(video_path, subtitles, output_path):
    """Add subtitle overlays to video"""
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False
    
    print(f"\nLoading video: {video_path}")
    video = VideoFileClip(video_path)
    
    text_clips = []
    print(f"\nCreating {len(subtitles)} subtitle clips...")
    
    for idx, sub in enumerate(subtitles, 1):
        try:
            reshaped_text = arabic_reshaper.reshape(sub['text'])
            bidi_text = get_display(reshaped_text)
    
    
            txt_clip = TextClip(
                text=bidi_text,  
                font_size=FONT_SIZE,
                color=FONT_COLOR,
                font=FONT_PATH,
                method='caption',
                size=(int(video.w * SUBTITLE_WIDTH_RATIO), None),
                stroke_color=STROKE_COLOR,
                stroke_width=STROKE_WIDTH
            )
            
            pos = ('center', video.h - txt_clip.h - SUBTITLE_POSITION_FROM_BOTTOM)
            
            txt_clip = (txt_clip.with_start(sub['start'])
                               .with_duration(sub['end'] - sub['start'])
                               .with_position(pos))
            
            text_clips.append(txt_clip)
            
        except Exception as e:
            print(f"Error creating subtitle {idx}: {e}")
    
    print(f"\n Compositing and Exporting...")
    final_video = CompositeVideoClip([video] + text_clips)
    

    final_video.write_videofile(
        output_path,
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        fps=video.fps,
        preset=PRESET,
        threads=THREADS,
        logger=None 
    )
    
    video.close()
    final_video.close()
    return True




def main():
    """Main execution function"""
    print("="*70)
    print("     STEP 2: ADD SUBTITLES TO VIDEO")
    print("="*70)
    
    # Check if video exists
    if not os.path.exists(VIDEO_PATH):
        print(f"\nError: Video file not found!")
        print(f"   Looking for: {VIDEO_PATH}")
        return
    
    print(f"\nVideo found: {VIDEO_PATH}")
    
    # Read subtitles
    print(f"\nLooking for subtitle file: {SUBTITLE_FILE}")
    subtitles = auto_detect_and_read_subtitles(SUBTITLE_FILE)
    
    if not subtitles:
        print("\nNo valid subtitles found!")
        print("\nAvailable subtitle files:")
        for file in os.listdir('.'):
            if file.endswith(('.txt', '.srt', '.json')):
                print(f"   - {file}")
        return
    
    print(f"✅ Loaded {len(subtitles)} subtitles")
    
    # Preview first subtitle
    if subtitles:
        first = subtitles[0]
        print(f"\nFirst subtitle preview:")
        print(f"   Time: {first['start']:.2f}s - {first['end']:.2f}s")
        print(f"   Text: {first['text'][:60]}{'...' if len(first['text']) > 60 else ''}")
    
    # Confirm before processing
    print("\n" + "="*70)
    print("Ready to add subtitles to video")
    print("="*70)
    print(f"Input video: {VIDEO_PATH}")
    print(f"Output video: {OUTPUT_VIDEO}")
    print(f"Subtitles: {len(subtitles)} segments")
    print(f"Font size: {FONT_SIZE}")
    print(f"Position: {SUBTITLE_POSITION_FROM_BOTTOM}px from bottom")
    
    response = input("\nProceed? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Cancelled by user")
        return
    
    # Process video
    try:
        success = add_subtitles_to_video(VIDEO_PATH, subtitles, OUTPUT_VIDEO)
        
        if success:
            file_size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)  # MB
            
            print("\n" + "="*70)
            print("SUCCESS! Video with subtitles created!")
            print("="*70)
            print(f"\n📹 Output: {OUTPUT_VIDEO}")
            print(f"   Size: {file_size:.2f} MB")
            print(f"   Subtitles: {len(subtitles)} segments")
            print("\n🎉 Your subtitled video is ready!")
            print("="*70)
        else:
            print("\nFailed to create video")
            
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)