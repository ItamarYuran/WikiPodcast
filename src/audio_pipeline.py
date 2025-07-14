# """
# Audio Generation Pipeline with Google Cloud TTS

# This module handles all audio-related operations:
# - Text-to-speech generation using Google Cloud TTS
# - Production effects and processing
# - Audio file management
# - Podcast package creation
# """

# from tts_processor import SSMLProcessor
# import json
# import subprocess
# import re
# import os
# from datetime import datetime
# from pathlib import Path
# from typing import Dict, List, Optional, Tuple

# # Google Cloud TTS imports
# from google.cloud import texttospeech


# class AudioGenerator:
#     """Handles audio generation and processing with Google Cloud TTS"""
    
#     def __init__(self, pipeline):
#         """Initialize with reference to main pipeline"""
#         self.pipeline = pipeline
#         self.audio_dir = pipeline.audio_dir
        
#         # Initialize Google Cloud TTS client
#         try:
#             self.tts_client = texttospeech.TextToSpeechClient()
#             print("✅ Google Cloud TTS client initialized")
#         except Exception as e:
#             print(f"❌ Failed to initialize Google Cloud TTS: {e}")
#             print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set correctly")
#             raise
    
#     def generate_complete_podcast(self, script, voice: str, topic: str, style: str) -> Optional[Dict]:
#         """Generate complete podcast package with audio"""
#         print(f"\n🎙️ COMPLETE PODCAST GENERATION: {topic}")
#         print("=" * 50)
        
#         # Generate audio
#         print(f"\n🎵 GENERATING AUDIO")
#         print("=" * 30)
        
#         audio_result = self._generate_audio_gcp(script, voice)
#         if audio_result:
#             # Create complete podcast package
#             podcast_info = self._create_podcast_package(script, audio_result, style, voice, topic)
            
#             print(f"\n🎉 COMPLETE PODCAST CREATED!")
#             print("=" * 40)
#             print(f"📝 Title: {podcast_info['title']}")
#             print(f"🎵 Audio: {podcast_info['audio_file']}")
#             print(f"⏱️  Duration: {podcast_info['duration']}")
#             print(f"📊 Size: {podcast_info['file_size_mb']:.2f} MB")
#             print(f"💰 Cost: ~${podcast_info['estimated_cost']:.3f}")
#             print(f"🎧 Play: open '{podcast_info['audio_path']}'")
            
#             return podcast_info
#         else:
#             print("⚠️  Audio generation failed, but script was created successfully")
#             return {"script": script, "audio": None}
    
#     def generate_from_script_file(self, script_filename: str) -> Optional[Dict]:
#         """
#         Generate audio from a cached script file
        
#         Args:
#             script_filename: Name of the script file to load
            
#         Returns:
#             Audio generation result or None if failed
#         """
#         try:
#             # Load the script from cache
#             script_data = self._load_script_from_cache(script_filename)
#             if not script_data:
#                 print(f"❌ Could not load script file: {script_filename}")
#                 return None
            
#             print(f"📝 Loaded script: {script_data.get('title', 'Unknown')}")
#             print(f"📊 Script length: {script_data.get('word_count', 0)} words")
            
#             # Create a mock script object from the data
#             from script_formatter import PodcastScript
#             script = PodcastScript(
#                 title=script_data.get('title', 'Unknown'),
#                 style=script_data.get('style', 'conversational'),
#                 script=script_data.get('script', ''),
#                 intro=script_data.get('intro', ''),
#                 outro=script_data.get('outro', ''),
#                 segments=script_data.get('segments', []),
#                 estimated_duration=script_data.get('estimated_duration', 0),
#                 word_count=script_data.get('word_count', 0),
#                 source_article=script_data.get('source_article', 'Unknown'),
#                 generated_timestamp=script_data.get('generated_timestamp', ''),
#                 custom_instructions=script_data.get('custom_instructions', None)
#             )
            
#             if not script.script:
#                 print("❌ Script content is empty")
#                 return None
            
#             # Generate audio - use default voice "en-US-Journey-D"
#             voice = "en-US-Journey-D"
#             print(f"🎤 Generating audio with voice: {voice}")
            
#             audio_result = self._generate_audio_gcp(script, voice)
            
#             if audio_result:
#                 # Create podcast package
#                 package_info = self._create_podcast_package(
#                     script, 
#                     audio_result, 
#                     script.style, 
#                     voice, 
#                     script.source_article
#                 )
#                 return package_info
#             else:
#                 print("❌ Audio generation failed")
#                 return None
                
#         except Exception as e:
#             print(f"❌ Error generating audio from script file: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def _load_script_from_cache(self, script_filename: str) -> Optional[dict]:
#         """
#         Load a script from the cache directory
        
#         Args:
#             script_filename: Name of the script file
            
#         Returns:
#             Script data dict or None if not found
#         """
#         try:
#             # Check common cache directories
#             cache_dirs = [
#                 "../processed_scripts",
#                 "processed_scripts",
#                 "../processed_scripts/conversational",
#                 "processed_scripts/conversational",
#                 "../processed_scripts/academic",
#                 "processed_scripts/academic",
#                 "../processed_scripts/storytelling",
#                 "processed_scripts/storytelling"
#             ]
            
#             for cache_dir in cache_dirs:
#                 cache_path = Path(cache_dir)
#                 if cache_path.exists():
#                     # Look for the file in this directory
#                     script_file = cache_path / script_filename
#                     if script_file.exists():
#                         with open(script_file, 'r', encoding='utf-8') as f:
#                             return json.load(f)
                    
#                     # Also check subdirectories (style-based organization)
#                     for style_dir in cache_path.iterdir():
#                         if style_dir.is_dir():
#                             script_file = style_dir / script_filename
#                             if script_file.exists():
#                                 with open(script_file, 'r', encoding='utf-8') as f:
#                                     return json.load(f)
            
