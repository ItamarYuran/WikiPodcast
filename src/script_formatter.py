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


class PodcastStyles:
    """Predefined podcast styles with their prompts and characteristics"""
    
    STYLES = {
        "conversational": {
            "name": "Conversational",
            "description": "Friendly, casual tone like talking to a friend",
            "target_duration": 900,  # 15 minutes
            "voice_style": "conversational",
            "prompt_template": """
Create a friendly, conversational podcast script about {topic}. 

Style Guidelines:
- Talk like you're explaining to a curious friend over coffee
- Use "you" and "we" to include the listener
- Include personal asides and relatable analogies
- Use contractions and casual language
- Ask rhetorical questions to keep engagement
- Include natural pauses with phrases like "Now here's the interesting part..."

Structure:
1. Warm, welcoming introduction that hooks the listener
2. 3-4 main segments with smooth transitions
3. Include fascinating details and surprising facts
4. End with a thoughtful conclusion that ties everything together

Content Focus:
- Emphasize the human stories and real-world impact
- Make complex topics accessible and relatable
- Include "did you know" moments throughout
- Connect historical events to modern day

Tone: Friendly, curious, accessible, engaging
Length: Create a comprehensive, detailed script that fully explores the topic
"""
        },
        
        "academic": {
            "name": "Academic/Scholarly",
            "description": "Professional, in-depth analysis with scholarly approach",
            "target_duration": 1200,  # 20 minutes
            "voice_style": "professional",
            "prompt_template": """
Create a scholarly, academic podcast script about {topic}.

Style Guidelines:
- Use precise, academic language while remaining accessible
- Include proper context and background information
- Reference key sources and methodologies where relevant
- Present multiple perspectives and scholarly debates
- Use formal structure with clear logical progression
- Include technical terms with explanations

Structure:
1. Formal introduction with thesis statement and overview
2. Historical context and background
3. Main analysis divided into clear sections
4. Current research and ongoing debates
5. Implications and future directions
6. Scholarly conclusion with key takeaways

Content Focus:
- Emphasize evidence-based information
- Include theoretical frameworks where applicable
- Discuss methodology and research approaches
- Present balanced view of controversies or debates
- Connect to broader academic discourse

Tone: Authoritative, analytical, scholarly, balanced
Length: Create a comprehensive, detailed academic exploration
"""
        },
        
        "storytelling": {
            "name": "Storytelling/Narrative",
            "description": "Dramatic narrative approach with story arc",
            "target_duration": 1080,  # 18 minutes
            "voice_style": "dramatic",
            "prompt_template": """
Create a compelling narrative podcast script about {topic} using storytelling techniques.

Style Guidelines:
- Build a story arc with tension, conflict, and resolution
- Use vivid, descriptive language to paint scenes
- Include character development and personal stakes
- Create suspense and emotional engagement
- Use narrative devices like foreshadowing and callbacks
- Show rather than tell through specific scenes and moments

Structure:
1. Hook: Start with an intriguing scene or moment
2. Setup: Establish the context, characters, and stakes
3. Rising Action: Build tension through conflicts and challenges
4. Climax: The pivotal moment or discovery
5. Resolution: How things were resolved or changed
6. Denouement: Reflection on lasting impact

Content Focus:
- Find the human drama within the facts
- Identify key moments of tension or turning points
- Develop character arcs for main figures
- Use specific scenes and dialogue where possible
- Connect events to universal human experiences

Tone: Dramatic, engaging, emotionally resonant, immersive
Length: Create a detailed narrative that fully develops the story
"""
        },
        
        "news_report": {
            "name": "News Report",
            "description": "Clear, factual reporting style like NPR or BBC",
            "target_duration": 720,  # 12 minutes
            "voice_style": "authoritative",
            "prompt_template": """
Create a professional news-style podcast script about {topic}.

Style Guidelines:
- Use clear, direct language with active voice
- Present information in order of importance
- Include specific facts, dates, and statistics
- Maintain objectivity and balance
- Use journalist's questions: who, what, when, where, why, how
- Include relevant quotes and expert perspectives where applicable

Structure:
1. Lead: Most important information first
2. Supporting Details: Key facts and background
3. Context: Historical or broader significance
4. Multiple Perspectives: Different viewpoints if applicable
5. Current Status: What's happening now
6. Looking Forward: Implications and what's next

Content Focus:
- Stick to verifiable facts and credible sources
- Provide necessary context without speculation
- Include relevant statistics and data points
- Address why this matters to the audience
- Present information clearly and concisely

Tone: Professional, objective, informative, credible
Length: Create a comprehensive news analysis with full context
"""
        },
        
        "documentary": {
            "name": "Documentary Style",
            "description": "Thoughtful, investigative approach with deep dives",
            "target_duration": 1500,  # 25 minutes
            "voice_style": "contemplative",
            "prompt_template": """
Create a documentary-style podcast script about {topic} with investigative depth.

Style Guidelines:
- Take a contemplative, investigative approach
- Explore underlying causes and deeper meanings
- Present information as an unfolding investigation
- Use thoughtful pacing with moments for reflection
- Include multiple layers of analysis
- Draw connections to broader themes and patterns

Structure:
1. Opening: Set the scene and pose central questions
2. Background Investigation: Dig into the foundational elements  
3. Key Evidence: Present findings and discoveries
4. Expert Analysis: Deeper interpretation and context
5. Broader Implications: Connect to larger patterns or themes
6. Reflection: What this reveals about human nature/society

Content Focus:
- Investigate the "why" behind the facts
- Explore cause-and-effect relationships
- Look for patterns and broader significance
- Include societal and cultural context
- Address misconceptions or hidden truths
- Connect to contemporary relevance

Tone: Thoughtful, investigative, contemplative, revealing
Length: Create an in-depth documentary exploration with comprehensive analysis
"""
        },
        
        "comedy": {
            "name": "Comedy/Humorous",
            "description": "Entertaining and funny while still informative",
            "target_duration": 810,  # 13.5 minutes
            "voice_style": "playful",
            "prompt_template": """
Create a humorous, entertaining podcast script about {topic} that's still informative.

Style Guidelines:
- Find the absurd, ironic, or amusing aspects of the topic
- Use witty observations and clever analogies
- Include light sarcasm and playful commentary
- Make jokes that enhance rather than distract from learning
- Use comedic timing with setup and punchline structure
- Keep humor appropriate and respectful

Structure:
1. Funny Hook: Start with an amusing observation or scenario
2. Setup: Present the topic with humorous framing
3. Comedic Exploration: Mix facts with funny commentary
4. Running Gags: Develop recurring comedic themes
5. Surprising Twists: Use humor to highlight unexpected facts
6. Amusing Conclusion: End with a memorable funny insight

Content Focus:
- Look for inherently funny or ironic elements
- Use anachronistic comparisons (historical figures as modern people)
- Find humor in human nature and behavior
- Make complex topics accessible through humor
- Include funny "what if" scenarios

Tone: Witty, playful, irreverent but respectful, entertaining
Length: Create an entertaining exploration that educates through humor
"""
        },
        
        "interview": {
            "name": "Interview Format", 
            "description": "Q&A style with imaginary expert or historical figure",
            "target_duration": 1170,  # 19.5 minutes
            "voice_style": "conversational",
            "prompt_template": """
Create an interview-style podcast script about {topic} with an imaginary expert or the historical figure themselves.

Style Guidelines:
- Structure as dialogue between host and guest
- Create natural-sounding questions and responses  
- Use the guest's expertise to dive deep into topics
- Include follow-up questions based on interesting answers
- Make the conversation feel spontaneous but informative
- Use the interview format to explore different angles

Structure:
1. Introduction: Introduce the guest and their expertise
2. Background Questions: Establish context and credentials
3. Deep Dive: Core questions about the main topic
4. Personal Insights: More intimate or thought-provoking questions
5. Contemporary Relevance: How this applies today
6. Closing: Final thoughts and key takeaways

Content Focus:
- What would people most want to ask this person?
- Include both facts and personal perspectives
- Use the Q&A format to address common misconceptions
- Allow for tangents that reveal character
- Include "behind the scenes" insights

Format:
- HOST: [Question or comment]
- GUEST: [Expert response]
- [Include natural conversation elements like "That's fascinating" or "Tell me more about..."]

Tone: Curious, probing, respectful, insightful
Length: Create a comprehensive interview with detailed responses
"""
        },
        
        "kids_educational": {
            "name": "Educational Kids",
            "description": "Simple, enthusiastic content for children",
            "target_duration": 540,  # 9 minutes
            "voice_style": "enthusiastic",
            "prompt_template": """
Create an educational podcast script about {topic} designed for children aged 8-12.

Style Guidelines:
- Use simple, clear language appropriate for the age group
- Be enthusiastic and energetic in tone
- Include interactive elements like "Can you imagine...?"
- Use comparisons to things kids know (school, playground, home)
- Break complex ideas into simple, digestible pieces
- Include fun facts and "wow" moments

Structure:
1. Exciting Introduction: Get kids interested immediately
2. Simple Explanation: Basic concepts in kid-friendly terms
3. Fun Facts: Amazing details that will surprise them
4. Make It Relatable: Connect to kids' everyday lives
5. Interactive Moments: Questions for kids to think about
6. Inspiring Conclusion: Encourage curiosity and learning

Content Focus:
- What would amaze or inspire a curious kid?
- Include sensory descriptions they can imagine
- Use simple analogies (like comparing sizes to school buses)
- Focus on the coolest, most interesting aspects
- Avoid scary or inappropriate content
- Encourage further exploration and questions

Safety Notes:
- Keep content age-appropriate and positive
- Avoid frightening or disturbing details
- Focus on wonder and discovery

Tone: Enthusiastic, encouraging, wonder-filled, age-appropriate
Length: Create an engaging educational adventure for young minds
"""
        }
    }


