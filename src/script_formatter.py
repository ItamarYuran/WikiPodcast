import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from content_fetcher import WikipediaArticle


@dataclass
class PodcastScript:
    """Structure for storing podcast script data"""
    title: str
    style: str
    script: str
    intro: str
    outro: str
    segments: List[Dict[str, str]]
    estimated_duration: int  # in seconds
    word_count: int
    source_article: str
    generated_timestamp: str
    custom_instructions: Optional[str] = None
    script_for_tts: Optional[str] = None  # Version with script instructions removed
    tts_instructions_count: Optional[Dict[str, int]] = None  # Track TTS instruction usage
    
    def __post_init__(self):
        """Generate missing fields for backward compatibility"""
        if self.script_for_tts is None:
            # Auto-generate TTS-ready script from the main script
            self.script_for_tts = TTS_InstructionProcessor.clean_script_for_tts(self.script)
            print("🔄 Auto-generated TTS-ready version for backward compatibility")
        
        if self.tts_instructions_count is None:
            # Auto-generate instruction counts
            self.tts_instructions_count = TTS_InstructionProcessor.count_instructions(self.script)
            print("📊 Auto-generated instruction counts for backward compatibility")


# TTS Enhancement Instructions with dual system
TTS_ENHANCEMENT_INSTRUCTIONS = """
🎬 DUAL INSTRUCTION SYSTEM FOR PODCAST SCRIPTS:

**SCRIPT WRITING INSTRUCTIONS** (removed before TTS conversion):
These guide content structure and writing - they won't be spoken:
- [TRANSITION] - Signal smooth topic changes and connections
- [SET_SCENE] - Establish context and paint mental pictures
- [BUILD_TENSION] - Create narrative suspense and engagement
- [BACKGROUND_INFO] - Provide necessary context information
- [MAIN_POINT] - Highlight key information or takeaways
- [EXAMPLE_NEEDED] - Indicate where specific examples should go
- [STORY_TIME] - Signal narrative storytelling moments
- [EXPLAIN_CONCEPT] - Break down complex ideas simply
- [CONNECT_TO_AUDIENCE] - Make personal connections with listeners

**TTS AUDIO INSTRUCTIONS** (converted to SSML for speech):
These control how the text sounds when spoken:
- [SHORT_PAUSE] - Brief pause (0.5 seconds) for natural breathing
- [MEDIUM_PAUSE] - Standard pause (1.0 second) between ideas  
- [LONG_PAUSE] - Dramatic pause (1.5 seconds) for emphasis
- [BREATH] - Natural breathing point (0.3 seconds) in long sentences
- [EMPHASIS]word or phrase[/EMPHASIS] - Stress important terms
- [SLOW]technical term[/SLOW] - Slow down for complex concepts
- [SECTION_BREAK] - Major pause between sections (1.2 seconds)
- [PARAGRAPH_BREAK] - End of paragraph pause (0.8 seconds)

**CRITICAL TTS WRITING RULES:**
1. Spell out ALL abbreviations: "AI" → "artificial intelligence", "US" → "United States"
2. Convert years to words: "2024" → "twenty twenty-four", "1990s" → "nineteen nineties"  
3. Write numbers as words: "5" → "five", "100" → "one hundred"
4. Use phonetic spelling for commonly mispronounced words
5. Replace symbols: "&" → "and", "%" → "percent", "$" → "dollars"
6. Avoid complex punctuation that TTS struggles with

**EXAMPLE OF DUAL SYSTEM USAGE:**
[SET_SCENE] Picture this scenario from twenty twenty-four. [SHORT_PAUSE] [MAIN_POINT] [EMPHASIS]Artificial intelligence[/EMPHASIS] wasn't just changing technology [MEDIUM_PAUSE] it was transforming how we think about intelligence itself. [PARAGRAPH_BREAK]

[TRANSITION] [SECTION_BREAK] Now let's explore the key developments that made this possible...

Remember: Script instructions guide your writing, TTS instructions optimize audio quality!
"""


