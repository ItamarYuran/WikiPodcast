"""
Audio Generation Pipeline

This module handles all audio-related operations:
- Text-to-speech generation
- Production effects and processing
- Audio file management
- Podcast package creation
"""

import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AudioGenerator:
    """Handles audio generation and processing"""
    
    def __init__(self, pipeline):
        """Initialize with reference to main pipeline"""
        self.pipeline = pipeline
        self.openai_client = pipeline.openai_client
        self.audio_dir = pipeline.audio_dir
    
    def generate_complete_podcast(self, script, voice: str, topic: str, style: str) -> Optional[Dict]:
        """Generate complete podcast package with audio"""
        print(f"\n🎙️ COMPLETE PODCAST GENERATION: {topic}")
        print("=" * 50)
        
        # Generate audio
        print(f"\n🎵 GENERATING AUDIO")
        print("=" * 30)
        
        audio_result = self._generate_audio_openai(script, voice)
        if audio_result:
            # Create complete podcast package
            podcast_info = self._create_podcast_package(script, audio_result, style, voice, topic)
            
            print(f"\n🎉 COMPLETE PODCAST CREATED!")
            print("=" * 40)
            print(f"📝 Title: {podcast_info['title']}")
            print(f"🎵 Audio: {podcast_info['audio_file']}")
            print(f"⏱️  Duration: {podcast_info['duration']}")
            print(f"📊 Size: {podcast_info['file_size_mb']:.2f} MB")
            print(f"💰 Cost: ~${podcast_info['estimated_cost']:.3f}")
            print(f"🎧 Play: open '{podcast_info['audio_path']}'")
            
            return podcast_info
        else:
            print("⚠️  Audio generation failed, but script was created successfully")
            return {"script": script, "audio": None}
    
    def _generate_audio_openai(self, script, voice: str) -> Optional[Dict]:
        """Generate audio using OpenAI TTS with production processing"""
        try:
            print(f"🎤 Using OpenAI TTS voice: {voice}")
            
            # Process script to extract production notes
            clean_script_text, production_timeline = self._process_script_with_production_notes(script.script)
            print(f"📝 Converting {len(clean_script_text)} characters to speech...")
            
            # Validate voice
            valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            if voice not in valid_voices:
                print(f"⚠️  Invalid voice '{voice}', using 'nova'")
                voice = "nova"
            
            # Check for character limit (OpenAI TTS has 4096 character limit)
            if len(clean_script_text) > 4096:
                print(f"⚠️  Script too long ({len(clean_script_text)} chars), chunking...")
                return self._generate_chunked_audio(clean_script_text, voice, script, production_timeline)
            
            # Generate basic audio with cleaned script
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=voice,
                input=clean_script_text,
                response_format="mp3"
            )
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self.pipeline._make_safe_filename(script.source_article)
            
            # Save raw TTS audio first
            raw_filename = f"{safe_title}_{voice}_{timestamp}_raw.mp3"
            raw_file_path = self.audio_dir / raw_filename
            response.stream_to_file(raw_file_path)
            
            # Process audio with production timeline
            final_filename = f"{safe_title}_{voice}_{timestamp}.mp3"
            final_file_path = self.audio_dir / final_filename
            
            processed_successfully = self._apply_production_effects(
                raw_file_path, 
                final_file_path, 
                production_timeline
            )
            
            # Use processed file if successful, otherwise use raw
            if processed_successfully:
                audio_file_path = final_file_path
                print("🎬 Production effects applied successfully")
                # Clean up raw file
                try:
                    raw_file_path.unlink()
                except:
                    pass
            else:
                # Rename raw file to final name
                try:
                    raw_file_path.rename(final_file_path)
                    audio_file_path = final_file_path
                    print("⚠️  Using basic TTS audio (production processing failed)")
                except:
                    audio_file_path = raw_file_path
                    final_filename = raw_filename
            
            # Get file info
            file_size_mb = audio_file_path.stat().st_size / (1024 * 1024)
            
            # Estimate duration and cost
            cleaned_word_count = len(clean_script_text.split())
            estimated_duration = (cleaned_word_count / 175) * 60
            char_count = len(clean_script_text)
            estimated_cost = (char_count / 1000) * 0.015
            
            print(f"✅ Audio generated successfully!")
            print(f"   📁 File: {final_filename}")
            print(f"   📊 Size: {file_size_mb:.2f} MB")
            print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
            print(f"   💰 Cost: ~${estimated_cost:.3f}")
            
            return {
                "file_path": str(audio_file_path),
                "filename": final_filename,
                "file_size_mb": file_size_mb,
                "estimated_duration": estimated_duration,
                "estimated_cost": estimated_cost,
                "voice_used": voice,
                "production_cues": len(production_timeline),
                "processed": processed_successfully
            }
            
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")
            return None
    
    def _generate_chunked_audio(self, script_text: str, voice: str, script, production_timeline: List[Dict]) -> Optional[Dict]:
        """Generate audio in chunks for long scripts"""
        print(f"📑 Splitting script into chunks for audio generation...")
        
        # Split script into chunks of ~3500 characters (safe margin under 4096)
        chunks = []
        current_chunk = ""
        sentences = script_text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') > 3500 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
            else:
                current_chunk += sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        print(f"📑 Split into {len(chunks)} audio chunks")
        
        # Generate audio for each chunk
        audio_files = []
        total_cost = 0
        
        for i, chunk in enumerate(chunks, 1):
            print(f"   🎤 Generating audio chunk {i}/{len(chunks)}...")
            
            try:
                response = self.openai_client.audio.speech.create(
                    model="tts-1-hd",
                    voice=voice,
                    input=chunk,
                    response_format="mp3"
                )
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_title = self.pipeline._make_safe_filename(script.source_article)
                chunk_filename = f"{safe_title}_{voice}_{timestamp}_chunk_{i}.mp3"
                chunk_file_path = self.audio_dir / chunk_filename
                
                response.stream_to_file(chunk_file_path)
                audio_files.append(str(chunk_file_path))
                
                # Calculate cost for this chunk
                char_count = len(chunk)
                chunk_cost = (char_count / 1000) * 0.015
                total_cost += chunk_cost
                
                print(f"     ✅ Chunk {i}: {len(chunk)} chars, ${chunk_cost:.3f}")
                
            except Exception as e:
                print(f"     ❌ Chunk {i} failed: {e}")
                return None
        
        # Combine audio files using ffmpeg if available
        final_filename = f"{safe_title}_{voice}_{timestamp}.mp3"
        final_file_path = self.audio_dir / final_filename
        
        if self._combine_audio_files(audio_files, final_file_path):
            # Clean up chunk files
            for chunk_file in audio_files:
                try:
                    Path(chunk_file).unlink()
                except:
                    pass
            
            # Get file info
            file_size_mb = final_file_path.stat().st_size / (1024 * 1024)
            cleaned_word_count = len(script_text.split())
            estimated_duration = (cleaned_word_count / 175) * 60
            
            print(f"✅ Combined audio generated successfully!")
            print(f"   📁 File: {final_filename}")
            print(f"   📊 Size: {file_size_mb:.2f} MB")
            print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
            print(f"   💰 Total cost: ~${total_cost:.3f}")
            
            return {
                "file_path": str(final_file_path),
                "filename": final_filename,
                "file_size_mb": file_size_mb,
                "estimated_duration": estimated_duration,
                "estimated_cost": total_cost,
                "voice_used": voice,
                "production_cues": len(production_timeline),
                "processed": False,  # Combined files skip production processing
                "chunked": True
            }
        else:
            print("❌ Failed to combine audio chunks")
            return None
    
    def _combine_audio_files(self, audio_files: List[str], output_path: Path) -> bool:
        """Combine multiple audio files using ffmpeg"""
        try:
            # Check if ffmpeg is available
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  ffmpeg not found - cannot combine audio chunks")
                return False
            
            print("🔗 Combining audio chunks...")
            
            # Create file list for ffmpeg
            file_list_path = output_path.parent / "audio_list.txt"
            with open(file_list_path, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
            
            # Combine files using ffmpeg
            ffmpeg_cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(file_list_path),
                '-c', 'copy',
                '-y',  # Overwrite output
                str(output_path)
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            # Clean up file list
            try:
                file_list_path.unlink()
            except:
                pass
            
            if result.returncode == 0:
                return True
            else:
                print(f"⚠️  Audio combination failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"⚠️  Audio combination error: {e}")
            return False
    
    def _process_script_with_production_notes(self, script_text: str) -> Tuple[str, List[Dict]]:
        """Process script to extract production notes and create audio timeline"""
        # Extract production notes and their positions
        production_timeline = []
        clean_script = script_text
        
        # Pattern to find production notes and their positions
        patterns = {
            'music_fade_in': r'\[(?:music fades? in|fade in music|intro music)\]',
            'music_fade_out': r'\[(?:music fades? out|fade out music|outro music)\]',
            'background_music': r'\[(?:background music|ambient music|soft music)\]',
            'pause': r'\[(?:pause|dramatic pause|brief pause|long pause)\]',
            'sound_effect': r'\[(?:sound effect|sfx|audio effect):\s*([^\]]+)\]',
            'emphasis': r'\[(?:emphasis|stressed|important)\]',
            'speed_change': r'\[(?:slow down|speed up|faster|slower)\]',
            'volume_change': r'\[(?:quieter|louder|whisper|shout)\]',
            'music_specific': r'\[(?:music|song):\s*([^\]]+)\]'
        }
        
        # Find all matches and their positions
        for note_type, pattern in patterns.items():
            for match in re.finditer(pattern, script_text, re.IGNORECASE):
                # Calculate approximate time position based on character position
                char_pos = match.start()
                text_before = script_text[:char_pos]
                words_before = len(text_before.split())
                time_position = (words_before / 175) * 60  # Approximate seconds
                
                production_note = {
                    'type': note_type,
                    'text': match.group(0),
                    'time_position': time_position,
                    'char_position': char_pos
                }
                
                # Extract specific content for some note types
                if note_type in ['sound_effect', 'music_specific'] and match.groups():
                    production_note['content'] = match.group(1)
                
                production_timeline.append(production_note)
        
        # Remove production notes from script for TTS
        for pattern in patterns.values():
            clean_script = re.sub(pattern, '', clean_script, flags=re.IGNORECASE)
        
        # Also remove other common production notes
        additional_patterns = [
            r'\[.*?music.*?\]',
            r'\[.*?pause.*?\]',
            r'\[.*?sound.*?\]',
            r'\[.*?fade.*?\]',
            r'\[.*?effect.*?\]',
            r'\*.*?\*',
            r'\(.*?producer.*?\)',
            r'\(.*?note.*?\)',
        ]
        
        for pattern in additional_patterns:
            clean_script = re.sub(pattern, '', clean_script, flags=re.IGNORECASE)
        
        # Clean up whitespace
        clean_script = re.sub(r'\n\s*\n\s*', '\n\n', clean_script)
        clean_script = re.sub(r'[ \t]+', ' ', clean_script)
        clean_script = clean_script.strip()
        
        # Sort timeline by time position
        production_timeline.sort(key=lambda x: x['time_position'])
        
        print(f"🎬 Found {len(production_timeline)} production cues")
        for cue in production_timeline[:3]:  # Show first 3
            print(f"   {cue['time_position']:.1f}s: {cue['type']} - {cue['text']}")
        if len(production_timeline) > 3:
            print(f"   ... and {len(production_timeline) - 3} more")
        
        return clean_script, production_timeline
    
    def _apply_production_effects(self, raw_audio_path: Path, output_path: Path, production_timeline: List[Dict]) -> bool:
        """Apply production effects to audio based on timeline"""
        try:
            # Check if ffmpeg is available
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  ffmpeg not found - install with: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)")
                return False
            
            print("🎬 Processing audio with production effects...")
            
            if not production_timeline:
                # No production notes, just copy the file
                import shutil
                shutil.copy2(raw_audio_path, output_path)
                return True
            
            # Build ffmpeg command for basic processing
            ffmpeg_cmd = [
                'ffmpeg', '-i', str(raw_audio_path),
                '-af', self._build_audio_filter_chain(production_timeline),
                '-y',  # Overwrite output
                str(output_path)
            ]
            
            # Execute ffmpeg command
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"⚠️  Audio processing failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"⚠️  Production processing error: {e}")
            return False
    
    def _build_audio_filter_chain(self, production_timeline: List[Dict]) -> str:
        """Build ffmpeg audio filter chain based on production timeline"""
        filters = []
        
        # Check for different types of effects needed
        has_music_cues = any(cue['type'].startswith('music') for cue in production_timeline)
        has_pause_cues = any(cue['type'] == 'pause' for cue in production_timeline)
        has_volume_changes = any(cue['type'] == 'volume_change' for cue in production_timeline)
        
        # Basic audio normalization
        filters.append('loudnorm')
        
        # Add subtle effects based on production cues
        if has_music_cues:
            # Add a subtle reverb for music sections
            filters.append('aecho=0.8:0.88:60:0.4')
        
        if has_pause_cues:
            # Add slight compression for dramatic pauses
            filters.append('acompressor=threshold=0.5:ratio=4:attack=200:release=1000')
        
        # Default enhancement
        filters.append('highpass=f=80')  # Remove low-frequency noise
        filters.append('lowpass=f=15000')  # Remove high-frequency noise
        
        return ','.join(filters)
    
    def _create_podcast_package(self, script, audio_result: Dict, style: str, voice: str, topic: str) -> Dict:
        """Create complete podcast package with metadata"""
        # Create package info
        package_info = {
            "success": True,
            "title": f"{script.source_article} - {style.title()} Podcast",
            "source_article": script.source_article,
            "style": style,
            "voice": voice,
            "audio_file": audio_result["filename"],
            "audio_path": audio_result["file_path"],
            "duration": f"{audio_result['estimated_duration']//60:.0f}:{audio_result['estimated_duration']%60:02.0f}",
            "file_size_mb": audio_result["file_size_mb"],
            "estimated_cost": audio_result["estimated_cost"],
            "created_timestamp": datetime.now().isoformat(),
            "script_word_count": script.word_count,
            "script_estimated_duration": script.estimated_duration
        }
        
        # Save package metadata
        metadata_file = self.audio_dir / f"{audio_result['filename']}.json"
        with open(metadata_file, 'w') as f:
            json.dump(package_info, f, indent=2)
        
        print(f"✅ Package metadata saved: {metadata_file.name}")
        
        return package_info
    
    def list_podcasts(self) -> List[Dict]:
        """List all created podcasts"""
        if not self.audio_dir or not self.audio_dir.exists():
            return []
        
        podcasts = []
        for json_file in self.audio_dir.glob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if data.get('success'):
                        podcasts.append({
                            'title': data['title'],
                            'style': data['style'],
                            'voice': data['voice'],
                            'duration': data['duration'],
                            'size_mb': data['file_size_mb'],
                            'cost': data['estimated_cost'],
                            'created': data['created_timestamp'][:10],
                            'audio_file': data['audio_file']
                        })
            except:
                continue
        
        return sorted(podcasts, key=lambda x: x['created'], reverse=True)