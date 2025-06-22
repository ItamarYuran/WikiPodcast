"""
Interactive Menu System
This module handles all user interaction:
- Main menu navigation
- User input and choice handling
- Interactive workflows
"""
import sys
from typing import Optional

class InteractiveMenus:
    """Handles all interactive menu operations"""
    
    def __init__(self, pipeline):
        """Initialize with reference to main pipeline"""
        self.pipeline = pipeline
        self.content_fetcher = pipeline.content_fetcher
        self.script_formatter = pipeline.script_formatter
        self.content_processor = pipeline.content_processor
        self.audio_generator = pipeline.audio_generator
    
    def run_main_menu(self):
        """Run interactive menu for pipeline operations"""
        print("\n🎛️  INTERACTIVE MODE")
        print("=" * 30)
        
        while True:
            print("\n📋 MAIN MENU")
            print("1. 📚 Fetch articles only (no scripts)")
            print("2. 📝 Create script from article")
            print("3. 🎙️ Create complete podcast (topic → audio)")
            print("4. 📝 Generate script from cached article")
            print("5. 🎵 Generate audio from existing script")
            print("6. 🎛️ Post-production enhancement")
            print("7. 📊 Show pipeline status")
            print("8. 📝 List cached scripts")
            print("9. 🎧 List generated podcasts")
            print("10. 🎨 Show available styles")
            print("11. 🧹 Clear old cache")
            print("12. ❌ Exit")
            
            choice = input("\nSelect an option (1-12): ").strip()
            
            if choice == "1":
                self._interactive_fetch_only()
            elif choice == "2":
                self._interactive_article_to_script()
            elif choice == "3":
                self._interactive_complete_podcast()
            elif choice == "4":
                self._interactive_cached_article_to_script()
            elif choice == "5":
                self._interactive_script_to_audio()
            elif choice == "6":
                self._interactive_post_production()
            elif choice == "7":
                self.pipeline.show_status()
            elif choice == "8":
                self._show_cached_scripts()
            elif choice == "9":
                self._show_podcasts()
            elif choice == "10":
                self._show_styles()
            elif choice == "11":
                self._clear_cache()
            elif choice == "12":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-12.")
    
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
        try:
            count = int(input("How many trending articles to fetch? (1-20, default 5): ") or "5")
            count = max(1, min(count, 20))
            
            print(f"\n🔥 FETCHING {count} TRENDING ARTICLES")
            print("=" * 40)
            
            articles = self.content_fetcher.get_trending_articles(count=count)
            
            if not articles:
                print("❌ No trending articles found")
                return
            
            print(f"\n✅ FETCHED {len(articles)} ARTICLES")
            print("=" * 40)
            
            for i, article in enumerate(articles, 1):
                print(f"{i:2d}. {article.title}")
                print(f"     📊 {article.word_count:,} words | Quality: {article.quality_score:.2f}")
                print(f"     👀 {article.page_views:,} recent views")
                
                # Show chapter editing eligibility
                if self.content_processor._should_use_chapter_editing(article):
                    print(f"     📑 Eligible for chapter-by-chapter editing")
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
                
                # Show chapter editing eligibility
                if self.content_processor._should_use_chapter_editing(article):
                    print(f"     📑 Eligible for chapter-by-chapter editing")
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
        
        article = self.content_fetcher.fetch_article(topic)
        
        if not article:
            print(f"❌ Could not find Wikipedia article for: {topic}")
            return
        
        print(f"\n✅ FETCHED ARTICLE: {article.title}")
        print("=" * 40)
        print(f"📊 Word count: {article.word_count:,}")
        print(f"📈 Quality score: {article.quality_score:.2f}")
        print(f"👀 Recent views: {article.page_views:,}")
        
        # Show chapter editing eligibility
        if self.content_processor._should_use_chapter_editing(article):
            print(f"📑 This article is eligible for chapter-by-chapter editing")
        
        print("\n💡 Article is cached and ready for script generation!")
    
    def _interactive_article_to_script(self):
        """Interactive script generation from any article"""
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
        cached_articles = self.content_fetcher.list_cached_articles()
        
        if not cached_articles:
            print("📚 No cached articles found")
            return
        
        print(f"\n📚 SELECT CACHED ARTICLE ({len(cached_articles)} available)")
        print("=" * 50)
        
        for i, article in enumerate(cached_articles[:10], 1):
            print(f"{i:2d}. {article['title']}")
            print(f"     📊 {article['word_count']:,} words")
            if article['word_count'] > 6000:
                print(f"     📑 Will use chapter-by-chapter editing")
        
        try:
            choice = int(input(f"\nSelect article (1-{min(len(cached_articles), 10)}): "))
            if not (1 <= choice <= min(len(cached_articles), 10)):
                print("❌ Invalid selection")
                return
            
            selected_article_info = cached_articles[choice - 1]
            article = self.content_fetcher.load_cached_article(selected_article_info['filename'])
            
            if not article:
                print("❌ Could not load article file")
                return
            
            self._generate_script_from_article(article)
            
        except (ValueError, IndexError):
            print("❌ Invalid selection")
    
    def _script_from_new_article(self):
        """Create script from newly fetched article"""
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        article = self.content_fetcher.fetch_article(topic)
        
        if not article:
            print(f"❌ Could not find Wikipedia article for: {topic}")
            return
        
        print(f"✅ Article fetched: {article.title}")
        self._generate_script_from_article(article)
    
    def _generate_script_from_article(self, article):
        """Common method to generate script from an article object"""
        print(f"\n📝 GENERATING SCRIPT FROM: {article.title}")
        print("=" * 50)
        
        # Get available styles - this returns a dictionary, not a list!
        styles_dict = self.script_formatter.get_available_styles()
        styles_list = list(styles_dict.keys())  # Convert to list of style names
        
        if not styles_list:
            print("❌ No styles available!")
            return
        
        print("\n🎨 Available styles:")
        for i, style_key in enumerate(styles_list, 1):
            style_info = styles_dict[style_key]
            print(f"{i}. {style_info['name']} - {style_info['description']}")
        
        # Get style choice
        try:
            style_choice = int(input(f"\nSelect style (1-{len(styles_list)}): "))
            
            if not (1 <= style_choice <= len(styles_list)):
                print(f"❌ Invalid style selection: {style_choice} (valid: 1-{len(styles_list)})")
                return
            
            selected_style_key = styles_list[style_choice - 1]
            
        except ValueError as e:
            print(f"❌ Invalid style selection: {e}")
            return
        except IndexError as e:
            print(f"❌ Index error: {e}")
            return
        
        # Generate script using the script formatter directly
        print(f"🎯 Generating script with style: {selected_style_key}")
        
        try:
            # Use the script formatter directly instead of pipeline.generate_script
            script = self.script_formatter.format_article_to_script(
                article, 
                style=selected_style_key
            )
            
            if script:
                print(f"\n✅ Script generated successfully!")
                print(f"📄 Title: {script.title}")
                print(f"📊 Script length: {script.word_count} words")
                print(f"🎨 Style: {script.style}")
                print(f"⏱️  Estimated duration: {script.estimated_duration//60} minutes")
                
                # Show where it was saved
                style_dir = self.script_formatter.cache_dir / script.style
                print(f"💾 Saved to: {style_dir}")
                
            else:
                print("❌ Failed to generate script")
                
        except Exception as e:
            print(f"❌ Error generating script: {e}")
            import traceback
            traceback.print_exc()
    
    def _interactive_complete_podcast(self):
        """Interactive complete podcast generation"""
        topic = input("Enter Wikipedia topic for podcast: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        # Get available styles
        styles_dict = self.script_formatter.get_available_styles()
        styles_list = list(styles_dict.keys())
        
        print("\n🎨 Available styles:")
        for i, style_key in enumerate(styles_list, 1):
            style_info = styles_dict[style_key]
            print(f"{i}. {style_info['name']} - {style_info['description']}")
        
        try:
            style_choice = int(input(f"\nSelect style (1-{len(styles_list)}): "))
            if not (1 <= style_choice <= len(styles_list)):
                print("❌ Invalid style selection")
                return
            
            selected_style_key = styles_list[style_choice - 1]
            
        except ValueError:
            print("❌ Invalid style selection")
            return
        
        print(f"\n🎙️ CREATING COMPLETE PODCAST: {topic}")
        print("=" * 50)
        
        result = self.pipeline.create_complete_podcast(topic, style=selected_style_key)
        
        if result:
            print(f"\n🎉 PODCAST CREATED SUCCESSFULLY!")
            print(f"📝 Script: {result['script_file']}")
            print(f"🎵 Audio: {result['audio_file']}")
            print(f"⏱️  Duration: {result['duration']} minutes")
            print(f"🎨 Style: {result['style']}")
        else:
            print("❌ Failed to create podcast")
    
    def _interactive_cached_article_to_script(self):
        """Interactive script generation from cached articles"""
        self._script_from_cached_article()
    
    def _interactive_script_to_audio(self):
        """Interactive audio generation from existing scripts"""
        scripts = self.script_formatter.list_cached_scripts()
        
        if not scripts:
            print("📝 No cached scripts found")
            return
        
        print(f"\n🎵 SELECT SCRIPT FOR AUDIO GENERATION ({len(scripts)} available)")
        print("=" * 60)
        
        for i, script in enumerate(scripts[:10], 1):
            print(f"{i:2d}. {script['title']}")
            print(f"     📊 {script['word_count']:,} words | Style: {script['style']}")
            print(f"     ⏱️  Est. duration: {script['duration']}")
        
        try:
            choice = int(input(f"\nSelect script (1-{min(len(scripts), 10)}): "))
            if not (1 <= choice <= min(len(scripts), 10)):
                print("❌ Invalid selection")
                return
            
            selected_script = scripts[choice - 1]
            
            print(f"\n🎵 GENERATING AUDIO FROM: {selected_script['title']}")
            print("=" * 50)
            
            audio_result = self.audio_generator.generate_from_script_file(selected_script['filename'])
            
            if audio_result:
                print(f"\n✅ Audio generated successfully!")
                print(f"🎵 Audio file: {audio_result['filename']}")
                print(f"⏱️  Duration: {audio_result['duration']:.1f} minutes")
                print(f"📊 File size: {audio_result['file_size']:.1f} MB")
            else:
                print("❌ Failed to generate audio")
                
        except (ValueError, IndexError):
            print("❌ Invalid selection")
    
    def _interactive_post_production(self):
        """Interactive post-production enhancement"""
        audio_files = self.audio_generator.list_generated_audio()
        
        if not audio_files:
            print("🎵 No generated audio files found")
            return
        
        print(f"\n🎛️ SELECT AUDIO FOR POST-PRODUCTION ({len(audio_files)} available)")
        print("=" * 60)
        
        for i, audio in enumerate(audio_files[:10], 1):
            print(f"{i:2d}. {audio['title']}")
            print(f"     🎵 {audio['filename']}")
            print(f"     ⏱️  Duration: {audio['duration']:.1f} min")
        
        try:
            choice = int(input(f"\nSelect audio (1-{min(len(audio_files), 10)}): "))
            if not (1 <= choice <= min(len(audio_files), 10)):
                print("❌ Invalid selection")
                return
            
            selected_audio = audio_files[choice - 1]
            
            print(f"\n🎛️ POST-PRODUCTION OPTIONS")
            print("=" * 30)
            print("1. 🎵 Add background music")
            print("2. 🔊 Normalize audio levels")
            print("3. 🎚️ Apply EQ enhancement")
            print("4. 🌟 Full enhancement suite")
            
            enhancement_choice = input("\nSelect enhancement (1-4): ").strip()
            
            print(f"\n🎛️ ENHANCING: {selected_audio['title']}")
            print("=" * 40)
            
            enhancement_result = self.audio_generator.enhance_audio(
                selected_audio['filename'], 
                enhancement_type=enhancement_choice
            )
            
            if enhancement_result:
                print(f"\n✅ Audio enhanced successfully!")
                print(f"🎵 Enhanced file: {enhancement_result['filename']}")
                print(f"📊 Improvements: {enhancement_result['enhancements']}")
            else:
                print("❌ Failed to enhance audio")
                
        except (ValueError, IndexError):
            print("❌ Invalid selection")
    
    def _show_cached_scripts(self):
        """Display cached scripts"""
        scripts = self.script_formatter.list_cached_scripts()
        
        if not scripts:
            print("📝 No cached scripts found")
            return
        
        print(f"\n📝 CACHED SCRIPTS ({len(scripts)} total)")
        print("=" * 40)
        
        for i, script in enumerate(scripts, 1):
            print(f"{i:2d}. {script['title']}")
            print(f"     📊 {script['word_count']:,} words | Style: {script['style']}")
            print(f"     ⏱️  Est. duration: {script['duration']}")
            print(f"     📁 File: {script['filename']}")
            print()
    
    def _show_podcasts(self):
        """Display generated podcasts"""
        podcasts = self.audio_generator.list_generated_audio()
        
        if not podcasts:
            print("🎧 No generated podcasts found")
            return
        
        print(f"\n🎧 GENERATED PODCASTS ({len(podcasts)} total)")
        print("=" * 40)
        
        for i, podcast in enumerate(podcasts, 1):
            print(f"{i:2d}. {podcast['title']}")
            print(f"     🎵 {podcast['filename']}")
            print(f"     ⏱️  Duration: {podcast['duration']:.1f} minutes")
            print(f"     📊 Size: {podcast['file_size']:.1f} MB")
            print()
    
    def _show_styles(self):
        """Display available styles with descriptions"""
        styles_dict = self.script_formatter.get_available_styles()
        
        print(f"\n🎨 AVAILABLE STYLES ({len(styles_dict)} total)")
        print("=" * 40)
        
        for i, (style_key, style_info) in enumerate(styles_dict.items(), 1):
            print(f"{i}. {style_info['name']}")
            print(f"   📝 {style_info['description']}")
            print(f"   ⏱️  Target duration: {style_info['target_duration']}")
            print(f"   🎤 Voice style: {style_info['voice_style']}")
            print()
    
    def _clear_cache(self):
        """Interactive cache clearing"""
        print("\n🧹 CACHE MANAGEMENT")
        print("=" * 25)
        print("1. 📚 Clear article cache")
        print("2. 📝 Clear script cache")
        print("3. 🎵 Clear audio cache")
        print("4. 🧹 Clear all caches")
        print("5. ❌ Cancel")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            confirm = input("⚠️  Clear all cached articles? (y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    cleared = self.content_fetcher.clear_cache()
                    print(f"✅ Cleared {cleared} cached articles")
                except Exception as e:
                    print(f"❌ Error clearing article cache: {e}")
        
        elif choice == "2":
            confirm = input("⚠️  Clear all cached scripts? (y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    # Clear script cache manually since the method doesn't exist
                    cleared = self._clear_script_cache()
                    print(f"✅ Cleared {cleared} cached scripts")
                except Exception as e:
                    print(f"❌ Error clearing script cache: {e}")
        
        elif choice == "3":
            confirm = input("⚠️  Clear all generated audio? (y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    cleared = self.audio_generator.clear_cache()
                    print(f"✅ Cleared {cleared} audio files")
                except Exception as e:
                    print(f"❌ Error clearing audio cache: {e}")
        
        elif choice == "4":
            confirm = input("⚠️  Clear ALL caches? This cannot be undone! (y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    # Clear articles
                    articles_cleared = self.content_fetcher.clear_cache()
                    print(f"✅ Cleared {articles_cleared} articles")
                    
                    # Clear scripts
                    scripts_cleared = self._clear_script_cache()
                    print(f"✅ Cleared {scripts_cleared} scripts")
                    
                    # Clear audio (if method exists)
                    try:
                        audio_cleared = self.audio_generator.clear_cache()
                        print(f"✅ Cleared {audio_cleared} audio files")
                    except AttributeError:
                        audio_cleared = self._clear_audio_cache()
                        print(f"✅ Cleared {audio_cleared} audio files")
                    
                    print(f"🎉 Total cleared: {articles_cleared} articles, {scripts_cleared} scripts, {audio_cleared} audio files")
                    
                except Exception as e:
                    print(f"❌ Error clearing caches: {e}")
        
        elif choice == "5":
            print("❌ Cache clearing cancelled")
        
        else:
            print("❌ Invalid choice")
    
    def _clear_script_cache(self):
        """Manually clear script cache since the method doesn't exist in PodcastScriptFormatter"""
        try:
            import os
            cleared = 0
            
            # Get the script cache directory
            cache_dir = self.script_formatter.cache_dir
            
            # Clear all subdirectories (styles)
            for style_dir in cache_dir.iterdir():
                if style_dir.is_dir():
                    for script_file in style_dir.glob('*.json'):
                        script_file.unlink()
                        cleared += 1
            
            return cleared
            
        except Exception as e:
            print(f"Warning: Could not clear script cache: {e}")
            return 0
    
    def _clear_audio_cache(self):
        """Manually clear audio cache if the method doesn't exist"""
        try:
            import os
            cleared = 0
            
            # You'll need to adjust this path based on where audio files are stored
            # This is a guess - you might need to check your audio_generator implementation
            audio_dir = Path("../audio_output")  # Adjust this path as needed
            
            if audio_dir.exists():
                for audio_file in audio_dir.glob('*.mp3'):
                    audio_file.unlink()
                    cleared += 1
                for audio_file in audio_dir.glob('*.wav'):
                    audio_file.unlink()
                    cleared += 1
                for json_file in audio_dir.glob('*.json'):
                    json_file.unlink()
                    cleared += 1
            
            return cleared
            
        except Exception as e:
            print(f"Warning: Could not clear audio cache: {e}")
            return 0
    
    def _display_processing_results(self, results, result_type):
        """Display results from processing multiple articles"""
        if not results:
            print(f"❌ No {result_type} articles could be processed")
            return
        
        print(f"\n✅ PROCESSED {len(results)} {result_type.upper()} ARTICLES")
        print("=" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. {result.title}")
            print(f"     📄 Script: {result.script_file}")
            print(f"     📊 {result.word_count} words | Style: {result.style}")
            print(f"     ⏱️  Est. duration: {result.estimated_duration} minutes")
            if hasattr(result, 'audio_file') and result.audio_file:
                print(f"     🎵 Audio: {result.audio_file}")
            print()
        
        print("💡 All scripts are cached and ready for audio generation!")
    
    def get_user_confirmation(self, message: str, default: bool = False) -> bool:
        """Get user confirmation with default option"""
        default_text = "Y/n" if default else "y/N"
        response = input(f"{message} ({default_text}): ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    
    def get_user_choice(self, options: list, prompt: str = "Select option") -> Optional[int]:
        """Get user choice from a list of options"""
        try:
            choice = int(input(f"{prompt} (1-{len(options)}): "))
            if 1 <= choice <= len(options):
                return choice - 1
            else:
                print(f"❌ Please select a number between 1 and {len(options)}")
                return None
        except ValueError:
            print("❌ Please enter a valid number")
            return None