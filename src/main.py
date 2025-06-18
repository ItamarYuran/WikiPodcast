#!/usr/bin/env python3
"""
Wikipedia to Podcast Pipeline - Main Control Script

This script orchestrates the entire pipeline:
1. Fetches Wikipedia content (trending, featured, or specific topics)
2. Generates podcast scripts in various styles
3. Provides interactive menu for different operations
4. Manages the entire workflow from content to scripts

Usage:
    python main.py                    # Interactive mode
    python main.py --trending 5       # Generate 5 trending articles
    python main.py --topic "AI"       # Generate script for specific topic
    python main.py --featured 3       # Generate 3 featured articles
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from content_fetcher import WikipediaContentFetcher, WikipediaArticle
    from script_formatter import PodcastScriptFormatter, PodcastScript
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you have: pip install openai python-dotenv requests")
    print("And that content_fetcher.py and script_formatter.py are in the same directory")
    sys.exit(1)


class PodcastPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        """Initialize the pipeline components"""
        print("🎙️  Wikipedia Podcast Pipeline Starting...")
        print("=" * 50)
        
        try:
            # Load environment variables
            load_dotenv('config/api_keys.env')
            
            # Initialize components
            self.content_fetcher = WikipediaContentFetcher()
            self.script_formatter = PodcastScriptFormatter()
            
            # Initialize OpenAI TTS
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if self.openai_api_key:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                
                # Set up audio output directory
                self.audio_dir = Path("../audio_output")
                self.audio_dir.mkdir(exist_ok=True)
                
                print("✅ Content Fetcher initialized")
                print("✅ Script Formatter initialized")
                print("✅ OpenAI TTS initialized")
                print(f"📁 Audio output: {self.audio_dir.absolute()}")
            else:
                print("✅ Content Fetcher initialized")
                print("✅ Script Formatter initialized")
                print("⚠️  OpenAI TTS not available (missing API key)")
                self.openai_client = None
                self.audio_dir = None
            
            print("✅ Pipeline ready!")
            
        except Exception as e:
            print(f"❌ Pipeline initialization failed: {e}")
            raise
    
    def show_status(self):
        """Show current pipeline status and cached content"""
        print("\n📊 PIPELINE STATUS")
        print("=" * 30)
        
        # Content cache status
        content_stats = self.content_fetcher.get_cache_stats()
        print(f"📚 Cached Articles: {content_stats['total_articles']}")
        print(f"📈 Trending Batches: {content_stats['trending_batches']}")
        print(f"⭐ Featured Batches: {content_stats['featured_batches']}")
        print(f"💾 Cache Size: {content_stats['total_size_mb']:.2f} MB")
        
        # Script cache status  
        script_cache = self.script_formatter.list_cached_scripts()
        print(f"📝 Generated Scripts: {len(script_cache)}")
        
        if script_cache:
            print("\nRecent Scripts:")
            for script in script_cache[:5]:
                print(f"  • {script['title']} ({script['style']}) - {script['duration']}")
    
    def fetch_and_generate_trending(self, count: int = 5, style: str = "conversational") -> List[PodcastScript]:
        """Fetch trending articles and generate scripts"""
        print(f"\n🔥 FETCHING {count} TRENDING ARTICLES")
        print("=" * 40)
        
        # Fetch trending articles
        articles = self.content_fetcher.get_trending_articles(count=count, min_views=5000)
        
        if not articles:
            print("❌ No trending articles found")
            return []
        
        print(f"✅ Found {len(articles)} trending articles")
        
        # Generate scripts
        print(f"\n📝 GENERATING {style.upper()} SCRIPTS")
        print("=" * 40)
        
        scripts = self.script_formatter.batch_generate_scripts(articles, style)
        
        print(f"\n✅ Generated {len(scripts)} scripts successfully!")
        return scripts
    
    def fetch_and_generate_featured(self, count: int = 3, style: str = "documentary") -> List[PodcastScript]:
        """Fetch featured articles and generate scripts"""
        print(f"\n⭐ FETCHING {count} FEATURED ARTICLES")
        print("=" * 40)
        
        # Fetch featured articles
        articles = self.content_fetcher.get_featured_articles(count=count)
        
        if not articles:
            print("❌ No featured articles found")
            return []
        
        print(f"✅ Found {len(articles)} featured articles")
        
        # Generate scripts
        print(f"\n📝 GENERATING {style.upper()} SCRIPTS")
        print("=" * 40)
        
        scripts = self.script_formatter.batch_generate_scripts(articles, style)
        
        print(f"\n✅ Generated {len(scripts)} scripts successfully!")
        return scripts
    
    def generate_complete_podcast(self, 
                                topic: str, 
                                style: str = "conversational", 
                                voice: str = "nova",
                                custom_instructions: str = None,
                                audio_enabled: bool = True) -> Optional[Dict]:
        """Generate complete podcast: content → script → audio"""
        print(f"\n🎙️ COMPLETE PODCAST GENERATION: {topic}")
        print("=" * 50)
        
        # Step 1: Get the script (fetch + generate)
        script = self.generate_single_topic(topic, style, custom_instructions)
        if not script:
            return None
    
    def _generate_audio_openai(self, script: PodcastScript, voice: str) -> Optional[Dict]:
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
            
            # Generate basic audio with cleaned script
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=voice,
                input=clean_script_text,
                response_format="mp3"
            )
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self._make_safe_filename(script.source_article)
            
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
        
        # Step 2: Generate audio if enabled and available
        if audio_enabled and self.openai_client:
            print(f"\n🎵 STEP 4: GENERATING AUDIO")
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
        
        elif audio_enabled and not self.openai_client:
            print("⚠️  Audio generation requested but OpenAI TTS not available")
            print("   Add OPENAI_API_KEY to config/api_keys.env to enable audio")
        
        return {"script": script, "audio": None}
        """Generate script for a specific topic"""
        print(f"\n🎯 PROCESSING TOPIC: {topic}")
        print("=" * 40)
        
        # First, let's try to find the exact title
        print(f"🔍 Searching for Wikipedia article: {topic}")
        
        # Get suggestions to help debug
        suggestions = self.content_fetcher.suggest_titles(topic, count=5)
        if suggestions:
            print(f"📋 Found similar titles: {', '.join(suggestions[:3])}")
        
        # Try to find exact title
        exact_title = self.content_fetcher.find_exact_title(topic)
        if exact_title:
            print(f"✅ Found exact title: {exact_title}")
            topic = exact_title
        
        # Fetch the article
        print(f"📥 Fetching Wikipedia article for: {topic}")
        article = self.content_fetcher.fetch_article(topic)
        
        if not article:
            print(f"❌ Could not find Wikipedia article for: {topic}")
            
            if suggestions:
                print(f"\n💡 Did you mean one of these?")
                for i, suggestion in enumerate(suggestions[:5], 1):
                    print(f"   {i}. {suggestion}")
                
                try:
                    choice = input(f"\nSelect a suggestion (1-{len(suggestions[:5])}) or press Enter to skip: ").strip()
                    if choice and choice.isdigit():
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(suggestions):
                            selected_topic = suggestions[choice_idx]
                            print(f"🔄 Trying with: {selected_topic}")
                            article = self.content_fetcher.fetch_article(selected_topic)
                except (ValueError, KeyboardInterrupt):
                    pass
            
            if not article:
                return None
        
        print(f"✅ Found article: {article.title}")
        print(f"   Word count: {article.word_count:,}")
        print(f"   Quality score: {article.quality_score:.2f}")
        print(f"   Recent views: {article.page_views:,}")
        
        # Generate script
        print(f"\n📝 GENERATING {style.upper()} SCRIPT")
        print("=" * 40)
        
        script = self.script_formatter.format_article_to_script(
            article, 
            style, 
            custom_instructions
        )
        
    def generate_single_topic(self, topic: str, style: str = "conversational", custom_instructions: str = None) -> Optional[PodcastScript]:
        """Generate script for a specific topic"""
        print(f"\n🎯 PROCESSING TOPIC: {topic}")
        print("=" * 40)
        
        # First, let's try to find the exact title
        print(f"🔍 Searching for Wikipedia article: {topic}")
        
        # Get suggestions to help debug
        suggestions = self.content_fetcher.suggest_titles(topic, count=5)
        if suggestions:
            print(f"📋 Found similar titles: {', '.join(suggestions[:3])}")
        
        # Try to find exact title
        exact_title = self.content_fetcher.find_exact_title(topic)
        if exact_title:
            print(f"✅ Found exact title: {exact_title}")
            topic = exact_title
        
        # Fetch the article
        print(f"📥 Fetching Wikipedia article for: {topic}")
        article = self.content_fetcher.fetch_article(topic)
        
        if not article:
            print(f"❌ Could not find Wikipedia article for: {topic}")
            
            if suggestions:
                print(f"\n💡 Did you mean one of these?")
                for i, suggestion in enumerate(suggestions[:5], 1):
                    print(f"   {i}. {suggestion}")
                
                try:
                    choice = input(f"\nSelect a suggestion (1-{len(suggestions[:5])}) or press Enter to skip: ").strip()
                    if choice and choice.isdigit():
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(suggestions):
                            selected_topic = suggestions[choice_idx]
                            print(f"🔄 Trying with: {selected_topic}")
                            article = self.content_fetcher.fetch_article(selected_topic)
                except (ValueError, KeyboardInterrupt):
                    pass
            
            if not article:
                return None
        
        print(f"✅ Found article: {article.title}")
        print(f"   Word count: {article.word_count:,}")
        print(f"   Quality score: {article.quality_score:.2f}")
        print(f"   Recent views: {article.page_views:,}")
        
        # Generate script
        print(f"\n📝 GENERATING {style.upper()} SCRIPT")
        print("=" * 40)
        
        script = self.script_formatter.format_article_to_script(
            article, 
            style, 
            custom_instructions
        )
        
        if script:
            print(f"✅ Generated script: {script.word_count} words, ~{script.estimated_duration//60} minutes")
            return script
        else:
            print("❌ Failed to generate script")
            return None
    
    def _process_script_with_production_notes(self, script_text: str) -> Tuple[str, List[Dict]]:
        """
        Process script to extract production notes and create audio timeline
        
        Returns:
            Tuple of (clean_script_for_tts, production_timeline)
        """
        import re
        
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
        """Clean script text by removing stage directions and production notes"""
        
        # Common patterns to remove for TTS
        patterns_to_remove = [
            # Stage directions in brackets
            r'\[.*?\]',
            # Music and sound cues
            r'\(.*?music.*?\)',
            r'\(.*?sound.*?\)',
            r'\(.*?audio.*?\)',
            r'\(.*?fade.*?\)',
            r'\(.*?sfx.*?\)',
            r'\(.*?background.*?\)',
            # Production notes in parentheses
            r'\(.*?producer.*?\)',
            r'\(.*?editor.*?\)',
            r'\(.*?note.*?\)',
            r'\(.*?timing.*?\)',
            r'\(.*?pause.*?\)',
            # Technical directions
            r'\*.*?\*',  # Text between asterisks
            r'--.*?--',  # Text between double dashes
            # HTML-style tags if any
            r'<.*?>',
            # Pronunciation guides (keep the word, remove the guide)
            r'(\w+)\s*\[pronounced:.*?\]',  # Replace with just the word
        ]
        
        cleaned_text = script_text
        
        # Apply all removal patterns
        import re
        for pattern in patterns_to_remove[:-1]:  # All except pronunciation
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Handle pronunciation guides specially (keep the word)
        cleaned_text = re.sub(patterns_to_remove[-1], r'\1', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and line breaks
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Multiple line breaks
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Multiple spaces/tabs
        cleaned_text = cleaned_text.strip()
        
        # Log what was removed for debugging
        original_length = len(script_text)
        cleaned_length = len(cleaned_text)
        removed_chars = original_length - cleaned_length
        
        if removed_chars > 0:
            print(f"🧹 Cleaned script: removed {removed_chars} characters of stage directions")
        
        return cleaned_text
        """Generate audio using OpenAI TTS"""
        try:
            print(f"🎤 Using OpenAI TTS voice: {voice}")
            print(f"📝 Converting {len(script.script)} characters to speech...")
            
            # Validate voice
            valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            if voice not in valid_voices:
                print(f"⚠️  Invalid voice '{voice}', using 'nova'")
                voice = "nova"
            
            # Generate audio
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # High quality model
                voice=voice,
                input=script.script,
                response_format="mp3"
            )
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = self._make_safe_filename(script.source_article)
            filename = f"{safe_title}_{voice}_{timestamp}.mp3"
            file_path = self.audio_dir / filename
            
            # Save audio file
            response.stream_to_file(file_path)
            
            # Get file info
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Estimate duration (OpenAI TTS: ~150-200 words per minute)
            estimated_duration = (script.word_count / 175) * 60  # seconds
            
            # Estimate cost (OpenAI TTS: $0.015 per 1K characters)
            char_count = len(script.script)
            estimated_cost = (char_count / 1000) * 0.015
            
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
                "voice_used": voice
            }
            
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")
            return None
    
    def _create_podcast_package(self, script: PodcastScript, audio_result: Dict, style: str, voice: str, topic: str) -> Dict:
        """Create complete podcast package with metadata"""
        import json
        
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
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    def _apply_production_effects(self, 
                                 raw_audio_path: Path, 
                                 output_path: Path, 
                                 production_timeline: List[Dict]) -> bool:
        """
        Apply production effects to audio based on timeline
        
        Returns True if processing was successful, False otherwise
        """
        try:
            # Check if ffmpeg is available
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  ffmpeg not found - install with: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)")
                return False
            
            print("🎬 Processing audio with production effects...")
            
            # For now, implement basic processing
            # You can expand this to handle more complex effects
            
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
        
        # Basic audio processing - you can expand this
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
    
    def _suggest_production_enhancements(self, script_text: str) -> str:
        """Suggest where production notes could be added to improve the script"""
        
        suggestions = []
        
        # Analyze script for potential enhancement points
        if "welcome" in script_text.lower()[:200]:
            suggestions.append("Consider adding [intro music] at the beginning")
        
        if any(word in script_text.lower() for word in ['conclusion', 'summary', 'finally']):
            suggestions.append("Consider adding [outro music] before conclusion")
        
        if '?' in script_text:
            suggestions.append("Consider adding [pause] after rhetorical questions")
        
        if len(script_text.split()) > 1000:
            suggestions.append("Consider adding [background music] for longer sections")
        
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return safe_title.replace(' ', '_')[:50]
    
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
    
    def interactive_mode(self):
        """Run interactive menu for pipeline operations"""
        print("\n🎛️  INTERACTIVE MODE")
        print("=" * 30)
        
        styles = self.script_formatter.get_available_styles()
        style_names = list(styles.keys())
        
        while True:
            print("\n📋 MAIN MENU")
            print("1. 🔥 Generate trending articles")
            print("2. ⭐ Generate featured articles") 
            print("3. 🎯 Generate specific topic")
            print("4. 🎙️ Create complete podcast (topic → audio)")
            print("5. 🎵 Generate audio from existing script")
            print("6. 📊 Show pipeline status")
            print("7. 📝 List cached scripts")
            print("8. 🎧 List generated podcasts")
            print("9. 🎨 Show available styles")
            print("10. 🧹 Clear old cache")
            print("11. ❌ Exit")
            
            choice = input("\nSelect an option (1-11): ").strip()
            
            if choice == "1":
                self._interactive_trending()
            elif choice == "2":
                self._interactive_featured()
            elif choice == "3":
                self._interactive_single_topic()
            elif choice == "4":
                self._interactive_complete_podcast()
            elif choice == "5":
                self._interactive_script_to_audio()
            elif choice == "6":
                self.show_status()
            elif choice == "7":
                self._show_cached_scripts()
            elif choice == "8":
                self._show_podcasts()
            elif choice == "9":
                self._show_styles()
            elif choice == "10":
                self._clear_cache()
            elif choice == "11":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-11.")
    
    def _interactive_trending(self):
        """Interactive trending articles generation"""
        try:
            count = int(input("How many trending articles? (1-20, default 5): ") or "5")
            count = max(1, min(count, 20))
            
            style = self._choose_style()
            if style:
                self.fetch_and_generate_trending(count, style)
        except ValueError:
            print("❌ Invalid number")
    
    def _interactive_featured(self):
        """Interactive featured articles generation"""
        try:
            count = int(input("How many featured articles? (1-10, default 3): ") or "3")
            count = max(1, min(count, 10))
            
            style = self._choose_style()
            if style:
                self.fetch_and_generate_featured(count, style)
        except ValueError:
            print("❌ Invalid number")
    
    def _interactive_single_topic(self):
        """Interactive single topic generation"""
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        style = self._choose_style()
        if not style:
            return
        
        custom = input("Custom instructions (optional): ").strip() or None
        
        self.generate_single_topic(topic, style, custom)
    
    def _interactive_complete_podcast(self):
        """Interactive complete podcast generation (topic → audio)"""
        if not self.openai_client:
            print("❌ Complete podcast creation requires OpenAI TTS")
            print("   Add OPENAI_API_KEY to config/api_keys.env")
            return
        
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        style = self._choose_style()
        if not style:
            return
        
        # Choose voice
        voices = ["nova", "onyx", "shimmer", "alloy", "echo", "fable"]
        print("\n🎤 Available voices:")
        print("1. nova - Professional female (news/documentary)")
        print("2. onyx - Conversational male (casual content)")
        print("3. shimmer - Dramatic female (storytelling)")
        print("4. alloy - Balanced, neutral")
        print("5. echo - Clear, articulate")
        print("6. fable - Expressive, engaging")
        
        try:
            voice_choice = int(input("Select voice (1-6, default 1): ") or "1")
            voice = voices[voice_choice - 1] if 1 <= voice_choice <= 6 else "nova"
        except ValueError:
            voice = "nova"
        
        custom = input("Custom instructions (optional): ").strip() or None
        
        # Generate complete podcast
        result = self.generate_complete_podcast(topic, style, voice, custom)
        
        if result and result.get("audio"):
            print(f"\n🎧 Your complete podcast is ready!")
            if sys.platform == "darwin":  # macOS
                print(f"   Play: open '{result['audio_path']}'")
            elif sys.platform == "win32":  # Windows
                print(f"   Play: start '{result['audio_path']}'")
            else:  # Linux
                print(f"   Play: xdg-open '{result['audio_path']}'")
    
    def _show_podcasts(self):
        """Show all generated podcasts"""
        podcasts = self.list_podcasts()
        
        if not podcasts:
            print("🎵 No podcasts generated yet")
            if not self.openai_client:
                print("   Enable audio generation by adding OPENAI_API_KEY to config/api_keys.env")
            return
        
        print(f"\n🎵 GENERATED PODCASTS ({len(podcasts)} total)")
        print("=" * 50)
        
        total_cost = 0
        total_duration = 0
        
        for i, podcast in enumerate(podcasts, 1):
            print(f"{i:2d}. {podcast['title']}")
            print(f"     Style: {podcast['style']} | Voice: {podcast['voice']}")
            print(f"     Duration: {podcast['duration']} | Size: {podcast['size_mb']:.1f}MB")
            print(f"     Cost: ${podcast['cost']:.3f} | Created: {podcast['created']}")
            print(f"     File: {podcast['audio_file']}")
            
            total_cost += podcast['cost']
            # Parse duration for totaling
            try:
                minutes, seconds = podcast['duration'].split(':')
                total_duration += int(minutes) * 60 + int(seconds)
            except:
                pass
        
        print(f"\n📊 TOTALS:")
        print(f"   🎵 {len(podcasts)} podcasts")
        print(f"   ⏱️  {total_duration//60}:{total_duration%60:02d} total duration")
    def _interactive_script_to_audio(self):
        """Interactive script-to-audio generation"""
        if not self.openai_client:
            print("❌ Audio generation requires OpenAI TTS")
            print("   Add OPENAI_API_KEY to config/api_keys.env")
            return
        
        # List available scripts
        scripts = self.script_formatter.list_cached_scripts()
        
        if not scripts:
            print("📝 No cached scripts found")
            print("   Generate some scripts first using options 1-3")
            return
        
        print(f"\n📝 AVAILABLE SCRIPTS ({len(scripts)} total)")
        print("=" * 50)
        
        # Show scripts with numbers
        for i, script in enumerate(scripts[:20], 1):  # Show max 20
            print(f"{i:2d}. {script['title']}")
            print(f"     Style: {script['style']} | Words: {script['word_count']} | Generated: {script['generated']}")
        
        if len(scripts) > 20:
            print(f"     ... and {len(scripts) - 20} more")
        
        try:
            choice = int(input(f"\nSelect script (1-{min(len(scripts), 20)}): "))
            if not (1 <= choice <= min(len(scripts), 20)):
                print("❌ Invalid selection")
                return
            
            selected_script_info = scripts[choice - 1]
            
            # Load the actual script
            script = self.script_formatter.load_cached_script(
                selected_script_info['filename'], 
                selected_script_info['style']
            )
            
            if not script:
                print("❌ Could not load script file")
                return
            
            print(f"\n✅ Selected: {script.title}")
            print(f"   📝 {script.word_count} words, ~{script.estimated_duration//60} min")
            
            # Choose voice
            voices = ["nova", "onyx", "shimmer", "alloy", "echo", "fable"]
            print("\n🎤 Available voices:")
            print("1. nova - Professional female (news/documentary)")
            print("2. onyx - Conversational male (casual content)")
            print("3. shimmer - Dramatic female (storytelling)")
            print("4. alloy - Balanced, neutral")
            print("5. echo - Clear, articulate")
            print("6. fable - Expressive, engaging")
            
            voice_choice = int(input("Select voice (1-6, default 1): ") or "1")
            voice = voices[voice_choice - 1] if 1 <= voice_choice <= 6 else "nova"
            
            print(f"\n🎵 GENERATING AUDIO")
            print("=" * 30)
            print(f"🎤 Voice: {voice}")
            print(f"📝 Script: {script.title}")
            
            # Generate audio
            audio_result = self._generate_audio_openai(script, voice)
            
            if audio_result:
                # Create podcast package
                podcast_info = self._create_podcast_package(
                    script, audio_result, script.style, voice, script.source_article
                )
                
                print(f"\n🎉 AUDIO GENERATED SUCCESSFULLY!")
                print("=" * 40)
                print(f"🎵 Audio: {podcast_info['audio_file']}")
                print(f"⏱️  Duration: {podcast_info['duration']}")
                print(f"📊 Size: {podcast_info['file_size_mb']:.2f} MB")
                print(f"💰 Cost: ~${podcast_info['estimated_cost']:.3f}")
                
                # Show play command based on OS
                if sys.platform == "darwin":  # macOS
                    print(f"🎧 Play: open '{podcast_info['audio_path']}'")
                elif sys.platform == "win32":  # Windows
                    print(f"🎧 Play: start '{podcast_info['audio_path']}'")
                else:  # Linux
                    print(f"🎧 Play: xdg-open '{podcast_info['audio_path']}'")
            else:
                print("❌ Audio generation failed")
                
        except (ValueError, IndexError):
            print("❌ Invalid selection")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _choose_style(self) -> Optional[str]:
        """Interactive style selection"""
        styles = self.script_formatter.get_available_styles()
        style_names = list(styles.keys())
        
        print("\n🎨 Available Styles:")
        for i, (name, info) in enumerate(styles.items(), 1):
            print(f"{i}. {info['name']} - {info['description']}")
        
        try:
            choice = int(input(f"\nSelect style (1-{len(style_names)}): "))
            if 1 <= choice <= len(style_names):
                return style_names[choice - 1]
            else:
                print("❌ Invalid style choice")
                return None
        except ValueError:
            print("❌ Invalid input")
            return None
    
    def _show_cached_scripts(self):
        """Show all cached scripts"""
        scripts = self.script_formatter.list_cached_scripts()
        
        if not scripts:
            print("📝 No cached scripts found")
            return
        
        print(f"\n📝 CACHED SCRIPTS ({len(scripts)} total)")
        print("=" * 50)
        
        for i, script in enumerate(scripts, 1):
            print(f"{i:2d}. {script['title']}")
            print(f"     Style: {script['style']} | Duration: {script['duration']} | Generated: {script['generated']}")
    
    def _show_styles(self):
        """Show available podcast styles"""
        styles = self.script_formatter.get_available_styles()
        
        print("\n🎨 AVAILABLE PODCAST STYLES")
        print("=" * 40)
        
        for name, info in styles.items():
            print(f"\n📻 {info['name']}")
            print(f"   {info['description']}")
            print(f"   Target Duration: {info['target_duration']}")
            print(f"   Voice Style: {info['voice_style']}")
    
    def _clear_cache(self):
        """Clear old cache files"""
        print("\n🧹 CACHE CLEANUP")
        print("=" * 20)
        
        try:
            days = int(input("Clear cache older than how many days? (default 7): ") or "7")
            
            confirm = input(f"Clear cache older than {days} days? (y/N): ").lower()
            if confirm == 'y':
                self.content_fetcher.clear_cache(older_than_days=days)
                print("✅ Cache cleaned successfully")
            else:
                print("❌ Cache cleanup cancelled")
        except ValueError:
            print("❌ Invalid number")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Wikipedia to Podcast Pipeline")
    parser.add_argument("--trending", type=int, metavar="COUNT", 
                       help="Generate scripts for COUNT trending articles")
    parser.add_argument("--featured", type=int, metavar="COUNT",
                       help="Generate scripts for COUNT featured articles")
    parser.add_argument("--topic", type=str, metavar="TOPIC",
                       help="Generate script for specific Wikipedia topic")
    parser.add_argument("--style", type=str, default="conversational",
                       help="Podcast style (default: conversational)")
    parser.add_argument("--custom", type=str, 
                       help="Custom instructions for script generation")
    parser.add_argument("--voice", type=str, default="nova",
                       help="OpenAI voice for audio generation (nova, onyx, shimmer, etc.)")
    parser.add_argument("--audio", action="store_true",
                       help="Generate complete podcast with audio (topic → script → audio)")
    parser.add_argument("--no-audio", action="store_true",
                       help="Generate script only, skip audio generation")
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = PodcastPipeline()
        
        # Command line mode
        if args.trending:
            pipeline.fetch_and_generate_trending(args.trending, args.style)
        elif args.featured:
            pipeline.fetch_and_generate_featured(args.featured, args.style)
        elif args.topic:
            # Decide whether to generate audio
            generate_audio = args.audio or (not args.no_audio and pipeline.openai_client)
            
            if generate_audio:
                pipeline.generate_complete_podcast(args.topic, args.style, args.voice, args.custom)
            else:
                pipeline.generate_single_topic(args.topic, args.style, args.custom)
        else:
            # Interactive mode
            pipeline.show_status()
            pipeline.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n👋 Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline Error: {e}")
        print("Check your API keys and internet connection")
        sys.exit(1)


if __name__ == "__main__":
    main()