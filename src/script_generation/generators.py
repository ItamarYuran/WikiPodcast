"""
Script Generation Logic

This module contains the core script generation implementations.
Separated from the original script_formatter.py for better modularity.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from core import (
    ScriptGenerator,
    ProcessingResult,
    ProcessingStatus,
    Article,
    PodcastScript,
    ScriptSegment,
    ScriptStyle,
    ScriptGenerationError,
    ConfigurationError
)

from script_generation.styles import StyleManager
from script_generation.processors import TTSProcessor, InstructionProcessor
from script_generation.cache import ScriptCache
from script_generation.validators import ScriptValidator


class ScriptGeneratorImpl(ScriptGenerator):
    """
    Main script generator implementation.
    Handles the core logic of converting articles to podcast scripts.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the script generator"""
        self.config = config or {}
        self.style_manager = StyleManager()
        self.tts_processor = TTSProcessor()
        self.instruction_processor = InstructionProcessor()
        self.cache = ScriptCache(self.config.get('cache_dir', 'processed_scripts'))
        self.validator = ScriptValidator()
        
        # Initialize OpenAI client
        self._setup_openai_client()
        
        print("✅ Script Generator initialized with modular architecture")
    
    def _setup_openai_client(self):
        """Setup OpenAI client with API key validation"""
        api_key = self._get_openai_api_key()
        
        if not api_key:
            raise ConfigurationError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable.",
                config_key="OPENAI_API_KEY"
            )
        
        if not api_key.startswith('sk-'):
            raise ConfigurationError(
                f"Invalid OpenAI API key format. Expected: sk-..., Got: {api_key[:10]}...",
                config_key="OPENAI_API_KEY"
            )
        
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
            print(f"✅ OpenAI client initialized (key ends with: ...{api_key[-8:]})")
        except ImportError:
            raise ConfigurationError(
                "OpenAI library not installed. Please install with: pip install openai",
                config_key="openai_library"
            )
    
    def _get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from various sources"""
        # Check config first
        if 'openai_api_key' in self.config:
            return self.config['openai_api_key']
        
        # Check environment variables
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
                from dotenv import load_dotenv
                load_dotenv(env_path)
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    print(f"🔧 Loaded OpenAI API key from: {env_path}")
                    return api_key
        
        return None
    
    def generate_script(self, 
                       article: Article,
                       style: str = "conversational",
                       custom_instructions: Optional[str] = None,
                       target_duration: Optional[int] = None) -> ProcessingResult:
        """
        Generate a podcast script from an article.
        Main entry point that orchestrates the entire process.
        """
        try:
            print(f"🎯 Generating script for: {article.title}")
            print(f"📊 Article: {article.word_count:,} words, Style: {style}")
            
            # Validate inputs
            validation_result = self._validate_inputs(article, style)
            if not validation_result.is_success:
                return validation_result
            
            # Check cache first
            cache_key = self._generate_cache_key(article, style, custom_instructions)
            cached_script = self.cache.get(cache_key)
            if cached_script:
                print("📋 Found cached script")
                return ProcessingResult(
                    status=ProcessingStatus.COMPLETED,
                    data=cached_script,
                    metadata={"source": "cache"}
                )
            
            # Get style configuration
            style_config = self.style_manager.get_style_config(style)
            if not style_config:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=f"Unknown style: {style}"
                )
            
            # Prepare content for generation
            prepared_content = self._prepare_article_content(article)
            
            # Generate script using OpenAI
            generation_result = self._generate_script_with_openai(
                article, style_config, prepared_content, custom_instructions, target_duration
            )
            
            if not generation_result.is_success:
                return generation_result
            
            # Process and validate the generated script
            script_text = generation_result.data
            processing_result = self._process_generated_script(
                script_text, article, style, custom_instructions
            )
            
            if not processing_result.is_success:
                return processing_result
            
            # Cache the result
            podcast_script = processing_result.data
            self.cache.set(cache_key, podcast_script)
            
            print(f"✅ Generated script: {podcast_script.word_count} words, ~{podcast_script.estimated_duration//60}min")
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=podcast_script,
                metadata={
                    "source": "generated",
                    "style": style,
                    "model": "gpt-3.5-turbo",
                    "processing_time": "calculated"
                }
            )
            
        except Exception as e:
            print(f"❌ Script generation failed: {str(e)}")
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=str(e)
            )
    
    def _validate_inputs(self, article: Article, style: str) -> ProcessingResult:
        """Validate inputs before processing"""
        if not article.content.strip():
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error="Article content is empty"
            )
        
        if not self.style_manager.is_valid_style(style):
            available_styles = list(self.style_manager.get_available_styles().keys())
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=f"Invalid style '{style}'. Available: {', '.join(available_styles)}"
            )
        
        return ProcessingResult(status=ProcessingStatus.COMPLETED)
    
    def _generate_cache_key(self, article: Article, style: str, custom_instructions: Optional[str]) -> str:
        """Generate a unique cache key for the script"""
        import hashlib
        
        content_hash = hashlib.md5(article.content.encode()).hexdigest()[:8]
        instructions_hash = hashlib.md5((custom_instructions or "").encode()).hexdigest()[:8]
        
        return f"{article.id}_{style}_{content_hash}_{instructions_hash}"
    
    def _prepare_article_content(self, article: Article) -> str:
        """Prepare article content for script generation"""
        content_parts = []
        
        # Add summary if available
        if article.summary:
            content_parts.append(f"SUMMARY: {article.summary}")
        
        # Clean and truncate main content
        main_content = article.content
        main_content = re.sub(r'\n\s*\n\s*\n', '\n\n', main_content)
        main_content = re.sub(r'\s+', ' ', main_content)
        
        # Truncate if too long (keep within token limits)
        words = main_content.split()
        if len(words) > 8000:
            print(f"⚠️ Article is long ({len(words)} words), truncating to 8000 words")
            main_content = ' '.join(words[:8000])
            # Try to end at a sentence
            last_period = main_content.rfind('.')
            if last_period > len(main_content) * 0.9:
                main_content = main_content[:last_period + 1]
        
        content_parts.append(f"CONTENT: {main_content}")
        
        # Add metadata
        if article.metadata.categories:
            content_parts.append(f"CATEGORIES: {', '.join(article.metadata.categories[:5])}")
        
        return '\n\n'.join(content_parts)
    
    def _generate_script_with_openai(self,
                                   article: Article,
                                   style_config: Dict[str, Any],
                                   prepared_content: str,
                                   custom_instructions: Optional[str],
                                   target_duration: Optional[int]) -> ProcessingResult:
        """Generate script using OpenAI API"""
        try:
            # Build the prompt
            prompt = self._build_generation_prompt(
                article, style_config, prepared_content, custom_instructions, target_duration
            )
            
            # Choose model and configure token limits
            model = self.config.get('model', 'gpt-3.5-turbo')
            max_tokens = self._calculate_max_tokens(model, prompt, target_duration)
            
            print(f"🤖 Using model: {model} (max_tokens: {max_tokens})")
            
            # If prompt is too long, truncate it
            if len(prompt.split()) * 1.3 > (8000 if model == "gpt-4" else 3000):
                print("⚠️ Prompt too long, truncating content...")
                prompt = self._truncate_prompt_for_model(prompt, model)
            
            # Make the API call
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.9,
                top_p=0.95,
                frequency_penalty=0.3,
                presence_penalty=0.6
            )
            
            script_content = response.choices[0].message.content.strip()
            
            if not script_content:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error="OpenAI returned empty response"
                )
            
            print(f"✅ Generated {len(script_content.split())} words from OpenAI")
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=script_content
            )
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            print(f"❌ {error_msg}")
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=error_msg
            )
    def format_article_to_script(self, article, style='conversational', target_duration='medium', custom_instructions=None, **kwargs):
        """
        Format an article to a script - compatibility method for interactive menu
        Delegates to the generate_script method to maintain interface compatibility
        """
        # Convert string target_duration to seconds if needed
        if isinstance(target_duration, str):
            duration_map = {
                'short': 300,    # 5 minutes
                'medium': 600,   # 10 minutes  
                'long': 900,     # 15 minutes
                'full': 1200     # 20 minutes
            }
            target_duration = duration_map.get(target_duration, 600)
        
        # Convert legacy WikipediaArticle to new Article format if needed
        if hasattr(article, 'title') and not hasattr(article, 'id'):
            # This is a legacy WikipediaArticle, convert it
            from core.models import Article, ContentMetadata, ContentType
            
            # Create a safe filename-like id from the title
            safe_title = "".join(c for c in article.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            article_id = safe_title.replace(' ', '_')[:50]
            
            # Create metadata with the REQUIRED source parameter
            try:
                # Try with common parameters that might exist
                metadata = ContentMetadata(
                    source="wikipedia",  # <-- REQUIRED parameter
                    language="en",
                    categories=getattr(article, 'categories', []),
                    quality_score=getattr(article, 'quality_score', 0.0),
                    page_views=getattr(article, 'page_views', 0),
                    last_modified=getattr(article, 'last_modified', None),
                    references=getattr(article, 'references', []),
                    images=getattr(article, 'images', [])
                )
            except TypeError as e:
                # If that fails, try with minimal required parameters
                try:
                    metadata = ContentMetadata(
                        source="wikipedia",  # <-- REQUIRED parameter
                        language="en",
                        categories=getattr(article, 'categories', [])
                    )
                except TypeError as e2:
                    # If that fails too, use only the required parameter
                    metadata = ContentMetadata(
                        source="wikipedia"  # <-- REQUIRED parameter
                    )
            
            # Convert to new Article format
            article = Article(
                id=article_id,
                title=article.title,
                content=article.content,
                summary=getattr(article, 'summary', ''),
                url=getattr(article, 'url', ''),
                content_type=ContentType.WIKIPEDIA_ARTICLE,  # Use the enum
                metadata=metadata
            )
            
            # Add word_count as a separate attribute if it doesn't exist
            if not hasattr(article, 'word_count'):
                article.word_count = getattr(article, 'word_count', len(article.content.split()))
        
        # Call the main generate_script method
        result = self.generate_script(
            article=article,
            style=style,
            custom_instructions=custom_instructions,
            target_duration=target_duration
        )
        
        # Return the script data if successful, otherwise raise the error
        if result.is_success:
            return result.data
        else:
            raise ScriptGenerationError(f"Script generation failed: {result.error}")

    def list_cached_scripts(self):
        """List cached scripts from the cache"""
        if hasattr(self, 'cache') and self.cache and hasattr(self.cache, 'list_cached_scripts'):
            return self.cache.list_cached_scripts()
        return []
    
    def _build_generation_prompt(self,
                               article: Article,
                               style_config: Dict[str, Any],
                               prepared_content: str,
                               custom_instructions: Optional[str],
                               target_duration: Optional[int]) -> str:
        """Build the generation prompt for OpenAI"""
        duration = target_duration or style_config.get('target_duration', 900)
        target_words = int((duration / 60) * 150)  # ~150 words per minute
        duration_minutes = duration // 60
        
        # Get the style template
        style_template = self.style_manager.get_style_template(style_config['name'])
        
        # Build the prompt with strong emphasis on word count
        prompt_parts = [
            f"Create an engaging podcast script about {article.title}",
            f"",
            f"CRITICAL REQUIREMENTS:",
            f"- Target duration: {duration_minutes} minutes ({duration} seconds)",
            f"- MUST write EXACTLY {target_words} words (this is essential!)",
            f"- Word count is more important than brevity",
            f"- Count words as you write and reach the target",
            f"- Style: {style_config['description']}",
            f"",
            f"WORD COUNT VERIFICATION:",
            f"- {duration_minutes} minutes × 150 words/minute = {target_words} words REQUIRED",
            f"- Do NOT stop writing until you reach {target_words} words",
            f"- Expand on topics to reach the word count",
            f"- Add more examples, details, and explanations",
            f"",
            style_template,
            f"",
            f"CONTENT TO ADAPT:",
            f"{prepared_content}",
        ]
        
        if custom_instructions:
            prompt_parts.insert(-2, f"CUSTOM INSTRUCTIONS:\n{custom_instructions}")
        
        prompt_parts.extend([
            f"",
            f"FINAL REMINDER:",
            f"- You MUST write exactly {target_words} words",
            f"- This is a {duration_minutes}-minute script",
            f"- Expand topics with details, examples, and explanations",
            f"- Do not summarize - write the full {target_words} words!",
            f"",
            f"BEGIN THE {target_words}-WORD SCRIPT:"
        ])
        
        return '\n'.join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for script generation"""
        return """You are an expert podcast script writer specializing in dual instruction systems for TTS optimization.

Your task is to create scripts with TWO types of instructions:

1. SCRIPT INSTRUCTIONS (removed before TTS): [TRANSITION], [SET_SCENE], [BUILD_TENSION], etc.
   - These guide your writing process and content structure
   - They help you create engaging, well-organized content
   - They will be automatically removed before text-to-speech conversion

2. TTS INSTRUCTIONS (converted to SSML): [SHORT_PAUSE], [EMPHASIS]word[/EMPHASIS], etc.
   - These optimize how the script sounds when spoken
   - They control pacing, emphasis, and audio quality
   - They get converted to SSML for Google Cloud TTS

CRITICAL REQUIREMENTS:
- Use BOTH instruction types strategically throughout the script
- Spell out ALL abbreviations and acronyms for TTS
- Convert years and numbers to words: "2024" → "twenty twenty-four"
- Replace symbols with words: "&" → "and", "%" → "percent"
- Create exactly the target word count (excluding instruction tags)
- Write in natural, conversational speech patterns
- Include strategic pauses and emphasis for audio engagement

Remember: Script instructions = writing guidance, TTS instructions = audio optimization!"""
    
    def _calculate_max_tokens(self, model: str, prompt: str, target_duration: Optional[int] = None) -> int:
        """Calculate maximum tokens for the response based on target duration"""
        prompt_words = len(prompt.split())
        estimated_prompt_tokens = int(prompt_words * 1.3)
        
        # Calculate target words based on duration
        if target_duration:
            target_words = int((target_duration / 60) * 150)  # 150 words per minute
            target_tokens = int(target_words * 1.3)  # Convert to tokens
            print(f"🎯 Target: {target_words} words → {target_tokens} tokens")
        else:
            target_tokens = 2000  # Default
        
        if model == "gpt-4":
            context_limit = 8192
            # For GPT-4, be more generous with token allocation
            max_response_tokens = min(target_tokens, 6000)  # Increased cap
        else:
            context_limit = 4096
            # For GPT-3.5, also increase the cap
            max_response_tokens = min(target_tokens, 3000)  # Increased cap
        
        max_prompt_tokens = context_limit - max_response_tokens - 200  # Safety buffer
        
        if estimated_prompt_tokens > max_prompt_tokens:
            print(f"⚠️ Prompt too long: {estimated_prompt_tokens} tokens (max: {max_prompt_tokens})")
            print(f"🔧 Will truncate prompt to fit")
        
        print(f"📊 Allocated: {max_response_tokens} tokens for response")
        
        return max_response_tokens
    
    def _process_generated_script(self,
                                script_text: str,
                                article: Article,
                                style: str,
                                custom_instructions: Optional[str]) -> ProcessingResult:
        """Process the generated script into a PodcastScript object"""
        try:
            # Process TTS instructions
            tts_result = self.tts_processor.process_script(script_text)
            if not tts_result.is_success:
                return tts_result
            
            tts_ready_script = tts_result.data
            
            # Validate the script
            validation_result = self.validator.validate_script(script_text)
            if not validation_result.is_success:
                print(f"⚠️ Script validation issues: {validation_result.error}")
                # Continue anyway, but log the issues
            
            # Parse script segments
            segments = self._parse_script_segments(tts_ready_script)
            
            # Calculate duration
            estimated_duration = self._estimate_script_duration(tts_ready_script)
            
            # Create PodcastScript object
            podcast_script = PodcastScript(
                id=f"script_{article.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=f"{article.title} - {style.title()} Style",
                style=ScriptStyle(style),
                source_article_id=article.id,
                segments=segments,
                script_text=script_text,
                tts_ready_text=tts_ready_script,
                estimated_duration=estimated_duration,
                word_count=len(tts_ready_script.split()),
                metadata={
                    "instruction_counts": self.instruction_processor.count_instructions(script_text),
                    "validation_results": validation_result.data if validation_result.data else {}
                },
                custom_instructions=custom_instructions
            )
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=podcast_script
            )
            
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=f"Script processing failed: {str(e)}"
            )
    
    def _parse_script_segments(self, script_text: str) -> List[ScriptSegment]:
        """Parse script into segments"""
        segments = []
        
        # Simple paragraph-based segmentation
        paragraphs = [p.strip() for p in script_text.split('\n\n') if len(p.strip()) > 50]
        
        for i, paragraph in enumerate(paragraphs):
            segment_type = "intro" if i == 0 else "outro" if i == len(paragraphs) - 1 else "main"
            
            segments.append(ScriptSegment(
                id=f"segment_{i}",
                content=paragraph,
                segment_type=segment_type,
                estimated_duration=self._estimate_script_duration(paragraph)
            ))
        
        return segments
    
    def _truncate_prompt_for_model(self, prompt: str, model: str) -> str:
        """Truncate prompt to fit model context window"""
        if model == "gpt-4":
            max_prompt_words = 5000  # Conservative limit for GPT-4
        else:
            max_prompt_words = 2000  # Conservative limit for GPT-3.5
        
        lines = prompt.split('\n')
        
        # Find the content section
        content_start = -1
        for i, line in enumerate(lines):
            if "ARTICLE CONTENT:" in line:
                content_start = i
                break
        
        if content_start == -1:
            # No content section found, just truncate
            words = prompt.split()
            return ' '.join(words[:max_prompt_words])
        
        # Keep everything before content, truncate content
        header_lines = lines[:content_start + 1]
        content_lines = lines[content_start + 1:]
        
        header_text = '\n'.join(header_lines)
        content_text = '\n'.join(content_lines)
        
        # Calculate remaining space
        header_words = len(header_text.split())
        remaining_words = max_prompt_words - header_words - 100  # Safety buffer
        
        if remaining_words > 0:
            content_words = content_text.split()
            truncated_content = ' '.join(content_words[:remaining_words])
            
            # Try to end at a sentence
            last_period = truncated_content.rfind('.')
            if last_period > len(truncated_content) * 0.8:  # If period is in last 20%
                truncated_content = truncated_content[:last_period + 1]
            
            return header_text + '\n' + truncated_content
        else:
            return header_text
    
    def _estimate_script_duration(self, text: str) -> int:
        """Estimate script duration in seconds"""
        word_count = len(text.split())
        # Assume 150 words per minute for TTS
        duration_minutes = word_count / 150
        duration_seconds = int(duration_minutes * 60)
        
        print(f"🔍 Duration calculation: {word_count} words ÷ 150 wpm = {duration_minutes:.1f} minutes = {duration_seconds} seconds")
        
        return duration_seconds


    def get_available_styles(self) -> Dict[str, Dict[str, Any]]:
        """Get available script styles"""
        return self.style_manager.get_available_styles()


class ChapterBasedGenerator(ScriptGeneratorImpl):
    """
    Generator that handles long articles by breaking them into chapters.
    Useful for articles that exceed token limits.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.chapter_editor = self._setup_chapter_editor()
    
    def _setup_chapter_editor(self):
        """Setup chapter editor for long articles"""
        try:
            from article_editor import ChapterEditor
            return ChapterEditor(self.openai_client.api_key)
        except ImportError:
            print("⚠️ ChapterEditor not available, falling back to standard generation")
            return None
    
    def generate_script(self,
                       article: Article,
                       style: str = "conversational",
                       custom_instructions: Optional[str] = None,
                       target_duration: Optional[int] = None) -> ProcessingResult:
        """Generate script with chapter-based processing for long articles"""
        
        # Use chapter-based processing for long articles
        if self.chapter_editor and self._should_use_chapter_editing(article, target_duration):
            return self._generate_with_chapter_editing(article, style, custom_instructions, target_duration)
        
        # Fall back to standard generation
        return super().generate_script(article, style, custom_instructions, target_duration)
    
    def _should_use_chapter_editing(self, article: Article, target_duration: Optional[int]) -> bool:
        """Determine if chapter editing should be used"""
        return article.word_count > 3000 or (target_duration and target_duration > 1200)
    
    def _generate_with_chapter_editing(self,
                                     article: Article,
                                     style: str,
                                     custom_instructions: Optional[str],
                                     target_duration: Optional[int]) -> ProcessingResult:
        """Generate script using chapter-by-chapter editing"""
        try:
            print("📚 Using chapter-based generation for long article")
            
            # Split article into chapters
            chapters = self.chapter_editor.split_into_chapters(article.content)
            
            # Process each chapter
            chapter_scripts = []
            for i, (chapter_title, chapter_content) in enumerate(chapters):
                print(f"📝 Processing chapter {i+1}/{len(chapters)}: {chapter_title}")
                
                # Create mini-article for this chapter
                chapter_article = Article(
                    id=f"{article.id}_chapter_{i}",
                    title=f"{article.title} - {chapter_title}",
                    content=chapter_content,
                    summary=f"Chapter {i+1} of {article.title}",
                    content_type=article.content_type,
                    metadata=article.metadata,
                    url=article.url
                )
                
                # Generate script for this chapter
                chapter_result = super().generate_script(
                    chapter_article, style, custom_instructions, target_duration // len(chapters)
                )
                
                if chapter_result.is_success:
                    chapter_scripts.append(chapter_result.data)
                else:
                    print(f"⚠️ Chapter {i+1} failed: {chapter_result.error}")
            
            # Combine chapters into final script
            if chapter_scripts:
                combined_script = self._combine_chapter_scripts(chapter_scripts, article, style)
                return ProcessingResult(
                    status=ProcessingStatus.COMPLETED,
                    data=combined_script
                )
            else:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error="All chapters failed to generate"
                )
                
        except Exception as e:
            print(f"❌ Chapter-based generation failed: {str(e)}")
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=str(e)
            )
    
    def _combine_chapter_scripts(self, chapter_scripts: List[PodcastScript], article: Article, style: str) -> PodcastScript:
        """Combine multiple chapter scripts into one"""
        # Combine all segments
        all_segments = []
        for script in chapter_scripts:
            all_segments.extend(script.segments)
        
        # Combine script text
        combined_script_text = "\n\n".join(script.script_text for script in chapter_scripts)
        combined_tts_text = "\n\n".join(script.tts_ready_text for script in chapter_scripts)
        
        # Calculate totals
        total_duration = sum(script.estimated_duration for script in chapter_scripts)
        total_words = sum(script.word_count for script in chapter_scripts)
        
        return PodcastScript(
            id=f"combined_{article.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=f"{article.title} - {style.title()} Style (Chapter-based)",
            style=ScriptStyle(style),
            source_article_id=article.id,
            segments=all_segments,
            script_text=combined_script_text,
            tts_ready_text=combined_tts_text,
            estimated_duration=total_duration,
            word_count=total_words,
            metadata={
                "generation_method": "chapter-based",
                "chapter_count": len(chapter_scripts)
            }
        )


class ConversationalGenerator(ScriptGeneratorImpl):
    """
    Specialized generator for conversational style scripts.
    Adds extra conversational elements and storytelling techniques.
    """
    
    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for conversational scripts"""
        return super()._get_system_prompt() + """

CONVERSATIONAL SPECIALIZATION:
- Use "you" and "we" to directly engage the listener
- Include personal asides and relatable analogies
- Ask rhetorical questions to maintain engagement
- Use contractions and casual language while maintaining authority
- Build narrative tension with phrases like "But here's where it gets interesting..."
- Include moments of wonder and curiosity
- Make complex topics accessible through storytelling
"""