"""
Core Pipeline Class - Orchestrates all components

This module contains the main PodcastPipeline class that coordinates
between content fetching, script generation, audio creation, and user interaction.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from content_fetcher import WikipediaContentFetcher, WikipediaArticle
    from script_formatter import PodcastScriptFormatter, PodcastScript
    from article_editor import ChapterEditor
    from openai import OpenAI
    from content_pipeline import ContentProcessor
    from audio_pipeline import AudioGenerator
    from interactive_menus import InteractiveMenus
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all required modules are available")
    raise


class PodcastPipeline:
    """Main pipeline orchestrator that coordinates all components"""
    
    def __init__(self):
        """Initialize the pipeline components"""
        print("🔧 Initializing pipeline components...")
        
        try:
            # Load environment variables
            load_dotenv('config/api_keys.env')
            
            # Initialize core components
            self.content_fetcher = WikipediaContentFetcher()
            self.script_formatter = PodcastScriptFormatter()
            
            # Initialize OpenAI components
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            if self.openai_api_key:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                self.chapter_editor = ChapterEditor(self.openai_api_key)
                
                # Set up audio output directory
                self.audio_dir = Path("audio_output")
                self.audio_dir.mkdir(exist_ok=True)
                
                print("✅ Content Fetcher initialized")
                print("✅ Script Formatter initialized")
                print("✅ Article Editor initialized")
                print("✅ OpenAI TTS initialized")
                print(f"📁 Audio output: {self.audio_dir.absolute()}")
            else:
                print("✅ Content Fetcher initialized")
                print("✅ Script Formatter initialized")
                print("⚠️  Article Editor not available (missing OpenAI API key)")
                print("⚠️  OpenAI TTS not available (missing API key)")
                self.openai_client = None
                self.chapter_editor = None
                self.audio_dir = None
            
            # Initialize specialized processors
            self.content_processor = ContentProcessor(self)
            self.audio_generator = AudioGenerator(self) if self.openai_client else None
            self.interactive_menus = InteractiveMenus(self)
            
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
        
        # Article editor status
        if hasattr(self, 'chapter_editor') and self.chapter_editor:
            print("✅ Article Editor: Available")
        else:
            print("⚠️  Article Editor: Not available (add OpenAI API key)")
        
        if script_cache:
            print("\nRecent Scripts:")
            for script in script_cache[:5]:
                print(f"  • {script['title']} ({script['style']}) - {script['duration']}")
    
    # Delegate main functionality to specialized processors
    def fetch_and_generate_trending(self, count: int = 5, style: str = "conversational") -> List[PodcastScript]:
        """Fetch trending articles and generate scripts"""
        return self.content_processor.fetch_and_generate_trending(count, style)
    
    def fetch_and_generate_featured(self, count: int = 3, style: str = "documentary") -> List[PodcastScript]:
        """Fetch featured articles and generate scripts"""
        return self.content_processor.fetch_and_generate_featured(count, style)
    
    def generate_single_topic(self, 
                             topic: str, 
                             style: str = "conversational", 
                             custom_instructions: str = None,
                             target_duration: str = "medium") -> Optional[PodcastScript]:
        """Generate script for a specific topic"""
        return self.content_processor.generate_single_topic(topic, style, custom_instructions, target_duration)
    
    def generate_complete_podcast(self, 
                                topic: str, 
                                style: str = "conversational", 
                                voice: str = "nova",
                                custom_instructions: str = None,
                                audio_enabled: bool = True,
                                target_duration: str = "medium") -> Optional[Dict]:
        """Generate complete podcast: content → script → audio"""
        # Generate script first
        script = self.generate_single_topic(topic, style, custom_instructions, target_duration)
        if not script:
            return None
        
        # Generate audio if enabled and available
        if audio_enabled and self.audio_generator:
            return self.audio_generator.generate_complete_podcast(script, voice, topic, style)
        else:
            return {"script": script, "audio": None}
    
    def list_podcasts(self) -> List[Dict]:
        """List all created podcasts"""
        if self.audio_generator:
            return self.audio_generator.list_podcasts()
        return []
    
    # Interactive mode delegation
    def interactive_mode(self):
        """Run interactive menu for pipeline operations"""
        self.interactive_menus.run_main_menu()
    
    # Utility methods that might be needed by multiple components
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        return safe_title.replace(' ', '_')[:50]
    
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
    
    def _choose_duration(self) -> str:
        """Interactive duration selection"""
        print("\n⏱️ Choose target podcast duration:")
        print("1. Short (~5 minutes) - Key highlights only")
        print("2. Medium (~10 minutes) - Main content with details")  
        print("3. Long (~15 minutes) - Comprehensive coverage")
        print("4. Full - Complete article content")
        
        # Article editing availability hint
        if hasattr(self, 'chapter_editor') and self.chapter_editor:
            print("     💡 Article editing available for long articles")
        else:
            print("     💡 Add OpenAI API key to enable article editing for better full-length coverage")
        
        try:
            choice = int(input("Select duration (1-4, default 2): ") or "2")
            duration_map = {1: "short", 2: "medium", 3: "long", 4: "full"}
            return duration_map.get(choice, "medium")
        except ValueError:
            return "medium"