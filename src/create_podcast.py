#!/usr/bin/env python3
"""
Complete Podcast Creator using Google Cloud TTS

This script creates a complete podcast from Wikipedia article to final audio:
1. Fetches Wikipedia content
2. Generates podcast script with GPT-4
3. Converts to audio using Google Cloud TTS
4. Saves everything with metadata

Usage:
    python create_podcast.py "Machine Learning" conversational en-US-Journey-D
    python create_podcast.py "Climate Change" documentary en-US-Studio-M
    python create_podcast.py "Ancient Rome" storytelling en-US-Neural2-C
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from content_fetcher import WikipediaContentFetcher
    from script_formatter import PodcastScriptFormatter
    from openai import OpenAI
    from dotenv import load_dotenv
    # Google Cloud TTS imports
    from google.cloud import texttospeech
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have: pip install openai python-dotenv requests google-cloud-texttospeech")
    sys.exit(1)


class PodcastCreator:
    """Complete podcast creation pipeline using Google Cloud TTS"""
    
    def __init__(self):
        """Initialize the podcast creator"""
        print("🎙️ Podcast Creator with Google Cloud TTS")
        print("=" * 45)
        
        # Load environment variables
        load_dotenv('../config/api_keys.env')
        
        # Initialize components
        self.content_fetcher = WikipediaContentFetcher()
        self.script_formatter = PodcastScriptFormatter()
        
        # Initialize OpenAI client for script generation
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in config/api_keys.env")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Google Cloud TTS client
        try:
            self.tts_client = texttospeech.TextToSpeechClient()
            print("✅ Google Cloud TTS client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Google Cloud TTS: {e}")
            print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set correctly")
            raise
        
        # Set up audio output directory
        self.audio_dir = Path("../audio_output")
        self.audio_dir.mkdir(exist_ok=True)
        
        print("✅ Content fetcher ready")
        print("✅ Script formatter ready")
        print("✅ OpenAI GPT-4 ready")
        print("✅ Google Cloud TTS ready")
        print(f"📁 Audio output: {self.audio_dir.absolute()}")
    
    def create_podcast(self, 
                      topic: str, 
                      style: str = "conversational",
                      voice: str = "en-US-Journey-D",
                      custom_instructions: str = None) -> dict:
        """
        Create complete podcast from topic to audio
        
        Args:
            topic: Wikipedia topic to create podcast about
            style: Podcast style (conversational, documentary, etc.)
            voice: Google Cloud TTS voice (e.g., "en-US-Journey-D")
            custom_instructions: Additional instructions for script generation
            
        Returns:
            Dictionary with all generated files and metadata
        """
        
        print(f"\n🎯 CREATING PODCAST: {topic}")
        print(f"📝 Style: {style}")
        print(f"🎤 Voice: {voice}")
        print("=" * 50)
        
        # Step 1: Fetch Wikipedia content
        print("\n📚 STEP 1: Fetching Wikipedia content")
        print("-" * 30)
        
        article = self.content_fetcher.fetch_article(topic)
        if not article:
            # Try with suggestions
            suggestions = self.content_fetcher.suggest_titles(topic, 5)
            if suggestions:
                print(f"💡 Suggestions: {', '.join(suggestions[:3])}")
                article = self.content_fetcher.fetch_article(suggestions[0])
        
        if not article:
            print(f"❌ Could not find Wikipedia article for: {topic}")
            return {"success": False, "error": "Article not found"}
        
        print(f"✅ Found: {article.title}")
        print(f"   📊 {article.word_count:,} words, Quality: {article.quality_score:.2f}")
        print(f"   👀 {article.page_views:,} recent views")
        
        # Step 2: Generate podcast script
        print(f"\n📝 STEP 2: Generating {style} script")
        print("-" * 30)
        
        script = self.script_formatter.format_article_to_script(
            article, 
            style=style,
            custom_instructions=custom_instructions
        )
        
        if not script:
            print("❌ Failed to generate script")
            return {"success": False, "error": "Script generation failed"}
        
        print(f"✅ Script generated: {script.word_count} words")
        print(f"   ⏱️  Estimated duration: {script.estimated_duration//60}:{script.estimated_duration%60:02d}")
        
        # Step 3: Generate audio with Google Cloud TTS
        print(f"\n🎵 STEP 3: Generating audio with Google Cloud TTS")
        print("-" * 30)
        
        audio_result = self._generate_audio_gcp(script, voice)
        
        if not audio_result:
            print("❌ Failed to generate audio")
            return {"success": False, "error": "Audio generation failed"}
        
        # Step 4: Create final podcast package
        print(f"\n📦 STEP 4: Creating podcast package")
        print("-" * 30)
        
        podcast_info = self._create_podcast_package(article, script, audio_result, style, voice)
        
        print(f"\n🎉 PODCAST CREATED SUCCESSFULLY!")
        print("=" * 40)
        print(f"📝 Title: {podcast_info['title']}")
        print(f"🎵 Audio: {podcast_info['audio_file']}")
        print(f"⏱️  Duration: {podcast_info['duration']}")
        print(f"📊 Size: {podcast_info['file_size_mb']:.2f} MB")
        print(f"💰 Cost: ~${podcast_info['estimated_cost']:.3f}")
        
        return podcast_info
    
    def _generate_audio_gcp(self, script, voice: str) -> dict:
        """Generate audio using Google Cloud TTS"""
        try:
            print(f"🎤 Using Google Cloud TTS voice: {voice}")
            
            # Clean the script text (remove production notes)
            clean_script_text = self._clean_script_for_tts(script.script)
            print(f"📝 Converting {len(clean_script_text)} characters to speech...")
            
            # Get voice configuration
            voice_config = self._get_voice_config(voice)
            if not voice_config:
                print(f"⚠️  Invalid voice '{voice}', using default")
                voice_config = self._get_voice_config("en-US-Journey-D")
            
            # Check for character limit (Google Cloud TTS has 5000 character limit)
            if len(clean_script_text) > 5000:
                print(f"⚠️  Script too long ({len(clean_script_text)} chars), chunking...")
                return self._generate_chunked_audio(clean_script_text, voice_config, script)
            
            # Generate audio
            audio_content = self._synthesize_speech(clean_script_text, voice_config)
            if not audio_content:
                print("❌ Failed to synthesize speech")
                return None
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self._make_safe_filename(script.source_article)
            filename = f"{safe_title}_{voice}_{timestamp}.mp3"
            file_path = self.audio_dir / filename
            
            # Save audio file
            with open(file_path, 'wb') as f:
                f.write(audio_content)
            
            # Get file info
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Estimate duration (rough calculation)
            # Google Cloud TTS typically generates about 150-200 words per minute
            estimated_duration = (script.word_count / 175) * 60  # seconds
            
            # Estimate cost (Google Cloud TTS pricing: $0.016 per 1K characters)
            char_count = len(clean_script_text)
            estimated_cost = (char_count / 1000) * 0.016
            
            print(f"✅ Audio generated successfully!")
            print(f"   📁 File: {filename}")
            print(f"   📊 Size: {file_size_mb:.2f} MB")
            print(f"   ⏱️  Duration: ~{estimated_duration//60:.0f}:{estimated_duration%60:02.0f}")
            print(f"   💰 Cost: ~${estimated_cost:.3f}")
            
            return {
                "file_path": str(file_path),
                "filename": filename,
                "file_size_mb": file_size_mb,
                "estimated_duration": estimated_duration,
                "estimated_cost": estimated_cost,
                "voice_used": voice,
                "chunked": False
            }
            
        except Exception as e:
            print(f"❌ Google Cloud TTS error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_chunked_audio(self, script_text: str, voice_config: dict, script) -> dict:
        """Generate audio in chunks for long scripts with better error handling"""
        print(f"📑 Splitting script into chunks for audio generation...")
        
        # Split script into chunks of ~4000 characters (more conservative for reliability)
        chunks = []
        current_chunk = ""
        sentences = script_text.split('. ')
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') > 4000 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
            else:
                current_chunk += sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        print(f"📑 Split into {len(chunks)} audio chunks")
        
        # Generate audio for each chunk with retry logic
        audio_files = []
        total_cost = 0
        
        for i, chunk in enumerate(chunks, 1):
            print(f"   🎤 Generating audio chunk {i}/{len(chunks)}...")
            
            # Try to synthesize this chunk
            audio_content = self._synthesize_speech(chunk, voice_config)
            if not audio_content:
                print(f"     ❌ Chunk {i} failed after all retries")
                # Clean up any successful chunks
                for chunk_file in audio_files:
                    try:
                        Path(chunk_file).unlink()
                    except:
                        pass
                return None
            
            # Save chunk audio
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self._make_safe_filename(script.source_article)
            chunk_filename = f"{safe_title}_{voice_config['name']}_{timestamp}_chunk_{i}.mp3"
            chunk_file_path = self.audio_dir / chunk_filename
            
            with open(chunk_file_path, 'wb') as f:
                f.write(audio_content)
            
            audio_files.append(str(chunk_file_path))
            
            # Calculate cost for this chunk
            char_count = len(chunk)
            chunk_cost = (char_count / 1000) * 0.016
            total_cost += chunk_cost
            
            print(f"     ✅ Chunk {i}: {len(chunk)} chars, ${chunk_cost:.3f}")
            
            # Small delay between chunks to be nice to the API
            if i < len(chunks):
                import time
                time.sleep(0.5)
        
        # Combine audio files using ffmpeg if available
        final_filename = f"{safe_title}_{voice_config['name']}_{timestamp}.mp3"
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
            estimated_duration = (script.word_count / 175) * 60
            
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
                "voice_used": voice_config['name'],
                "chunked": True
            }
        else:
            print("❌ Failed to combine audio chunks")
            # Clean up chunk files
            for chunk_file in audio_files:
                try:
                    Path(chunk_file).unlink()
                except:
                    pass
            return None
    
    def _get_voice_config(self, voice_name: str) -> dict:
        """Get voice configuration for Google Cloud TTS"""
        
        # Popular Google Cloud TTS voices for podcasts
        voice_configs = {
            # Journey voices (best for podcasts)
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
            "en-US-Journey-O": {
                "language_code": "en-US",
                "name": "en-US-Journey-O",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            # Studio voices (high quality)
            "en-US-Studio-M": {
                "language_code": "en-US",
                "name": "en-US-Studio-M", 
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "en-US-Studio-O": {
                "language_code": "en-US",
                "name": "en-US-Studio-O",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            # Neural2 voices (good quality)
            "en-US-Neural2-A": {
                "language_code": "en-US",
                "name": "en-US-Neural2-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "en-US-Neural2-C": {
                "language_code": "en-US",
                "name": "en-US-Neural2-C", 
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            "en-US-Neural2-D": {
                "language_code": "en-US",
                "name": "en-US-Neural2-D",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "en-US-Neural2-E": {
                "language_code": "en-US",
                "name": "en-US-Neural2-E",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            # Standard voices
            "en-US-Standard-A": {
                "language_code": "en-US",
                "name": "en-US-Standard-A",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            },
            "en-US-Standard-C": {
                "language_code": "en-US",
                "name": "en-US-Standard-C",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            },
        }
        
        return voice_configs.get(voice_name)
    
    def _synthesize_speech(self, text: str, voice_config: dict) -> bytes:
        """Synthesize speech using Google Cloud TTS with retry logic"""
        import time
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Set up the synthesis input
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # Configure the voice
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_config["language_code"],
                    name=voice_config["name"],
                    ssml_gender=voice_config["ssml_gender"]
                )
                
                # Configure audio format
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.0,  # Normal speed
                    pitch=0.0,  # Normal pitch
                    volume_gain_db=0.0  # Normal volume
                )
                
                # Perform the text-to-speech request
                response = self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                return response.audio_content
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Speech synthesis error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                # Check if it's a retryable error
                if any(code in error_msg for code in ['503', '502', '500', '429', 'Bad Gateway', 'Service Unavailable']):
                    if attempt < max_retries - 1:
                        print(f"⏳ Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                
                # If not retryable or max retries reached, return None
                return None
        
        return None
    
    def _clean_script_for_tts(self, script_text: str) -> str:
        """Clean script text for TTS by removing production notes"""
        import re
        
        # Remove production notes in brackets
        patterns = [
            r'\[.*?music.*?\]',
            r'\[.*?pause.*?\]',
            r'\[.*?sound.*?\]',
            r'\[.*?fade.*?\]',
            r'\[.*?effect.*?\]',
            r'\*.*?\*',
            r'\(.*?producer.*?\)',
            r'\(.*?note.*?\)',
        ]
        
        clean_script = script_text
        for pattern in patterns:
            clean_script = re.sub(pattern, '', clean_script, flags=re.IGNORECASE)
        
        # Clean up whitespace
        clean_script = re.sub(r'\n\s*\n\s*', '\n\n', clean_script)
        clean_script = re.sub(r'[ \t]+', ' ', clean_script)
        clean_script = clean_script.strip()
        
        return clean_script
    
    def _combine_audio_files(self, audio_files: list, output_path: Path) -> bool:
        """Combine multiple audio files using ffmpeg"""
        try:
            import subprocess
            
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
    
    def _create_podcast_package(self, article, script, audio_result, style, voice) -> dict:
        """Create complete podcast package with metadata"""
        
        # Create package info
        package_info = {
            "success": True,
            "title": f"{article.title} - {style.title()} Podcast",
            "source_article": article.title,
            "wikipedia_url": article.url,
            "style": style,
            "voice": voice,
            "audio_file": audio_result["filename"],
            "audio_path": audio_result["file_path"],
            "duration": f"{audio_result['estimated_duration']//60:.0f}:{audio_result['estimated_duration']%60:02.0f}",
            "file_size_mb": audio_result["file_size_mb"],
            "estimated_cost": audio_result["estimated_cost"],
            "created_timestamp": datetime.now().isoformat(),
            "script_word_count": script.word_count,
            "article_word_count": article.word_count,
            "article_quality_score": article.quality_score,
            "article_page_views": article.page_views,
            "tts_provider": "Google Cloud TTS",
            "chunked": audio_result.get("chunked", False)
        }
        
        # Save package metadata
        metadata_file = self.audio_dir / f"{audio_result['filename']}.json"
        with open(metadata_file, 'w') as f:
            json.dump(package_info, f, indent=2)
        
        print(f"✅ Package metadata saved: {metadata_file.name}")
        
        return package_info
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return safe_title.replace(' ', '_')[:50]
    
    def list_podcasts(self) -> list:
        """List all created podcasts"""
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
                            'audio_file': data['audio_file'],
                            'provider': data.get('tts_provider', 'Unknown'),
                            'chunked': data.get('chunked', False)
                        })
            except:
                continue
        
        return sorted(podcasts, key=lambda x: x['created'], reverse=True)
    
    def get_available_voices(self) -> dict:
        """Get available Google Cloud TTS voices organized by quality"""
        return {
            "Journey (Premium - Best for Podcasts)": [
                "en-US-Journey-D (Male)",
                "en-US-Journey-F (Female)",
                "en-US-Journey-O (Male)"
            ],
            "Studio (High Quality)": [
                "en-US-Studio-M (Male)",
                "en-US-Studio-O (Female)"
            ],
            "Neural2 (Good Quality)": [
                "en-US-Neural2-A (Male)",
                "en-US-Neural2-C (Female)", 
                "en-US-Neural2-D (Male)",
                "en-US-Neural2-E (Female)"
            ],
            "Standard (Basic)": [
                "en-US-Standard-A (Male)",
                "en-US-Standard-C (Female)"
            ]
        }


def main():
    """Main function for command line usage"""
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python create_podcast.py <topic> [style] [voice]")
        print("\nExamples:")
        print("  python create_podcast.py 'Machine Learning'")
        print("  python create_podcast.py 'Climate Change' documentary")
        print("  python create_podcast.py 'Ancient Rome' storytelling en-US-Journey-F")
        print("\nAvailable styles: conversational, documentary, storytelling, news_report, comedy, academic")
        print("\nAvailable voices:")
        print("  Journey (Premium): en-US-Journey-D, en-US-Journey-F, en-US-Journey-O")
        print("  Studio (High Quality): en-US-Studio-M, en-US-Studio-O")
        print("  Neural2 (Good Quality): en-US-Neural2-A, en-US-Neural2-C, en-US-Neural2-D, en-US-Neural2-E")
        print("  Standard (Basic): en-US-Standard-A, en-US-Standard-C")
        sys.exit(1)
    
    topic = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    voice = sys.argv[3] if len(sys.argv) > 3 else "en-US-Journey-D"
    
    try:
        # Create podcast
        creator = PodcastCreator()
        result = creator.create_podcast(topic, style, voice)
        
        if result.get("success"):
            print(f"\n🎧 Your podcast is ready!")
            print(f"Play it with: open '{result['audio_path']}'")
            
            # Show other podcasts
            podcasts = creator.list_podcasts()
            if len(podcasts) > 1:
                print(f"\n📚 You have {len(podcasts)} podcasts total:")
                for p in podcasts[:5]:
                    provider = p.get('provider', 'Unknown')
                    chunked = ' (chunked)' if p.get('chunked') else ''
                    print(f"  • {p['title']} ({p['style']}, {p['duration']}) - {provider}{chunked}")
                    
            # Show available voices
            print(f"\n🎤 Available voices for next time:")
            voices = creator.get_available_voices()
            for category, voice_list in voices.items():
                print(f"  {category}:")
                for voice_name in voice_list:
                    print(f"    • {voice_name}")
                    
        else:
            print(f"\n❌ Podcast creation failed: {result.get('error')}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Podcast creation interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your Google Cloud TTS credentials are set up correctly")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()