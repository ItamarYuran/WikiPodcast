"""
TTS Processing Module
Handles enhanced text-to-speech processing with SSML support
"""

import re
from typing import Dict, List, Tuple
from google.cloud import texttospeech

class SSMLProcessor:
    """Processes TTS instructions and converts them to SSML or audio cues"""
    
    def __init__(self):
        self.tts_instructions = {
            # Pause instructions
            'SHORT_PAUSE': '<break time="0.5s"/>',
            'MEDIUM_PAUSE': '<break time="1.0s"/>',
            'LONG_PAUSE': '<break time="1.5s"/>',
            'PARAGRAPH_BREAK': '<break time="0.8s"/>',
            'SECTION_BREAK': '<break time="1.2s"/>',
            'BREATH': '<break time="0.3s"/>',
            
            # Emphasis instructions
            'EMPHASIS': '<emphasis level="strong">',
            'EMPHASIS_END': '</emphasis>',
            'SLOW': '<prosody rate="slow">',
            'SLOW_END': '</prosody>',
            'FASTER': '<prosody rate="fast">',
            'FASTER_END': '</prosody>',
        }
        
        # Common pronunciation fixes
        self.pronunciation_fixes = {
            r'\binto\b': 'in-to',  # Fix "into" pronunciation
            r'\bread\b': 'red',    # Past tense of read
            r'\bAI\b': 'artificial intelligence',
            r'\bUS\b': 'United States',
            r'\bDr\.\s*': 'Doctor ',
            r'\bMr\.\s*': 'Mister ',
            r'\bMs\.\s*': 'Miss ',
            r'\bCEO\b': 'Chief Executive Officer',
            r'\bCTO\b': 'Chief Technology Officer',
            r'\bAPI\b': 'Application Programming Interface',
            r'\bURL\b': 'U-R-L',
            r'\bHTML\b': 'H-T-M-L',
            r'\bCSS\b': 'C-S-S',
            r'\bJSON\b': 'Jason', # Common pronunciation
            r'\bGPT\b': 'G-P-T',
            r'\bNASA\b': 'N-A-S-A',
            r'\bFBI\b': 'F-B-I',
            r'\bCIA\b': 'C-I-A',
        }
        
        # Number pronunciation
        self.year_pattern = r'\b(19|20)\d{2}\b'
        self.number_words = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
            '10': 'ten', '11': 'eleven', '12': 'twelve', '13': 'thirteen',
            '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
            '18': 'eighteen', '19': 'nineteen', '20': 'twenty'
        }
    
    def process_script_for_tts(self, script_text: str, use_ssml: bool = True) -> str:
        """
        Process script text for optimal TTS output
        
        Args:
            script_text: Raw script text with TTS instructions
            use_ssml: Whether to use SSML (Google Cloud supports this)
            
        Returns:
            Processed text ready for TTS
        """
        text = script_text
        
        # Step 1: Apply pronunciation fixes
        text = self._fix_pronunciations(text)
        
        # Step 2: Convert numbers and years
        text = self._convert_numbers(text)
        
        # Step 3: Process TTS instructions
        if use_ssml:
            text = self._convert_to_ssml(text)
        else:
            text = self._convert_to_pauses(text)
        
        # Step 4: Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _fix_pronunciations(self, text: str) -> str:
        """Apply pronunciation fixes"""
        for pattern, replacement in self.pronunciation_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def _convert_numbers(self, text: str) -> str:
        """Convert years and numbers to words"""
        # Convert years (1900-2099)
        def replace_year(match):
            year = match.group()
            if len(year) == 4:
                try:
                    y = int(year)
                    if 1900 <= y <= 2099:
                        if y >= 2000:
                            # 2024 → "twenty twenty-four"
                            first_part = "twenty"
                            remainder = y % 100
                            if remainder == 0:
                                return first_part
                            elif remainder < 10:
                                return f"{first_part} oh-{self.number_words.get(str(remainder), str(remainder))}"
                            elif remainder <= 20:
                                return f"{first_part} {self.number_words.get(str(remainder), str(remainder))}"
                            else:
                                tens = remainder // 10
                                ones = remainder % 10
                                tens_word = {2: 'twenty', 3: 'thirty', 4: 'forty', 5: 'fifty', 
                                           6: 'sixty', 7: 'seventy', 8: 'eighty', 9: 'ninety'}.get(tens, str(tens))
                                if ones == 0:
                                    return f"{first_part} {tens_word}"
                                else:
                                    return f"{first_part} {tens_word}-{self.number_words.get(str(ones), str(ones))}"
                        else:
                            # 1995 → "nineteen ninety-five"
                            remainder = y % 100
                            if remainder <= 20:
                                return f"nineteen {self.number_words.get(str(remainder), str(remainder))}"
                            else:
                                tens = remainder // 10
                                ones = remainder % 10
                                tens_word = {2: 'twenty', 3: 'thirty', 4: 'forty', 5: 'fifty', 
                                           6: 'sixty', 7: 'seventy', 8: 'eighty', 9: 'ninety'}.get(tens, str(tens))
                                if ones == 0:
                                    return f"nineteen {tens_word}"
                                else:
                                    return f"nineteen {tens_word}-{self.number_words.get(str(ones), str(ones))}"
                except ValueError:
                    pass
            return year
        
        text = re.sub(self.year_pattern, replace_year, text)
        
        # Convert simple numbers (1-20)
        for num, word in self.number_words.items():
            text = re.sub(rf'\b{num}\b', word, text)
        
        return text
    
    def _convert_to_ssml(self, text: str) -> str:
        """Convert TTS instructions to SSML"""
        # Handle paired instructions (emphasis, slow, etc.)
        paired_instructions = ['EMPHASIS', 'SLOW', 'FASTER']
        
        for instruction in paired_instructions:
            # Find all instances of the instruction with closing tags
            pattern = rf'\[{instruction}\](.*?)\[/{instruction}\]'
            start_tag = self.tts_instructions[instruction]
            end_tag = self.tts_instructions[f'{instruction}_END']
            
            text = re.sub(pattern, rf'{start_tag}\1{end_tag}', text, flags=re.DOTALL)
            
            # Handle unclosed instructions (auto-close at end of sentence)
            pattern = rf'\[{instruction}\](.*?)(\.|!|\?)'
            replacement = rf'{start_tag}\1{end_tag}\2'
            text = re.sub(pattern, replacement, text)
        
        # Handle simple pause instructions
        for instruction, ssml_tag in self.tts_instructions.items():
            if instruction not in paired_instructions and not instruction.endswith('_END'):
                text = text.replace(f'[{instruction}]', ssml_tag)
        
        # Wrap in SSML speak tag if not already wrapped
        if not text.strip().startswith('<speak>'):
            text = f'<speak>{text}</speak>'
        
        return text
    
    def _convert_to_pauses(self, text: str) -> str:
        """Convert TTS instructions to natural pauses (for non-SSML TTS)"""
        # Replace instructions with appropriate punctuation/spacing
        replacements = {
            '[SHORT_PAUSE]': ', ',
            '[MEDIUM_PAUSE]': '. ',
            '[LONG_PAUSE]': '... ',
            '[PARAGRAPH_BREAK]': '.\n\n',
            '[SECTION_BREAK]': '.\n\n',
            '[BREATH]': ', ',
            '[EMPHASIS]': '',
            '[/EMPHASIS]': '',
            '[SLOW]': '',
            '[/SLOW]': '',
            '[FASTER]': '',
            '[/FASTER]': '',
        }
        
        for instruction, replacement in replacements.items():
            text = text.replace(instruction, replacement)
        
        return text


