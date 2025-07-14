"""
Interactive Menu System - Fixed with Robust Data Handling
This module handles all user interaction with graceful error handling
"""
import sys
from pathlib import Path
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
                
                # Robust access to article properties
                word_count = getattr(article, 'word_count', 0)
                quality_score = getattr(article, 'quality_score', 0.0)
                page_views = getattr(article, 'page_views', 0)
                
                if word_count > 0:
                    print(f"     📊 {word_count:,} words | Quality: {quality_score:.2f}")
                else:
                    print(f"     📊 Word count not available | Quality: {quality_score:.2f}")
                
                if page_views > 0:
                    print(f"     👀 {page_views:,} recent views")
                else:
                    print(f"     👀 View count not available")
                
                # Show chapter editing eligibility
                if hasattr(self.content_processor, '_should_use_chapter_editing'):
                    try:
                        if self.content_processor._should_use_chapter_editing(article):
                            print(f"     📑 Eligible for chapter-by-chapter editing")
                    except:
                        pass
                print()
            
            print("💡 Articles are cached and ready for script generation!")
            
        except ValueError:
            print("❌ Invalid number")
        except Exception as e:
            print(f"❌ Error fetching trending articles: {e}")
    
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
                
                # Robust access to article properties
                word_count = getattr(article, 'word_count', 0)
                quality_score = getattr(article, 'quality_score', 0.0)
                page_views = getattr(article, 'page_views', 0)
                
                if word_count > 0:
                    print(f"     📊 {word_count:,} words | Quality: {quality_score:.2f}")
                else:
                    print(f"     📊 Word count not available | Quality: {quality_score:.2f}")
                
                if page_views > 0:
                    print(f"     👀 {page_views:,} recent views")
                else:
                    print(f"     👀 View count not available")
                
                # Show chapter editing eligibility
                if hasattr(self.content_processor, '_should_use_chapter_editing'):
                    try:
                        if self.content_processor._should_use_chapter_editing(article):
                            print(f"     📑 Eligible for chapter-by-chapter editing")
                    except:
                        pass
                print()
            
            print("💡 Articles are cached and ready for script generation!")
            
        except ValueError:
            print("❌ Invalid number")
        except Exception as e:
            print(f"❌ Error fetching featured articles: {e}")
    
    def _fetch_specific_only(self):
        """Fetch specific topic without generating script"""
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        print(f"\n🎯 FETCHING ARTICLE: {topic}")
        print("=" * 40)
        
        try:
            article = self.content_fetcher.fetch_article(topic)
            
            if not article:
                print(f"❌ Could not find Wikipedia article for: {topic}")
                return
            
            print(f"\n✅ FETCHED ARTICLE: {article.title}")
            print("=" * 40)
            
            # Robust access to article properties
            word_count = getattr(article, 'word_count', 0)
            quality_score = getattr(article, 'quality_score', 0.0)
            page_views = getattr(article, 'page_views', 0)
            
            if word_count > 0:
                print(f"📊 Word count: {word_count:,}")
            else:
                print(f"📊 Word count: Not available")
            
            print(f"📈 Quality score: {quality_score:.2f}")
            
            if page_views > 0:
                print(f"👀 Recent views: {page_views:,}")
            else:
                print(f"👀 Recent views: Not available")
            
            # Show chapter editing eligibility
            if hasattr(self.content_processor, '_should_use_chapter_editing'):
                try:
                    if self.content_processor._should_use_chapter_editing(article):
                        print(f"📑 This article is eligible for chapter-by-chapter editing")
                except:
                    pass
            
            print("\n💡 Article is cached and ready for script generation!")
            
        except Exception as e:
            print(f"❌ Error fetching article: {e}")
    
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
        """Create script from cached article - FIXED with robust data access"""
        # Add this temporary debug code to your interactive_menus.py at the top of the _script_from_cached_article method
        print(f"🔍 Content fetcher type: {type(self.content_fetcher)}")
        print(f"🔍 Content fetcher file: {self.content_fetcher.__class__.__module__}")
        print(f"🔍 Available methods: {[method for method in dir(self.content_fetcher) if not method.startswith('_')]}")
        try:
            cached_articles = self.content_fetcher.list_cached_articles()
            
            if not cached_articles:
                print("📚 No cached articles found")
                return
            
            print(f"\n📚 SELECT CACHED ARTICLE ({len(cached_articles)} available)")
            print("=" * 50)
            
            for i, article in enumerate(cached_articles[:10], 1):
                # Robust access to article data - handle both dict and object formats
                if isinstance(article, dict):
                    title = article.get('title', 'Unknown Title')
                    word_count = article.get('word_count', 0)
                    filename = article.get('filename', 'Unknown')
                else:
                    title = getattr(article, 'title', 'Unknown Title')
                    word_count = getattr(article, 'word_count', 0) 
                    filename = getattr(article, 'filename', 'Unknown')
                
                print(f"{i:2d}. {title}")
                
                if word_count and word_count > 0:
                    print(f"     📊 {word_count:,} words")
                    if word_count > 6000:
                        print(f"     📑 Will use chapter-by-chapter editing")
                else:
                    print(f"     📊 Word count not available")
            
            try:
                choice = int(input(f"\nSelect article (1-{min(len(cached_articles), 10)}): "))
                if not (1 <= choice <= min(len(cached_articles), 10)):
                    print("❌ Invalid selection")
                    return
                
                selected_article_info = cached_articles[choice - 1]
                
                # Get filename for loading
                if isinstance(selected_article_info, dict):
                    filename = selected_article_info.get('filename', '')
                else:
                    filename = getattr(selected_article_info, 'filename', '')
                
                if not filename:
                    print("❌ No filename available for selected article")
                    return
                
                article = self.content_fetcher.load_cached_article(filename)
                
                if not article:
                    print("❌ Could not load article file")
                    return
                
                self._generate_script_from_article(article)
                
            except (ValueError, IndexError):
                print("❌ Invalid selection")
                
        except Exception as e:
            print(f"❌ Error in cached article selection: {e}")
            import traceback
            traceback.print_exc()
    
    def _script_from_new_article(self):
        """Create script from newly fetched article"""
        topic = input("Enter Wikipedia topic/title: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        try:
            article = self.content_fetcher.fetch_article(topic)
            
            if not article:
                print(f"❌ Could not find Wikipedia article for: {topic}")
                return
            
            print(f"✅ Article fetched: {article.title}")
            self._generate_script_from_article(article)
            
        except Exception as e:
            print(f"❌ Error fetching new article: {e}")
    
    def _generate_script_from_article(self, article):
        """Common method to generate script from an article object"""
        try:
            # Robust access to article title
            title = getattr(article, 'title', 'Unknown Article')
            
            print(f"\n📝 GENERATING SCRIPT FROM: {title}")
            print("=" * 50)
            
            # Duration Selection
            print("\n⏱️  PODCAST DURATION")
            print("=" * 25)
            print("1. 🚀 5 minutes (quick)")
            print("2. 📱 10 minutes (standard)")  
            print("3. 📺 15 minutes (detailed)")
            print("4. 📚 20 minutes (comprehensive)")
            print("5. 🎓 25 minutes (deep dive)")
            print("6. ⚙️  Custom duration")
            
            # Get duration choice
            duration_choice = input("\nSelect duration (1-6, default 2): ").strip() or "2"
            
            duration_map = {
                '1': 300,   # 5 minutes
                '2': 600,   # 10 minutes  
                '3': 900,   # 15 minutes
                '4': 1200,  # 20 minutes
                '5': 1500,  # 25 minutes
            }
            
            if duration_choice in duration_map:
                target_duration = duration_map[duration_choice]
                minutes = target_duration // 60
                print(f"✅ Selected: {minutes} minutes")
            elif duration_choice == '6':
                try:
                    custom_minutes = int(input("Enter duration in minutes (5-30): "))
                    if 5 <= custom_minutes <= 30:
                        target_duration = custom_minutes * 60
                        print(f"✅ Custom duration: {custom_minutes} minutes")
                    else:
                        print("⚠️  Invalid range, using 10 minutes")
                        target_duration = 600
                except ValueError:
                    print("⚠️  Invalid input, using 10 minutes")
                    target_duration = 600
            else:
                print("⚠️  Invalid choice, using 10 minutes")
                target_duration = 600
            
            # Get available styles
            try:
                styles_dict = self.script_formatter.get_available_styles()
                styles_list = list(styles_dict.keys())
                
                if not styles_list:
                    print("❌ No styles available!")
                    return
                
                print("\n🎨 Available styles:")
                for i, style_key in enumerate(styles_list, 1):
                    style_info = styles_dict[style_key]
                    style_name = style_info.get('name', style_key)
                    style_desc = style_info.get('description', 'No description')
                    print(f"{i}. {style_name} - {style_desc}")
                
                # Get style choice
                style_choice = int(input(f"\nSelect style (1-{len(styles_list)}): "))
                
                if not (1 <= style_choice <= len(styles_list)):
                    print(f"❌ Invalid style selection: {style_choice} (valid: 1-{len(styles_list)})")
                    return
                
                selected_style_key = styles_list[style_choice - 1]
                
            except (ValueError, IndexError, KeyError) as e:
                print(f"❌ Error with style selection: {e}")
                return
            except Exception as e:
                print(f"❌ Unexpected error getting styles: {e}")
                return
            
            # Model selection
            print("\n🤖 AI MODEL SELECTION")
            print("=" * 25)
            print("1. 🚀 GPT-3.5 Turbo (faster, cheaper)")
            print("2. 🧠 GPT-4 (slower, more expensive, better at following length requirements)")
            
            model_choice = input("\nSelect model (1-2, default 1): ").strip() or "1"
            
            if model_choice == "2":
                selected_model = "gpt-4"
                print("✅ Selected: GPT-4 (better length compliance)")
            else:
                selected_model = "gpt-3.5-turbo-16k"
                print("✅ Selected: GPT-3.5 Turbo 16k")
            
            # Generate script
            print(f"🎯 Generating {selected_style_key} script with {target_duration//60} minute target...")
            
            try:
                # Generate the script with robust parameter handling
                script_params = {
                    'style': selected_style_key
                }
                
                # Add optional parameters if the method supports them
                if hasattr(self.script_formatter, 'format_article_to_script'):
                    try:
                        import inspect
                        sig = inspect.signature(self.script_formatter.format_article_to_script)
                        
                        if 'target_duration' in sig.parameters:
                            script_params['target_duration'] = target_duration
                        if 'model' in sig.parameters:
                            script_params['model'] = selected_model
                    except:
                        pass  # If inspection fails, just use basic parameters
                
                script = self.script_formatter.format_article_to_script(article, **script_params)
                
                if script:
                    # Robust access to script properties
                    script_title = getattr(script, 'title', 'Unknown Script')
                    script_word_count = getattr(script, 'word_count', 0)
                    script_style = getattr(script, 'style', 'Unknown')
                    script_duration = getattr(script, 'estimated_duration', 0)
                    
                    actual_minutes = script_duration // 60 if script_duration else 0
                    target_minutes = target_duration // 60
                    
                    print(f"\n✅ Script generated successfully!")
                    print(f"📄 Title: {script_title}")
                    print(f"📊 Script length: {script_word_count} words")
                    print(f"🎨 Style: {script_style}")
                    print(f"⏱️  Estimated duration: {actual_minutes} minutes")
                    print(f"🎯 Target was: {target_minutes} minutes")
                    
                    # Show length compliance
                    if actual_minutes >= target_minutes * 0.8:
                        print("✅ Length target achieved!")
                    else:
                        print(f"⚠️  Script is shorter than target ({actual_minutes}/{target_minutes} min)")
                        print("💡 Try using GPT-4 for better length compliance")
                    
                    # Show where it was saved
                    if hasattr(self.script_formatter, 'cache_dir'):
                        style_dir = self.script_formatter.cache_dir / script_style
                        print(f"💾 Saved to: {style_dir}")
                    
                else:
                    print("❌ Failed to generate script")
                    
            except Exception as e:
                print(f"❌ Error generating script: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Error in script generation process: {e}")
            import traceback
            traceback.print_exc()
    
    def _interactive_complete_podcast(self):
        """Interactive complete podcast generation"""
        topic = input("Enter Wikipedia topic for podcast: ").strip()
        if not topic:
            print("❌ Topic cannot be empty")
            return
        
        try:
            # Get available styles
            styles_dict = self.script_formatter.get_available_styles()
            styles_list = list(styles_dict.keys())
            
            print("\n🎨 Available styles:")
            for i, style_key in enumerate(styles_list, 1):
                style_info = styles_dict[style_key]
                style_name = style_info.get('name', style_key)
                style_desc = style_info.get('description', 'No description')
                print(f"{i}. {style_name} - {style_desc}")
            
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
            
            # Check if the pipeline has the create_complete_podcast method
            if hasattr(self.pipeline, 'create_complete_podcast'):
                result = self.pipeline.create_complete_podcast(topic, style=selected_style_key)
                
                if result:
                    print(f"\n🎉 PODCAST CREATED SUCCESSFULLY!")
                    print(f"📝 Script: {result.get('script_file', 'Unknown')}")
                    print(f"🎵 Audio: {result.get('audio_file', 'Unknown')}")
                    print(f"⏱️  Duration: {result.get('duration', 'Unknown')} minutes")
                    print(f"🎨 Style: {result.get('style', 'Unknown')}")
                else:
                    print("❌ Failed to create podcast")
            else:
                print("❌ Complete podcast creation not available")
                
        except Exception as e:
            print(f"❌ Error creating complete podcast: {e}")
    
    def _interactive_cached_article_to_script(self):
        """Interactive script generation from cached articles"""
        self._script_from_cached_article()
    
    def _interactive_script_to_audio(self):
        """Interactive audio generation from existing scripts"""
        try:
            scripts = self.script_formatter.list_cached_scripts()
            
            if not scripts:
                print("📝 No cached scripts found")
                return
            
            print(f"\n🎵 SELECT SCRIPT FOR AUDIO GENERATION ({len(scripts)} available)")
            print("=" * 60)
            
            for i, script in enumerate(scripts[:10], 1):
                # Robust access to script data
                title = script.get('title', 'Unknown Title')
                word_count = script.get('word_count', 0)
                style = script.get('style', 'Unknown')
                duration = script.get('duration', 'Unknown')
                
                print(f"{i:2d}. {title}")
                if word_count > 0:
                    print(f"     📊 {word_count:,} words | Style: {style}")
                else:
                    print(f"     📊 Word count not available | Style: {style}")
                print(f"     ⏱️  Est. duration: {duration}")
            
            try:
                choice = int(input(f"\nSelect script (1-{min(len(scripts), 10)}): "))
                if not (1 <= choice <= min(len(scripts), 10)):
                    print("❌ Invalid selection")
                    return
                
                selected_script = scripts[choice - 1]
                
                script_title = selected_script.get('title', 'Unknown')
                script_filename = selected_script.get('filename', '')
                
                if not script_filename:
                    print("❌ No filename available for selected script")
                    return
                
                print(f"\n🎵 GENERATING AUDIO FROM: {script_title}")
                print("=" * 50)
                
                if self.audio_generator and hasattr(self.audio_generator, 'generate_from_script_file'):
                    audio_result = self.audio_generator.generate_from_script_file(script_filename)
                    
                    if audio_result:
                        print(f"\n🎉 AUDIO GENERATED SUCCESSFULLY!")
                        print("=" * 40)
                        
                        # Robust access to audio result data
                        filename = audio_result.get('filename', audio_result.get('audio_file', 'Unknown'))
                        file_path = audio_result.get('file_path', audio_result.get('audio_path', 'Unknown'))
                        duration = audio_result.get('estimated_duration', 0)
                        file_size = audio_result.get('file_size_mb', 0)
                        cost = audio_result.get('estimated_cost', 0)
                        voice = audio_result.get('voice_used', 'Unknown')
                        provider = audio_result.get('tts_provider', 'Unknown')
                        
                        print(f"🎵 Audio file: {filename}")
                        print(f"📁 Path: {file_path}")
                        
                        if duration > 0:
                            duration_min = duration / 60
                            print(f"⏱️  Duration: {duration_min:.1f} minutes")
                        
                        if file_size > 0:
                            print(f"📊 File size: {file_size:.1f} MB")
                        
                        if cost > 0:
                            print(f"💰 Cost: ~${cost:.3f}")
                        
                        print(f"🎤 Voice: {voice}")
                        
                        if provider != 'Unknown':
                            print(f"🔧 Provider: {provider}")
                        
                        if file_path != 'Unknown':
                            print(f"🎧 Play: open '{file_path}'")
                        
                    else:
                        print("❌ Failed to generate audio")
                else:
                    print("❌ Audio generation not available")
                    
            except (ValueError, IndexError):
                print("❌ Invalid selection")
                
        except Exception as e:
            print(f"❌ Error in audio generation: {e}")
    
    def _interactive_post_production(self):
        """Interactive post-production enhancement"""
        print("⚠️  Post-production features not implemented yet")
        print("💡 This will be available in a future update")
    
    def _show_cached_scripts(self):
        """Display cached scripts"""
        try:
            scripts = self.script_formatter.list_cached_scripts()
            
            if not scripts:
                print("📝 No cached scripts found")
                return
            
            print(f"\n📝 CACHED SCRIPTS ({len(scripts)} total)")
            print("=" * 40)
            
            for i, script in enumerate(scripts, 1):
                # Robust access to script data
                title = script.get('title', 'Unknown Title')
                word_count = script.get('word_count', 0)
                style = script.get('style', 'Unknown')
                duration = script.get('duration', 'Unknown')
                filename = script.get('filename', 'Unknown')
                
                print(f"{i:2d}. {title}")
                if word_count > 0:
                    print(f"     📊 {word_count:,} words | Style: {style}")
                else:
                    print(f"     📊 Word count not available | Style: {style}")
                print(f"     ⏱️  Est. duration: {duration}")
                print(f"     📁 File: {filename}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing cached scripts: {e}")
    
    def _show_podcasts(self):
        """Display generated podcasts"""
        try:
            if self.audio_generator and hasattr(self.audio_generator, 'list_podcasts'):
                podcasts = self.audio_generator.list_podcasts()
                
                if not podcasts:
                    print("🎧 No generated podcasts found")
                    return
                
                print(f"\n🎧 GENERATED PODCASTS ({len(podcasts)} total)")
                print("=" * 40)
                
                for i, podcast in enumerate(podcasts, 1):
                    # Robust access to podcast data
                    title = podcast.get('title', 'Unknown')
                    audio_file = podcast.get('audio_file', 'Unknown')
                    duration = podcast.get('duration', 'Unknown')
                    size_mb = podcast.get('size_mb', 0)
                    cost = podcast.get('cost', 0)
                    voice = podcast.get('voice', 'Unknown')
                    provider = podcast.get('provider', 'Unknown')
                    
                    print(f"{i:2d}. {title}")
                    print(f"     🎵 {audio_file}")
                    print(f"     ⏱️  Duration: {duration}")
                    if size_mb > 0:
                        print(f"     📊 Size: {size_mb:.1f} MB")
                    if cost > 0:
                        print(f"     💰 Cost: ~${cost:.3f}")
                    print(f"     🎤 Voice: {voice}")
                    if provider != 'Unknown':
                        print(f"     🔧 Provider: {provider}")
                    print()
            else:
                print("🎧 Audio generation not available - no podcasts to list")
                
        except Exception as e:
            print(f"❌ Error listing podcasts: {e}")
    
    def _show_styles(self):
        """Display available styles with descriptions"""
        try:
            styles_dict = self.script_formatter.get_available_styles()
            
            print(f"\n🎨 AVAILABLE STYLES ({len(styles_dict)} total)")
            print("=" * 40)
            
            for i, (style_key, style_info) in enumerate(styles_dict.items(), 1):
                name = style_info.get('name', style_key)
                description = style_info.get('description', 'No description')
                target_duration = style_info.get('target_duration', 'Unknown')
                voice_style = style_info.get('voice_style', 'Unknown')
                
                print(f"{i}. {name}")
                print(f"   📝 {description}")
                print(f"   ⏱️  Target duration: {target_duration}")
                print(f"   🎤 Voice style: {voice_style}")
                print()
                
        except Exception as e:
            print(f"❌ Error showing styles: {e}")
    
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
        
        try:
            if choice == "1":
                confirm = input("⚠️  Clear all cached articles? (y/N): ").strip().lower()
                if confirm == 'y':
                    if hasattr(self.content_fetcher, 'clear_cache'):
                        self.content_fetcher.clear_cache()
                        print("✅ Article cache cleared")
                    else:
                        print("⚠️  Clear cache method not available")
            
            elif choice == "2":
                confirm = input("⚠️  Clear all cached scripts? (y/N): ").strip().lower()
                if confirm == 'y':
                    cleared = self._clear_script_cache()
                    print(f"✅ Cleared {cleared} cached scripts")
            
            elif choice == "3":
                confirm = input("⚠️  Clear all generated audio? (y/N): ").strip().lower()
                if confirm == 'y':
                    cleared = self._clear_audio_cache()
                    print(f"✅ Cleared {cleared} audio files")
            
            elif choice == "4":
                confirm = input("⚠️  Clear ALL caches? This cannot be undone! (y/N): ").strip().lower()
                if confirm == 'y':
                    # Clear articles
                    if hasattr(self.content_fetcher, 'clear_cache'):
                        self.content_fetcher.clear_cache()
                        print("✅ Article cache cleared")
                    
                    # Clear scripts
                    scripts_cleared = self._clear_script_cache()
                    print(f"✅ Cleared {scripts_cleared} scripts")
                    
                    # Clear audio
                    audio_cleared = self._clear_audio_cache()
                    print(f"✅ Cleared {audio_cleared} audio files")
                    
                    print("🎉 All caches cleared!")
            
            elif choice == "5":
                print("❌ Cache clearing cancelled")
            
            else:
                print("❌ Invalid choice")
                
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
    
    def _clear_script_cache(self):
        """Manually clear script cache"""
        try:
            cleared = 0
            if hasattr(self.script_formatter, 'cache_dir'):
                cache_dir = self.script_formatter.cache_dir
                for style_dir in cache_dir.iterdir():
                    if style_dir.is_dir():
                        for script_file in style_dir.glob('*.json'):
                            script_file.unlink()
                            cleared += 1
            return cleared
        except Exception:
            return 0
    
    def _clear_audio_cache(self):
        """Manually clear audio cache"""
        try:
            cleared = 0
            if hasattr(self.audio_generator, 'audio_dir'):
                audio_dir = self.audio_generator.audio_dir
            else:
                audio_dir = Path("audio_output")
            
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
        except Exception:
            return 0
    
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