#             print(f"❌ Script file not found: {script_filename}")
#             return None
            
#         except Exception as e:
#             print(f"❌ Error loading script from cache: {e}")
#             return None
    
#     def _generate_audio_gcp(self, script, voice: str) -> Optional[Dict]:
#         """Generate audio using Google Cloud TTS with fallback strategies"""
#         try:
#             print(f"🎤 Using Google Cloud TTS voice: {voice}")
            
#             # Process script to extract production notes
#             clean_script_text, production_timeline = self._process_script_with_production_notes(script.script)
#             print(f"📝 Converting {len(clean_script_text)} characters to speech...")
            
#             # Strategy 1: Try with smaller chunks first if text is long (more reliable)
#             if len(clean_script_text) > 3000:
#                 print(f"📑 Using conservative chunking (3000 chars) for better reliability...")
#                 return self._generate_chunked_audio_conservative(clean_script_text, voice, script, production_timeline)
            
#             # Strategy 2: Try different voices if original fails
#             voice_fallbacks = [
#                 voice,  # Original voice
#                 "en-US-Neural2-A",  # Stable fallback
#                 "en-US-Standard-A",  # Most stable
#             ]
            
#             for attempt, fallback_voice in enumerate(voice_fallbacks, 1):
#                 print(f"🎯 Attempt {attempt}: Trying voice {fallback_voice}")
                
#                 voice_config = self._get_voice_config(fallback_voice)
#                 if not voice_config:
#                     continue
                    
#                 audio_content = self._synthesize_speech_gcp(clean_script_text, voice_config)
#                 if audio_content:
#                     # Success! Create and save audio file
#                     timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#                     safe_title = self.pipeline._make_safe_filename(script.source_article)
                    
#                     # Save raw TTS audio first
#                     raw_filename = f"{safe_title}_{fallback_voice}_{timestamp}_raw.mp3"
#                     raw_file_path = self.audio_dir / raw_filename
#                     with open(raw_file_path, 'wb') as f:
#                         f.write(audio_content)
                    
#                     # Process audio with production timeline
#                     final_filename = f"{safe_title}_{fallback_voice}_{timestamp}.mp3"
#                     final_file_path = self.audio_dir / final_filename
                    
#                     processed_successfully = self._apply_production_effects(
#                         raw_file_path, 
#                         final_file_path, 
#                         production_timeline
#                     )
                    
#                     # Use processed file if successful, otherwise use raw
#                     if processed_successfully:
#                         audio_file_path = final_file_path
#                         print("🎬 Production effects applied successfully")
#                         # Clean up raw file
#                         try:
#                             raw_file_path.unlink()
#                         except:
#                             pass
#                     else:
#                         # Rename raw file to final name
#                         try:
#                             raw_file_path.rename(final_file_path)
#                             audio_file_path = final_file_path
#                             print("⚠️  Using basic TTS audio (production processing failed)")
#                         except:
#                             audio_file_path = raw_file_path
#                             final_filename = raw_filename
                    
#                     # Get file info
#                     file_size_mb = audio_file_path.stat().st_size / (1024 * 1024)
#                     cleaned_word_count = len(clean_script_text.split())
#                     estimated_duration = (cleaned_word_count / 175) * 60
#                     char_count = len(clean_script_text)
#                     estimated_cost = (char_count / 1000) * 0.016
                    
#                     print(f"✅ Audio generated successfully with voice: {fallback_voice}")
#                     print(f"   📁 File: {final_filename}")
#                     print(f"   📊 Size: {file_size_mb:.2f} MB")
#                     print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
#                     print(f"   💰 Cost: ~${estimated_cost:.3f}")
                    
#                     return {
#                         "file_path": str(audio_file_path),
#                         "filename": final_filename,
#                         "file_size_mb": file_size_mb,
#                         "estimated_duration": estimated_duration,
#                         "estimated_cost": estimated_cost,
#                         "voice_used": fallback_voice,
#                         "production_cues": len(production_timeline),
#                         "processed": processed_successfully
#                     }
#                 else:
#                     print(f"❌ Voice {fallback_voice} failed, trying next...")
            
#             print("❌ All voice fallbacks failed")
#             return None
            
#         except Exception as e:
#             print(f"❌ Google Cloud TTS error: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def _generate_chunked_audio_conservative(self, script_text: str, voice: str, script, production_timeline: List[Dict]) -> Optional[Dict]:
#         """Generate audio in very small chunks for maximum reliability"""
#         print(f"📑 Using conservative chunking (3000 chars) for better reliability...")
        
#         # Get voice config with fallbacks
#         voice_config = self._get_voice_config(voice)
#         if not voice_config:
#             voice_config = self._get_voice_config("en-US-Standard-A")  # Fallback to most stable
        
#         # Split script into smaller chunks of ~3000 characters
#         chunks = []
#         current_chunk = ""
#         sentences = script_text.split('. ')
        
#         for sentence in sentences:
#             if len(current_chunk + sentence + '. ') > 3000 and current_chunk:
#                 chunks.append(current_chunk.strip())
#                 current_chunk = sentence + '. '
#             else:
#                 current_chunk += sentence + '. '
        
#         if current_chunk:
#             chunks.append(current_chunk.strip())
        
#         print(f"📑 Split into {len(chunks)} conservative chunks")
        
#         # Generate audio for each chunk with multiple fallback voices
#         audio_files = []
#         total_cost = 0
        
#         for i, chunk in enumerate(chunks, 1):
#             print(f"   🎤 Generating audio chunk {i}/{len(chunks)}...")
            
