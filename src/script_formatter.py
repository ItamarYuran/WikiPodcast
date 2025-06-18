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
            "target_duration": 600,  # 10 minutes
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
Length: Aim for about 10 minutes of speaking time
"""
        },
        
        "academic": {
            "name": "Academic/Scholarly",
            "description": "Professional, in-depth analysis with scholarly approach",
            "target_duration": 900,  # 15 minutes
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
Length: Aim for about 15 minutes of comprehensive coverage
"""
        },
        
        "storytelling": {
            "name": "Storytelling/Narrative",
            "description": "Dramatic narrative approach with story arc",
            "target_duration": 720,  # 12 minutes
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
Length: Aim for about 12 minutes of narrative storytelling
"""
        },
        
        "news_report": {
            "name": "News Report",
            "description": "Clear, factual reporting style like NPR or BBC",
            "target_duration": 480,  # 8 minutes
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
Length: Aim for about 8 minutes of efficient information delivery
"""
        },
        
        "documentary": {
            "name": "Documentary Style",
            "description": "Thoughtful, investigative approach with deep dives",
            "target_duration": 1200,  # 20 minutes
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
Length: Aim for about 20 minutes of in-depth exploration
"""
        },
        
        "comedy": {
            "name": "Comedy/Humorous",
            "description": "Entertaining and funny while still informative",
            "target_duration": 540,  # 9 minutes
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
Length: Aim for about 9 minutes of educational entertainment
"""
        },
        
        "interview": {
            "name": "Interview Format", 
            "description": "Q&A style with imaginary expert or historical figure",
            "target_duration": 780,  # 13 minutes
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
Length: Aim for about 13 minutes of engaging dialogue
"""
        },
        
        "kids_educational": {
            "name": "Educational Kids",
            "description": "Simple, enthusiastic content for children",
            "target_duration": 360,  # 6 minutes
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
Length: Aim for about 6 minutes to match attention spans
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
        # Load environment variables
        load_dotenv('config/api_keys.env')
        
        # Use provided key or get from environment
        if openai_api_key:
            self.openai_api_key = openai_api_key
        else:
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            
        if not self.openai_api_key:
            raise ValueError(
                "OpenAI API key not found. Either:\n"
                "1. Pass it directly: PodcastScriptFormatter('your-key-here')\n"
                "2. Set OPENAI_API_KEY in config/api_keys.env file\n"
                "3. Set OPENAI_API_KEY environment variable"
            )
        
        # Set up cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different styles
        for style_name in PodcastStyles.STYLES.keys():
            (self.cache_dir / style_name).mkdir(exist_ok=True)
        
        print(f"✅ OpenAI API key loaded")
        print(f"✅ Script cache directory: {self.cache_dir.absolute()}")
    
    def format_article_to_script(self, 
                                article: WikipediaArticle,
                                style: str = "conversational",
                                custom_instructions: str = None,
                                target_duration: int = None,
                                model: str = "gpt-4") -> Optional[PodcastScript]:
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
            print(f"Generating {style} script for: {article.title}")
            
            # Prepare the content for processing
            processed_content, recommended_model = self._prepare_content(article, model)
            
            # Use the recommended model if it's different
            if recommended_model != model:
                print(f"🔄 Using {recommended_model} instead of {model} for optimal results")
                model = recommended_model
            
            # Build the prompt
            prompt = self._build_prompt(
                article, 
                style_config, 
                processed_content, 
                custom_instructions,
                target_duration
            )
            
            # Generate script using OpenAI
            script_content = self._generate_with_openai(prompt, model)
            
            if not script_content:
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
            
            print(f"✓ Generated script: {podcast_script.word_count} words, ~{podcast_script.estimated_duration//60} minutes")
            
            return podcast_script
            
        except Exception as e:
            print(f"Error generating script for '{article.title}': {str(e)}")
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
            print(f"\nProcessing article {i}/{len(articles)}: {article.title}")
            
            script = self.format_article_to_script(
                article, 
                style, 
                custom_instructions
            )
            
            if script:
                scripts.append(script)
            
            # Rate limiting for API calls
            if i < len(articles):  # Don't sleep after the last one
                print("Waiting 2 seconds for API rate limiting...")
                import time
                time.sleep(2)
        
        print(f"\n✓ Generated {len(scripts)} scripts out of {len(articles)} articles")
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
    
    # Private helper methods
    
    def _prepare_content(self, article: WikipediaArticle, model: str = "gpt-4") -> Tuple[str, str]:
        """Prepare article content for script generation
        
        Returns:
            Tuple of (content, recommended_model)
        """
        # Start with the summary for context
        content_parts = []
        
        if article.summary:
            content_parts.append(f"SUMMARY: {article.summary}")
        
        # Add main content with some cleaning
        main_content = article.content
        
        # Remove excessive whitespace and clean up formatting
        main_content = re.sub(r'\n\s*\n\s*\n', '\n\n', main_content)
        main_content = re.sub(r'\s+', ' ', main_content)
        
        # Estimate token count BEFORE adding metadata (more accurate)
        words = main_content.split()
        estimated_content_tokens = len(words) * 1.33
        
        print(f"📊 Article analysis: {len(words)} words, ~{estimated_content_tokens:.0f} content tokens")
        
        # Determine strategy based on content length
        recommended_model = model
        
        if estimated_content_tokens > 12000:  # Lowered threshold for safety
            print(f"⚠️  Article is extremely long (~{estimated_content_tokens:.0f} tokens)")
            print("🎯 Creating condensed version focusing on most important sections")
            
            # Intelligent content selection - take key sections
            sentences = main_content.split('. ')
            
            # Take first 30% (introduction and early content)
            first_section = '. '.join(sentences[:int(len(sentences) * 0.3)])
            
            # Take some middle content (skip some middle, take key parts)
            middle_start = int(len(sentences) * 0.4)
            middle_end = int(len(sentences) * 0.7)
            middle_section = '. '.join(sentences[middle_start:middle_end:3])  # Every 3rd sentence
            
            # Take last 20% (recent developments, conclusion)
            last_section = '. '.join(sentences[int(len(sentences) * 0.8):])
            
            # Combine sections
            condensed_content = f"{first_section}.\n\n[... condensed middle sections covering key developments ...]\n\n{middle_section}.\n\n[... recent developments ...]\n\n{last_section}."
            
            # Ensure it's within limits - target 6000 words max
            condensed_words = condensed_content.split()
            if len(condensed_words) > 6000:
                condensed_content = ' '.join(condensed_words[:6000])
                # Try to end at a sentence
                last_period = condensed_content.rfind('.')
                if last_period > len(condensed_content) * 0.9:
                    condensed_content = condensed_content[:last_period + 1]
                condensed_content += "..."
            
            main_content = condensed_content + "\n\n[Note: This is an intelligently condensed version focusing on the most important sections of this extensive article]"
            recommended_model = "gpt-3.5-turbo"
            print(f"✅ Condensed to {len(main_content.split())} words")
            
        elif model == "gpt-4" and estimated_content_tokens > 6000:
            print(f"⚠️  Content is long (~{estimated_content_tokens:.0f} tokens), switching to GPT-3.5-turbo for better handling")
            recommended_model = "gpt-3.5-turbo"
            
        elif model == "gpt-3.5-turbo" and estimated_content_tokens > 9000:
            print(f"⚠️  Content is very long (~{estimated_content_tokens:.0f} tokens), creating focused version")
            # Smart truncation for 3.5-turbo
            target_words = 6000
            if len(words) > target_words:
                # Take first 70% and last 30%
                first_part = words[:int(target_words * 0.7)]
                last_part = words[-int(target_words * 0.3):]
                
                main_content = ' '.join(first_part) + "\n\n[... middle sections condensed ...]\n\n" + ' '.join(last_part)
                main_content += "\n\n[Note: This is a focused version of the full article, emphasizing key information]"
        
        content_parts.append(f"MAIN CONTENT: {main_content}")
        
        # Add metadata that might be useful
        if article.categories:
            content_parts.append(f"CATEGORIES: {', '.join(article.categories[:10])}")
        
        if article.page_views > 0:
            content_parts.append(f"RECENT POPULARITY: {article.page_views:,} views in past 7 days")
        
        full_content = '\n\n'.join(content_parts)
        
        return full_content, recommended_model
    
    def _build_prompt(self, 
                     article: WikipediaArticle,
                     style_config: Dict,
                     content: str,
                     custom_instructions: str = None,
                     target_duration: int = None) -> str:
        """Build the prompt for OpenAI"""
        
        duration = target_duration or style_config['target_duration']
        duration_minutes = duration // 60
        
        prompt_parts = [
            f"You are an expert podcast script writer. Your task is to transform the following Wikipedia article about '{article.title}' into an engaging podcast script.",
            "",
            style_config['prompt_template'].format(topic=article.title),
            "",
            f"TARGET DURATION: {duration_minutes} minutes",
            f"ESTIMATED WORDS NEEDED: {duration // 4} words (assuming 4 words per second)",
            "",
            "ADDITIONAL REQUIREMENTS:",
            "- Include specific timestamps or segment markers",
            "- Write in a way that sounds natural when spoken aloud", 
            "- Include pronunciation guides for difficult names/terms in [brackets]",
            "- Add natural pause indicators with [...] where appropriate",
            "- Make sure the content flows smoothly when read as audio",
            "",
        ]
        
        if custom_instructions:
            prompt_parts.extend([
                "CUSTOM INSTRUCTIONS:",
                custom_instructions,
                "",
            ])
        
        prompt_parts.extend([
            "SOURCE MATERIAL:",
            "================",
            content,
            "",
            "Please generate the complete podcast script now:"
        ])
        
        return '\n'.join(prompt_parts)
    
    def _generate_with_openai(self, prompt: str, model: str = "gpt-4") -> Optional[str]:
        """Generate script content using OpenAI"""
        try:
            from openai import OpenAI
            
            # Initialize client with API key
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert podcast script writer who creates engaging, natural-sounding audio content from written material. Always write scripts that sound great when spoken aloud."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,  # Adjust based on target length
                temperature=0.7,  # Some creativity but not too random
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
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
                
            print(f"✓ Script saved: {filename}")
            
        except Exception as e:
            print(f"Warning: Could not save script to cache: {e}")


# Example usage and testing
def example_usage():
    """Example of how to use the PodcastScriptFormatter"""
    
    print("=== Podcast Script Formatter ===")
    
    try:
        # Initialize formatter (will auto-load API key from environment)
        formatter = PodcastScriptFormatter()
        
        # Show available styles
        print("\nAvailable podcast styles:")
        styles = formatter.get_available_styles()
        
        for style_key, info in styles.items():
            print(f"- {info['name']}: {info['description']}")
            print(f"  Duration: {info['target_duration']}, Voice: {info['voice_style']}")
        
        print(f"\nScript cache directory: {formatter.cache_dir}")
        
        # Show any cached scripts
        cached = formatter.list_cached_scripts()
        if cached:
            print(f"\nFound {len(cached)} cached scripts:")
            for script in cached[:5]:  # Show first 5
                print(f"- {script['title']} ({script['style']}) - {script['duration']}")
        
        # Example of how you'd use it with a real article:
        print("\nExample usage with real article:")
        print("""
        # Fetch an article first
        from content_fetcher import WikipediaContentFetcher
        fetcher = WikipediaContentFetcher()
        article = fetcher.fetch_article("Artificial Intelligence")
        
        # Generate different style scripts (API key loaded automatically)
        formatter = PodcastScriptFormatter()
        
        # Conversational style
        script1 = formatter.format_article_to_script(article, "conversational")
        
        # Comedy style  
        script2 = formatter.format_article_to_script(article, "comedy")
        
        # With custom instructions
        custom = "Focus on the ethical implications and make connections to current events"
        script3 = formatter.format_article_to_script(article, "documentary", custom)
        
        # Batch generate for multiple articles
        trending = fetcher.get_trending_articles(5)
        scripts = formatter.batch_generate_scripts(trending, "news_report")
        """)
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        print("\nTo fix this:")
        print("1. Create a file: config/api_keys.env")
        print("2. Add your OpenAI API key: OPENAI_API_KEY=sk-your-key-here")
        print("3. Make sure you have python-dotenv installed: pip install python-dotenv")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def create_env_file_template():
    """Helper function to create the API keys environment file template"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    env_file = config_dir / "api_keys.env"
    
    if not env_file.exists():
        template_content = """# API Keys for Wikipedia Podcast Automation
# Replace 'your-key-here' with your actual API keys

# OpenAI API Key (required for script generation)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-key-here

# ElevenLabs API Key (for future TTS integration)
# Get from: https://elevenlabs.io/
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Other future integrations
BUZZSPROUT_API_KEY=your-buzzsprout-key-here
"""
        
        with open(env_file, 'w') as f:
            f.write(template_content)
        
        print(f"✓ Created template: {env_file.absolute()}")
        print("Please edit this file and add your actual API keys!")
        return env_file
    else:
        print(f"✓ Config file already exists: {env_file.absolute()}")
        return env_file


if __name__ == "__main__":
    # Create environment file template if it doesn't exist
    create_env_file_template()
    print()
    
    # Run example usage
    example_usage()