class PodcastStyles:
    """Predefined podcast styles with enhanced TTS instructions"""
    
    STYLES = {
        "conversational": {
            "name": "Conversational Storytelling",
            "description": "Friendly, informative conversation with compelling storytelling elements",
            "target_duration": 900,  # 15 minutes
            "voice_style": "conversational",
            "prompt_template": """
Create a friendly, conversational podcast script about {topic} using the DUAL INSTRUCTION SYSTEM.

Style Guidelines:
- Talk like you're sharing a fascinating story with a curious friend over coffee
- Use "you" and "we" to include the listener in the journey
- Weave facts into compelling narratives and human stories
- Include personal asides, relatable analogies, and thought-provoking moments
- Use contractions and casual language while maintaining authority
- Ask rhetorical questions to keep engagement: "But here's where it gets interesting..."
- Build narrative tension and reveal information like unfolding a mystery

Structure with DUAL INSTRUCTIONS:
1. [SET_SCENE] Captivating Hook: Start with intriguing story + [SHORT_PAUSE]
2. [BACKGROUND_INFO] Setting the Scene: Context through storytelling + [MEDIUM_PAUSE]  
3. [STORY_TIME] The Journey Unfolds: Present as story with [EMPHASIS] on key points
4. [EXPLAIN_CONCEPT] Deeper Insights: Complex ideas with [SLOW] technical terms
5. [CONNECT_TO_AUDIENCE] Connection to Today: Modern relevance + [SECTION_BREAK]
6. [MAIN_POINT] Memorable Conclusion: Powerful ending + [LONG_PAUSE]

Content Focus:
- [STORY_TIME] Find human drama and emotion within facts
- [EXAMPLE_NEEDED] Use specific, relatable examples with [EMPHASIS]
- [BUILD_TENSION] Create suspense with strategic [MEDIUM_PAUSE] placement
- [CONNECT_TO_AUDIENCE] Make personal connections using conversational tone
- [EXPLAIN_CONCEPT] Complex topics through [SLOW] delivery and metaphors

Narrative Techniques:
- [SET_SCENE] Use scene-setting: "Picture this..." + [SHORT_PAUSE]
- [BUILD_TENSION] Create suspense: "Little did they know..." + [MEDIUM_PAUSE]
- [TRANSITION] Smooth topic changes with natural connectors
- [PARAGRAPH_BREAK] End each paragraph for natural flow

Tone: Friendly, curious, engaging, informative, storytelling-driven
Balance: 60% storytelling and narrative, 40% direct information and analysis
Length: Create comprehensive script using both instruction systems effectively
"""
        }
    }


