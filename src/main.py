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
                
                # Set up audio output directory (relative to current working directory)
                self.audio_dir = Path("audio_output")  # Changed from "../audio_output"
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
        
        # Fetch trending articles with better filtering
        articles = self.content_fetcher.get_trending_articles(
            count=count * 2,  # Get more to account for filtering
            min_views=5000,
            exclude_categories=[
                'Disambiguation pages', 'Redirects', 'Wikipedia',
                'Articles with dead external links', 'Mathematical series',
                'Lists of', 'Categories', 'Templates'
            ]
        )
        
        if not articles:
            print("❌ No trending articles found")
            return []
        
        # Filter articles that are suitable for podcasts and not too long
        suitable_articles = []
        for article in articles:
            # Skip very long articles that might cause token issues
            if article.word_count > 8000:
                print(f"⚠️  Skipping '{article.title}' - too long ({article.word_count} words)")
                continue
            
            # Skip articles with unusual characters or mathematical content
            if any(char in article.title for char in ['−', '+', '⋯', '∞', '∑', '∏']):
                print(f"⚠️  Skipping '{article.title}' - mathematical content")
                continue
            
            # Skip very short articles
            if article.word_count < 500:
                print(f"⚠️  Skipping '{article.title}' - too short ({article.word_count} words)")
                continue
            
            suitable_articles.append(article)
            if len(suitable_articles) >= count:
                break
        
        if not suitable_articles:
            print("❌ No suitable articles found after filtering")
            return []
        
        print(f"✅ Found {len(suitable_articles)} suitable trending articles")
        
        # Generate scripts with length control
        print(f"\n📝 GENERATING {style.upper()} SCRIPTS")
        print("=" * 40)
        
        scripts = []
        for i, article in enumerate(suitable_articles, 1):
            print(f"\n[{i}/{len(suitable_articles)}] Processing: {article.title}")
            print(f"   📊 {article.word_count:,} words, Quality: {article.quality_score:.2f}")
            
            # Apply medium length control for trending articles to avoid token issues
            if article.word_count > 3000:
                print("   🎯 Applying medium length control to prevent token limits...")
                article.content = self.content_fetcher._control_content_length(
                    article.content, "medium"
                )
                article.word_count = len(article.content.split())
            
            script = self.script_formatter.format_article_to_script(article, style)
            
            if script:
                scripts.append(script)
                print(f"   ✅ Generated script: {script.word_count} words")
            else:
                print(f"   ❌ Failed to generate script")
            
            # Rate limiting
            if i < len(suitable_articles):
                print("   ⏳ Rate limiting pause...")
                import time
                time.sleep(3)  # Increased pause
        
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
    
    def generate_single_topic(self, 
                             topic: str, 
                             style: str = "conversational", 
                             custom_instructions: str = None,
                             target_duration: str = "medium") -> Optional[PodcastScript]:
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
        
        # Fetch the article with target length
        print(f"📥 Fetching Wikipedia article for: {topic}")
        print(f"🎯 Target duration: {target_duration}")
        article = self.content_fetcher.fetch_article(topic, target_length=target_duration)
        
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
                            article = self.content_fetcher.fetch_article(selected_topic, target_length=target_duration)
                except (ValueError, KeyboardInterrupt):
                    pass
            
            if not article:
                return None
        
        print(f"✅ Found article: {article.title}")
        print(f"   Word count: {article.word_count:,}")
        print(f"   Quality score: {article.quality_score:.2f}")
        print(f"   Recent views: {article.page_views:,}")
        
        # Show estimated duration
        duration_seconds, formatted_duration = self.content_fetcher.estimate_podcast_duration(
            article.word_count, style
        )
        print(f"   📊 Estimated podcast duration: {formatted_duration}")
        print(f"       ({duration_seconds//60} min {duration_seconds%60} sec in {style} style)")
        
        # Generate script
        print(f"\n📝 GENERATING {style.upper()} SCRIPT")
        print("=" * 40)
        
        # Add full-length instruction if target_duration is "full"
        if target_duration == "full":
            if custom_instructions:
                custom_instructions += " Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided."
            else:
                custom_instructions = "Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided. This should be a full-length, thorough presentation."
            print(f"🔍 Using full-length instruction for comprehensive coverage")
        
        script = self.script_formatter.format_article_to_script(
            article, 
            style, 
            custom_instructions
        )
        
        if script:
            actual_ratio = (script.word_count / article.word_count) * 100
            print(f"✅ Generated script: {script.word_count} words, ~{script.estimated_duration//60} minutes")
            print(f"📈 Content ratio: {actual_ratio:.1f}% of original article")
            
            # Warn if the script is much shorter than expected for "full" duration
            if target_duration == "full" and actual_ratio < 50:
                print(f"⚠️  WARNING: Script seems shorter than expected for 'full' duration")
                print(f"   Expected: Close to {article.word_count:,} words")  
                print(f"   Got: {script.word_count} words ({actual_ratio:.1f}%)")
                print(f"   This might be due to LLM token limits or script formatter settings")
            
            return script
        else:
            print("❌ Failed to generate script")
            return None
    
    def generate_complete_podcast(self, 
                                topic: str, 
                                style: str = "conversational", 
                                voice: str = "nova",
                                custom_instructions: str = None,
                                audio_enabled: bool = True,
                                target_duration: str = "medium") -> Optional[Dict]:
        """Generate complete podcast: content → script → audio"""
        print(f"\n🎙️ COMPLETE PODCAST GENERATION: {topic}")
        print("=" * 50)
        
        # Step 1: Get the script (fetch + generate)
        script = self.generate_single_topic(topic, style, custom_instructions, target_duration)
        if not script:
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
    
    def _choose_duration(self) -> str:
        """Interactive duration selection"""
        print("\n⏱️ Choose target podcast duration:")
        print("1. Short (~5 minutes) - Key highlights only")
        print("2. Medium (~10 minutes) - Main content with details")  
        print("3. Long (~15 minutes) - Comprehensive coverage")
        print("4. Full - Complete article content")
        
        try:
            choice = int(input("Select duration (1-4, default 2): ") or "2")
            duration_map = {1: "short", 2: "medium", 3: "long", 4: "full"}
            return duration_map.get(choice, "medium")
        except ValueError:
            return "medium"
    
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
        return safe_title.replace(' ', '_')[:50]
    
    def list_podcasts(self) -> List[Dict]:
        """List all created podcasts"""
        if not self.audio_dir or not self.audio_dir.exists():
            return []
        
        podcasts = []
        for json_file in self.audio_dir.glob('*.json'):
            try:
                import json
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
            print("1. 📚 Fetch articles only (no scripts)")
            print("2. 📝 Create script from article")
            print("3. 🔥 Generate trending articles")
            print("4. ⭐ Generate featured articles") 
            print("5. 🎯 Generate specific topic")
            print("6. 🎙️ Create complete podcast (topic → audio)")
            print("7. 📝 Generate script from cached article")
            print("8. 🎵 Generate audio from existing script")
            print("9. 🎛️ Post-production enhancement")
            print("10. 📊 Show pipeline status")
            print("11. 📝 List cached scripts")
            print("12. 🎧 List generated podcasts")
            print("13. 🎨 Show available styles")
            print("14. 🧹 Clear old cache")
            print("15. ❌ Exit")
            
            choice = input("\nSelect an option (1-15): ").strip()
            
            if choice == "1":
                self._interactive_fetch_only()
            elif choice == "2":
                self._interactive_article_to_script()
            elif choice == "3":
                self._interactive_trending()
            elif choice == "4":
                self._interactive_featured()
            elif choice == "5":
                self._interactive_single_topic()
            elif choice == "6":
                self._interactive_complete_podcast()
            elif choice == "7":
                self._interactive_cached_article_to_script()
            elif choice == "8":
                self._interactive_script_to_audio()
            elif choice == "9":
                self._interactive_post_production()
            elif choice == "10":
                self.show_status()
            elif choice == "11":
                self._show_cached_scripts()
            elif choice == "12":
                self._show_podcasts()
            elif choice == "13":
                self._show_styles()
            elif choice == "14":
                self._clear_cache()
            elif choice == "15":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-15.")
    
    def _manual_cache_article(self, article) -> bool:
        """Manual fallback method to cache article if other methods fail"""
        try:
            import json
            from datetime import datetime
            
            # Create articles directory if it doesn't exist
            articles_dir = Path("articles")
            articles_dir.mkdir(exist_ok=True)
            
            # Create safe filename
            safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_title}_{timestamp}.json"
            
            # Create article data
            article_data = {
                'title': article.title,
                'content': article.content,
                'word_count': article.word_count,
                'quality_score': getattr(article, 'quality_score', 1.0),
                'page_views': getattr(article, 'page_views', 0),
                'url': getattr(article, 'url', f"https://en.wikipedia.org/wiki/{article.title.replace(' ', '_')}"),
                'cached_timestamp': datetime.now().isoformat(),
                'summary': getattr(article, 'summary', ''),
                'categories': getattr(article, 'categories', []),
                'images': getattr(article, 'images', [])
            }
            
            # Save to file
            file_path = articles_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, indent=2, ensure_ascii=False)
            
            print(f"📁 Manually saved: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Manual caching failed: {e}")
            return False
    
    def _ensure_articles_directory(self):
        """Ensure articles directory exists and is writable"""
        try:
            articles_dir = Path("articles")
            articles_dir.mkdir(exist_ok=True)
            
            # Test write permissions
            test_file = articles_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            print(f"📁 Articles directory: {articles_dir.absolute()}")
            return True
            
        except Exception as e:
            print(f"❌ Articles directory issue: {e}")
            return False
    
    def _debug_caching(self, article_title: str):
        """Debug caching issues"""
        print(f"\n🔍 DEBUG: Checking cache for '{article_title}'")
        
        # Check if articles directory exists
        articles_dir = Path("articles")
        if articles_dir.exists():
            print(f"✅ Articles directory exists: {articles_dir.absolute()}")
            
            # List files in directory
            files = list(articles_dir.glob("*.json"))
            print(f"📁 Found {len(files)} cached articles")
            
            # Look for our specific article
            safe_title = article_title.replace(" ", "_").replace("/", "_")[:50]
            matching_files = [f for f in files if safe_title.lower() in f.name.lower()]
            
            if matching_files:
                print(f"✅ Found cached file: {matching_files[0].name}")
            else:
                print(f"❌ No cached file found for: {safe_title}")
                print(f"   Recent files: {[f.name for f in files[-3:]]}")
        else:
            print(f"❌ Articles directory doesn't exist: {articles_dir.absolute()}")
    
    def _interactive_fetch_only(self):
        """Interactive article fetching without script generation"""
        print("\n📚 FETCH ARTICLES ONLY")
        print("=" * 30)
        print("1. 🔥 Fetch trending articles")
        print("2. ⭐ Fetch featured articles")
        print("3. 🎯 Fetch specific topic")
        
        choice = input("\nSelect fetch type (1-3): ").strip()
        
        if choice == "1":
            self._fetch_trending_only()
        elif choice == "2":
            self._fetch_featured_only()
        elif choice == "3":
            self._fetch_specific_only()
        else:
            print("❌ Invalid choice")
    
    def _fetch_trending_only(self):
        """Fetch trending articles without generating scripts"""
        # Ensure articles directory exists
        if not self._ensure_articles_directory():
            return
            
        try:
            count = int(input("How many trending articles to fetch? (1-20, default 5): ") or "5")
            count = max(1, min(count, 20))
            
            print(f"\n🔥 FETCHING {count} TRENDING ARTICLES")
            print("=" * 40)
            
            articles = self.content_fetcher.get_trending_articles(
                count=count * 2,  # Get more to account for filtering
                min_views=5000,
                exclude_categories=[
                    'Disambiguation pages', 'Redirects', 'Wikipedia',
                    'Articles with dead external links', 'Mathematical series',
                    'Lists of', 'Categories', 'Templates'
                ]
            )
            
            if not articles:
                print("❌ No trending articles found")
                return
            
            # Filter and show articles
            suitable_articles = []
            for article in articles:
                # Skip very long articles
                if article.word_count > 15000:
                    print(f"⚠️  Skipping '{article.title}' - too long ({article.word_count} words)")
                    continue
                
                # Skip articles with unusual characters
                if any(char in article.title for char in ['−', '+', '⋯', '∞', '∑', '∏']):
                    print(f"⚠️  Skipping '{article.title}' - mathematical content")
                    continue
                
                # Skip very short articles
                if article.word_count < 300:
                    print(f"⚠️  Skipping '{article.title}' - too short ({article.word_count} words)")
                    continue
                
                suitable_articles.append(article)
                if len(suitable_articles) >= count:
                    break
            
            print(f"\n✅ FETCHED {len(suitable_articles)} ARTICLES")
            print("=" * 40)
            
            for i, article in enumerate(suitable_articles, 1):
                print(f"{i:2d}. {article.title}")
                print(f"     📊 {article.word_count:,} words | Quality: {article.quality_score:.2f}")
                print(f"     👀 {article.page_views:,} recent views")
                
                # Show estimated duration for different styles
                duration_conv, _ = self.content_fetcher.estimate_podcast_duration(article.word_count, "conversational")
                duration_doc, _ = self.content_fetcher.estimate_podcast_duration(article.word_count, "documentary")
                print(f"     ⏱️  Estimated: {duration_conv//60}min (conversational), {duration_doc//60}min (documentary)")
                print()
            
            print("💡 Articles are cached and ready for script generation!")
            
        except ValueError:
            print("❌ Invalid number")
    
    def _fetch_featured_only(self):
        """Fetch featured articles without generating scripts"""
        try:
            count = int(input("How many featured articles to fetch? (1-10, default 3): ") or "3")
            count = max(1, min(count, 10))
            
            print(f"\n⭐ FETCHING {count} FEATURED ARTICLES")
            print("=" * 40)
            
            articles = self.content_fetcher.get_featured_articles(count=count)
            
            if not articles:
                print("❌ No featured articles found")
                return
            
            print(f"\n✅ FETCHED {len(articles)} FEATURED ARTICLES")
            print("=" * 40)
            
            for i, article in enumerate(articles, 1):
                print(f"{i:2d}. {article.title}")
                print(f"     📊 {article.word_count:,} words | Quality: {article.quality_score:.2f}")
                print(f"     👀 {article.page_views:,} recent views")
                
                # Show estimated duration for different styles
                duration_conv, _ = self.content_fetcher.estimate_podcast_duration(article.word_count, "conversational")
                duration_doc, _ = self.content_fetcher.estimate_podcast_duration(article.word_count, "documentary")
                print(f"     ⏱️  Estimated: {duration_conv//60}min (conversational), {duration_doc//60}min (documentary)")
                print()
            
            print("💡 Articles are cached and ready for script generation!")
            
        except ValueError:
            print("❌ Invalid number")
    
    def _fetch_specific_only(self):
        """Fetch specific topic without generating script"""
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        print(f"\n🎯 FETCHING ARTICLE: {topic}")
        print("=" * 40)
        
        # Search for the article
        print(f"🔍 Searching for Wikipedia article: {topic}")
        
        # Get suggestions
        suggestions = self.content_fetcher.suggest_titles(topic, count=5)
        if suggestions:
            print(f"📋 Found similar titles: {', '.join(suggestions[:3])}")
        
        # Try to find exact title
        exact_title = self.content_fetcher.find_exact_title(topic)
        if exact_title:
            print(f"✅ Found exact title: {exact_title}")
            topic = exact_title
        
        # Fetch the article
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
                return
        
        print(f"\n✅ FETCHED ARTICLE: {article.title}")
        print("=" * 40)
        print(f"📊 Word count: {article.word_count:,}")
        print(f"📈 Quality score: {article.quality_score:.2f}")
        print(f"👀 Recent views: {article.page_views:,}")
        
        # Show estimated durations for different styles
        print(f"\n⏱️  ESTIMATED PODCAST DURATIONS:")
        styles = ["conversational", "documentary", "educational", "storytelling"]
        for style in styles:
            duration_seconds, formatted_duration = self.content_fetcher.estimate_podcast_duration(
                article.word_count, style
            )
            print(f"   {style.capitalize()}: {formatted_duration}")
        
        print("\n💡 Article is cached and ready for script generation!")
    
    def _interactive_article_to_script(self):
        """Interactive script generation from any article (cached or fetch new)"""
        print("\n📝 CREATE SCRIPT FROM ARTICLE")
        print("=" * 35)
        print("1. 📚 Use cached article")
        print("2. 🔍 Fetch new article")
        
        choice = input("\nSelect source (1-2): ").strip()
        
        if choice == "1":
            self._script_from_cached_article()
        elif choice == "2":
            self._script_from_new_article()
        else:
            print("❌ Invalid choice")
    
    def _script_from_cached_article(self):
        """Create script from cached article"""
        # This is essentially the same as _interactive_cached_article_to_script
        # but with a different flow/presentation
        cached_articles = self.content_fetcher.list_cached_articles()
        
        if not cached_articles:
            print("📚 No cached articles found")
            print("   Try option 1 (Fetch articles only) first, or option 2 (Fetch new article)")
            return
        
        print(f"\n📚 SELECT CACHED ARTICLE ({len(cached_articles)} available)")
        print("=" * 50)
        
        # Show articles with numbers
        for i, article in enumerate(cached_articles[:20], 1):  # Show max 20
            print(f"{i:2d}. {article['title']}")
            print(f"     📊 {article['word_count']:,} words | Quality: {article['quality_score']:.2f}")
            print(f"     📅 Cached: {article['cached_date']}")
        
        if len(cached_articles) > 20:
            print(f"     ... and {len(cached_articles) - 20} more")
        
        try:
            choice = int(input(f"\nSelect article (1-{min(len(cached_articles), 20)}): "))
            if not (1 <= choice <= min(len(cached_articles), 20)):
                print("❌ Invalid selection")
                return
            
            selected_article_info = cached_articles[choice - 1]
            
            # Load the actual article
            article = self.content_fetcher.load_cached_article(selected_article_info['filename'])
            
            if not article:
                print("❌ Could not load article file")
                return
            
            self._generate_script_from_article(article)
            
        except (ValueError, IndexError):
            print("❌ Invalid selection")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _script_from_new_article(self):
        """Create script from newly fetched article"""
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        print(f"\n🔍 FETCHING ARTICLE: {topic}")
        print("=" * 40)
        
        # Search and fetch article (similar to _fetch_specific_only)
        suggestions = self.content_fetcher.suggest_titles(topic, count=5)
        if suggestions:
            print(f"📋 Found similar titles: {', '.join(suggestions[:3])}")
        
        exact_title = self.content_fetcher.find_exact_title(topic)
        if exact_title:
            print(f"✅ Found exact title: {exact_title}")
            topic = exact_title
        
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
                return
        
        print(f"✅ Article fetched: {article.title}")
        self._generate_script_from_article(article)
    
    def _generate_full_length_script(self, article, style, custom_instructions):
        """Generate full-length script with special handling for long content"""
        print("🎯 Using full-length generation strategy...")
        
        # Strategy 1: Try with explicit length requirements and force GPT-4 if available
        enhanced_instructions = f"""
        {custom_instructions}
        
        CRITICAL REQUIREMENTS FOR FULL-LENGTH SCRIPT:
        - Target output: {int(article.word_count * 0.8)}-{int(article.word_count * 0.9)} words
        - Include ALL major sections and subsections from the article
        - Expand on key points with detailed explanations
        - Include all statistics, dates, names, and specific details
        - Use transitions and elaboration to maintain flow
        - Do NOT summarize or condense - expand and elaborate
        - This is a comprehensive presentation, not a summary
        - Break into clear sections with detailed coverage of each
        
        SPECIFIC INSTRUCTION: Generate approximately {int(article.word_count * 0.85)} words.
        Original article: {article.word_count} words
        Target script: ~{int(article.word_count * 0.85)} words
        
        IMPORTANT: This should be a detailed, comprehensive script that covers the full article content.
        """
        
        # Try multiple approaches
        attempts = [
            ("Enhanced instructions", enhanced_instructions),
            ("Sectioned approach", self._create_sectioned_instructions(article, style, custom_instructions)),
            ("Force expansion", self._create_expansion_instructions(article, style, custom_instructions))
        ]
        
        for approach_name, instructions in attempts:
            print(f"🔄 Trying {approach_name}...")
            
            script = self.script_formatter.format_article_to_script(
                article, 
                style, 
                instructions
            )
            
            if script:
                ratio = (script.word_count / article.word_count) * 100
                print(f"   📊 Result: {script.word_count} words ({ratio:.1f}%)")
                
                if script.word_count > article.word_count * 0.6:  # At least 60% coverage
                    print(f"✅ {approach_name} successful!")
                    return script
                elif script.word_count > article.word_count * 0.4:  # 40%+ is decent
                    print(f"⚠️  {approach_name} got decent coverage, continuing to chunked approach...")
                    break
            else:
                print(f"   ❌ {approach_name} failed")
        
        # Fallback to chunked generation
        print(f"🔄 All single-generation attempts insufficient, trying chunked approach...")
        return self._try_chunked_generation(article, style, custom_instructions)
    
    def _create_sectioned_instructions(self, article, style, custom_instructions):
        """Create instructions that break the script into sections"""
        return f"""
        {custom_instructions}
        
        Generate a comprehensive {style} podcast script covering the entire article about "{article.title}".
        
        STRUCTURE THE SCRIPT INTO THESE SECTIONS:
        1. Introduction (150-200 words) - Introduce the topic and why it's important
        2. Background/History (300-400 words) - Cover the historical context and development
        3. Current State (400-500 words) - Present day status, recent developments
        4. Key Issues/Challenges (300-400 words) - Major problems or debates
        5. Impact/Significance (300-400 words) - Why this matters, effects on society
        6. Future Outlook (200-300 words) - What's expected to happen next
        7. Conclusion (100-150 words) - Wrap up key points
        
        TARGET: {int(article.word_count * 0.85)} total words across all sections.
        
        For each section, include:
        - Specific details from the article
        - Examples and explanations
        - Smooth transitions between topics
        - All relevant statistics, names, dates
        
        Do NOT summarize - EXPAND on the content provided.
        """
    
    def _create_expansion_instructions(self, article, style, custom_instructions):
        """Create instructions that force expansion of content"""
        return f"""
        {custom_instructions}
        
        CRITICAL EXPANSION REQUIREMENTS:
        
        You MUST create a script of approximately {int(article.word_count * 0.85)} words.
        
        EXPANSION TECHNIQUES TO USE:
        - Explain the significance of each major point
        - Provide context for all technical terms and concepts
        - Include examples and analogies to clarify complex ideas
        - Elaborate on the implications of facts and statistics
        - Add transitional phrases and connecting sentences
        - Expand abbreviations and explain acronyms
        - Provide background for people and organizations mentioned
        - Discuss the broader context and connections to other topics
        
        CONTENT COVERAGE:
        - Include ALL information from the original article
        - Expand each paragraph into 2-3 paragraphs of script
        - Add explanatory content that helps listeners understand
        - Include all numbers, dates, names, and specific details
        - Maintain the {style} tone throughout
        
        QUALITY CHECK:
        - Each major topic should get substantial coverage (200+ words)
        - No important information should be omitted
        - The script should feel comprehensive and complete
        - Aim for {int(article.word_count * 0.85)} words total
        
        Remember: This is NOT a summary - it's a comprehensive presentation that should be nearly as detailed as the original article.
        """
    
    def _try_chunked_generation(self, article, style, custom_instructions):
        """Try generating script in chunks for very long content"""
        print("📑 Attempting chunked generation for better coverage...")
        
        # Split article into chunks (roughly by paragraphs or sections)
        content_chunks = self._split_article_content(article.content)
        
        if len(content_chunks) <= 1:
            print("📝 Content too short for chunking, using standard generation")
            return self.script_formatter.format_article_to_script(article, style, custom_instructions)
        
        print(f"📑 Split content into {len(content_chunks)} chunks")
        
        # Generate script for each chunk
        chunk_scripts = []
        total_words = 0
        
        for i, chunk in enumerate(content_chunks, 1):
            print(f"   Processing chunk {i}/{len(content_chunks)}...")
            
            # Create a temporary article object for this chunk using copy and modify approach
            try:
                # Create a copy of the original article and modify its content
                import copy
                chunk_article = copy.deepcopy(article)
                chunk_article.title = f"{article.title} - Part {i}"
                chunk_article.content = chunk
                chunk_article.word_count = len(chunk.split())
            except Exception as e:
                print(f"   ❌ Error creating chunk article: {e}")
                # Fallback: try to create minimal article object
                try:
                    from content_fetcher import WikipediaArticle
                    chunk_article = WikipediaArticle(
                        title=f"{article.title} - Part {i}",
                        content=chunk,
                        word_count=len(chunk.split()),
                        url=getattr(article, 'url', ''),
                        summary=f"Part {i} of {article.title}",
                        categories=getattr(article, 'categories', []),
                        last_modified=getattr(article, 'last_modified', ''),
                        references=getattr(article, 'references', []),
                        images=getattr(article, 'images', []),
                        quality_score=getattr(article, 'quality_score', 1.0),
                        page_views=getattr(article, 'page_views', 0)
                    )
                except Exception as e2:
                    print(f"   ❌ Error creating fallback article: {e2}")
                    print(f"   ⚠️  Skipping chunk {i}")
                    continue
            
            chunk_instructions = f"""
            {custom_instructions}
            
            This is part {i} of {len(content_chunks)} of a comprehensive script for "{article.title}".
            Generate a detailed script segment that covers ALL content in this section.
            Maintain the {style} style and include smooth transitions.
            Do not summarize - expand and elaborate on the content provided.
            Target length for this chunk: {int(len(chunk.split()) * 0.9)} words.
            """
            
            chunk_script = self.script_formatter.format_article_to_script(
                chunk_article,
                style,
                chunk_instructions
            )
            
            if chunk_script:
                chunk_scripts.append(chunk_script.script)
                total_words += chunk_script.word_count
                print(f"   ✅ Chunk {i}: {chunk_script.word_count} words")
            else:
                print(f"   ❌ Failed to generate chunk {i}")
            
            # Rate limiting between chunks
            if i < len(content_chunks):
                import time
                time.sleep(2)
        
        if chunk_scripts:
            # Combine all chunks into one script
            combined_script_text = "\n\n".join(chunk_scripts)
            
            # Create a combined script object
            try:
                from script_formatter import PodcastScript
                combined_script = PodcastScript(
                    title=f"{article.title} - Full Script",
                    script=combined_script_text,
                    style=style,
                    source_article=article.title,
                    word_count=total_words,
                    estimated_duration=int((total_words / 150) * 60)  # Rough estimate
                )
            except Exception as e:
                print(f"❌ Error creating combined script object: {e}")
                # Create a simple object if PodcastScript fails
                class SimpleScript:
                    def __init__(self, title, script, style, source_article, word_count, estimated_duration):
                        self.title = title
                        self.script = script
                        self.style = style
                        self.source_article = source_article
                        self.word_count = word_count
                        self.estimated_duration = estimated_duration
                
                combined_script = SimpleScript(
                    title=f"{article.title} - Full Script",
                    script=combined_script_text,
                    style=style,
                    source_article=article.title,
                    word_count=total_words,
                    estimated_duration=int((total_words / 150) * 60)
                )
            
            print(f"🔗 Combined {len(chunk_scripts)} chunks into {total_words} word script")
            return combined_script
        else:
            print("❌ Chunked generation failed")
            return None
    
    def _split_article_content(self, content):
        """Split article content into manageable chunks"""
        # Split by double newlines (paragraphs) first
        paragraphs = content.split('\n\n')
        
        # Target chunk size (in words)
        target_chunk_size = 800  # Smaller chunks for better processing
        max_chunk_size = 1200
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            
            # If adding this paragraph would exceed max size, start new chunk
            if current_word_count + paragraph_words > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_word_count = paragraph_words
            else:
                current_chunk.append(paragraph)
                current_word_count += paragraph_words
                
                # If we've reached target size, consider starting new chunk
                if current_word_count >= target_chunk_size:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_word_count = 0
        
        # Add remaining content
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _generate_script_from_article(self, article):
        """Common method to generate script from an article object"""
        print(f"\n📝 GENERATING SCRIPT FROM: {article.title}")
        print("=" * 50)
        print(f"📊 Word count: {article.word_count:,}")
        print(f"📈 Quality score: {article.quality_score:.2f}")
        print(f"👀 Recent views: {article.page_views:,}")
        
        # Choose style
        style = self._choose_style()
        if not style:
            return
        
        # Choose target duration
        duration = self._choose_duration()
        
        # Apply duration control to the article if needed
        if duration != "full":
            print(f"\n🎯 Applying {duration} duration control...")
            original_word_count = article.word_count
            article.content = self.content_fetcher._control_content_length(article.content, duration)
            article.word_count = len(article.content.split())
            
            if article.word_count != original_word_count:
                print(f"   📝 Content adjusted: {original_word_count:,} → {article.word_count:,} words")
        else:
            print(f"\n🎯 Using FULL article content - no length reduction")
            print(f"   📝 Keeping original: {article.word_count:,} words")
        
        # Show estimated duration
        duration_seconds, formatted_duration = self.content_fetcher.estimate_podcast_duration(
            article.word_count, style
        )
        print(f"\n📊 Estimated podcast duration: {formatted_duration} in {style} style")
        
        # Custom instructions
        custom = input("\nCustom instructions (optional): ").strip() or None
        
        # Add full-length instruction if duration is "full"
        if duration == "full":
            if custom:
                custom += " IMPORTANT: Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided. The script should be approximately 80-90% of the original article length. Include all key details, examples, statistics, and explanations. This should be a full-length, thorough presentation that covers the entire article comprehensively."
            else:
                custom = "IMPORTANT: Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided. The script should be approximately 80-90% of the original article length. Include all key details, examples, statistics, and explanations. This should be a full-length, thorough presentation that covers the entire article comprehensively. Expand on topics rather than condensing them."
            print(f"🔍 Added full-length instruction to ensure comprehensive coverage")
        
        print(f"\n📝 GENERATING {style.upper()} SCRIPT")
        print("=" * 40)
        print(f"📊 Input article: {article.word_count:,} words")
        print(f"🎯 Target: {'Full comprehensive script (~2,500+ words)' if duration == 'full' else f'{duration} duration script'}")
        
        # For full duration, try to force better model usage and longer output
        if duration == "full":
            print(f"🚀 Attempting full-length generation...")
            
            # Try to call script formatter with special full-length parameters
            script = self._generate_full_length_script(article, style, custom)
        else:
            # Generate regular script  
            script = self.script_formatter.format_article_to_script(
                article, 
                style, 
                custom
            )
        
        if script:
            actual_ratio = (script.word_count / article.word_count) * 100
            print(f"✅ Generated script: {script.word_count} words (~{script.estimated_duration//60} minutes)")
            print(f"📈 Content ratio: {actual_ratio:.1f}% of original article")
            
            # Warn if the script is much shorter than expected for "full" duration
            if duration == "full" and actual_ratio < 50:
                print(f"⚠️  WARNING: Script seems shorter than expected for 'full' duration")
                print(f"   Expected: Close to {article.word_count:,} words")
                print(f"   Got: {script.word_count} words ({actual_ratio:.1f}%)")
                print(f"   This might be due to script formatter limitations")
            
            # Ask if they want to generate audio too
            if self.openai_client:
                generate_audio = input("\n🎵 Generate audio from this script? (y/N): ").lower() == 'y'
                if generate_audio:
                    # Choose voice
                    voices = ["nova", "onyx", "shimmer", "alloy", "echo", "fable"]
                    print("\n🎤 Available voices:")
                    for i, voice in enumerate(voices, 1):
                        print(f"{i}. {voice}")
                    
                    try:
                        voice_choice = int(input("Select voice (1-6, default 1): ") or "1")
                        voice = voices[voice_choice - 1] if 1 <= voice_choice <= 6 else "nova"
                    except ValueError:
                        voice = "nova"
                    
                    # Generate audio
                    audio_result = self._generate_audio_openai(script, voice)
                    
                    if audio_result:
                        # Create podcast package
                        podcast_info = self._create_podcast_package(
                            script, audio_result, script.style, voice, script.source_article
                        )
                        
                        print(f"\n🎉 COMPLETE PODCAST CREATED!")
                        print("=" * 40)
                        print(f"🎵 Audio: {podcast_info['audio_file']}")
                        print(f"⏱️  Duration: {podcast_info['duration']}")
                        print(f"📊 Size: {podcast_info['file_size_mb']:.2f} MB")
                        print(f"💰 Cost: ~${podcast_info['estimated_cost']:.3f}")
            else:
                print("💡 Script saved! Use option 8 to generate audio later.")
        else:
            print("❌ Failed to generate script")
    
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
        
        # Choose target duration
        duration = self._choose_duration()
        
        custom = input("Custom instructions (optional): ").strip() or None
        
        self.generate_single_topic(topic, style, custom, duration)
    
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
        
        # Choose target duration
        duration = self._choose_duration()
        
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
        result = self.generate_complete_podcast(topic, style, voice, custom, True, duration)
        
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
        print(f"   💰 ${total_cost:.3f} total cost")
    
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
    
    def _interactive_cached_article_to_script(self):
        """Interactive script generation from cached articles"""
        # Get cached articles
        cached_articles = self.content_fetcher.list_cached_articles()
        
        if not cached_articles:
            print("📚 No cached articles found")
            print("   Fetch some articles first using options 1-3")
            return
        
        print(f"\n📚 CACHED ARTICLES ({len(cached_articles)} total)")
        print("=" * 50)
        
        # Show articles with numbers
        for i, article in enumerate(cached_articles[:20], 1):  # Show max 20
            print(f"{i:2d}. {article['title']}")
            print(f"     Words: {article['word_count']:,} | Quality: {article['quality_score']:.2f} | Cached: {article['cached_date']}")
        
        if len(cached_articles) > 20:
            print(f"     ... and {len(cached_articles) - 20} more")
        
        try:
            choice = int(input(f"\nSelect article (1-{min(len(cached_articles), 20)}): "))
            if not (1 <= choice <= min(len(cached_articles), 20)):
                print("❌ Invalid selection")
                return
            
            selected_article_info = cached_articles[choice - 1]
            
            # Load the actual article
            article = self.content_fetcher.load_cached_article(selected_article_info['filename'])
            
            if not article:
                print("❌ Could not load article file")
                return
            
            print(f"\n✅ Selected: {article.title}")
            print(f"   📝 {article.word_count:,} words, Quality: {article.quality_score:.2f}")
            
            # Choose style
            style = self._choose_style()
            if not style:
                return
            
            # Choose target duration
            duration = self._choose_duration()
            
            # Apply duration control to the article if needed
            if duration != "full":
                print(f"\n🎯 Applying {duration} duration control...")
                article.content = self.content_fetcher._control_content_length(article.content, duration)
                article.word_count = len(article.content.split())
            
            # Show estimated duration
            duration_seconds, formatted_duration = self.content_fetcher.estimate_podcast_duration(
                article.word_count, style
            )
            print(f"📊 Estimated podcast duration: {formatted_duration} in {style} style")
            
            custom = input("Custom instructions (optional): ").strip() or None
            
            print(f"\n📝 GENERATING {style.upper()} SCRIPT")
            print("=" * 40)
            
            # Generate script
            script = self.script_formatter.format_article_to_script(
                article, 
                style, 
                custom
            )
            
            if script:
                print(f"✅ Generated script: {script.word_count} words, ~{script.estimated_duration//60} minutes")
                
                # Ask if they want to generate audio too
                if self.openai_client:
                    generate_audio = input("\n🎵 Generate audio from this script? (y/N): ").lower() == 'y'
                    if generate_audio:
                        # Choose voice
                        voices = ["nova", "onyx", "shimmer", "alloy", "echo", "fable"]
                        print("\n🎤 Available voices:")
                        for i, voice in enumerate(voices, 1):
                            print(f"{i}. {voice}")
                        
                        try:
                            voice_choice = int(input("Select voice (1-6, default 1): ") or "1")
                            voice = voices[voice_choice - 1] if 1 <= voice_choice <= 6 else "nova"
                        except ValueError:
                            voice = "nova"
                        
                        # Generate audio
                        audio_result = self._generate_audio_openai(script, voice)
                        
                        if audio_result:
                            # Create podcast package
                            podcast_info = self._create_podcast_package(
                                script, audio_result, script.style, voice, script.source_article
                            )
                            
                            print(f"\n🎉 COMPLETE PODCAST CREATED!")
                            print("=" * 40)
                            print(f"🎵 Audio: {podcast_info['audio_file']}")
                            print(f"⏱️  Duration: {podcast_info['duration']}")
                            print(f"📊 Size: {podcast_info['file_size_mb']:.2f} MB")
                            print(f"💰 Cost: ~${podcast_info['estimated_cost']:.3f}")
            else:
                print("❌ Failed to generate script")
                
        except (ValueError, IndexError):
            print("❌ Invalid selection")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _interactive_post_production(self):
        """Interactive post-production enhancement"""
        try:
            from podcast_post_production import PodcastPostProduction
            
            # Show available podcasts for enhancement
            podcasts = self.list_podcasts()
            
            if not podcasts:
                print("🎵 No podcasts available for post-production")
                print("   Generate some podcasts first using options 4-6")
                return
            
            print(f"\n🎛️ POST-PRODUCTION ENHANCEMENT")
            print("=" * 40)
            print("1. 🎵 Enhance existing podcast")
            print("2. 🎙️ Create custom intro/outro")
            print("3. 📦 Create podcast series package") 
            print("4. 🎼 Music suggestions and setup")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                self._enhance_podcast_interactive(podcasts)
            elif choice == "2":
                self._create_intro_interactive()
            elif choice == "3":
                self._create_series_interactive(podcasts)
            elif choice == "4":
                self._show_music_suggestions()
            else:
                print("❌ Invalid choice")
                
        except ImportError:
            print("🎛️ POST-PRODUCTION ENHANCEMENT")
            print("=" * 40)
            print("❌ Post-production system not available")
            print("")
            print("To enable post-production features:")
            print("1. Save the post-production code as 'podcast_post_production.py'")
            print("2. Place it in the same directory as main.py")
            print("3. Install ffmpeg: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)")
            print("")
            print("💡 Post-production features include:")
            print("  - Custom intro/outro generation with TTS")
            print("  - Background music integration") 
            print("  - Professional audio mixing and mastering")
            print("  - Series branding and consistency")
            print("  - Batch processing for podcast series")
            
            input("\nPress Enter to continue...")
            return
    
    def _enhance_podcast_interactive(self, podcasts):
        """Interactive single podcast enhancement"""
        from podcast_post_production import PodcastPostProduction
        
        print(f"\n🎵 SELECT PODCAST TO ENHANCE")
        print("=" * 35)
        
        for i, podcast in enumerate(podcasts[:10], 1):
            print(f"{i:2d}. {podcast['title']}")
            print(f"     Duration: {podcast['duration']} | Voice: {podcast['voice']}")
        
        try:
            choice = int(input(f"\nSelect podcast (1-{min(len(podcasts), 10)}): "))
            if not (1 <= choice <= min(len(podcasts), 10)):
                print("❌ Invalid selection")
                return
            
            selected = podcasts[choice - 1]
            
            # Initialize post-production
            post_prod = PodcastPostProduction()
            
            # Show available templates
            print("\n🎨 Available templates:")
            print("1. default - Clean professional sound")
            print("2. news - Authoritative news style")
            print("3. storytelling - Atmospheric with background music")
            
            template_choice = input("Select template (1-3, default 1): ").strip() or "1"
            template_map = {"1": "default", "2": "news", "3": "storytelling"}
            template = template_map.get(template_choice, "default")
            
            # Find the audio file
            audio_path = None
            if self.audio_dir:
                audio_file = self.audio_dir / selected['audio_file']
                if audio_file.exists():
                    audio_path = str(audio_file)
            
            if not audio_path:
                print("❌ Could not find audio file")
                return
            
            print(f"\n🎛️ Enhancing: {selected['title']}")
            print(f"   Template: {template}")
            
            # Enhance podcast
            enhanced_path = post_prod.enhance_podcast(
                audio_path,
                template_name=template
            )
            
            if enhanced_path:
                print(f"✅ Enhanced podcast created!")
                print(f"📁 Location: {enhanced_path}")
            
        except (ValueError, IndexError):
            print("❌ Invalid selection")
    
    def _create_intro_interactive(self):
        """Interactive custom intro creation"""
        from podcast_post_production import PodcastPostProduction
        
        print(f"\n🎙️ CREATE CUSTOM INTRO")
        print("=" * 30)
        
        title = input("Podcast series title: ").strip()
        if not title:
            print("❌ Title required")
            return
        
        host_name = input("Host name (default: AI Assistant): ").strip() or "AI Assistant"
        
        # Voice selection
        voices = ["nova", "onyx", "shimmer", "alloy", "echo", "fable"]
        print("\n🎤 Available voices:")
        for i, voice in enumerate(voices, 1):
            print(f"{i}. {voice}")
        
        try:
            voice_choice = int(input("Select voice (1-6, default 1): ") or "1")
            voice = voices[voice_choice - 1] if 1 <= voice_choice <= 6 else "nova"
        except ValueError:
            voice = "nova"
        
        post_prod = PodcastPostProduction()
        
        print(f"\n🎙️ Creating intro for '{title}' with voice '{voice}'")
        
        intro_path = post_prod.create_custom_intro(
            title=title,
            host_name=host_name,
            voice=voice
        )
        
        if intro_path:
            print(f"✅ Custom intro created!")
            print(f"📁 Location: {intro_path}")
            print("💡 Use this intro in future podcast enhancements")
    
    def _show_music_suggestions(self):
        """Show music sources and setup suggestions"""
        from podcast_post_production import PodcastPostProduction
        
        post_prod = PodcastPostProduction()
        
        print(f"\n🎼 MUSIC SETUP GUIDE")
        print("=" * 30)
        
        # Show music suggestions for different types
        for music_type in ['intro', 'outro', 'background']:
            post_prod.download_free_music(music_type)
            print()
        
        print("📝 QUICK SETUP STEPS:")
        print("1. Visit the recommended music sites above")
        print("2. Download royalty-free music files")
        print(f"3. Save them to: {post_prod.assets_dir / 'music'}")
        print("4. Use them in post-production enhancement")
        print("\n💡 Pro tip: Keep intro/outro under 10 seconds for best results")
    
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
    parser.add_argument("--duration", type=str, default="medium",
                       choices=["short", "medium", "long", "full"],
                       help="Target podcast duration (short=5min, medium=10min, long=15min, full=complete)")
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
                pipeline.generate_complete_podcast(args.topic, args.style, args.voice, args.custom, True, args.duration)
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