#             # Try multiple voices for this chunk if needed
#             voice_fallbacks = [voice_config['name'], "en-US-Neural2-A", "en-US-Standard-A"]
            
#             audio_content = None
#             successful_voice = None
            
#             for voice_attempt in voice_fallbacks:
#                 chunk_voice_config = self._get_voice_config(voice_attempt)
#                 if not chunk_voice_config:
#                     continue
                    
#                 print(f"     🎯 Trying voice: {voice_attempt}")
#                 audio_content = self._synthesize_speech_gcp(chunk, chunk_voice_config)
#                 if audio_content:
#                     successful_voice = voice_attempt
#                     break
#                 else:
#                     print(f"     ❌ Voice {voice_attempt} failed, trying next...")
            
#             if not audio_content:
#                 print(f"     ❌ Chunk {i} failed with all voice attempts")
#                 # Clean up any successful chunks
#                 for chunk_file in audio_files:
#                     try:
#                         Path(chunk_file).unlink()
#                     except:
#                         pass
#                 return None
            
#             # Save chunk audio
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             safe_title = self.pipeline._make_safe_filename(script.source_article)
#             chunk_filename = f"{safe_title}_{successful_voice}_{timestamp}_chunk_{i}.mp3"
#             chunk_file_path = self.audio_dir / chunk_filename
            
#             with open(chunk_file_path, 'wb') as f:
#                 f.write(audio_content)
            
#             audio_files.append(str(chunk_file_path))
            
#             # Calculate cost for this chunk
#             char_count = len(chunk)
#             chunk_cost = (char_count / 1000) * 0.016
#             total_cost += chunk_cost
            
#             print(f"     ✅ Chunk {i}: {len(chunk)} chars, ${chunk_cost:.3f} (voice: {successful_voice})")
            
#             # Longer delay between chunks to be extra nice to the API
#             if i < len(chunks):
#                 import time
#                 time.sleep(1.0)  # 1 second delay instead of 0.5
        
#         # Combine audio files using ffmpeg if available
#         final_filename = f"{safe_title}_{voice}_{timestamp}.mp3"
#         final_file_path = self.audio_dir / final_filename
        
#         if self._combine_audio_files(audio_files, final_file_path):
#             # Clean up chunk files
#             for chunk_file in audio_files:
#                 try:
#                     Path(chunk_file).unlink()
#                 except:
#                     pass
            
#             # Get file info
#             file_size_mb = final_file_path.stat().st_size / (1024 * 1024)
#             cleaned_word_count = len(script_text.split())
#             estimated_duration = (cleaned_word_count / 175) * 60
            
#             print(f"✅ Combined audio generated successfully!")
#             print(f"   📁 File: {final_filename}")
#             print(f"   📊 Size: {file_size_mb:.2f} MB")
#             print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
#             print(f"   💰 Total cost: ~${total_cost:.3f}")
            
#             return {
#                 "file_path": str(final_file_path),
#                 "filename": final_filename,
#                 "file_size_mb": file_size_mb,
#                 "estimated_duration": estimated_duration,
#                 "estimated_cost": total_cost,
#                 "voice_used": voice,
#                 "production_cues": len(production_timeline),
#                 "processed": False,
#                 "chunked": True,
#                 "audio_file": final_filename,
#                 "audio_path": str(final_file_path)
#             }
#         else:
#             print("❌ Failed to combine audio chunks")
#             # Clean up chunk files
#             for chunk_file in audio_files:
#                 try:
#                     Path(chunk_file).unlink()
#                 except:
#                     pass
#             return None
    
#     def _get_voice_config(self, voice_name: str) -> Optional[Dict]:
#         """Get voice configuration for Google Cloud TTS"""
        
#         # Popular Google Cloud TTS voices for podcasts
#         voice_configs = {
#             # Journey voices (best for podcasts)
#             "en-US-Journey-D": {
#                 "language_code": "en-US",
#                 "name": "en-US-Journey-D",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.MALE
#             },
#             "en-US-Journey-F": {
#                 "language_code": "en-US", 
#                 "name": "en-US-Journey-F",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
#             },
#             # Studio voices (high quality)
#             "en-US-Studio-M": {
#                 "language_code": "en-US",
#                 "name": "en-US-Studio-M", 
#                 "ssml_gender": texttospeech.SsmlVoiceGender.MALE
#             },
#             "en-US-Studio-O": {
#                 "language_code": "en-US",
#                 "name": "en-US-Studio-O",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
#             },
#             # Neural2 voices (good quality)
#             "en-US-Neural2-A": {
#                 "language_code": "en-US",
#                 "name": "en-US-Neural2-A",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.MALE
#             },
#             "en-US-Neural2-C": {
#                 "language_code": "en-US",
#                 "name": "en-US-Neural2-C", 
#                 "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
#             },
#             "en-US-Neural2-D": {
#                 "language_code": "en-US",
#                 "name": "en-US-Neural2-D",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.MALE
#             },
#             "en-US-Neural2-E": {
#                 "language_code": "en-US",
#                 "name": "en-US-Neural2-E",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
#             },
#             # Standard voices
#             "en-US-Standard-A": {
#                 "language_code": "en-US",
#                 "name": "en-US-Standard-A",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.MALE
#             },
#             "en-US-Standard-C": {
#                 "language_code": "en-US",
#                 "name": "en-US-Standard-C",
#                 "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
#             },
#         }
        
#         return voice_configs.get(voice_name)
    
#     def _synthesize_speech_gcp(self, text: str, voice_config: Dict) -> Optional[bytes]:
#         """Synthesize speech using Google Cloud TTS with retry logic"""
#         import time
        
#         max_retries = 3
#         retry_delay = 2  # seconds
        
#         for attempt in range(max_retries):
#             try:
#                 # Set up the synthesis input
#                 synthesis_input = texttospeech.SynthesisInput(text=text)
                
