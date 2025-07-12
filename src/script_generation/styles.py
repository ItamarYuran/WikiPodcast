"""
Style Management System

This module handles all script styles and templates.
Separated from the main generator for better organization and extensibility.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class StyleCategory(Enum):
    """Categories of script styles"""
    CONVERSATIONAL = "conversational"
    EDUCATIONAL = "educational"
    NARRATIVE = "narrative"
    PROFESSIONAL = "professional"


@dataclass
class StyleTemplate:
    """Template for a script style"""
    name: str
    category: StyleCategory
    description: str
    target_duration: int  # in seconds
    voice_style: str
    template_text: str
    parameters: Dict[str, Any]
    
    def get_formatted_template(self, **kwargs) -> str:
        """Get template with parameters filled in"""
        return self.template_text.format(**kwargs)


class StyleManager:
    """
    Manages all available script styles and templates.
    Provides a clean interface for style configuration.
    """
    
    def __init__(self):
        self.styles = {}
        self._initialize_default_styles()
    
    def _initialize_default_styles(self):
        """Initialize default style templates"""
        
        # Conversational Style
        conversational_template = """
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
        
        self.styles["conversational"] = StyleTemplate(
            name="conversational",
            category=StyleCategory.CONVERSATIONAL,
            description="Friendly, informative conversation with compelling storytelling elements",
            target_duration=900,  # 15 minutes
            voice_style="conversational",
            template_text=conversational_template,
            parameters={
                "storytelling_ratio": 0.6,
                "information_ratio": 0.4,
                "engagement_techniques": ["rhetorical_questions", "personal_asides", "analogies"],
                "tone_keywords": ["friendly", "curious", "engaging", "informative"]
            }
        )
        
        # Educational Style
        educational_template = """
Create an educational podcast script about {topic} using the DUAL INSTRUCTION SYSTEM.

Style Guidelines:
- Structure information clearly with logical progression
- Use precise, academic language while remaining accessible
- Include definitions, examples, and explanations
- Build knowledge systematically from basics to advanced concepts
- Use teaching techniques like repetition and summarization
- Include learning objectives and key takeaways
- Make complex topics understandable through clear explanations

Structure with DUAL INSTRUCTIONS:
1. [SET_SCENE] Learning Objectives: What will the audience learn + [SHORT_PAUSE]
2. [BACKGROUND_INFO] Foundation: Essential background knowledge + [MEDIUM_PAUSE]
3. [EXPLAIN_CONCEPT] Core Content: Main educational content with [EMPHASIS] on key terms
4. [EXAMPLE_NEEDED] Practical Examples: Real-world applications + [SECTION_BREAK]
5. [MAIN_POINT] Key Takeaways: Essential points to remember + [LONG_PAUSE]
6. [CONNECT_TO_AUDIENCE] Next Steps: How to apply this knowledge

Content Focus:
- [EXPLAIN_CONCEPT] Clear, step-by-step explanations with [SLOW] technical terms
- [EXAMPLE_NEEDED] Concrete examples and case studies with [EMPHASIS]
- [BACKGROUND_INFO] Necessary context and prerequisites
- [MAIN_POINT] Important concepts and principles
- [TRANSITION] Logical connections between topics

Educational Techniques:
- Define technical terms clearly with [SLOW] pronunciation
- Use [EMPHASIS] for key concepts and vocabulary
- Include [MEDIUM_PAUSE] for processing complex information
- End sections with [SECTION_BREAK] for mental organization
- Use [PARAGRAPH_BREAK] for natural learning rhythm

Tone: Authoritative, clear, instructional, comprehensive
Balance: 70% direct instruction, 30% examples and applications
Length: Create comprehensive educational content using both instruction systems
"""
        
        self.styles["educational"] = StyleTemplate(
            name="educational",
            category=StyleCategory.EDUCATIONAL,
            description="Structured, informative teaching approach with clear explanations",
            target_duration=1200,  # 20 minutes
            voice_style="educational",
            template_text=educational_template,
            parameters={
                "instruction_ratio": 0.7,
                "example_ratio": 0.3,
                "teaching_techniques": ["definitions", "examples", "repetition", "summarization"],
                "tone_keywords": ["authoritative", "clear", "instructional", "comprehensive"]
            }
        )
        
        # Narrative Style
        narrative_template = """
Create a narrative podcast script about {topic} using the DUAL INSTRUCTION SYSTEM.

Style Guidelines:
- Tell the story chronologically with dramatic structure
- Use narrative techniques like foreshadowing and character development
- Build tension and create emotional moments
- Include vivid descriptions and scene-setting
- Use a storyteller's voice with dramatic pacing
- Focus on the human elements and personal stories
- Create immersive experiences through detailed storytelling

Structure with DUAL INSTRUCTIONS:
1. [SET_SCENE] Opening Scene: Set the stage dramatically + [SHORT_PAUSE]
2. [STORY_TIME] Rising Action: Build the story with [BUILD_TENSION]
3. [BACKGROUND_INFO] Character Development: Introduce key figures + [MEDIUM_PAUSE]
4. [BUILD_TENSION] Climax: The crucial moment with [EMPHASIS] and [LONG_PAUSE]
5. [STORY_TIME] Resolution: How it all ends + [SECTION_BREAK]
6. [CONNECT_TO_AUDIENCE] Reflection: What it means today

Content Focus:
- [STORY_TIME] Chronological narrative with dramatic pacing
- [BUILD_TENSION] Suspenseful moments with strategic pauses
- [SET_SCENE] Vivid descriptions and atmosphere
- [BACKGROUND_INFO] Character backgrounds and motivations
- [EMPHASIS] Dramatic moments and turning points

Narrative Techniques:
- Use [SET_SCENE] for vivid scene descriptions
- Build [BUILD_TENSION] with foreshadowing and suspense
- [EMPHASIS] key dramatic moments and revelations
- [LONG_PAUSE] for emotional impact and reflection
- [STORY_TIME] for immersive storytelling sequences

Tone: Dramatic, immersive, emotional, captivating
Balance: 80% narrative storytelling, 20% factual information
Length: Create compelling narrative using both instruction systems
"""
        
        self.styles["narrative"] = StyleTemplate(
            name="narrative",
            category=StyleCategory.NARRATIVE,
            description="Dramatic storytelling approach with immersive narrative techniques",
            target_duration=1800,  # 30 minutes
            voice_style="dramatic",
            template_text=narrative_template,
            parameters={
                "narrative_ratio": 0.8,
                "factual_ratio": 0.2,
                "narrative_techniques": ["foreshadowing", "character_development", "scene_setting"],
                "tone_keywords": ["dramatic", "immersive", "emotional", "captivating"]
            }
        )
        
        # Professional Style
        professional_template = """
Create a professional podcast script about {topic} using the DUAL INSTRUCTION SYSTEM.

Style Guidelines:
- Use professional, business-appropriate language
- Focus on practical insights and actionable information
- Include expert perspectives and industry analysis
- Maintain formal tone while being accessible
- Emphasize data, trends, and professional implications
- Structure content for busy professionals
- Include strategic insights and practical applications

Structure with DUAL INSTRUCTIONS:
1. [SET_SCENE] Executive Summary: Key points upfront + [SHORT_PAUSE]
2. [BACKGROUND_INFO] Industry Context: Current landscape + [MEDIUM_PAUSE]
3. [MAIN_POINT] Core Analysis: Detailed examination with [EMPHASIS] on insights
4. [EXAMPLE_NEEDED] Case Studies: Real-world applications + [SECTION_BREAK]
5. [CONNECT_TO_AUDIENCE] Strategic Implications: What this means for professionals
6. [MAIN_POINT] Action Items: Next steps and recommendations + [LONG_PAUSE]

Content Focus:
- [MAIN_POINT] Key insights and professional implications
- [EXAMPLE_NEEDED] Industry case studies and best practices
- [BACKGROUND_INFO] Market context and competitive analysis
- [EMPHASIS] Critical data points and trends
- [CONNECT_TO_AUDIENCE] Practical applications for professionals

Professional Techniques:
- Use [EMPHASIS] for key metrics and important data
- Include [MEDIUM_PAUSE] for processing complex analysis
- [SLOW] technical terms and industry jargon
- [SECTION_BREAK] between major topic areas
- [PARAGRAPH_BREAK] for structured information flow

Tone: Professional, analytical, authoritative, practical
Balance: 60% analysis and insights, 40% practical applications
Length: Create comprehensive professional content using both instruction systems
"""
        
        self.styles["professional"] = StyleTemplate(
            name="professional",
            category=StyleCategory.PROFESSIONAL,
            description="Business-focused approach with expert analysis and practical insights",
            target_duration=900,  # 15 minutes
            voice_style="professional",
            template_text=professional_template,
            parameters={
                "analysis_ratio": 0.6,
                "application_ratio": 0.4,
                "professional_techniques": ["data_analysis", "case_studies", "strategic_insights"],
                "tone_keywords": ["professional", "analytical", "authoritative", "practical"]
            }
        )
    
    def get_style_config(self, style_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific style"""
        if style_name not in self.styles:
            return None
        
        style = self.styles[style_name]
        return {
            "name": style.name,
            "description": style.description,
            "target_duration": style.target_duration,
            "voice_style": style.voice_style,
            "parameters": style.parameters
        }
    
    def get_style_template(self, style_name: str) -> Optional[str]:
        """Get template text for a specific style"""
        if style_name not in self.styles:
            return None
        
        return self.styles[style_name].template_text
    
    def get_available_styles(self) -> Dict[str, Dict[str, Any]]:
        """Get all available styles with their information"""
        return {
            name: {
                "name": style.name,
                "category": style.category.value,
                "description": style.description,
                "target_duration": f"{style.target_duration//60} minutes",
                "voice_style": style.voice_style,
                "parameters": style.parameters
            }
            for name, style in self.styles.items()
        }
    
    def is_valid_style(self, style_name: str) -> bool:
        """Check if a style name is valid"""
        return style_name in self.styles
    
    def add_custom_style(self, style: StyleTemplate):
        """Add a custom style template"""
        self.styles[style.name] = style
        print(f"✅ Added custom style: {style.name}")
    
    def get_styles_by_category(self, category: StyleCategory) -> Dict[str, StyleTemplate]:
        """Get all styles in a specific category"""
        return {
            name: style for name, style in self.styles.items()
            if style.category == category
        }
    
    def get_style_recommendations(self, 
                                article_length: int, 
                                target_duration: int,
                                content_type: str = "general") -> List[str]:
        """Get style recommendations based on content characteristics"""
        recommendations = []
        
        # Short content - conversational works well
        if article_length < 1000:
            recommendations.append("conversational")
        
        # Medium content - educational or professional
        elif article_length < 3000:
            recommendations.extend(["educational", "professional"])
        
        # Long content - narrative works well
        else:
            recommendations.append("narrative")
        
        # Duration-based recommendations
        if target_duration < 600:  # < 10 minutes
            recommendations.append("conversational")
        elif target_duration > 1800:  # > 30 minutes
            recommendations.append("narrative")
        
        # Content type recommendations
        if content_type in ["science", "technology", "education"]:
            recommendations.append("educational")
        elif content_type in ["history", "biography", "story"]:
            recommendations.append("narrative")
        elif content_type in ["business", "finance", "industry"]:
            recommendations.append("professional")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:3]  # Return top 3 recommendations