class TTS_InstructionProcessor:
    """Handles processing and conversion of TTS instructions"""
    
    # Script writing instructions (removed before TTS)
    SCRIPT_INSTRUCTIONS = [
        'TRANSITION', 'SET_SCENE', 'BUILD_TENSION', 'BACKGROUND_INFO',
        'MAIN_POINT', 'EXAMPLE_NEEDED', 'STORY_TIME', 'EXPLAIN_CONCEPT',
        'CONNECT_TO_AUDIENCE'
    ]
    
    # TTS audio instructions (converted to SSML)
    TTS_INSTRUCTIONS = {
        'SHORT_PAUSE': 0.5,
        'MEDIUM_PAUSE': 1.0, 
        'LONG_PAUSE': 1.5,
        'BREATH': 0.3,
        'SECTION_BREAK': 1.2,
        'PARAGRAPH_BREAK': 0.8
    }
    
    @classmethod
    def clean_script_for_tts(cls, script: str) -> str:
        """Remove script writing instructions and prepare for TTS"""
        
        # Remove script writing instructions
        for instruction in cls.SCRIPT_INSTRUCTIONS:
            pattern = rf'\[{instruction}\]\s*'
            script = re.sub(pattern, '', script, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        script = re.sub(r'\n\s*\n\s*\n', '\n\n', script)
        script = re.sub(r'\s+', ' ', script)
        
        return script.strip()
    
    @classmethod
    def convert_to_ssml(cls, script: str) -> str:
        """Convert TTS instructions to SSML format for Google Cloud TTS"""
        
        # First clean script instructions
        ssml_script = cls.clean_script_for_tts(script)
        
        # Convert pause instructions to SSML
        for instruction, duration in cls.TTS_INSTRUCTIONS.items():
            pattern = rf'\[{instruction}\]'
            ssml_replacement = f'<break time="{duration}s"/>'
            ssml_script = re.sub(pattern, ssml_replacement, ssml_script, flags=re.IGNORECASE)
        
        # Convert emphasis tags
        ssml_script = re.sub(r'\[EMPHASIS\](.*?)\[/EMPHASIS\]', r'<emphasis level="strong">\1</emphasis>', ssml_script, flags=re.IGNORECASE)
        
        # Convert slow tags  
        ssml_script = re.sub(r'\[SLOW\](.*?)\[/SLOW\]', r'<prosody rate="slow">\1</prosody>', ssml_script, flags=re.IGNORECASE)
        
        # Wrap in SSML speak tags
        ssml_script = f'<speak>{ssml_script}</speak>'
        
        return ssml_script
    
    @classmethod
    def count_instructions(cls, script: str) -> Dict[str, int]:
        """Count usage of different instruction types"""
        
        counts = {}
        
        # Count script instructions
        for instruction in cls.SCRIPT_INSTRUCTIONS:
            pattern = rf'\[{instruction}\]'
            counts[f'script_{instruction.lower()}'] = len(re.findall(pattern, script, flags=re.IGNORECASE))
        
        # Count TTS instructions
        for instruction in cls.TTS_INSTRUCTIONS.keys():
            pattern = rf'\[{instruction}\]'
            counts[f'tts_{instruction.lower()}'] = len(re.findall(pattern, script, flags=re.IGNORECASE))
        
        # Count emphasis and slow tags
        counts['tts_emphasis'] = len(re.findall(r'\[EMPHASIS\].*?\[/EMPHASIS\]', script, flags=re.IGNORECASE))
        counts['tts_slow'] = len(re.findall(r'\[SLOW\].*?\[/SLOW\]', script, flags=re.IGNORECASE))
        
        return counts
    
    @classmethod
    def validate_instructions(cls, script: str) -> Dict[str, any]:
        """Validate proper usage of instruction system"""
        
        validation = {
            'has_script_instructions': False,
            'has_tts_instructions': False,
            'unclosed_tags': [],
            'issues': [],
            'suggestions': []
        }
        
        # Check for script instructions
        for instruction in cls.SCRIPT_INSTRUCTIONS:
            if f'[{instruction}]' in script.upper():
                validation['has_script_instructions'] = True
                break
        
        # Check for TTS instructions
        for instruction in cls.TTS_INSTRUCTIONS.keys():
            if f'[{instruction}]' in script.upper():
                validation['has_tts_instructions'] = True
                break
        
        # Check for unclosed emphasis/slow tags
        emphasis_opens = len(re.findall(r'\[EMPHASIS\]', script, flags=re.IGNORECASE))
        emphasis_closes = len(re.findall(r'\[/EMPHASIS\]', script, flags=re.IGNORECASE))
        
        if emphasis_opens != emphasis_closes:
            validation['unclosed_tags'].append('EMPHASIS')
            validation['issues'].append(f"Unmatched EMPHASIS tags: {emphasis_opens} open, {emphasis_closes} close")
        
        slow_opens = len(re.findall(r'\[SLOW\]', script, flags=re.IGNORECASE))
        slow_closes = len(re.findall(r'\[/SLOW\]', script, flags=re.IGNORECASE))
        
        if slow_opens != slow_closes:
            validation['unclosed_tags'].append('SLOW')
            validation['issues'].append(f"Unmatched SLOW tags: {slow_opens} open, {slow_closes} close")
        
        # Check for common TTS issues
        abbreviations = ['AI', 'US', 'UK', 'Dr.', 'Mr.', 'CEO', 'API', 'URL', 'FAQ']
        for abbr in abbreviations:
            if re.search(rf'\b{re.escape(abbr)}\b', script):
                validation['issues'].append(f"Found abbreviation '{abbr}' - should be spelled out for TTS")
        
        # Check for numbers that should be written out
        numbers = re.findall(r'\b\d+\b', script)
        if numbers:
            validation['suggestions'].append(f"Consider writing numbers as words: {', '.join(numbers[:5])}")
        
        # Check for symbols
        symbols = ['&', '%', '$', '@', '#']
        for symbol in symbols:
            if symbol in script:
                validation['issues'].append(f"Found symbol '{symbol}' - should be written as word for TTS")
        
        return validation


class PodcastScriptFormatter:
    """Enhanced script formatter with dual instruction system"""
    
    def __init__(self, openai_api_key: str = None, cache_dir: str = "../processed_scripts"):
        """Initialize the enhanced script formatter"""
        
        # Load environment variables
        env_paths = [
            'config/api_keys.env',
            '../config/api_keys.env', 
            'src/config/api_keys.env',
            '.env'
        ]
        
        env_loaded = False
        for env_path in env_paths:
            if os.path.exists(env_path):
                print(f"🔧 Loading environment from: {env_path}")
                load_dotenv(env_path)
                env_loaded = True
                break
        
        if not env_loaded:
            print("⚠️  No .env file found, trying environment variables...")
        
        # Use provided key or get from environment
        if openai_api_key:
            self.openai_api_key = openai_api_key
        else:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            
        if not self.openai_api_key:
            raise ValueError(
                "❌ OpenAI API key not found!\n\n"
                "Fix this by either:\n"
                "1. Creating config/api_keys.env with: OPENAI_API_KEY=sk-your-key-here\n"
                "2. Setting environment variable: export OPENAI_API_KEY=sk-your-key-here\n"
                "3. Passing key directly: PodcastScriptFormatter('sk-your-key-here')\n\n"
                "Get your API key from: https://platform.openai.com/api-keys"
            )
        
        # Validate API key format
        if not self.openai_api_key.startswith('sk-'):
            raise ValueError(
                f"❌ Invalid OpenAI API key format!\n"
                f"Expected: sk-..., Got: {self.openai_api_key[:10]}...\n"
                f"Check your API key at: https://platform.openai.com/api-keys"
            )
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different styles
        for style_name in PodcastStyles.STYLES.keys():
            (self.cache_dir / style_name).mkdir(exist_ok=True)
        
        print(f"✅ OpenAI API key loaded (ends with: ...{self.openai_api_key[-8:]})")
        print(f"✅ Script cache directory: {self.cache_dir.absolute()}")
        print(f"🎬 Enhanced dual instruction system enabled")
    
    def format_article_to_script(self, 
                                article: WikipediaArticle,
                                style: str = "conversational",
                                custom_instructions: str = None,
                                target_duration: int = None,
                                model: str = "gpt-3.5-turbo") -> Optional[PodcastScript]:
        """Convert article to script with dual instruction system"""
        
        if style not in PodcastStyles.STYLES:
            available_styles = ", ".join(PodcastStyles.STYLES.keys())
            raise ValueError(f"Unknown style '{style}'. Available styles: {available_styles}")
        
        style_config = PodcastStyles.STYLES[style]
        
        try:
            print(f"🎯 Generating dual-instruction script for: {article.title}")
            print(f"📊 Article: {article.word_count:,} words")
            print(f"🎬 Using script + TTS instruction system")
            
            # Prepare content
            processed_content = self._prepare_content(article)
            
            # Build enhanced prompt
            prompt = self._build_enhanced_prompt(
                article, 
                style_config, 
                processed_content, 
                custom_instructions,
                target_duration
            )
            
            print(f"🤖 Using model: {model}")
            
            # Generate script
            script_content = self._generate_with_openai(prompt, model)
            
            if not script_content:
                print("❌ Failed to generate script content")
                return None
            
            # Process and validate instructions
            instruction_counts = TTS_InstructionProcessor.count_instructions(script_content)
            validation = TTS_InstructionProcessor.validate_instructions(script_content)
            
            # Create TTS-ready version
            tts_script = TTS_InstructionProcessor.clean_script_for_tts(script_content)
            
            # Report validation results
            self._report_validation(validation, instruction_counts)
            
            # Parse script
            parsed_script = self._parse_generated_script(script_content, style, article.title)
            
            # Create enhanced PodcastScript object
            podcast_script = PodcastScript(
                title=f"{article.title} - {style_config['name']} Style",
                style=style,
                script=script_content,  # Full script with all instructions
                script_for_tts=tts_script,  # Cleaned version for TTS
                intro=parsed_script.get('intro', ''),
                outro=parsed_script.get('outro', ''),
                segments=parsed_script.get('segments', []),
                estimated_duration=self._estimate_duration(tts_script),
                word_count=len(tts_script.split()),  # Count actual spoken words
                source_article=article.title,
                generated_timestamp=datetime.now().isoformat(),
                custom_instructions=custom_instructions,
                tts_instructions_count=instruction_counts
            )
            
            # Save to cache
            self._save_script_to_cache(podcast_script)
            
            print(f"✅ Generated enhanced script: {podcast_script.word_count} spoken words, ~{podcast_script.estimated_duration//60}min")
            print(f"🎬 Ready for Google Cloud TTS conversion")
            
            return podcast_script
            
        except Exception as e:
            print(f"❌ Error generating script for '{article.title}': {str(e)}")
            import traceback
            print(f"📋 Full error: {traceback.format_exc()}")
            return None
    
    def get_tts_ready_script(self, script: PodcastScript) -> str:
        """Get the TTS-ready version of a script"""
        return script.script_for_tts
    
    def get_ssml_script(self, script: PodcastScript) -> str:
        """Get SSML version for Google Cloud TTS"""
        return TTS_InstructionProcessor.convert_to_ssml(script.script_for_tts)
    
    def _build_enhanced_prompt(self, 
                             article: WikipediaArticle,
                             style_config: Dict,
                             content: str,
                             custom_instructions: str = None,
                             target_duration: int = None) -> str:
        """Build enhanced prompt with dual instruction system"""
        
        duration = target_duration or style_config.get('target_duration', 600)
        target_words = int((duration / 60) * 150)  # ~150 words per minute
        
        prompt = f"""
Create an engaging podcast script about {article.title} using the DUAL INSTRUCTION SYSTEM.

{TTS_ENHANCEMENT_INSTRUCTIONS}

TARGET SPECIFICATIONS:
- Duration: {duration//60} minutes  
- Word Count: approximately {target_words} SPOKEN words (excluding instruction tags)
- Style: {style_config['name']} - {style_config['description']}
- Voice Style: {style_config.get('voice_style', 'conversational')}

CRITICAL: Use BOTH instruction types strategically:

**SCRIPT INSTRUCTIONS** (for writing guidance - will be removed before TTS):
Use these to structure your content and guide your writing process:
- [TRANSITION] - before changing topics
- [SET_SCENE] - when establishing context
- [BUILD_TENSION] - for narrative engagement  
- [BACKGROUND_INFO] - for necessary context
- [MAIN_POINT] - for key information
- [EXAMPLE_NEEDED] - where examples go
- [STORY_TIME] - for narrative moments
- [EXPLAIN_CONCEPT] - for complex ideas
- [CONNECT_TO_AUDIENCE] - for personal connections

**TTS INSTRUCTIONS** (for audio quality - converted to SSML):
Use these to optimize how the script sounds when spoken:
- [SHORT_PAUSE] [MEDIUM_PAUSE] [LONG_PAUSE] - for natural timing
- [BREATH] - in long sentences
- [EMPHASIS]important term[/EMPHASIS] - for key concepts
- [SLOW]technical term[/SLOW] - for complex words
- [SECTION_BREAK] - between major topics
- [PARAGRAPH_BREAK] - at paragraph ends

CONTENT STRUCTURE WITH DUAL INSTRUCTIONS:
1. [SET_SCENE] ENGAGING INTRODUCTION (10% of content):
   - Hook immediately [SHORT_PAUSE]
   - [MAIN_POINT] Introduce topic clearly [MEDIUM_PAUSE]
   - Preview learning outcomes [PARAGRAPH_BREAK]

2. [STORY_TIME] MAIN CONTENT (75% of content):
   - [TRANSITION] Break into 3-4 clear sections [SECTION_BREAK]
   - [EXAMPLE_NEEDED] Use specific examples with [EMPHASIS]key terms[/EMPHASIS]
   - [BUILD_TENSION] Include narrative elements [MEDIUM_PAUSE]
   - [EXPLAIN_CONCEPT] Make complex ideas accessible with [SLOW]technical terms[/SLOW]
   - [CONNECT_TO_AUDIENCE] Relate to listener experience [PARAGRAPH_BREAK]

3. [MAIN_POINT] STRONG CONCLUSION (15% of content):
   - [BACKGROUND_INFO] Summarize key takeaways [LONG_PAUSE]
   - [CONNECT_TO_AUDIENCE] End with actionable insights [PARAGRAPH_BREAK]

ARTICLE CONTENT TO ADAPT:
{content}

{f"CUSTOM INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

CRITICAL TTS REQUIREMENTS:
- Write exactly {target_words} SPOKEN words (not including instruction tags)
- Spell out ALL abbreviations: "AI" → "artificial intelligence"
- Convert years: "2024" → "twenty twenty-four"  
- Write numbers as words: "5" → "five"
- Replace symbols: "&" → "and", "%" → "percent"
- Use both instruction systems strategically
- End paragraphs with [PARAGRAPH_BREAK]
- Use [SECTION_BREAK] between major topics
- Include [EMPHASIS] for 5-8 key terms throughout
- Use [SLOW] for 2-3 technical concepts
- Add [BREATH] in sentences over 20 words

EXAMPLE OF PROPER DUAL USAGE:
[SET_SCENE] Picture the year twenty twenty-four. [SHORT_PAUSE] [MAIN_POINT] The field of [EMPHASIS]artificial intelligence[/EMPHASIS] wasn't just evolving [MEDIUM_PAUSE] it was revolutionizing everything we thought we knew about machine learning. [PARAGRAPH_BREAK]

[TRANSITION] [SECTION_BREAK] Now let's explore how this transformation began...

Remember: Script instructions guide your writing structure, TTS instructions optimize audio delivery!

GENERATE THE DUAL-INSTRUCTION PODCAST SCRIPT:
"""
        
        return prompt
    
    def _report_validation(self, validation: Dict, instruction_counts: Dict):
        """Report validation results and instruction usage"""
        
        print(f"\n🎬 DUAL INSTRUCTION SYSTEM ANALYSIS:")
        print(f"=" * 50)
        
        # Check if both systems are used
        if validation['has_script_instructions']:
            print(f"✅ Script writing instructions: PRESENT")
        else:
            print(f"⚠️  Script writing instructions: MISSING")
        
        if validation['has_tts_instructions']:
            print(f"✅ TTS audio instructions: PRESENT")
        else:
            print(f"⚠️  TTS audio instructions: MISSING")
        
        # Show instruction counts
        print(f"\n📊 INSTRUCTION USAGE:")
        script_total = sum(count for key, count in instruction_counts.items() if key.startswith('script_'))
        tts_total = sum(count for key, count in instruction_counts.items() if key.startswith('tts_'))
        
        print(f"   📝 Script instructions: {script_total}")
        print(f"   🎵 TTS instructions: {tts_total}")
        
        # Show issues and suggestions
        if validation['issues']:
            print(f"\n⚠️  ISSUES TO ADDRESS:")
            for issue in validation['issues']:
                print(f"   • {issue}")
        
        if validation['suggestions']:
            print(f"\n💡 SUGGESTIONS:")
            for suggestion in validation['suggestions']:
                print(f"   • {suggestion}")
        
        if validation['unclosed_tags']:
            print(f"\n❌ UNCLOSED TAGS:")
            for tag in validation['unclosed_tags']:
                print(f"   • {tag}")
        
        print(f"=" * 50)
    
    def _generate_with_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> Optional[str]:
        """Generate script with enhanced system prompt for dual instructions"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Token management (same as before but with enhanced system prompt)
            prompt_words = len(prompt.split())
            estimated_prompt_tokens = int(prompt_words * 1.3)
            
            print(f"📊 Prompt: {prompt_words} words (~{estimated_prompt_tokens} tokens)")
            
            if model == "gpt-4":
                context_limit = 8192
                max_response_tokens = 3000
                max_prompt_tokens = context_limit - max_response_tokens - 200
                
                if estimated_prompt_tokens > max_prompt_tokens:
                    print(f"⚠️  Prompt too long, truncating...")
                    prompt = self._truncate_prompt_aggressively(prompt, max_prompt_tokens)
                    estimated_prompt_tokens = int(len(prompt.split()) * 1.3)
            else:
                max_prompt_tokens = 2500
                max_response_tokens = 1500
                
                if estimated_prompt_tokens > max_prompt_tokens:
                    prompt = self._truncate_prompt_aggressively(prompt, max_prompt_tokens)
                    estimated_prompt_tokens = int(len(prompt.split()) * 1.3)
            
            # Enhanced system prompt for dual instruction system
            system_prompt = """You are an expert podcast script writer specializing in dual instruction systems for TTS optimization.

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

EXAMPLE FORMAT:
[SET_SCENE] Picture this scenario. [SHORT_PAUSE] In twenty twenty-four, [EMPHASIS]artificial intelligence[/EMPHASIS] transformed everything. [MEDIUM_PAUSE]

[TRANSITION] [SECTION_BREAK] Now let's explore the key developments...

Remember: Script instructions = writing guidance, TTS instructions = audio optimization!"""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_response_tokens,
                temperature=0.9,
                top_p=0.95,
                frequency_penalty=0.3,
                presence_penalty=0.6
            )
            
            result = response.choices[0].message.content.strip()
            generated_words = len(result.split())
            print(f"✅ Generated {generated_words} total words (including instructions)")
            
            return result
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None
    
    # Include all other methods from original class (with same logic)
    def _prepare_content(self, article: WikipediaArticle) -> str:
        """Prepare article content for script generation"""
        content_parts = []
        
        if article.summary:
            content_parts.append(f"SUMMARY: {article.summary}")
        
        main_content = article.content
        main_content = re.sub(r'\n\s*\n\s*\n', '\n\n', main_content)
        main_content = re.sub(r'\s+', ' ', main_content)
        
        words = main_content.split()
        if len(words) > 8000:
            print(f"⚠️  Article is long ({len(words)} words), truncating to 8000 words")
            main_content = ' '.join(words[:8000])
            last_period = main_content.rfind('.')
            if last_period > len(main_content) * 0.9:
                main_content = main_content[:last_period + 1]
        
        content_parts.append(f"CONTENT: {main_content}")
        
        if article.categories:
            content_parts.append(f"CATEGORIES: {', '.join(article.categories[:5])}")
        
        return '\n\n'.join(content_parts)
    
    def _truncate_prompt_aggressively(self, prompt: str, max_tokens: int) -> str:
        """Aggressively truncate prompt while preserving dual instruction guidance"""
        target_words = int(max_tokens / 1.3)
        lines = prompt.split('\n')
        
        # Find content section
        content_start = -1
        for i, line in enumerate(lines):
            if "ARTICLE CONTENT TO ADAPT:" in line:
                content_start = i
                break
        
        if content_start == -1:
            words = prompt.split()
            return ' '.join(words[:target_words])
        
        # Build minimal prompt preserving dual instruction guidance
        essential_parts = []
        essential_parts.append("Create a podcast script using the DUAL INSTRUCTION SYSTEM:")
        essential_parts.append("")
        essential_parts.append("SCRIPT INSTRUCTIONS (removed before TTS):")
        essential_parts.append("- [TRANSITION] - topic changes")
        essential_parts.append("- [SET_SCENE] - establish context")
        essential_parts.append("- [MAIN_POINT] - key information")
        essential_parts.append("- [STORY_TIME] - narrative moments")
        essential_parts.append("")
        essential_parts.append("TTS INSTRUCTIONS (converted to SSML):")
        essential_parts.append("- [SHORT_PAUSE] [MEDIUM_PAUSE] [LONG_PAUSE]")
        essential_parts.append("- [EMPHASIS]word[/EMPHASIS] - important terms")
        essential_parts.append("- [SLOW]term[/SLOW] - complex concepts")
        essential_parts.append("- [SECTION_BREAK] [PARAGRAPH_BREAK]")
        essential_parts.append("")
        essential_parts.append("Target: 1,750 spoken words. Spell out abbreviations.")
        essential_parts.append("")
        essential_parts.append("ARTICLE CONTENT:")
        
        # Add truncated content
        content_lines = lines[content_start + 1:]
        content_text = '\n'.join(content_lines)
        content_words = content_text.split()
        
        current_words = len(' '.join(essential_parts).split())
        remaining = target_words - current_words - 50  # Safety buffer
        
        if remaining > 100:
            truncated_content = ' '.join(content_words[:remaining])
            essential_parts.append(truncated_content)
        
        essential_parts.append("")
        essential_parts.append("Generate the dual-instruction script:")
        
        return '\n'.join(essential_parts)
    
    def _estimate_duration(self, text: str) -> int:
        """Enhanced duration estimation for TTS-ready text"""
        # Count only spoken words (TTS instructions removed)
        clean_text = TTS_InstructionProcessor.clean_script_for_tts(text)
        clean_text = re.sub(r'\[[\w/_]+\]', '', clean_text)  # Remove any remaining instructions
        word_count = len(clean_text.split())
        
        # Base duration (150 words per minute for TTS)
        base_duration = (word_count / 150) * 60
        
        # Add time for TTS pauses (from original text before cleaning)
        pause_time = 0
        for instruction, duration in TTS_InstructionProcessor.TTS_INSTRUCTIONS.items():
            pause_time += text.count(f'[{instruction}]') * duration
        
        total_duration = base_duration + pause_time
        
        print(f"🎬 TTS Duration calculation:")
        print(f"   📝 Spoken words: {word_count}")
        print(f"   ⏱️  Base duration: {base_duration//60:.0f}:{base_duration%60:02.0f}")
        print(f"   ⏸️  Pause time: {pause_time:.1f}s")
        print(f"   🎯 Total duration: {total_duration//60:.0f}:{total_duration%60:02.0f}")
        
        return int(total_duration)
    
    def _parse_generated_script(self, script: str, style: str, title: str) -> Dict[str, any]:
        """Parse script to extract segments (using TTS-ready version)"""
        tts_script = TTS_InstructionProcessor.clean_script_for_tts(script)
        
        # Find intro and outro in TTS-ready version
        intro_match = re.search(r'(^.*?(?:welcome|hello|today we|this is).*?)(?:\n\n|\n.*?:)', tts_script, re.IGNORECASE | re.DOTALL)
        outro_match = re.search(r'((?:in conclusion|to wrap up|that\'s all|thanks for|until next).*?$)', tts_script, re.IGNORECASE | re.DOTALL)
        
        intro = intro_match.group(1).strip() if intro_match else ""
        outro = outro_match.group(1).strip() if outro_match else ""
        
        # Parse segments from TTS-ready version
        segments = []
        paragraphs = [p.strip() for p in tts_script.split('\n\n') if len(p.strip()) > 100]
        segments = [
            {
                'content': para,
                'estimated_duration': self._estimate_duration(para)
            }
            for para in paragraphs
        ]
        
        return {
            'intro': intro,
            'outro': outro,
            'segments': segments
        }
    
    def _save_script_to_cache(self, script: PodcastScript):
        """Save enhanced script with both versions to cache"""
        try:
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', script.source_article)
            safe_title = re.sub(r'[^\w\s-]', '', safe_title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"{safe_title}_{timestamp}.json"
            
            file_path = self.cache_dir / script.style / filename
            
            # Enhanced script data with both versions
            script_data = {
                'title': script.title,
                'style': script.style,
                'script': script.script,  # Full script with all instructions
                'script_for_tts': script.script_for_tts,  # TTS-ready version
                'intro': script.intro,
                'outro': script.outro,
                'segments': script.segments,
                'estimated_duration': script.estimated_duration,
                'word_count': script.word_count,
                'source_article': script.source_article,
                'generated_timestamp': script.generated_timestamp,
                'custom_instructions': script.custom_instructions,
                'tts_instructions_count': script.tts_instructions_count
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Enhanced script saved: {filename}")
            
        except Exception as e:
            print(f"Warning: Could not save script to cache: {e}")
    
    # Additional utility methods
    def get_available_styles(self) -> Dict[str, Dict[str, str]]:
        """Get information about available podcast styles"""
        return {
            name: {
                "name": config["name"],
                "description": config["description"],
                "target_duration": f"{config['target_duration']//60} minutes",
                "voice_style": config["voice_style"]
            }
            for name, config in PodcastStyles.STYLES.items()
        }
    
    def list_cached_scripts(self, style: str = None) -> List[Dict[str, str]]:
        """List all cached scripts, optionally filtered by style"""
        cached_scripts = []
        
        if style:
            search_dirs = [self.cache_dir / style] if style in PodcastStyles.STYLES else []
        else:
            search_dirs = [self.cache_dir / style_name for style_name in PodcastStyles.STYLES.keys()]
        
        for style_dir in search_dirs:
            if not style_dir.exists():
                continue
                
            for file_path in style_dir.glob('*.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        cached_scripts.append({
                            'title': data.get('title', 'Unknown'),
                            'style': data.get('style', 'Unknown'),
                            'filename': file_path.name,
                            'word_count': data.get('word_count', 0),
                            'duration': f"{data.get('estimated_duration', 0)//60}min",
                            'source': data.get('source_article', 'Unknown'),
                            'generated': data.get('generated_timestamp', '')[:10]  # Just date
                        })
                except Exception:
                    continue
        
        return sorted(cached_scripts, key=lambda x: x['generated'], reverse=True)
    
    def load_cached_script(self, filename: str, style: str = None) -> Optional[PodcastScript]:
        """Load a specific cached script"""
        if style and style in PodcastStyles.STYLES:
            file_path = self.cache_dir / style / filename
        else:
            # Search all style directories
            for style_name in PodcastStyles.STYLES.keys():
                file_path = self.cache_dir / style_name / filename
                if file_path.exists():
                    break
            else:
                return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle backward compatibility for scripts without script_for_tts
            if 'script_for_tts' not in data:
                data['script_for_tts'] = TTS_InstructionProcessor.clean_script_for_tts(data.get('script', ''))
            
            # Handle backward compatibility for scripts without tts_instructions_count
            if 'tts_instructions_count' not in data:
                data['tts_instructions_count'] = TTS_InstructionProcessor.count_instructions(data.get('script', ''))
            
            return PodcastScript(**data)
            
        except Exception as e:
            print(f"Error loading script: {e}")
            return None
    
    def batch_generate_scripts(self,
                              articles: List[WikipediaArticle],
                              style: str = "conversational",
                              custom_instructions: str = None) -> List[PodcastScript]:
        """Generate scripts for multiple articles"""
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
            if i < len(articles):  # Don't sleep after the last one
                print("⏳ Waiting 3 seconds for API rate limiting...")
                import time
                time.sleep(3)
        
        print(f"\n✅ Generated {len(scripts)} scripts out of {len(articles)} articles")
        return scripts
    
    def test_api_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            print("🧪 Testing OpenAI API connection...")
            
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
                print(f"⚠️  API responded but with unexpected content: {result}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI API test failed: {str(e)}")
            return False


# Testing and demonstration functions
def test_dual_instruction_system():
    """Test the enhanced dual instruction system"""
    print("🧪 TESTING DUAL INSTRUCTION SYSTEM")
    print("=" * 60)
    
    # Test script with both instruction types
    test_script = """
[SET_SCENE] Picture the world of twenty twenty-four. [SHORT_PAUSE] [MAIN_POINT] The field of [EMPHASIS]artificial intelligence[/EMPHASIS] wasn't just evolving [MEDIUM_PAUSE] it was revolutionizing everything. [PARAGRAPH_BREAK]

[TRANSITION] [SECTION_BREAK] Now let's explore how [SLOW]machine learning algorithms[/SLOW] transformed our understanding of intelligence. [LONG_PAUSE]

[STORY_TIME] The journey began decades ago, but the real breakthrough came when researchers realized [EMPHASIS]neural networks[/EMPHASIS] could learn patterns. [BREATH] This discovery changed everything. [PARAGRAPH_BREAK]
"""
    
    print("📝 ORIGINAL SCRIPT WITH DUAL INSTRUCTIONS:")
    print(test_script)
    print()
    
    # Test instruction processing
    counts = TTS_InstructionProcessor.count_instructions(test_script)
    validation = TTS_InstructionProcessor.validate_instructions(test_script)
    
    print("📊 INSTRUCTION ANALYSIS:")
    print(f"Script instructions: {sum(v for k, v in counts.items() if k.startswith('script_'))}")
    print(f"TTS instructions: {sum(v for k, v in counts.items() if k.startswith('tts_'))}")
    print()
    
    # Test TTS cleaning
    tts_ready = TTS_InstructionProcessor.clean_script_for_tts(test_script)
    print("🎬 TTS-READY SCRIPT (script instructions removed):")
    print(tts_ready)
    print()
    
    # Test SSML conversion
    ssml_script = TTS_InstructionProcessor.convert_to_ssml(test_script)
    print("🔊 SSML FOR GOOGLE CLOUD TTS:")
    print(ssml_script)
    print()
    
    print("✅ Dual instruction system test complete!")
    return True


def create_demo_script():
    """Create a demo script showing the enhanced system"""
    try:
        from content_fetcher import WikipediaArticle
        
        # Create test article
        test_article = WikipediaArticle(
            title="Artificial Intelligence Revolution",
            url="https://example.com",
            content="""Artificial intelligence has transformed from science fiction to reality. Modern AI systems use machine learning algorithms to process vast amounts of data. Deep learning networks have achieved breakthrough results in image recognition, natural language processing, and game playing. The technology continues to advance rapidly with new applications emerging daily.""",
            summary="AI has evolved from fiction to transformative technology",
            categories=["Technology", "Computer Science", "AI"],
            page_views=5000,
            last_modified="2024-01-01",
            references=["https://example.com/ai"],
            images=["ai.jpg"],
            word_count=100,
            quality_score=0.9
        )
        
        formatter = PodcastScriptFormatter()
        
        print("🎬 Generating demo script with dual instruction system...")
        script = formatter.format_article_to_script(test_article, "conversational")
        
        if script:
            print("✅ Demo script generated successfully!")
            print(f"📝 Title: {script.title}")
            print(f"📊 Spoken words: {script.word_count}")
            print(f"⏱️  Duration: ~{script.estimated_duration//60} minutes")
            
            print("\n" + "="*60)
            print("🎬 TTS-READY VERSION:")
            print("="*60)
            print(script.script_for_tts[:500] + "...")
            
            print("\n" + "="*60)
            print("🔊 SSML VERSION (first 300 chars):")
            print("="*60)
            ssml = formatter.get_ssml_script(script)
            print(ssml[:300] + "...")
            
            return True
        else:
            print("❌ Demo script generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


if __name__ == "__main__":
    print("🎙️ ENHANCED PODCAST SCRIPT FORMATTER WITH DUAL INSTRUCTIONS")
    print("=" * 70)
    
    # Test instruction system first
    if test_dual_instruction_system():
        print("\n" + "="*70)
        
        # Test full system
        try:
            formatter = PodcastScriptFormatter()
            if formatter.test_api_connection():
                print("✅ Enhanced system ready!")
                
                # Run demo
                demo_choice = input("\nGenerate demo script? (y/n): ").lower()
                if demo_choice == 'y':
                    create_demo_script()
            else:
                print("❌ API connection failed")
        except Exception as e:
            print(f"❌ Setup error: {e}")
    
    print("\n" + "="*70)
    print("🎯 USAGE SUMMARY:")
    print("""
The enhanced system provides:

1. 📝 SCRIPT INSTRUCTIONS - Guide content structure:
   [TRANSITION] [SET_SCENE] [BUILD_TENSION] [MAIN_POINT] etc.

2. 🎵 TTS INSTRUCTIONS - Optimize audio quality:
   [SHORT_PAUSE] [EMPHASIS]word[/EMPHASIS] [SLOW]term[/SLOW] etc.

3. 🔄 AUTOMATIC PROCESSING:
   - script.script = Full version with all instructions
   - script.script_for_tts = Clean version for TTS conversion  
   - formatter.get_ssml_script(script) = SSML for Google Cloud TTS

4. ✅ VALIDATION & REPORTING:
   - Instruction usage analysis
   - TTS optimization checks
   - Content quality validation

Ready for Google Cloud TTS integration! 🎬
""")