# TTS Enhancement Instructions for Script Generation
TTS_ENHANCEMENT_INSTRUCTIONS = """
IMPORTANT TTS AUDIO INSTRUCTIONS:
When writing the podcast script, include these specific formatting instructions for optimal text-to-speech conversion:

1. PRONUNCIATION GUIDANCE:
   - Use phonetic spelling for difficult words: "artificial intelligence" not "AI"
   - Spell out abbreviations: "United States" not "US", "Doctor" not "Dr."
   - Use full words for numbers: "twenty twenty-four" not "2024"

2. NATURAL PAUSES & RHYTHM:
   - Add [SHORT_PAUSE] after important points for emphasis
   - Add [MEDIUM_PAUSE] between major sections or topics
   - Add [LONG_PAUSE] before conclusion or major transitions
   - Use [BREATH] for natural breathing spots in long sentences

3. PRONUNCIATION CORRECTIONS:
   - For words that TTS mispronounces, use alternative spelling:
     * "into" → "in-to" (if pronounced wrong)
     * "read" (past tense) → "red" 
     * "live" (verb) → "liv" vs "live" (adjective) → "lye-v"

4. EMPHASIS & TONE:
   - Use [EMPHASIS] before words that need stress: [EMPHASIS]important term[/EMPHASIS]
   - Use [SLOW] for important technical terms: [SLOW]machine learning[/SLOW]
   - Use [FASTER] for excitement or energy

5. PARAGRAPH STRUCTURE:
   - End each paragraph with [PARAGRAPH_BREAK]
   - Start new sections with [SECTION_BREAK]

Example formatting:
"Welcome to today's podcast about artificial intelligence. [SHORT_PAUSE] 
We'll explore how AI systems work in twenty twenty-four. [MEDIUM_PAUSE]

[SECTION_BREAK] First, let's understand machine learning. [EMPHASIS]Machine learning[/EMPHASIS] [SLOW]is a subset of artificial intelligence[/SLOW] [PARAGRAPH_BREAK]

The field has grown rapidly since two thousand and ten. [BREATH] Today, we see AI everywhere. [LONG_PAUSE]"

CRITICAL: These instructions are ONLY for audio generation. The actual script content should be engaging and informative for listeners.
"""