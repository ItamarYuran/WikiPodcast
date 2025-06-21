"""
Content Processing Pipeline

This module handles all content-related operations:
- Fetching and filtering articles
- Script generation with chapter editing
- Content length management
"""

import time
import copy
from datetime import datetime
from typing import List, Optional
from script_formatter import PodcastScript


class ContentProcessor:
    """Handles content fetching, processing, and script generation"""
    
    def __init__(self, pipeline):
        """Initialize with reference to main pipeline"""
        self.pipeline = pipeline
        self.content_fetcher = pipeline.content_fetcher
        self.script_formatter = pipeline.script_formatter
        self.chapter_editor = getattr(pipeline, 'chapter_editor', None)
    
    def _should_use_chapter_editing(self, article, target_duration: str = "medium") -> bool:
        """Determine if an article should use chapter-by-chapter editing"""
        if not self.chapter_editor:
            return False
        
        # Use chapter editing for very long articles
        if article.word_count > 6000:
            print(f"📑 Article has {article.word_count:,} words - using chapter-by-chapter editing")
            return True
        
        # Use chapter editing for full duration articles over 4000 words
        if target_duration == "full" and article.word_count > 4000:
            print(f"📑 Full duration + {article.word_count:,} words - using chapter-by-chapter editing")
            return True
        
        return False
    
    def _generate_script_with_chapter_editor(self, article, style: str, custom_instructions: str = None) -> Optional[PodcastScript]:
        """Generate script using chapter-by-chapter editing for long articles"""
        if not self.chapter_editor:
            print("❌ Article editor not available")
            return None
        
        print(f"\n📑 CHAPTER-BY-CHAPTER EDITING")
        print("=" * 40)
        print(f"📝 Article: {article.title}")
        print(f"📊 Length: {article.word_count:,} words")
        print(f"🎨 Style: {style}")
        
        # Prepare editing instructions
        base_instructions = f"""
        Convert this Wikipedia article content into a {style} podcast script.
        
        Requirements:
        - Maintain the {style} tone and style throughout
        - Include smooth transitions between topics
        - Make content engaging for audio listeners
        - Preserve important facts, dates, and details
        - Add natural speech patterns and pauses where appropriate
        - Structure content logically for audio presentation
        """
        
        if custom_instructions:
            base_instructions += f"\n\nAdditional Instructions:\n{custom_instructions}"
        
        try:
            # Use chapter editor to process the article
            edited_content = self.chapter_editor.edit_article_by_chapters(
                article.content, 
                base_instructions,
                delay=2.0  # Slightly longer delay for podcast generation
            )
            
            if not edited_content:
                print("❌ Chapter editing failed")
                return None
            
            # Create PodcastScript object with proper parameters
            word_count = len(edited_content.split())
            estimated_duration = int((word_count / 150) * 60)  # Rough estimate
            
            # Try to create script object using standard script formatter method
            try:
                # Use the same method as your script formatter for consistency
                script = self.script_formatter.format_article_to_script(
                    article, 
                    style, 
                    custom_instructions,
                    override_content=edited_content  # Pass the edited content
                )
            except:
                # Fallback: Create script object manually with required parameters
                try:
                    script = PodcastScript(
                        title=f"{article.title} - {style.title()} Podcast",
                        script=edited_content,
                        style=style,
                        source_article=article.title,
                        word_count=word_count,
                        estimated_duration=estimated_duration,
                        intro="",  # Add required parameters
                        outro="",
                        segments=[edited_content],  # Put content in segments
                        generated_timestamp=datetime.now().isoformat()
                    )
                    
                    # Cache manually since we created it manually
                    try:
                        self.script_formatter._cache_script(script)
                        print(f"💾 Script cached successfully")
                    except Exception as e:
                        print(f"⚠️  Script caching failed: {e}")
                        
                except Exception as e:
                    print(f"❌ Error creating script object manually: {e}")
                    # Create minimal working object
                    class ChapterScript:
                        def __init__(self, title, script, style, source_article, word_count, estimated_duration):
                            self.title = title
                            self.script = script
                            self.style = style
                            self.source_article = source_article
                            self.word_count = word_count
                            self.estimated_duration = estimated_duration
                    
                    script = ChapterScript(
                        title=f"{article.title} - {style.title()} Podcast",
                        script=edited_content,
                        style=style,
                        source_article=article.title,
                        word_count=word_count,
                        estimated_duration=estimated_duration
                    )
            
            print(f"✅ Chapter-by-chapter editing completed!")
            print(f"📝 Generated: {word_count:,} words")
            print(f"⏱️  Estimated duration: {estimated_duration//60}:{estimated_duration%60:02d}")
            
            return script
            
        except Exception as e:
            print(f"❌ Chapter editing error: {e}")
            return None
    
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
        
        # Filter articles that are suitable for podcasts
        suitable_articles = []
        for article in articles:
            # Skip very long articles that might cause issues
            if article.word_count > 12000:
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
        
        # Generate scripts
        print(f"\n📝 GENERATING {style.upper()} SCRIPTS")
        print("=" * 40)
        
        scripts = []
        for i, article in enumerate(suitable_articles, 1):
            print(f"\n[{i}/{len(suitable_articles)}] Processing: {article.title}")
            print(f"   📊 {article.word_count:,} words, Quality: {article.quality_score:.2f}")
            
            # Check if we should use chapter editing
            if self._should_use_chapter_editing(article):
                script = self._generate_script_with_chapter_editor(article, style)
            else:
                # Apply medium length control for regular articles
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
                time.sleep(3)
        
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
        
        # For featured articles, also check if we should use chapter editing for very long ones
        enhanced_scripts = []
        for i, (article, script) in enumerate(zip(articles, scripts), 1):
            if script:
                enhanced_scripts.append(script)
            elif self._should_use_chapter_editing(article):
                print(f"\n[{i}/{len(articles)}] Retrying with chapter editing: {article.title}")
                enhanced_script = self._generate_script_with_chapter_editor(article, style)
                if enhanced_script:
                    enhanced_scripts.append(enhanced_script)
                    print(f"   ✅ Generated with chapter editing: {enhanced_script.word_count} words")
        
        scripts = enhanced_scripts
        
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
        
        # Search for the article
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
        
        # Generate script - choose method based on article length and target duration
        print(f"\n📝 GENERATING {style.upper()} SCRIPT")
        print("=" * 40)
        
        # Check if we should use chapter editing
        if self._should_use_chapter_editing(article, target_duration):
            # Enhanced instructions for chapter editing
            if target_duration == "full":
                if custom_instructions:
                    custom_instructions += " Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided."
                else:
                    custom_instructions = "Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided. This should be a full-length, thorough presentation."
                print(f"🔍 Using chapter-by-chapter editing for comprehensive coverage")
            
            script = self._generate_script_with_chapter_editor(article, style, custom_instructions)
        else:
            # Use regular script formatter
            if target_duration == "full":
                if custom_instructions:
                    custom_instructions += " Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided."
                else:
                    custom_instructions = "Please create a comprehensive, detailed script covering ALL major points from the article. Do not summarize or condense - use the complete content provided. This should be a full-length, thorough presentation."
                print(f"🔍 Using standard generation with full-length instruction")
            
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
                if not self.chapter_editor:
                    print(f"   💡 Tip: Add OpenAI API key to enable chapter-by-chapter editing for better coverage")
            
            return script
        else:
            print("❌ Failed to generate script")
            return None