#                 # Configure the voice
#                 voice = texttospeech.VoiceSelectionParams(
#                     language_code=voice_config["language_code"],
#                     name=voice_config["name"],
#                     ssml_gender=voice_config["ssml_gender"]
#                 )
                
#                 # Configure audio format
#                 audio_config = texttospeech.AudioConfig(
#                     audio_encoding=texttospeech.AudioEncoding.MP3,
#                     speaking_rate=1.0,  # Normal speed
#                     pitch=0.0,  # Normal pitch
#                     volume_gain_db=0.0  # Normal volume
#                 )
                
#                 # Perform the text-to-speech request
#                 response = self.tts_client.synthesize_speech(
#                     input=synthesis_input,
#                     voice=voice,
#                     audio_config=audio_config
#                 )
                
#                 return response.audio_content
                
#             except Exception as e:
#                 error_msg = str(e)
#                 print(f"❌ Speech synthesis error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
#                 # Check if it's a retryable error
#                 if any(code in error_msg for code in ['503', '502', '500', '429', 'Bad Gateway', 'Service Unavailable']):
#                     if attempt < max_retries - 1:
#                         print(f"⏳ Retrying in {retry_delay} seconds...")
#                         time.sleep(retry_delay)
#                         retry_delay *= 2  # Exponential backoff
#                         continue
                
#                 # If not retryable or max retries reached, return None
#                 return None
        
#         return None
    
#     def _combine_audio_files(self, audio_files: List[str], output_path: Path) -> bool:
#         """Combine multiple audio files using ffmpeg or fallback method"""
#         try:
#             # First try ffmpeg
#             result = subprocess.run(['ffmpeg', '-version'], 
#                                   capture_output=True, text=True)
#             if result.returncode == 0:
#                 return self._combine_with_ffmpeg(audio_files, output_path)
#             else:
#                 print("⚠️  ffmpeg not found, using fallback method...")
#                 return self._combine_with_fallback(audio_files, output_path)
                
#         except FileNotFoundError:
#             print("⚠️  ffmpeg not found, using fallback method...")
#             return self._combine_with_fallback(audio_files, output_path)
#         except Exception as e:
#             print(f"⚠️  Audio combination error: {e}")
#             return False
    
#     def _combine_with_ffmpeg(self, audio_files: List[str], output_path: Path) -> bool:
#         """Combine audio files using ffmpeg"""
#         try:
#             print("🔗 Combining audio chunks with ffmpeg...")
            
#             # Create file list for ffmpeg with absolute paths
#             file_list_path = output_path.parent / "audio_list.txt"
#             with open(file_list_path, 'w') as f:
#                 for audio_file in audio_files:
#                     # Use absolute path and escape any special characters
#                     abs_path = str(Path(audio_file).resolve())
#                     f.write(f"file '{abs_path}'\n")
            
#             print(f"📝 Created file list: {file_list_path}")
#             print(f"📁 Output path: {output_path}")
            
#             # Debug: Show the file list contents
#             with open(file_list_path, 'r') as f:
#                 content = f.read()
#                 print(f"📋 File list contents:")
#                 for line in content.strip().split('\n'):
#                     print(f"   {line}")
            
#             # Combine files using ffmpeg
#             ffmpeg_cmd = [
#                 'ffmpeg', '-f', 'concat', '-safe', '0',
#                 '-i', str(file_list_path),
#                 '-c', 'copy',
#                 '-y',  # Overwrite output
#                 str(output_path)
#             ]
            
#             print(f"🎯 Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
            
#             result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
#             # Clean up file list
#             try:
#                 file_list_path.unlink()
#             except:
#                 pass
            
#             if result.returncode == 0:
#                 print("✅ ffmpeg combination successful!")
#                 return True
#             else:
#                 print(f"❌ ffmpeg combination failed:")
#                 print(f"   stdout: {result.stdout}")
#                 print(f"   stderr: {result.stderr}")
#                 return False
                
#         except Exception as e:
#             print(f"❌ ffmpeg combination error: {e}")
#             import traceback
#             traceback.print_exc()
#             return False
    
#     def _combine_with_fallback(self, audio_files: List[str], output_path: Path) -> bool:
#         """Combine audio files using simple binary concatenation (fallback)"""
#         try:
#             print("🔗 Combining audio chunks with fallback method...")
#             print("   📝 Note: For best quality, install ffmpeg with: brew install ffmpeg")
            
#             # Simple binary concatenation (works for MP3 files)
#             with open(output_path, 'wb') as output_file:
#                 for i, audio_file in enumerate(audio_files, 1):
#                     print(f"   📎 Adding chunk {i}/{len(audio_files)}")
#                     with open(audio_file, 'rb') as input_file:
#                         output_file.write(input_file.read())
            
#             # Check if file was created successfully
#             if output_path.exists() and output_path.stat().st_size > 0:
#                 print("✅ Audio chunks combined successfully (fallback method)")
#                 return True
#             else:
#                 print("❌ Failed to create combined audio file")
#                 return False
                
#         except Exception as e:
#             print(f"❌ Fallback combination error: {e}")
#             return False
    
#     def _process_script_with_production_notes(self, script_text: str) -> Tuple[str, List[Dict]]:
#         """Enhanced script processing with TTS instructions"""
        
#         # Initialize SSML processor
#         ssml_processor = SSMLProcessor()
        
#         # Process script for TTS
#         clean_script = ssml_processor.process_script_for_tts(script_text, use_ssml=True)
        
#         # Extract any remaining production notes
#         production_timeline = []
        
