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
        """Build the prompt for OpenAI"""
        
        duration = target_duration or style_config['target_duration']
        duration_minutes = duration // 60
        target_words = duration_minutes * 175  # ~175 words per minute
        
        # More efficient prompt building
        prompt_parts = [
            f"Create a {style_config['name'].lower()} podcast script about: {article.title}",
            "",
            f"REQUIREMENTS:",
            f"- Style: {style_config['description']}",
            f"- Length: {duration_minutes} minutes (~{target_words} words)",
            f"- Tone: {style_config.get('voice_style', 'engaging')}",
            f"- Format: Complete script ready for audio recording",
            "",
            "GUIDELINES:",
            "- Write for natural speech delivery",
            "- Include engaging details and examples", 
            "- Make it comprehensive and informative",
            "- Use clear pronunciation guides [like this] for difficult terms",
            "- Create smooth transitions between topics",
        ]
        
        if custom_instructions:
            prompt_parts.extend([
                "",
                f"SPECIAL INSTRUCTIONS: {custom_instructions}",
            ])
        
        # Add a condensed version of the style template
        style_guidance = style_config['prompt_template'].format(topic=article.title)
        # Take key parts of the template
        style_lines = style_guidance.split('\n')
        key_style_lines = [line for line in style_lines if line.strip() and not line.startswith('Length:')][:15]
        
        prompt_parts.extend([
            "",
            "STYLE DETAILS:",
            '\n'.join(key_style_lines[:10]),  # Limit to prevent token overflow
            "",
            "SOURCE CONTENT:",
            content,
            "",
            f"Generate the complete {duration_minutes}-minute podcast script now:"
        ])
        
        return '\n'.join(prompt_parts)
    
    def _generate_with_openai(self, prompt: str, model: str = "gpt-3.5-turbo") -> Optional[str]:
        """Generate script content using OpenAI with better error handling"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Estimate prompt tokens (rough: 1 token ≈ 0.75 words)
            prompt_words = len(prompt.split())
            estimated_prompt_tokens = int(prompt_words * 1.33)
            
            print(f"📊 Prompt: {prompt_words} words (~{estimated_prompt_tokens} tokens)")
            
            # Adjust model and tokens based on prompt size
            if estimated_prompt_tokens > 14000:
                print("⚠️  Prompt is very long, truncating to prevent API errors...")
                # Aggressively truncate
                words = prompt.split()
                truncated_prompt = ' '.join(words[:10000])
                prompt = truncated_prompt + "\n\nGenerate the complete podcast script based on the content above."
                estimated_prompt_tokens = 13000
            
            # Set response token limits
            if model == "gpt-4":
                max_response_tokens = min(3000, 8192 - estimated_prompt_tokens - 100)
            else:  # gpt-3.5-turbo
                max_response_tokens = min(3500, 4096 - estimated_prompt_tokens - 100)
            
            if max_response_tokens < 500:
                print("⚠️  Prompt too long, switching to gpt-3.5-turbo-16k...")
                model = "gpt-3.5-turbo-16k"
                max_response_tokens = min(4000, 16384 - estimated_prompt_tokens - 100)
            
            print(f"🤖 Model: {model}, Max response tokens: {max_response_tokens}")
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert podcast script writer. Create engaging, comprehensive scripts ready for audio recording. Write naturally for speech, include interesting details, and maintain the target length."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_response_tokens,
                temperature=0.7,
                top_p=0.9
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Generated {len(result.split())} words")
            return result
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ OpenAI API error: {error_str}")
            
            # Provide specific error guidance
            if "authentication" in error_str.lower():
                print("💡 Check your API key at: https://platform.openai.com/api-keys")
            elif "quota" in error_str.lower() or "billing" in error_str.lower():
                print("💡 Check your billing at: https://platform.openai.com/account/billing")
            elif "rate_limit" in error_str.lower():
                print("💡 Rate limit hit, trying again in 5 seconds...")
                import time
                time.sleep(5)
                # One retry
                try:
                    return self._generate_with_openai(prompt, "gpt-3.5-turbo")
                except:
                    pass
            elif "context_length" in error_str.lower():
                print("💡 Content too long, try with a shorter article or use chapter editing")
            
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