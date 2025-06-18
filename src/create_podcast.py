#!/usr/bin/env python3
"""
Complete Podcast Creator using OpenAI TTS

This script creates a complete podcast from Wikipedia article to final audio:
1. Fetches Wikipedia content
2. Generates podcast script with GPT-4
3. Converts to audio using OpenAI TTS
4. Saves everything with metadata

Usage:
    python create_podcast.py "Machine Learning" conversational nova
    python create_podcast.py "Climate Change" documentary onyx
    python create_podcast.py "Ancient Rome" storytelling shimmer
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
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have: pip install openai python-dotenv requests")
    sys.exit(1)


class PodcastCreator:
    """Complete podcast creation pipeline using OpenAI TTS"""
    
    def __init__(self):
        """Initialize the podcast creator"""
        print("🎙️ Podcast Creator with OpenAI TTS")
        print("=" * 40)
        
        # Load environment variables
        load_dotenv('config/api_keys.env')
        
        # Initialize components
        self.content_fetcher = WikipediaContentFetcher()
        self.script_formatter = PodcastScriptFormatter()
        
        # Initialize OpenAI client
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in config/api_keys.env")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Set up audio output directory
        self.audio_dir = Path("../audio_output")
        self.audio_dir.mkdir(exist_ok=True)
        
        print("✅ Content fetcher ready")
        print("✅ Script formatter ready")
        print("✅ OpenAI TTS ready")
        print(f"📁 Audio output: {self.audio_dir.absolute()}")
    
    def create_podcast(self, 
                      topic: str, 
                      style: str = "conversational",
                      voice: str = "nova",
                      custom_instructions: str = None) -> dict:
        """
        Create complete podcast from topic to audio
        
        Args:
            topic: Wikipedia topic to create podcast about
            style: Podcast style (conversational, documentary, etc.)
            voice: OpenAI voice (nova, onyx, shimmer, alloy, echo, fable)
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
        
        # Step 3: Generate audio with OpenAI TTS
        print(f"\n🎵 STEP 3: Generating audio with OpenAI TTS")
        print("-" * 30)
        
        audio_result = self._generate_audio_openai(script, voice)
        
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
    
    def _generate_audio_openai(self, script, voice: str) -> dict:
        """Generate audio using OpenAI TTS"""
        try:
            print(f"🎤 Using voice: {voice}")
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
            
            # Estimate duration (rough calculation)
            # OpenAI TTS typically generates about 150-200 words per minute
            estimated_duration = (script.word_count / 175) * 60  # seconds
            
            # Estimate cost (OpenAI TTS pricing: $0.015 per 1K characters)
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
            "article_page_views": article.page_views
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
                            'audio_file': data['audio_file']
                        })
            except:
                continue
        
        return sorted(podcasts, key=lambda x: x['created'], reverse=True)


def main():
    """Main function for command line usage"""
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python create_podcast.py <topic> [style] [voice]")
        print("\nExamples:")
        print("  python create_podcast.py 'Machine Learning'")
        print("  python create_podcast.py 'Climate Change' documentary")
        print("  python create_podcast.py 'Ancient Rome' storytelling shimmer")
        print("\nAvailable styles: conversational, documentary, storytelling, news_report, comedy, academic")
        print("Available voices: nova, onyx, shimmer, alloy, echo, fable")
        sys.exit(1)
    
    topic = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "conversational"
    voice = sys.argv[3] if len(sys.argv) > 3 else "nova"
    
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
                    print(f"  • {p['title']} ({p['style']}, {p['duration']})")
        else:
            print(f"\n❌ Podcast creation failed: {result.get('error')}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Podcast creation interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your OpenAI API key is set in config/api_keys.env")


if __name__ == "__main__":
    main()