class PodcastScriptFormatter:
    """
    Advanced script formatter that converts Wikipedia articles into various podcast styles
    """
    
    def __init__(self, openai_api_key: str = None, cache_dir: str = "../processed_scripts"):
        """
        Initialize the script formatter
        
        Args:
            openai_api_key: OpenAI API key (if None, will load from environment)
            cache_dir: Directory to save generated scripts
        """
        # Load environment variables from multiple possible locations
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
    
    def format_article_to_script(self, 
                                article: WikipediaArticle,
                                style: str = "conversational",
                                custom_instructions: str = None,
                                target_duration: int = None,
                                model: str = "gpt-3.5-turbo") -> Optional[PodcastScript]:
        """
        Convert a Wikipedia article into a podcast script
        
        Args:
            article: WikipediaArticle object to convert
            style: Podcast style to use (from PodcastStyles.STYLES)
            custom_instructions: Additional instructions to include
            target_duration: Override default duration for the style
            model: OpenAI model to use ("gpt-4" or "gpt-3.5-turbo")
            
        Returns:
            PodcastScript object or None if generation failed
        """
        if style not in PodcastStyles.STYLES:
            available_styles = ", ".join(PodcastStyles.STYLES.keys())
            raise ValueError(f"Unknown style '{style}'. Available styles: {available_styles}")
        
        style_config = PodcastStyles.STYLES[style]
        
        try:
            print(f"🎯 Generating {style} script for: {article.title}")
            print(f"📊 Article: {article.word_count:,} words")
            
            # Prepare the content for processing
            processed_content = self._prepare_content(article)
            
            # Build the prompt
            prompt = self._build_prompt(
                article, 
                style_config, 
                processed_content, 
                custom_instructions,
                target_duration
            )
            
            print(f"🤖 Using model: {model}")
            
            # Generate script using OpenAI
            script_content = self._generate_with_openai(prompt, model)
            
            if not script_content:
                print("❌ Failed to generate script content")
                return None
            
            # Parse the generated script
            parsed_script = self._parse_generated_script(script_content, style, article.title)
            
            # Create PodcastScript object
            podcast_script = PodcastScript(
                title=f"{article.title} - {style_config['name']} Style",
                style=style,
                script=script_content,
                intro=parsed_script.get('intro', ''),
                outro=parsed_script.get('outro', ''),
                segments=parsed_script.get('segments', []),
                estimated_duration=self._estimate_duration(script_content),
                word_count=len(script_content.split()),
                source_article=article.title,
                generated_timestamp=datetime.now().isoformat(),
                custom_instructions=custom_instructions
            )
            
            # Save to cache
            self._save_script_to_cache(podcast_script)
            
            print(f"✅ Generated script: {podcast_script.word_count} words, ~{podcast_script.estimated_duration//60}min")
            
            return podcast_script
            
        except Exception as e:
            print(f"❌ Error generating script for '{article.title}': {str(e)}")
            import traceback
            print(f"📋 Full error: {traceback.format_exc()}")
            return None
    
    def batch_generate_scripts(self,
                              articles: List[WikipediaArticle],
                              style: str = "conversational",
                              custom_instructions: str = None) -> List[PodcastScript]:
        """
        Generate scripts for multiple articles
        
        Args:
            articles: List of WikipediaArticle objects
            style: Podcast style to use
            custom_instructions: Additional instructions
            
        Returns:
            List of generated PodcastScript objects
        """
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
            
            return PodcastScript(**data)
            
        except Exception as e:
            print(f"Error loading script: {e}")
            return None
    
    def test_api_connection(self) -> bool:
        """Test if the OpenAI API connection is working"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            print("🧪 Testing OpenAI API connection...")
            
            # Simple test request
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
            
            # Check for common error types
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str:
                print("💡 This looks like an API key problem. Check your key at: https://platform.openai.com/api-keys")
            elif "quota" in error_str or "billing" in error_str:
                print("💡 This looks like a billing/quota issue. Check your account at: https://platform.openai.com/account/billing")
            elif "rate limit" in error_str:
                print("💡 Rate limit hit. Wait a moment and try again.")
            else:
                print("💡 Check your internet connection and OpenAI service status.")
            
            return False
    
    # Private helper methods
    
    def _prepare_content(self, article: WikipediaArticle) -> str:
        """Prepare article content for script generation"""
        # Start with the summary for context
        content_parts = []
        
        if article.summary:
            content_parts.append(f"SUMMARY: {article.summary}")
        
        # Add main content but limit length to avoid token limits
        main_content = article.content
        
        # Remove excessive whitespace and clean up formatting
        main_content = re.sub(r'\n\s*\n\s*\n', '\n\n', main_content)
        main_content = re.sub(r'\s+', ' ', main_content)
        
        # Limit content length to avoid token limits (roughly 8000 words max)
        words = main_content.split()
        if len(words) > 8000:
            print(f"⚠️  Article is long ({len(words)} words), truncating to 8000 words for processing")
            main_content = ' '.join(words[:8000])
            # Try to end at a sentence
            last_period = main_content.rfind('.')
            if last_period > len(main_content) * 0.9:
                main_content = main_content[:last_period + 1]
        
        content_parts.append(f"CONTENT: {main_content}")
        
        # Add some metadata that might be useful
        if article.categories:
            content_parts.append(f"CATEGORIES: {', '.join(article.categories[:5])}")
        
        return '\n\n'.join(content_parts)
    
    def _build_prompt(self, 
                     article: WikipediaArticle,
                     style_config: Dict,
                     content: str,
                     custom_instructions: str = None,
                     target_duration: int = None) -> str:
        """Build the prompt for OpenAI with smart truncation for long articles"""
        
        duration = target_duration or style_config['target_duration']
        duration_minutes = duration // 60
        target_words = duration_minutes * 175  # ~175 words per minute
        
        # Build the core requirements and instructions first
        requirements_section = f"""Create a {style_config['name'].lower()} podcast script about: {article.title}
    
    CRITICAL REQUIREMENTS:
    - Target Length: EXACTLY {duration_minutes} minutes of spoken content
    - Word Count: Approximately {target_words} words (THIS IS MANDATORY)
    - Style: {style_config['description']}
    - Tone: {style_config.get('voice_style', 'engaging')}
    - Format: Complete script ready for audio recording
    
    LENGTH REQUIREMENTS (VERY IMPORTANT):
    - You MUST write approximately {target_words} words
    - This should take exactly {duration_minutes} minutes to read aloud
    - Do NOT write a short summary - write a FULL {duration_minutes}-minute script
    - Include comprehensive details, examples, and thorough explanations
    - If the content seems insufficient, expand with related context and background
    
    CONTENT GUIDELINES:
    - Write for natural speech delivery at normal pace
    - Include engaging details, examples, and anecdotes
    - Make it comprehensive and informative
    - Use clear pronunciation guides [like this] for difficult terms
    - Create smooth transitions between topics
    - Fill the ENTIRE time with valuable, interesting content"""
    
        if custom_instructions:
            requirements_section += f"\n\nSPECIAL INSTRUCTIONS: {custom_instructions}"
    
        # Add condensed style guidance
        style_guidance = style_config['prompt_template'].format(topic=article.title)
        style_lines = [line.strip() for line in style_guidance.split('\n') if line.strip() and not line.startswith('Length:')]
        condensed_style = '\n'.join(style_lines[:8])  # Take only first 8 meaningful lines
    
        style_section = f"""
    STYLE DETAILS:
    {condensed_style}
    
    REMINDER: Write {target_words} words for {duration_minutes} minutes of content!"""
    
        # Smart content truncation based on available space
        base_prompt = requirements_section + style_section
        base_tokens = len(base_prompt.split()) * 1.33  # Rough token estimate
        
        # Leave room for final instructions and model overhead
        available_tokens_for_content = 5000 - base_tokens - 500  # Conservative limit
        available_words_for_content = int(available_tokens_for_content / 1.33)
        
        # Truncate content intelligently
        if len(content.split()) > available_words_for_content:
            print(f"⚠️  Truncating content from {len(content.split())} to ~{available_words_for_content} words")
            
            # Split content into sections
            content_parts = content.split('\n\n')
            
            # Always keep the summary if it exists
            truncated_parts = []
            word_count = 0
            
            for part in content_parts:
                part_words = len(part.split())
                if word_count + part_words <= available_words_for_content:
                    truncated_parts.append(part)
                    word_count += part_words
                else:
                    # Add partial content if there's room
                    remaining_words = available_words_for_content - word_count
                    if remaining_words > 50:  # Only if meaningful amount left
                        partial_part = ' '.join(part.split()[:remaining_words])
                        truncated_parts.append(partial_part)
                    break
            
            content = '\n\n'.join(truncated_parts)
            
            # Add note about truncation
            content += f"\n\n[Content has been truncated for processing. Use the key information above and your knowledge to create a comprehensive {duration_minutes}-minute script about {article.title}.]"
    
        # Build final prompt
        final_prompt_parts = [
            requirements_section,
            style_section,
            "",
            "SOURCE CONTENT:",
            content,
            "",
            f"Generate the complete {duration_minutes}-minute podcast script now.",
            f"Remember: {target_words} words minimum, comprehensive coverage, full {duration_minutes} minutes of content!",
            "Be thorough and detailed - expand topics with examples, context, and explanations to reach the target length."
        ]
        
        return '\n'.join(final_prompt_parts)
    
    def _generate_with_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> Optional[str]:
            """Generate script content using OpenAI with FIXED token management"""
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_api_key)
                
                prompt_words = len(prompt.split())
                estimated_prompt_tokens = int(prompt_words * 1.3)
                
                print(f"📊 Initial prompt: {prompt_words} words (~{estimated_prompt_tokens} tokens)")
                
                # STRICT token limits for GPT-4
                if model == "gpt-4":
                    print("🧠 Using GPT-4 as requested...")
                    context_limit = 8192
                    max_response_tokens = 3000  # Conservative but allows long responses
                    max_prompt_tokens = context_limit - max_response_tokens - 200  # Safety buffer = ~4992
                    
                    # ALWAYS truncate for GPT-4 - prompts are too long
                    if estimated_prompt_tokens > max_prompt_tokens:
                        print(f"⚠️  Prompt too long ({estimated_prompt_tokens} tokens), truncating to {max_prompt_tokens}...")
                        prompt = self._truncate_prompt_aggressively(prompt, max_prompt_tokens)
                        # Verify truncation worked
                        new_tokens = int(len(prompt.split()) * 1.3)
                        print(f"✅ Truncated prompt: {len(prompt.split())} words (~{new_tokens} tokens)")
                        estimated_prompt_tokens = new_tokens
                    
                else:
                    max_prompt_tokens = 2500
                    max_response_tokens = 1500
                    
                    if estimated_prompt_tokens > max_prompt_tokens:
                        prompt = self._truncate_prompt_aggressively(prompt, max_prompt_tokens)
                        estimated_prompt_tokens = int(len(prompt.split()) * 1.3)
                
                print(f"🤖 Model: {model}")
                print(f"📤 Max response tokens: {max_response_tokens}")
                print(f"🎯 Target: ~1750 words for 10 minutes")
                
                # Focused system prompt
                system_prompt = """You are a podcast script writer. Create a 1,750-word conversational script using ONLY the article information provided.
    
    FOCUS on the most interesting and engaging aspects. Create a coherent narrative with clear beginning, middle, and end. Use a conversational tone like talking to a friend."""
                
                # Single attempt with good settings
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
                print(f"✅ Generated {generated_words} words")
                
                # Try extension if too short
                if generated_words < 1400:  # Less than 80% of target
                    print(f"⚠️  Script too short, attempting extension...")
                    extended_result = self._extend_script_simple(client, result, model)
                    if extended_result and len(extended_result.split()) > generated_words:
                        result = extended_result
                        generated_words = len(extended_result.split())
                        print(f"✅ Extended to {generated_words} words")
                
                return result
                
            except Exception as e:
                print(f"❌ OpenAI API error: {e}")
                return None
    
    def _truncate_prompt_aggressively(self, prompt: str, max_tokens: int) -> str:
        """Aggressively truncate prompt to fit token limit"""
        
        # Target words based on token limit
        target_words = int(max_tokens / 1.3)
        
        # Extract the essential parts
        lines = prompt.split('\n')
        
        # Find content section
        content_start = -1
        for i, line in enumerate(lines):
            if "SOURCE CONTENT:" in line:
                content_start = i
                break
        
        if content_start == -1:
            # No content section, just truncate everything
            words = prompt.split()
            return ' '.join(words[:target_words])
        
        # Build minimal prompt
        essential_parts = []
        
        # Add basic instructions (keep minimal)
        essential_parts.append("Create a 10-minute conversational podcast script about the subject.")
        essential_parts.append("Target: 1,750 words using only the article information below.")
        essential_parts.append("Focus on the most interesting aspects with clear beginning, middle, end.")
        essential_parts.append("")
        essential_parts.append("ARTICLE CONTENT:")
        
        # Add content but heavily truncated
        content_lines = lines[content_start + 1:]
        content_text = '\n'.join(content_lines)
        
        # Keep only the most essential content
        content_parts = content_text.split('\n\n')
        selected_content = []
        current_words = len(' '.join(essential_parts).split())
        
        for part in content_parts:
            part = part.strip()
            if not part:
                continue
            
            # Prioritize summary and key info
            if any(keyword in part.lower() for keyword in ['summary:', 'born', 'career', 'tennis', 'championship', 'sabalenka']):
                part_words = len(part.split())
                if current_words + part_words < target_words - 50:  # Leave room for instructions
                    selected_content.append(part)
                    current_words += part_words
                else:
                    # Add partial content
                    remaining = target_words - current_words - 50
                    if remaining > 20:
                        partial = ' '.join(part.split()[:remaining])
                        selected_content.append(partial)
                    break
        
        # Combine everything
        essential_parts.extend(selected_content)
        essential_parts.append("")
        essential_parts.append("Create the 1,750-word script focusing on the most engaging aspects:")
        
        final_prompt = '\n'.join(essential_parts)
        
        # Verify it fits
        final_words = len(final_prompt.split())
        if final_words > target_words:
            words = final_prompt.split()
            final_prompt = ' '.join(words[:target_words])
        
        return final_prompt
    
    def _extend_script_simple(self, client, script: str, model: str) -> Optional[str]:
        """Simple extension method"""
        try:
            extension_prompt = f"""Extend this podcast script to 1,750 words by adding more detail and examples from the original article.