#         # Look for any remaining manual production notes
#         patterns = {
#             'music_fade_in': r'\[(?:music fades? in|fade in music|intro music)\]',
#             'music_fade_out': r'\[(?:music fades? out|fade out music|outro music)\]',
#             'background_music': r'\[(?:background music|ambient music|soft music)\]',
#         }
        
#         for note_type, pattern in patterns.items():
#             for match in re.finditer(pattern, script_text, re.IGNORECASE):
#                 char_pos = match.start()
#                 text_before = script_text[:char_pos]
#                 words_before = len(text_before.split())
#                 time_position = (words_before / 175) * 60
                
#                 production_note = {
#                     'type': note_type,
#                     'text': match.group(0),
#                     'time_position': time_position,
#                     'char_position': char_pos
#                 }
#                 production_timeline.append(production_note)
        
#         # Remove any remaining production notes
#         for pattern in patterns.values():
#             clean_script = re.sub(pattern, '', clean_script, flags=re.IGNORECASE)
        
#         print(f"🎬 Enhanced TTS processing completed")
#         print(f"   📝 Original: {len(script_text)} chars")
#         print(f"   ✨ Enhanced: {len(clean_script)} chars")
#         print(f"   🎵 Production cues: {len(production_timeline)}")
        
#         return clean_script, production_timeline
    
#     # REPLACE the _synthesize_speech_gcp method with this:
    
#     def _synthesize_speech_gcp(self, text: str, voice_config: Dict) -> Optional[bytes]:
#         """Enhanced speech synthesis with SSML support"""
#         import time
        
#         max_retries = 3
#         retry_delay = 2
        
#         for attempt in range(max_retries):
#             try:
#                 # Determine if we should use SSML
#                 use_ssml = '<speak>' in text
                
#                 if use_ssml:
#                     # Use SSML input for enhanced audio
#                     synthesis_input = texttospeech.SynthesisInput(ssml=text)
#                     print(f"   🎤 Using SSML for enhanced audio")
#                 else:
#                     # Use plain text input
#                     synthesis_input = texttospeech.SynthesisInput(text=text)
#                     print(f"   🎤 Using plain text")
                
#                 # Configure the voice
#                 voice = texttospeech.VoiceSelectionParams(
#                     language_code=voice_config["language_code"],
#                     name=voice_config["name"],
#                     ssml_gender=voice_config["ssml_gender"]
#                 )
                
#                 # Configure audio format
#                 audio_config = texttospeech.AudioConfig(
#                     audio_encoding=texttospeech.AudioEncoding.MP3,
#                     speaking_rate=1.0,
#                     pitch=0.0,
#                     volume_gain_db=0.0
#                 )
                
#                 # Perform the text-to-speech request
#                 response = self.tts_client.synthesize_speech(
#                     input=synthesis_input,
#                     voice=voice,
#                     audio_config=audio_config
#                 )
                
#                 return response.audio_content
                
#             except Exception as e:
#                 error_msg = str(e)
#                 print(f"❌ Enhanced TTS error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
#                 if any(code in error_msg for code in ['503', '502', '500', '429', 'Bad Gateway', 'Service Unavailable']):
#                     if attempt < max_retries - 1:
#                         print(f"⏳ Retrying in {retry_delay} seconds...")
#                         time.sleep(retry_delay)
#                         retry_delay *= 2
#                         continue
                
#                 return None
        
#         return None   

#     def _apply_production_effects(self, raw_audio_path: Path, output_path: Path, production_timeline: List[Dict]) -> bool:
#         """Apply production effects to audio based on timeline"""
#         try:
#             # Check if ffmpeg is available
#             result = subprocess.run(['ffmpeg', '-version'], 
#                                   capture_output=True, text=True)
#             if result.returncode != 0:
#                 print("⚠️  ffmpeg not found - install with: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)")
#                 return False
            
#             print("🎬 Processing audio with production effects...")
            
#             if not production_timeline:
#                 # No production notes, just copy the file
#                 import shutil
#                 shutil.copy2(raw_audio_path, output_path)
#                 return True
            
#             # Build ffmpeg command for basic processing
#             ffmpeg_cmd = [
#                 'ffmpeg', '-i', str(raw_audio_path),
#                 '-af', self._build_audio_filter_chain(production_timeline),
#                 '-y',  # Overwrite output
#                 str(output_path)
#             ]
            
#             # Execute ffmpeg command
#             result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
#             if result.returncode == 0:
#                 return True
#             else:
#                 print(f"⚠️  Audio processing failed: {result.stderr}")
#                 return False
                
#         except Exception as e:
#             print(f"⚠️  Production processing error: {e}")
#             return False
    
#     def _build_audio_filter_chain(self, production_timeline: List[Dict]) -> str:
#         """Build ffmpeg audio filter chain based on production timeline"""
#         filters = []
        
#         # Check for different types of effects needed
#         has_music_cues = any(cue['type'].startswith('music') for cue in production_timeline)
#         has_pause_cues = any(cue['type'] == 'pause' for cue in production_timeline)
#         has_volume_changes = any(cue['type'] == 'volume_change' for cue in production_timeline)
        
#         # Basic audio normalization
#         filters.append('loudnorm')
        
#         # Add subtle effects based on production cues
#         if has_music_cues:
#             # Add a subtle reverb for music sections
#             filters.append('aecho=0.8:0.88:60:0.4')
        
#         if has_pause_cues:
#             # Add slight compression for dramatic pauses
#             filters.append('acompressor=threshold=0.5:ratio=4:attack=200:release=1000')
        
#         # Default enhancement
#         filters.append('highpass=f=80')  # Remove low-frequency noise
#         filters.append('lowpass=f=15000')  # Remove high-frequency noise
        
#         return ','.join(filters)
    
