"""
Script Formatter - Bridge to New Modular System

This file maintains compatibility with existing code while using the new modular system.
It exports the old PodcastScriptFormatter class that your existing code expects.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path


class PodcastScriptFormatter:
    """
    Compatibility wrapper for the old PodcastScriptFormatter.
    This allows existing code to work while using the new modular system underneath.
    """
    
    def __init__(self, openai_api_key: str = None, cache_dir: str = "../processed_scripts"):
        """Initialize with same interface as old formatter"""
        self.openai_api_key = openai_api_key or self._get_openai_api_key()
        self.cache_dir = Path(cache_dir)
        
        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)
        
        # Try to initialize the new system
        try:
            self._initialize_new_system()
            print("✅ PodcastScriptFormatter initialized with new modular system")
        except Exception as e:
            print(f"⚠️ Could not initialize new system: {e}")
            print("📋 Falling back to basic compatibility mode")
            self.generator = None
    
    def _get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from various sources"""
        # Check environment variables first
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        # Check environment files
        env_paths = [
            'config/api_keys.env',
            '../config/api_keys.env',
            'src/config/api_keys.env',
            '.env'
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_path)
                    api_key = os.getenv('OPENAI_API_KEY')
                    if api_key:
                        print(f"🔧 Loaded OpenAI API key from: {env_path}")
                        return api_key
                except ImportError:
                    pass
        
        return None
    
    def _initialize_new_system(self):
        """Initialize the new modular system"""
        try:
            from script_generation import create_script_generator
            
            config = {
                "openai_api_key": self.openai_api_key,
                "cache_dir": str(self.cache_dir)
            }
            
            self.generator = create_script_generator(config)
            
        except ImportError as e:
            print(f"⚠️ New system not available: {e}")
            self.generator = None
    
    def format_article_to_script(self, 
                               article,  # WikipediaArticle from old system
                               style: str = "conversational",
                               custom_instructions: str = None,
                               target_duration: int = None,
                               model: str = "gpt-3.5-turbo") -> Optional[Dict]:
        """
        Convert article to script using new system or fallback.
        Returns old-style result for compatibility.
        """
        
        print(f"🔍 Debug: Generator available: {self.generator is not None}")
        
        # Update config with the selected model
        if self.generator:
            self.generator.config['model'] = model
            print(f"🔧 Updated model to: {model}")
            return self._generate_with_new_system(article, style, custom_instructions, target_duration)
        else:
            print("⚠️ Generator not available, using fallback")
            return self._generate_with_fallback(article, style, custom_instructions, target_duration, model)
    
    def _generate_with_new_system(self, article, style, custom_instructions, target_duration):
        """Generate script using new modular system"""
        try:
            # Convert old article format to new Article model
            new_article = self._convert_article_format(article)
            
            # Generate script using new system
            result = self.generator.generate_script(
                new_article, 
                style, 
                custom_instructions, 
                target_duration
            )
            
            if result.is_success:
                # Get the new PodcastScript object
                script = result.data
                
                # Create a wrapper that behaves like both dict and object
                class ScriptWrapper:
                    def __init__(self, podcast_script):
                        self._script = podcast_script
                        
                        # Add all attributes from the PodcastScript
                        self.title = podcast_script.title
                        self.style = podcast_script.style.value if hasattr(podcast_script.style, 'value') else str(podcast_script.style)
                        self.script = podcast_script.script_text
                        self.script_text = podcast_script.script_text
                        self.script_for_tts = podcast_script.tts_ready_text
                        self.tts_ready_text = podcast_script.tts_ready_text
                        self.estimated_duration = podcast_script.estimated_duration
                        self.word_count = podcast_script.word_count
                        self.source_article = podcast_script.source_article_id
                        self.source_article_id = podcast_script.source_article_id
                        self.generated_timestamp = podcast_script.created_at.isoformat()
                        self.created_at = podcast_script.created_at
                        self.custom_instructions = podcast_script.custom_instructions
                        self.metadata = podcast_script.metadata
                        self.segments = podcast_script.segments
                        self.tts_instructions_count = podcast_script.metadata.get('instruction_counts', {})
                        
                        # Add intro and outro
                        self.intro = ""
                        self.outro = ""
                        
                        if podcast_script.intro_segment:
                            self.intro = podcast_script.intro_segment.content
                        
                        if podcast_script.outro_segment:
                            self.outro = podcast_script.outro_segment.content
                    
                    def __getitem__(self, key):
                        """Allow dictionary-style access"""
                        return getattr(self, key)
                    
                    def __setitem__(self, key, value):
                        """Allow dictionary-style assignment"""
                        setattr(self, key, value)
                    
                    def get(self, key, default=None):
                        """Dictionary-style get method"""
                        return getattr(self, key, default)
                    
                    def keys(self):
                        """Dictionary-style keys method"""
                        return [attr for attr in dir(self) if not attr.startswith('_')]
                    
                    def items(self):
                        """Dictionary-style items method"""
                        return [(attr, getattr(self, attr)) for attr in self.keys()]
                
                return ScriptWrapper(script)
            else:
                print(f"❌ Script generation failed: {result.error}")
                return None
                
        except Exception as e:
            print(f"❌ Error in new system: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_with_fallback(self, article, style, custom_instructions, target_duration, model):
        """Fallback generation using direct OpenAI API with iterative approach"""
        try:
            print("🔄 Using fallback generation method")
            
            if not self.openai_api_key:
                print("❌ No OpenAI API key available")
                return None
            
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Calculate target words
            duration_minutes = (target_duration or 600) // 60
            target_words = max(int(duration_minutes * 150), 1000)  # Minimum 1000 words
            
            print(f"🎯 Fallback target: {duration_minutes} minutes = {target_words} words (minimum 1000)")
            
            # Try iterative generation if we need a lot of words
            if target_words > 800:
                script_content = self._generate_long_script_iteratively(client, article, style, custom_instructions, target_words, model)
            else:
                script_content = self._generate_single_script(client, article, style, custom_instructions, target_words, model)
            
            if not script_content:
                return None
            
            # Calculate actual duration
            actual_word_count = len(script_content.split())
            actual_duration = int((actual_word_count / 150) * 60)  # seconds
            
            print(f"📊 Fallback result: {actual_word_count} words = {actual_duration//60} minutes")
            
            # Create a simple object with the required attributes
            class FallbackScript:
                def __init__(self, title, style, script_content, target_duration, custom_instructions, actual_duration):
                    self.title = f"{title} - {style.title()} Style"
                    self.style = style
                    self.script = script_content
                    self.script_text = script_content
                    self.script_for_tts = script_content
                    self.tts_ready_text = script_content
                    self.intro = script_content[:200] + "..." if len(script_content) > 200 else script_content
                    self.outro = "..." + script_content[-200:] if len(script_content) > 200 else script_content
                    self.segments = [{'content': script_content, 'estimated_duration': actual_duration}]
                    self.estimated_duration = actual_duration  # Use actual calculated duration
                    self.word_count = len(script_content.split())
                    self.source_article = title
                    self.source_article_id = title
                    self.generated_timestamp = datetime.now().isoformat()
                    self.created_at = datetime.now()
                    self.custom_instructions = custom_instructions
                    self.tts_instructions_count = {}
                    self.metadata = {}
            
            fallback_script = FallbackScript(article.title, style, script_content, target_duration, custom_instructions, actual_duration)
            
            # Save to cache manually since we're using fallback
            self._save_fallback_script_to_cache(fallback_script)
            
            return fallback_script
            
        except Exception as e:
            print(f"❌ Fallback generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_fallback_script_to_cache(self, script):
        """Save fallback script to cache"""
        try:
            import json
            import re
            
            # Create safe filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', script.source_article)
            safe_title = re.sub(r'[^\w\s-]', '', safe_title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"{safe_title}_{timestamp}.json"
            
            # Create style directory
            style_dir = self.cache_dir / script.style
            style_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = style_dir / filename
            
            # Create script data in the format expected by the system
            script_data = {
                'title': script.title,
                'style': script.style,
                'script': script.script,
                'script_for_tts': script.script_for_tts,
                'intro': script.intro,
                'outro': script.outro,
                'segments': script.segments,
                'estimated_duration': script.estimated_duration,
                'word_count': script.word_count,
                'source_article': script.source_article,
                'generated_timestamp': script.generated_timestamp,
                'custom_instructions': script.custom_instructions,
                'tts_instructions_count': script.tts_instructions_count,
                'metadata': script.metadata
            }
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Fallback script saved to cache: {filename}")
            
        except Exception as e:
            print(f"⚠️ Could not save fallback script to cache: {e}")
            # Don't fail the whole process if caching fails
    
    def _generate_single_script(self, client, article, style, custom_instructions, target_words, model):
        """Generate script in single API call"""
        # Enhanced prompt for single generation
        prompt = f"""Create a comprehensive {style} podcast script about {article.title}.

CRITICAL REQUIREMENTS:
- Write EXACTLY {target_words} words (count as you write!)
- This is ESSENTIAL - the script must be {target_words} words
- Include detailed explanations, examples, and stories
- Expand on every topic with rich detail
- Add personal anecdotes and relatable examples
- Include transitions and thoughtful commentary

STRUCTURE TO REACH {target_words} WORDS:
1. Engaging introduction (150-200 words)
2. Historical background/context (200-300 words)
3. Main story/content with detailed examples (400-500 words)
4. Analysis and implications (200-300 words)
5. Personal connections and modern relevance (200-300 words)
6. Memorable conclusion (100-150 words)

Article content to adapt:
{article.content[:3000]}...

Custom instructions: {custom_instructions or 'Focus on storytelling and engagement'}

IMPORTANT: You MUST write exactly {target_words} words. Do not stop until you reach this target!

BEGIN THE {target_words}-WORD SCRIPT:"""
        
        max_tokens = min(int(target_words * 1.4), 4000 if model == "gpt-4" else 3000)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a professional podcast script writer. You must write scripts of exactly {target_words} words. Count words as you write and ensure you reach exactly {target_words} words."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.9
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_long_script_iteratively(self, client, article, style, custom_instructions, target_words, model):
        """Generate long script by building it section by section"""
        print(f"🔄 Using iterative generation for {target_words} words")
        
        # Split into sections
        sections = [
            ("Introduction", 200, "Create an engaging introduction that hooks the listener"),
            ("Background", 300, "Provide detailed historical context and background"),
            ("Main Content", 400, "Present the core story with rich details and examples"),
            ("Analysis", 250, "Analyze the significance and implications"),
            ("Modern Relevance", 200, "Connect to today's world and personal experiences"),
            ("Conclusion", 150, "Provide a memorable and impactful conclusion")
        ]
        
        script_parts = []
        total_words = 0
        
        for section_name, word_target, description in sections:
            print(f"📝 Generating {section_name}: {word_target} words")
            
            section_prompt = f"""Continue the {style} podcast script about {article.title}.

SECTION: {section_name}
TARGET: Exactly {word_target} words
DESCRIPTION: {description}

CONTEXT: This is part of a larger podcast script. {'Previous sections: ' + ' '.join(script_parts[-200:]) if script_parts else 'This is the opening section.'}

REQUIREMENTS:
- Write exactly {word_target} words for this section
- Maintain {style} style throughout
- Include specific details and examples
- Make it engaging and informative

Article content reference:
{article.content[:2000]}...

Write the {section_name} section ({word_target} words):"""
            
            max_tokens = min(int(word_target * 1.5), 1000)
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"You are writing a section of a podcast script. Write exactly {word_target} words for this section."},
                        {"role": "user", "content": section_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.9
                )
                
                section_content = response.choices[0].message.content.strip()
                section_words = len(section_content.split())
                
                print(f"✅ {section_name}: {section_words} words")
                
                script_parts.append(section_content)
                total_words += section_words
                
                # Add natural transitions between sections
                if len(script_parts) < len(sections):
                    script_parts.append("\n\n")
                
            except Exception as e:
                print(f"⚠️ Error generating {section_name}: {e}")
                continue
        
        final_script = "".join(script_parts)
        print(f"📊 Iterative generation complete: {total_words} words total")
        
        return final_script
    
    def _convert_article_format(self, old_article):
        """Convert old WikipediaArticle to new Article model"""
        try:
            from core import Article, ContentType, ContentMetadata
            
            # Create metadata
            metadata = ContentMetadata(
                source=getattr(old_article, 'url', 'unknown'),
                language="en",
                categories=getattr(old_article, 'categories', []),
                quality_score=getattr(old_article, 'quality_score', 0.0),
                page_views=getattr(old_article, 'page_views', 0),
                references=getattr(old_article, 'references', []),
                images=getattr(old_article, 'images', [])
            )
            
            # Create new article
            return Article(
                id=f"wiki_{hash(old_article.title) % 10000}",
                title=old_article.title,
                content=old_article.content,
                summary=getattr(old_article, 'summary', ''),
                content_type=ContentType.WIKIPEDIA_ARTICLE,
                metadata=metadata,
                url=getattr(old_article, 'url', None),
                word_count=getattr(old_article, 'word_count', 0)
            )
        except ImportError:
            # If new system not available, return a simple dict
            return {
                'title': old_article.title,
                'content': old_article.content,
                'summary': getattr(old_article, 'summary', ''),
                'word_count': getattr(old_article, 'word_count', 0)
            }
    
    def _convert_script_to_old_format(self, new_script):
        """Convert new PodcastScript to old format"""
        try:
            # Extract segments
            segments = []
            for segment in new_script.segments:
                segments.append({
                    'content': segment.content,
                    'estimated_duration': segment.estimated_duration
                })
            
            # Find intro and outro
            intro = ""
            outro = ""
            
            if new_script.intro_segment:
                intro = new_script.intro_segment.content
            
            if new_script.outro_segment:
                outro = new_script.outro_segment.content
            
            # Return old format
            return {
                'title': new_script.title,
                'style': new_script.style.value,
                'script': new_script.script_text,
                'intro': intro,
                'outro': outro,
                'segments': segments,
                'estimated_duration': new_script.estimated_duration,
                'word_count': new_script.word_count,
                'source_article': new_script.source_article_id,
                'generated_timestamp': new_script.created_at.isoformat(),
                'custom_instructions': new_script.custom_instructions,
                'script_for_tts': new_script.tts_ready_text,
                'tts_instructions_count': new_script.metadata.get('instruction_counts', {})
            }
        except Exception as e:
            print(f"⚠️ Error converting script format: {e}")
            return None
    
    def get_available_styles(self) -> Dict[str, Dict[str, str]]:
        """Get available styles in old format"""
        if self.generator:
            try:
                new_styles = self.generator.get_available_styles()
                
                # Convert to old format
                old_format = {}
                for name, style_info in new_styles.items():
                    old_format[name] = {
                        "name": style_info.get("name", name),
                        "description": style_info.get("description", ""),
                        "target_duration": style_info.get("target_duration", "15 minutes"),
                        "voice_style": style_info.get("voice_style", "conversational")
                    }
                
                return old_format
            except Exception as e:
                print(f"⚠️ Error getting styles: {e}")
        
        # Fallback styles
        return {
            "conversational": {
                "name": "Conversational Storytelling",
                "description": "Friendly, informative conversation with storytelling elements",
                "target_duration": "15 minutes",
                "voice_style": "conversational"
            },
            "educational": {
                "name": "Educational",
                "description": "Structured, informative teaching approach",
                "target_duration": "20 minutes",
                "voice_style": "educational"
            }
        }
    
    def test_api_connection(self) -> bool:
        """Test API connection"""
        if not self.openai_api_key:
            print("❌ No OpenAI API key available")
            return False
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Say 'API test successful' in exactly those words."}
                ],
                max_tokens=10,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            
            if "API test successful" in result:
                print("✅ OpenAI API connection successful!")
                return True
            else:
                print(f"⚠️ API responded but with unexpected content: {result}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI API test failed: {str(e)}")
            return False
    
    def list_cached_scripts(self, style: str = None) -> List[Dict[str, str]]:
        """List cached scripts"""
        cached_scripts = []
        
        try:
            if style:
                search_dirs = [self.cache_dir / style]
            else:
                search_dirs = [self.cache_dir / "conversational"]  # Default
            
            for style_dir in search_dirs:
                if not style_dir.exists():
                    continue
                    
                for file_path in style_dir.glob('*.json'):
                    try:
                        import json
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cached_scripts.append({
                                'title': data.get('title', 'Unknown'),
                                'style': data.get('style', 'Unknown'),
                                'filename': file_path.name,
                                'word_count': data.get('word_count', 0),
                                'duration': f"{data.get('estimated_duration', 0)//60}min",
                                'source': data.get('source_article', 'Unknown'),
                                'generated': data.get('generated_timestamp', '')[:10]
                            })
                    except Exception:
                        continue
            
            return sorted(cached_scripts, key=lambda x: x['generated'], reverse=True)
            
        except Exception as e:
            print(f"⚠️ Error listing cached scripts: {e}")
            return []
    
    def batch_generate_scripts(self, articles, style: str = "conversational", custom_instructions: str = None):
        """Batch generate scripts"""
        scripts = []
        
        for i, article in enumerate(articles, 1):
            print(f"\n🔄 Processing article {i}/{len(articles)}: {article.title}")
            
            script = self.format_article_to_script(
                article, 
                style, 
                custom_instructions
            )
            
            if script:
                scripts.append(script)
            
            # Rate limiting for API calls
            if i < len(articles):
                print("⏳ Waiting 3 seconds for API rate limiting...")
                import time
                time.sleep(3)
        
        print(f"\n✅ Generated {len(scripts)} scripts out of {len(articles)} articles")
        return scripts


# Export the class and models for backward compatibility
from core import PodcastScript as CorePodcastScript

# Create alias for backward compatibility
PodcastScript = CorePodcastScript

__all__ = ['PodcastScriptFormatter', 'PodcastScript']