Current script ({len(script.split())} words):
{script}

Make it longer and more detailed while staying engaging:"""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Extend this script to 1,750 words with more detail and examples."},
                    {"role": "user", "content": extension_prompt}
                ],
                max_tokens=3000,
                temperature=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Extension failed: {e}")
            return None    
    def _extend_script_aggressively(self, client, script: str, target_words: int, model: str) -> Optional[str]:
        """Extend script while maintaining article focus and coherence"""
        try:
            current_words = len(script.split())
            needed_words = target_words - current_words
            
            extension_prompt = f"""I have a {current_words}-word podcast script that needs to be expanded to {target_words} words.
    
    🎯 EXPANSION STRATEGY:
    - Identify sections that can be expanded with more detail from the article
    - Add more explanation of interesting facts and details
    - Expand on compelling human stories or dramatic moments
    - Provide more context for significant events or achievements
    - Elaborate on the impact or significance of key developments
    
    📋 REQUIREMENTS:
    - Use ONLY information from the original article (no external knowledge)
    - Maintain the coherent beginning-middle-end structure
    - Keep the conversational, engaging tone
    - Expand interesting parts more than boring parts
    - Ensure smooth transitions between sections
    
    Current script:
    {script}
    
    Rewrite as a comprehensive, coherent {target_words}-word script:"""
    
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"Expand this article-based script to exactly {target_words} words. Focus on the most interesting aspects while maintaining coherence and using only article information."},
                    {"role": "user", "content": extension_prompt}
                ],
                max_tokens=4000,
                temperature=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Extension failed: {e}")
            return None  

    def _truncate_prompt_to_tokens(self, prompt: str, max_tokens: int) -> str:
        """Aggressively truncate prompt to fit within token limit"""
        lines = prompt.split('\n')
        
        # Find the content section
        content_start = -1
        for i, line in enumerate(lines):
            if "SOURCE CONTENT:" in line:
                content_start = i
                break
        
        if content_start == -1:
            # No content section found, just truncate from end
            words = prompt.split()
            target_words = int(max_tokens / 1.3)
            return ' '.join(words[:target_words])
        
        # Keep everything before content
        pre_content = '\n'.join(lines[:content_start + 1])
        
        # Calculate how many tokens we have left for content
        pre_content_tokens = int(len(pre_content.split()) * 1.3)
        remaining_tokens = max_tokens - pre_content_tokens - 200  # Large buffer
        remaining_words = max(100, int(remaining_tokens / 1.3))  # Minimum 100 words
        
        # Take only the most essential content
        content_lines = lines[content_start + 1:]
        content_text = '\n'.join(content_lines)
        
        # Prioritize summary and key information
        content_parts = content_text.split('\n\n')
        essential_content = []
        word_count = 0
        
        for part in content_parts:
            part = part.strip()
            if not part:
                continue
                
            # Prioritize summary and key biographical info
            if any(keyword in part for keyword in ['SUMMARY:', 'born', 'career', 'achievement', 'championship']):
                part_words = len(part.split())
                if word_count + part_words <= remaining_words:
                    essential_content.append(part)
                    word_count += part_words
                else:
                    # Add partial content
                    remaining = remaining_words - word_count
                    if remaining > 20:
                        partial = ' '.join(part.split()[:remaining])
                        essential_content.append(partial)
                    break
            elif word_count < remaining_words * 0.7:  # Only add other content if we have room
                part_words = len(part.split())
                if word_count + part_words <= remaining_words:
                    essential_content.append(part)
                    word_count += part_words
        
        truncated_content = '\n\n'.join(essential_content)
        
        # Create minimal but effective prompt
        final_prompt = f"""{pre_content}
    {truncated_content}
    
    🎯 TASK: Create a fascinating 10-minute conversational podcast script (1,750 words) about this subject.
    Focus on the most interesting and engaging aspects from the content above.
    Create a coherent narrative with clear beginning, middle, and end.
    Use only the information provided - no external knowledge."""
        
        return final_prompt   

    def _generate_with_minimal_prompt(self, original_prompt: str, model: str) -> Optional[str]:
        """Emergency fallback with minimal prompt"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            print("🚨 Using emergency minimal prompt...")
            
            # Extract just the topic from the original prompt
            topic_match = re.search(r'TOPIC:\s*([^\n]+)', original_prompt)
            topic = topic_match.group(1) if topic_match else "the subject"
            
            # Extract key content
            content_match = re.search(r'(SUMMARY:.*?)(?=\n\n[A-Z]+:|$)', original_prompt, re.DOTALL)
            key_content = content_match.group(1) if content_match else "No content available"
            
            # Minimal but effective prompt
            minimal_prompt = f"""Create a comprehensive 10-minute conversational podcast script about {topic}.

TARGET: 1,750 words (10 minutes of speech)

Key information:
{key_content[:1000]}

Write a detailed, engaging script that:
- Includes extensive background and context
- Provides detailed examples and stories
- Explains concepts thoroughly
- Reaches the full 1,750 word target

Begin the script:"""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a podcast script writer. Create comprehensive 10-minute scripts with 1,750 words. Expand topics with detailed explanations and examples."},
                    {"role": "user", "content": minimal_prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            generated_words = len(result.split())
            print(f"✅ Emergency prompt generated {generated_words} words")
            
            return result
            
        except Exception as e:
            print(f"❌ Emergency prompt also failed: {e}")
            return None
    
    def _generate_with_openai_reduced(self, prompt: str, model: str) -> Optional[str]:
        """Fallback method with conservative token limits"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            print("🔄 Retrying with conservative token limits...")
            
            # Very conservative token limits
            if model == "gpt-4":
                max_tokens = 2000
            else:
                max_tokens = 1500
            
            system_prompt = "You are a podcast script writer. Write comprehensive, detailed scripts that meet the target length. Expand with examples and thorough explanations."
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            generated_words = len(result.split())
            print(f"✅ Generated {generated_words} words (reduced mode)")
            
            return result
            
        except Exception as e:
            print(f"❌ Reduced mode also failed: {e}")
            return None 
    
    
    def _parse_generated_script(self, script: str, style: str, title: str) -> Dict[str, any]:
        """Parse the generated script to extract segments"""
        
        # Try to identify intro, main content, and outro
        intro_match = re.search(r'(^.*?(?:welcome|hello|today we|this is).*?)(?:\n\n|\n.*?:)', script, re.IGNORECASE | re.DOTALL)
        outro_match = re.search(r'((?:in conclusion|to wrap up|that\'s all|thanks for|until next).*?$)', script, re.IGNORECASE | re.DOTALL)
        
        intro = intro_match.group(1).strip() if intro_match else ""
        outro = outro_match.group(1).strip() if outro_match else ""
        
        # Try to identify segments (this is basic - could be enhanced)
        segments = []
        
        # Look for numbered sections, headers, or natural breaks
        segment_patterns = [
            r'^\d+\.\s*(.+?)(?=^\d+\.|$)',  # Numbered sections
            r'^#+\s*(.+?)(?=^#+|$)',        # Headers
            r'(.*?)(?:\n\n\n|\n---|\nNext)',  # Natural breaks
        ]
        
        for pattern in segment_patterns:
            matches = re.finditer(pattern, script, re.MULTILINE | re.DOTALL)
            for match in matches:
                segment_content = match.group(1).strip()
                if len(segment_content) > 100:  # Only substantial segments
                    segments.append({
                        'content': segment_content,
                        'estimated_duration': self._estimate_duration(segment_content)
                    })
            if segments:  # If we found segments with this pattern, use them
                break
        
        # If no clear segments found, split by paragraphs
        if not segments:
            paragraphs = [p.strip() for p in script.split('\n\n') if len(p.strip()) > 100]
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
    
    def _estimate_duration(self, text: str) -> int:
        """Estimate duration in seconds based on word count"""
        words = len(text.split())
        # Average speaking rate is about 150-160 words per minute for podcasts
        # We'll use 150 wpm = 2.5 words per second
        return int(words / 2.5)
    
    def _save_script_to_cache(self, script: PodcastScript):
        """Save script to file cache"""
        try:
            # Create safe filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', script.source_article)
            safe_title = re.sub(r'[^\w\s-]', '', safe_title)
            safe_title = re.sub(r'\s+', '_', safe_title)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"{safe_title}_{timestamp}.json"
            
            file_path = self.cache_dir / script.style / filename
            
            # Convert to dict for JSON serialization
            script_data = {
                'title': script.title,
                'style': script.style,
                'script': script.script,
                'intro': script.intro,
                'outro': script.outro,
                'segments': script.segments,
                'estimated_duration': script.estimated_duration,
                'word_count': script.word_count,
                'source_article': script.source_article,
                'generated_timestamp': script.generated_timestamp,
                'custom_instructions': script.custom_instructions
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Script saved: {filename}")
            
        except Exception as e:
            print(f"Warning: Could not save script to cache: {e}")

# Diagnostic and testing functions
def test_setup():
    """Test the setup and API connection"""
    print("🧪 TESTING PODCAST SCRIPT FORMATTER SETUP")
    print("=" * 50)
    
    try:
        formatter = PodcastScriptFormatter()
        
        # Test API connection
        if formatter.test_api_connection():
            print("✅ Setup complete! Ready to generate scripts.")
            return True
        else:
            print("❌ Setup failed - API connection issues")
            return False
            
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False


def create_example_script():
    """Create an example script to test the system"""
    try:
        # Create a minimal test article
        from content_fetcher import WikipediaArticle
        
        test_article = WikipediaArticle(
            title="Test Article",
            url="https://example.com",
            content="This is a test article about artificial intelligence. AI is a fascinating field that involves creating machines that can think and learn. It has many applications in modern technology, from smartphones to autonomous vehicles. The field continues to evolve rapidly with new breakthroughs happening regularly.",
            summary="A test article about AI",
            categories=["Technology", "Computer Science"],
            page_views=1000,
            last_modified="2024-01-01",
            references=["https://example.com/ref1"],
            images=["test.jpg"],
            word_count=50,
            quality_score=0.8
        )
        
        formatter = PodcastScriptFormatter()
        
        print("🧪 Generating test script...")
        script = formatter.format_article_to_script(test_article, "conversational")
        
        if script:
            print("✅ Test script generated successfully!")
            print(f"📝 Title: {script.title}")
            print(f"📊 Words: {script.word_count}")
            print(f"⏱️  Duration: ~{script.estimated_duration//60} minutes")
            return True
        else:
            print("❌ Test script generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🎙️ PODCAST SCRIPT FORMATTER")
    print("=" * 30)
    
    if test_setup():
        print("\n" + "="*50)
        print("Ready to use! Example usage:")
        print("""
from script_formatter import PodcastScriptFormatter
from content_fetcher import WikipediaContentFetcher

# Setup
fetcher = WikipediaContentFetcher()
formatter = PodcastScriptFormatter()

# Get an article
article = fetcher.fetch_article("Artificial Intelligence")

# Generate script
script = formatter.format_article_to_script(article, "conversational")

print(f"Generated: {script.title}")
print(f"Duration: {script.estimated_duration//60} minutes")
""")
        
        # Optionally run the test
        test_choice = input("\nRun a test script generation? (y/n): ").lower()
        if test_choice == 'y':
            create_example_script()
    else:
        print("""
❌ Setup incomplete! To fix:

1. Create config/api_keys.env with:
   OPENAI_API_KEY=sk-your-key-here

2. Get your API key from:
   https://platform.openai.com/api-keys

3. Install required packages:
   pip install openai python-dotenv
""")