#     def _create_podcast_package(self, script, audio_result: Dict, style: str, voice: str, topic: str) -> Dict:
#         """Create complete podcast package with metadata"""
#         # Create package info
#         package_info = {
#             "success": True,
#             "title": f"{script.source_article} - {style.title()} Podcast",
#             "source_article": script.source_article,
#             "style": style,
#             "voice": voice,
#             "audio_file": audio_result["filename"],
#             "audio_path": audio_result["file_path"],
#             "duration": f"{audio_result['estimated_duration']//60:.0f}:{audio_result['estimated_duration']%60:02.0f}",
#             "file_size_mb": audio_result["file_size_mb"],
#             "estimated_cost": audio_result["estimated_cost"],
#             "created_timestamp": datetime.now().isoformat(),
#             "script_word_count": script.word_count,
#             "script_estimated_duration": script.estimated_duration,
#             "tts_provider": "Google Cloud TTS"
#         }
        
#         # Save package metadata
#         metadata_file = self.audio_dir / f"{audio_result['filename']}.json"
#         with open(metadata_file, 'w') as f:
#             json.dump(package_info, f, indent=2)
        
#         print(f"✅ Package metadata saved: {metadata_file.name}")
        
#         return package_info
    
#     def list_podcasts(self) -> List[Dict]:
#         """List all created podcasts"""
#         if not self.audio_dir or not self.audio_dir.exists():
#             return []
        
#         podcasts = []
#         for json_file in self.audio_dir.glob('*.json'):
#             try:
#                 with open(json_file, 'r') as f:
#                     data = json.load(f)
#                     if data.get('success'):
#                         podcasts.append({
#                             'title': data['title'],
#                             'style': data['style'],
#                             'voice': data['voice'],
#                             'duration': data['duration'],
#                             'size_mb': data['file_size_mb'],
#                             'cost': data['estimated_cost'],
#                             'created': data['created_timestamp'][:10],
#                             'audio_file': data['audio_file'],
#                             'provider': data.get('tts_provider', 'Unknown')
#                         })
#             except:
#                 continue
        
#         return sorted(podcasts, key=lambda x: x['created'], reverse=True)
    
#     def get_available_voices(self) -> Dict[str, List[str]]:
#         """Get available Google Cloud TTS voices organized by quality"""
#         return {
#             "Journey (Premium - Best for Podcasts)": [
#                 "en-US-Journey-D (Male)",
#                 "en-US-Journey-F (Female)",
#                 "en-US-Journey-O (Male)"
#             ],
#             "Studio (High Quality)": [
#                 "en-US-Studio-M (Male)",
#                 "en-US-Studio-O (Female)"
#             ],
#             "Neural2 (Good Quality)": [
#                 "en-US-Neural2-A (Male)",
#                 "en-US-Neural2-C (Female)", 
#                 "en-US-Neural2-D (Male)",
#                 "en-US-Neural2-E (Female)"
#             ],
#             "Standard (Basic)": [
#                 "en-US-Standard-A (Male)",
#                 "en-US-Standard-C (Female)"
#             ]
#         }

"""
Simplified Audio Generation Pipeline
Handles audio generation with graceful fallback when TTS not available
"""

import json
import subprocess
import re
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Google Cloud TTS imports with error handling
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("⚠️ Google Cloud TTS not available - install with: pip install google-cloud-texttospeech")

try:
    from tts_processor import SSMLProcessor
    SSML_PROCESSOR_AVAILABLE = True
except ImportError:
    SSML_PROCESSOR_AVAILABLE = False
    print("⚠️ SSML Processor not available")


class AudioGenerator:
    """Simplified audio generation with graceful error handling"""
    
    def __init__(self, pipeline):
        """Initialize with reference to main pipeline"""
        self.pipeline = pipeline
        self.audio_dir = pipeline.audio_dir
        self.tts_client = None
        self.tts_available = False
        
        # Try to initialize Google Cloud TTS client
        if GOOGLE_TTS_AVAILABLE:
            try:
                self.tts_client = texttospeech.TextToSpeechClient()
                self.tts_available = True
                print("✅ Google Cloud TTS client initialized")
            except Exception as e:
                print(f"⚠️ Google Cloud TTS not available: {e}")
                print("   Pipeline will work without audio generation")
                self.tts_client = None
                self.tts_available = False
        else:
            print("⚠️ Google Cloud TTS package not installed")
            print("   Install with: pip install google-cloud-texttospeech")
    
    def is_available(self) -> bool:
        """Check if audio generation is available"""
        return self.tts_available and self.tts_client is not None
    
    def generate_complete_podcast(self, script, voice: str, topic: str, style: str) -> Optional[Dict]:
        """Generate complete podcast package with audio"""
        if not self.is_available():
            print("⚠️ Audio generation not available - returning script only")
            return {
                "success": False,
                "script": script,
                "audio": None,
                "message": "Audio generation not available - check Google Cloud TTS setup"
            }
        
        print(f"\n🎙️ COMPLETE PODCAST GENERATION: {topic}")
        print("=" * 50)
        
        try:
            # Generate audio
            print(f"\n🎵 GENERATING AUDIO")
            print("=" * 30)
            
            audio_result = self._generate_audio_gcp(script, voice)
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
                return {"script": script, "audio": None, "success": False}
                
        except Exception as e:
            print(f"❌ Error in audio generation: {e}")
            return {"script": script, "audio": None, "success": False, "error": str(e)}
    
    def generate_from_script_file(self, script_filename: str) -> Optional[Dict]:
        """Generate audio from a cached script file"""
        if not self.is_available():
            print("⚠️ Audio generation not available")
            return None
        
        try:
            # Load the script from cache
            script_data = self._load_script_from_cache(script_filename)
            if not script_data:
                print(f"❌ Could not load script file: {script_filename}")
                return None
            
            print(f"📝 Loaded script: {script_data.get('title', 'Unknown')}")
            print(f"📊 Script length: {script_data.get('word_count', 0)} words")
            
            # Create a mock script object from the data
            script = self._create_script_object(script_data)
            
            if not script or not script.script:
                print("❌ Script content is empty")
                return None
            
            # Generate audio with default voice
            voice = "en-US-Journey-D"
            print(f"🎤 Generating audio with voice: {voice}")
            
            audio_result = self._generate_audio_gcp(script, voice)
            
            if audio_result:
                package_info = self._create_podcast_package(
                    script, audio_result, script.style, voice, script.source_article
                )
                return package_info
            else:
                print("❌ Audio generation failed")
                return None
                
        except Exception as e:
            print(f"❌ Error generating audio from script file: {e}")
            return None
    
    def _create_script_object(self, script_data: dict):
        """Create script object from data"""
        try:
            from script_formatter import PodcastScript
            return PodcastScript(
                title=script_data.get('title', 'Unknown'),
                style=script_data.get('style', 'conversational'),
                script=script_data.get('script', ''),
                intro=script_data.get('intro', ''),
                outro=script_data.get('outro', ''),
                segments=script_data.get('segments', []),
                estimated_duration=script_data.get('estimated_duration', 0),
                word_count=script_data.get('word_count', 0),
                source_article=script_data.get('source_article', 'Unknown'),
                generated_timestamp=script_data.get('generated_timestamp', ''),
                custom_instructions=script_data.get('custom_instructions', None)
            )
        except Exception as e:
            print(f"❌ Error creating script object: {e}")
            return None
    
    def _load_script_from_cache(self, script_filename: str) -> Optional[dict]:
        """Load a script from the cache directory"""
        cache_dirs = [
            "../processed_scripts", "processed_scripts",
            "../processed_scripts/conversational", "processed_scripts/conversational",
            "../processed_scripts/academic", "processed_scripts/academic",
            "../processed_scripts/storytelling", "processed_scripts/storytelling"
        ]
        
        for cache_dir in cache_dirs:
            cache_path = Path(cache_dir)
            if cache_path.exists():
                # Look for the file in this directory
                script_file = cache_path / script_filename
                if script_file.exists():
                    try:
                        with open(script_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        print(f"❌ Error loading {script_file}: {e}")
                        continue
                
                # Also check subdirectories
                for style_dir in cache_path.iterdir():
                    if style_dir.is_dir():
                        script_file = style_dir / script_filename
                        if script_file.exists():
                            try:
                                with open(script_file, 'r', encoding='utf-8') as f:
                                    return json.load(f)
                            except Exception as e:
                                continue
        
        return None
    
    def _generate_audio_gcp(self, script, voice: str) -> Optional[Dict]:
        """Generate audio using Google Cloud TTS with simplified approach"""
        if not self.is_available():
            return None
        
        try:
            print(f"🎤 Using Google Cloud TTS voice: {voice}")
            
            # Process script text
            script_text = script.script
            if SSML_PROCESSOR_AVAILABLE:
                ssml_processor = SSMLProcessor()
                script_text = ssml_processor.process_script_for_tts(script_text, use_ssml=False)
            
            # Clean up text
            script_text = self._clean_text_for_tts(script_text)
            
            print(f"📝 Converting {len(script_text)} characters to speech...")
            
            # For long content, use chunking
            if len(script_text) > 4000:
                return self._generate_chunked_audio(script_text, voice, script)
            else:
                return self._generate_single_audio(script_text, voice, script)
                
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS"""
        # Remove production notes
        text = re.sub(r'\[.*?\]', '', text)
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s.,!?;:\-\']', ' ', text)
        return text.strip()
    
    def _generate_single_audio(self, text: str, voice: str, script) -> Optional[Dict]:
        """Generate audio for short text in one request"""
        try:
            voice_config = self._get_voice_config(voice)
            if not voice_config:
                voice_config = self._get_voice_config("en-US-Standard-A")  # Fallback
            
            audio_content = self._synthesize_speech(text, voice_config)
            if not audio_content:
                return None
            
            # Save audio file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self._make_safe_filename(script.source_article)
            filename = f"{safe_title}_{voice}_{timestamp}.mp3"
            file_path = self.audio_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(audio_content)
            
            # Calculate metrics
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            word_count = len(text.split())
            estimated_duration = (word_count / 175) * 60
            estimated_cost = (len(text) / 1000) * 0.016
            
            print(f"✅ Audio generated: {filename}")
            print(f"   📊 Size: {file_size_mb:.2f} MB")
            print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
            print(f"   💰 Cost: ~${estimated_cost:.3f}")
            
            return {
                "file_path": str(file_path),
                "filename": filename,
                "file_size_mb": file_size_mb,
                "estimated_duration": estimated_duration,
                "estimated_cost": estimated_cost,
                "voice_used": voice
            }
            
        except Exception as e:
            print(f"❌ Single audio generation failed: {e}")
            return None
    
    def _generate_chunked_audio(self, text: str, voice: str, script) -> Optional[Dict]:
        """Generate audio in chunks for long text"""
        try:
            print(f"📑 Using chunked generation for {len(text)} characters")
            
            # Split into chunks of ~3000 characters
            chunks = self._split_text_into_chunks(text, 3000)
            print(f"📑 Split into {len(chunks)} chunks")
            
            voice_config = self._get_voice_config(voice)
            if not voice_config:
                voice_config = self._get_voice_config("en-US-Standard-A")
            
            # Generate audio for each chunk
            audio_files = []
            total_cost = 0
            
            for i, chunk in enumerate(chunks, 1):
                print(f"   🎤 Generating chunk {i}/{len(chunks)}...")
                
                audio_content = self._synthesize_speech(chunk, voice_config)
                if not audio_content:
                    # Clean up on failure
                    for chunk_file in audio_files:
                        try:
                            Path(chunk_file).unlink()
                        except:
                            pass
                    return None
                
                # Save chunk
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_title = self._make_safe_filename(script.source_article)
                chunk_filename = f"{safe_title}_{voice}_{timestamp}_chunk_{i}.mp3"
                chunk_path = self.audio_dir / chunk_filename
                
                with open(chunk_path, 'wb') as f:
                    f.write(audio_content)
                
                audio_files.append(str(chunk_path))
                total_cost += (len(chunk) / 1000) * 0.016
                
                # Rate limiting
                time.sleep(0.5)
            
            # Combine chunks
            final_filename = f"{safe_title}_{voice}_{timestamp}.mp3"
            final_path = self.audio_dir / final_filename
            
            if self._combine_audio_files(audio_files, final_path):
                # Clean up chunks
                for chunk_file in audio_files:
                    try:
                        Path(chunk_file).unlink()
                    except:
                        pass
                
                # Calculate final metrics
                file_size_mb = final_path.stat().st_size / (1024 * 1024)
                word_count = len(text.split())
                estimated_duration = (word_count / 175) * 60
                
                print(f"✅ Combined audio generated: {final_filename}")
                print(f"   📊 Size: {file_size_mb:.2f} MB")
                print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
                print(f"   💰 Total cost: ~${total_cost:.3f}")
                
                return {
                    "file_path": str(final_path),
                    "filename": final_filename,
                    "file_size_mb": file_size_mb,
                    "estimated_duration": estimated_duration,
                    "estimated_cost": total_cost,
                    "voice_used": voice,
                    "chunked": True
                }
            else:
                # Clean up on failure
                for chunk_file in audio_files:
                    try:
                        Path(chunk_file).unlink()
                    except:
                        pass
                return None
                
        except Exception as e:
            print(f"❌ Chunked audio generation failed: {e}")
            return None
    
    def _split_text_into_chunks(self, text: str, max_chars: int) -> List[str]:
        """Split text into chunks at sentence boundaries"""
        chunks = []
        current_chunk = ""
        sentences = text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
            else:
                current_chunk += sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _synthesize_speech(self, text: str, voice_config: Dict) -> Optional[bytes]:
        """Synthesize speech with retry logic"""
        if not self.tts_client:
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_config["language_code"],
                    name=voice_config["name"],
                    ssml_gender=voice_config["ssml_gender"]
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.0,
                    pitch=0.0,
                    volume_gain_db=0.0
                )
                
                response = self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                return response.audio_content
                
            except Exception as e:
                print(f"❌ TTS attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
        return None
    
    def _get_voice_config(self, voice_name: str) -> Optional[Dict]:
        """Get voice configuration"""
        if not GOOGLE_TTS_AVAILABLE:
            return None
        
        voice_configs = {
            "en-US-Journey-D": {
                "language_code": "en-US",
                "name": "en-US-Journey-D",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "en-US-Journey-F": {
                "language_code": "en-US", 
                "name": "en-US-Journey-F",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            "en-US-Neural2-A": {
                "language_code": "en-US",
                "name": "en-US-Neural2-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "en-US-Standard-A": {
                "language_code": "en-US",
                "name": "en-US-Standard-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
        }
        
        return voice_configs.get(voice_name)
    
    def _combine_audio_files(self, audio_files: List[str], output_path: Path) -> bool:
        """Combine audio files using ffmpeg or fallback"""
        try:
            # Try ffmpeg first
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return self._combine_with_ffmpeg(audio_files, output_path)
            else:
                return self._combine_with_fallback(audio_files, output_path)
        except:
            return self._combine_with_fallback(audio_files, output_path)
    
    def _combine_with_ffmpeg(self, audio_files: List[str], output_path: Path) -> bool:
        """Combine using ffmpeg"""
        try:
            # Create file list
            file_list_path = output_path.parent / "audio_list.txt"
            with open(file_list_path, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{Path(audio_file).resolve()}'\n")
            
            # Combine files
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(file_list_path),
                '-c', 'copy', '-y', str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up
            try:
                file_list_path.unlink()
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ ffmpeg combination failed: {e}")
            return False
    
    def _combine_with_fallback(self, audio_files: List[str], output_path: Path) -> bool:
        """Simple binary concatenation fallback"""
        try:
            with open(output_path, 'wb') as output_file:
                for audio_file in audio_files:
                    with open(audio_file, 'rb') as input_file:
                        output_file.write(input_file.read())
            
            return output_path.exists() and output_path.stat().st_size > 0
            
        except Exception as e:
            print(f"❌ Fallback combination failed: {e}")
            return False
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'[^\w\s-]', '', safe_title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        return safe_title[:100]
    
    def _create_podcast_package(self, script, audio_result: Dict, style: str, voice: str, topic: str) -> Dict:
        """Create podcast package with metadata"""
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
            "tts_provider": "Google Cloud TTS"
        }
        
        # Save metadata
        try:
            metadata_file = self.audio_dir / f"{audio_result['filename']}.json"
            with open(metadata_file, 'w') as f:
                json.dump(package_info, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save metadata: {e}")
        
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
    
    def get_available_voices(self) -> Dict[str, List[str]]:
        """Get available voices"""
        if not self.is_available():
            return {"Error": ["Google Cloud TTS not available"]}
        
        return {
            "Journey (Premium)": [
                "en-US-Journey-D (Male)",
                "en-US-Journey-F (Female)"
            ],
            "Neural2 (Good Quality)": [
                "en-US-Neural2-A (Male)"
            ],
            "Standard (Basic)": [
                "en-US-Standard-A (Male)"
            ]
        }