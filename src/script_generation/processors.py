"""
Enhanced TTS Processing Module
Production-ready implementation with comprehensive error handling and voice optimization.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core import ProcessingResult, ProcessingStatus


class VoiceType(Enum):
    """TTS Voice types with different SSML capabilities"""
    JOURNEY = "journey"        # Plain text only
    NEURAL2 = "neural2"        # Perfect SSML required
    STANDARD = "standard"      # Forgiving SSML
    WAVENET = "wavenet"        # Legacy voices
    UNKNOWN = "unknown"        # Fallback


class InstructionType(Enum):
    """Types of instructions in scripts"""
    TTS = "tts"               # For TTS processing (converted to SSML)
    SCRIPT = "script"         # For writing guidance (removed before TTS)
    INVALID = "invalid"       # Malformed instructions


@dataclass
class ProcessingStats:
    """Statistics from script processing"""
    original_word_count: int
    processed_word_count: int
    instructions_removed: int
    instructions_converted: int
    ssml_tags_added: int
    issues_found: List[str]


@dataclass
class ValidationResult:
    """Result of script validation"""
    overall_score: float      # 0.0 to 1.0
    readability_score: float
    structure_score: float
    tts_compatibility_score: float
    issues: List[str]
    suggestions: List[str]


class TTSProcessor:
    """
    Enhanced TTS processor that converts script instructions to SSML
    and optimizes text for different voice types.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Instruction patterns for parsing
        self.instruction_patterns = {
            # TTS instructions (converted to SSML)
            'emphasis': re.compile(r'\[EMPHASIS\](.*?)\[/EMPHASIS\]', re.IGNORECASE | re.DOTALL),
            'strong_emphasis': re.compile(r'\[STRONG_EMPHASIS\](.*?)\[/STRONG_EMPHASIS\]', re.IGNORECASE | re.DOTALL),
            'pause_short': re.compile(r'\[SHORT_PAUSE\]', re.IGNORECASE),
            'pause_medium': re.compile(r'\[MEDIUM_PAUSE\]', re.IGNORECASE),
            'pause_long': re.compile(r'\[LONG_PAUSE\]', re.IGNORECASE),
            'pause_custom': re.compile(r'\[PAUSE:(\d+(?:\.\d+)?)s?\]', re.IGNORECASE),
            'speed_slow': re.compile(r'\[SLOW\](.*?)\[/SLOW\]', re.IGNORECASE | re.DOTALL),
            'speed_fast': re.compile(r'\[FAST\](.*?)\[/FAST\]', re.IGNORECASE | re.DOTALL),
            'pitch_high': re.compile(r'\[HIGH_PITCH\](.*?)\[/HIGH_PITCH\]', re.IGNORECASE | re.DOTALL),
            'pitch_low': re.compile(r'\[LOW_PITCH\](.*?)\[/LOW_PITCH\]', re.IGNORECASE | re.DOTALL),
            'volume_loud': re.compile(r'\[LOUD\](.*?)\[/LOUD\]', re.IGNORECASE | re.DOTALL),
            'volume_soft': re.compile(r'\[SOFT\](.*?)\[/SOFT\]', re.IGNORECASE | re.DOTALL),
            
            # Script instructions (removed before TTS)
            'transition': re.compile(r'\[TRANSITION\]', re.IGNORECASE),
            'set_scene': re.compile(r'\[SET_SCENE\]', re.IGNORECASE),
            'build_tension': re.compile(r'\[BUILD_TENSION\]', re.IGNORECASE),
            'add_humor': re.compile(r'\[ADD_HUMOR\]', re.IGNORECASE),
            'expert_insight': re.compile(r'\[EXPERT_INSIGHT\]', re.IGNORECASE),
            'call_to_action': re.compile(r'\[CALL_TO_ACTION\]', re.IGNORECASE),
            'narrator_note': re.compile(r'\[NARRATOR:(.*?)\]', re.IGNORECASE | re.DOTALL),
            'production_note': re.compile(r'\[PRODUCTION:(.*?)\]', re.IGNORECASE | re.DOTALL),
            'background_info': re.compile(r'\[BACKGROUND_INFO\]', re.IGNORECASE),
            'story_time': re.compile(r'\[STORY_TIME\]', re.IGNORECASE),
            'explain_concept': re.compile(r'\[EXPLAIN_CONCEPT\]', re.IGNORECASE),
            'connect_to_audience': re.compile(r'\[CONNECT_TO_AUDIENCE\]', re.IGNORECASE),
            'section_break': re.compile(r'\[SECTION_BREAK\]', re.IGNORECASE),
            'main_point': re.compile(r'\[MAIN_POINT\]', re.IGNORECASE),
            'paragraph_break': re.compile(r'\[PARAGRAPH_BREAK\]', re.IGNORECASE),
        }
        
        # Abbreviation expansions for better TTS
        self.abbreviations = {
            'AI': 'artificial intelligence',
            'API': 'A P I',
            'CPU': 'C P U',
            'GPU': 'G P U',
            'URL': 'U R L',
            'HTML': 'H T M L',
            'CSS': 'C S S',
            'SQL': 'sequel',
            'JSON': 'jay-son',
            'XML': 'X M L',
            'HTTP': 'H T T P',
            'HTTPS': 'H T T P S',
            'FTP': 'F T P',
            'SSH': 'S S H',
            'DNS': 'D N S',
            'TCP': 'T C P',
            'UDP': 'U D P',
            'WiFi': 'wi-fi',
            'Bluetooth': 'bluetooth',
            'USB': 'U S B',
            'SSD': 'solid state drive',
            'HDD': 'hard disk drive',
            'RAM': 'ram',
            'ROM': 'rom',
            'BIOS': 'buy-oss',
            'OS': 'operating system',
            'UI': 'user interface',
            'UX': 'user experience',
            'CEO': 'C E O',
            'CTO': 'C T O',
            'PhD': 'P H D',
            'NASA': 'nasa',
            'FBI': 'F B I',
            'CIA': 'C I A',
            'UK': 'United Kingdom',
            'US': 'United States',
            'USA': 'United States of America',
            'EU': 'European Union',
            'UN': 'United Nations',
            'UNESCO': 'unesco',
            'WHO': 'world health organization',
            'NATO': 'nato',
            'GDP': 'G D P',
            'CEO': 'chief executive officer',
            'vs': 'versus',
            'etc': 'etcetera',
            'i.e.': 'that is',
            'e.g.': 'for example',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Dr.': 'Doctor',
            'Prof.': 'Professor',
            'St.': 'Saint',
            'Ave.': 'Avenue',
            'Blvd.': 'Boulevard',
            'Rd.': 'Road',
            'Inc.': 'Incorporated',
            'Corp.': 'Corporation',
            'Ltd.': 'Limited'
        }
    
    def detect_voice_type(self, voice_name: str) -> VoiceType:
        """Detect voice type from voice name to determine SSML compatibility"""
        voice_lower = voice_name.lower()
        
        if 'journey' in voice_lower:
            return VoiceType.JOURNEY
        elif 'neural2' in voice_lower:
            return VoiceType.NEURAL2
        elif 'wavenet' in voice_lower:
            return VoiceType.WAVENET
        elif 'standard' in voice_lower:
            return VoiceType.STANDARD
        else:
            return VoiceType.UNKNOWN
    
    def process_script(self, script_text: str, voice_name: str = "neural2", use_ssml: Optional[bool] = None) -> ProcessingResult:
        """
        Process script for TTS with intelligent SSML handling based on voice type.
        
        Args:
            script_text: Raw script with instructions
            voice_name: TTS voice name to optimize for
            use_ssml: Override SSML usage (None = auto-detect)
        
        Returns:
            ProcessingResult with processed text and statistics
        """
        try:
            voice_type = self.detect_voice_type(voice_name)
            
            # Auto-detect SSML usage based on voice type
            if use_ssml is None:
                use_ssml = voice_type in [VoiceType.NEURAL2, VoiceType.STANDARD, VoiceType.WAVENET]
            
            self.logger.info(f"Processing script for {voice_type.value} voice, SSML: {use_ssml}")
            
            # Initialize statistics
            stats = ProcessingStats(
                original_word_count=len(script_text.split()),
                processed_word_count=0,
                instructions_removed=0,
                instructions_converted=0,
                ssml_tags_added=0,
                issues_found=[]
            )
            
            # Step 1: Remove script instructions (writing guidance)
            processed_text, removed_count = self._remove_script_instructions(script_text)
            stats.instructions_removed = removed_count
            
            # Step 2: Convert TTS instructions to SSML (if supported)
            if use_ssml:
                processed_text, converted_count, ssml_count = self._convert_tts_instructions_to_ssml(processed_text, voice_type)
                stats.instructions_converted = converted_count
                stats.ssml_tags_added = ssml_count
                
                # Wrap in SSML speak tags if not already present
                if not processed_text.strip().startswith('<speak>'):
                    processed_text = f'<speak>{processed_text}</speak>'
                    stats.ssml_tags_added += 1
            else:
                # For Journey voices, remove all TTS instructions
                processed_text, removed_tts = self._remove_tts_instructions(processed_text)
                stats.instructions_removed += removed_tts
            
            # Step 3: Normalize text for TTS
            processed_text = self._normalize_text_for_tts(processed_text)
            
            # Step 4: Validate SSML if using it
            if use_ssml:
                validation_issues = self._validate_ssml(processed_text, voice_type)
                stats.issues_found.extend(validation_issues)
            
            stats.processed_word_count = len(self._extract_text_from_ssml(processed_text).split())
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=processed_text,
                metadata={
                    'voice_type': voice_type.value,
                    'use_ssml': use_ssml,
                    'stats': stats,
                    'processing_method': 'enhanced_tts_processor'
                }
            )
            
        except Exception as e:
            self.logger.error(f"TTS processing failed: {str(e)}", exc_info=True)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=f"TTS processing error: {str(e)}",
                data=script_text  # Return original text as fallback
            )
    
    def _remove_script_instructions(self, text: str) -> Tuple[str, int]:
        """Remove script instructions that are for writing guidance only"""
        removed_count = 0
        processed = text
        
        script_instruction_patterns = [
            'transition', 'set_scene', 'build_tension', 'add_humor',
            'expert_insight', 'call_to_action', 'narrator_note', 'production_note',
            'background_info', 'story_time', 'explain_concept', 'connect_to_audience',
            'section_break', 'main_point', 'paragraph_break'
        ]
        
        for pattern_name in script_instruction_patterns:
            pattern = self.instruction_patterns[pattern_name]
            matches = pattern.findall(processed)
            removed_count += len(matches)
            processed = pattern.sub('', processed)
        
        return processed, removed_count
    
    def _convert_tts_instructions_to_ssml(self, text: str, voice_type: VoiceType) -> Tuple[str, int, int]:
        """Convert TTS instructions to SSML markup"""
        converted_count = 0
        ssml_tag_count = 0
        processed = text
        
        # Emphasis instructions
        if self.instruction_patterns['emphasis'].search(processed):
            processed = self.instruction_patterns['emphasis'].sub(r'<emphasis level="moderate">\1</emphasis>', processed)
            converted_count += len(self.instruction_patterns['emphasis'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['emphasis'].findall(text)) * 2
        
        if self.instruction_patterns['strong_emphasis'].search(processed):
            processed = self.instruction_patterns['strong_emphasis'].sub(r'<emphasis level="strong">\1</emphasis>', processed)
            converted_count += len(self.instruction_patterns['strong_emphasis'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['strong_emphasis'].findall(text)) * 2
        
        # Pause instructions
        processed = self.instruction_patterns['pause_short'].sub('<break time="0.5s"/>', processed)
        converted_count += len(self.instruction_patterns['pause_short'].findall(text))
        ssml_tag_count += len(self.instruction_patterns['pause_short'].findall(text))
        
        processed = self.instruction_patterns['pause_medium'].sub('<break time="1s"/>', processed)
        converted_count += len(self.instruction_patterns['pause_medium'].findall(text))
        ssml_tag_count += len(self.instruction_patterns['pause_medium'].findall(text))
        
        processed = self.instruction_patterns['pause_long'].sub('<break time="2s"/>', processed)
        converted_count += len(self.instruction_patterns['pause_long'].findall(text))
        ssml_tag_count += len(self.instruction_patterns['pause_long'].findall(text))
        
        # Custom pause durations
        def replace_custom_pause(match):
            duration = match.group(1)
            return f'<break time="{duration}s"/>'
        
        custom_pauses = self.instruction_patterns['pause_custom'].findall(text)
        processed = self.instruction_patterns['pause_custom'].sub(replace_custom_pause, processed)
        converted_count += len(custom_pauses)
        ssml_tag_count += len(custom_pauses)
        
        # Prosody instructions (speed, pitch, volume) - only for compatible voices
        if voice_type in [VoiceType.NEURAL2, VoiceType.WAVENET]:
            # Speed modifications
            processed = self.instruction_patterns['speed_slow'].sub(r'<prosody rate="slow">\1</prosody>', processed)
            converted_count += len(self.instruction_patterns['speed_slow'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['speed_slow'].findall(text)) * 2
            
            processed = self.instruction_patterns['speed_fast'].sub(r'<prosody rate="fast">\1</prosody>', processed)
            converted_count += len(self.instruction_patterns['speed_fast'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['speed_fast'].findall(text)) * 2
            
            # Pitch modifications
            processed = self.instruction_patterns['pitch_high'].sub(r'<prosody pitch="high">\1</prosody>', processed)
            converted_count += len(self.instruction_patterns['pitch_high'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['pitch_high'].findall(text)) * 2
            
            processed = self.instruction_patterns['pitch_low'].sub(r'<prosody pitch="low">\1</prosody>', processed)
            converted_count += len(self.instruction_patterns['pitch_low'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['pitch_low'].findall(text)) * 2
            
            # Volume modifications
            processed = self.instruction_patterns['volume_loud'].sub(r'<prosody volume="loud">\1</prosody>', processed)
            converted_count += len(self.instruction_patterns['volume_loud'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['volume_loud'].findall(text)) * 2
            
            processed = self.instruction_patterns['volume_soft'].sub(r'<prosody volume="soft">\1</prosody>', processed)
            converted_count += len(self.instruction_patterns['volume_soft'].findall(text))
            ssml_tag_count += len(self.instruction_patterns['volume_soft'].findall(text)) * 2
        
        return processed, converted_count, ssml_tag_count
    
    def _remove_tts_instructions(self, text: str) -> Tuple[str, int]:
        """Remove all TTS instructions for voices that don't support SSML"""
        removed_count = 0
        processed = text
        
        tts_instruction_patterns = [
            'emphasis', 'strong_emphasis', 'pause_short', 'pause_medium', 'pause_long', 'pause_custom',
            'speed_slow', 'speed_fast', 'pitch_high', 'pitch_low', 'volume_loud', 'volume_soft'
        ]
        
        for pattern_name in tts_instruction_patterns:
            pattern = self.instruction_patterns[pattern_name]
            matches = pattern.findall(processed)
            removed_count += len(matches)
            
            if pattern_name in ['emphasis', 'strong_emphasis', 'speed_slow', 'speed_fast', 
                              'pitch_high', 'pitch_low', 'volume_loud', 'volume_soft']:
                # Keep the content, remove the tags
                processed = pattern.sub(r'\1', processed)
            else:
                # Remove entirely (pauses)
                processed = pattern.sub('', processed)
        
        return processed, removed_count
    
    def _normalize_text_for_tts(self, text: str) -> str:
        """Normalize text for better TTS pronunciation"""
        processed = text
        
        # First, temporarily protect SSML tags
        ssml_tags = []
        tag_pattern = r'<[^>]+>'
        
        def protect_tag(match):
            tag = match.group(0)
            placeholder = f"__SSML_TAG_{len(ssml_tags)}__"
            ssml_tags.append(tag)
            return placeholder
        
        # Protect existing SSML tags
        processed = re.sub(tag_pattern, protect_tag, processed)
        
        # Expand abbreviations
        for abbrev, expansion in self.abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            processed = re.sub(pattern, expansion, processed, flags=re.IGNORECASE)
        
        # Convert years to spoken format
        processed = re.sub(r'\b(19|20)(\d{2})\b', r'\1 \2', processed)
        
        # Convert numbers with commas
        processed = re.sub(r'\b(\d{1,3}),(\d{3})\b', r'\1 thousand \2', processed)
        processed = re.sub(r'\b(\d{1,3}),(\d{3}),(\d{3})\b', r'\1 million \2 thousand \3', processed)
        
        # Convert common symbols (excluding < and > to protect SSML)
        symbol_replacements = {
            '&': ' and ',
            '%': ' percent',
            '$': ' dollars',
            '€': ' euros',
            '£': ' pounds',
            '#': ' number ',
            '@': ' at ',
            '+': ' plus ',
            '°': ' degrees',
            '™': ' trademark',
            '®': ' registered',
            '©': ' copyright'
            # Note: Removed '=' , '<', '>' to protect SSML
        }
        
        for symbol, replacement in symbol_replacements.items():
            processed = processed.replace(symbol, replacement)
        
        # Clean up extra whitespace
        processed = re.sub(r'\s+', ' ', processed)
        processed = processed.strip()
        
        # Restore protected SSML tags
        for i, tag in enumerate(ssml_tags):
            placeholder = f"__SSML_TAG_{i}__"
            processed = processed.replace(placeholder, tag)
        
        return processed
    
    def _validate_ssml(self, text: str, voice_type: VoiceType) -> List[str]:
        """Validate SSML markup for compatibility issues"""
        issues = []
        
        # Check for proper SSML structure
        if not text.strip().startswith('<speak>') or not text.strip().endswith('</speak>'):
            issues.append("SSML must be wrapped in <speak> tags")
        
        # Check for unclosed tags
        open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?>(?!</)', text)
        close_tags = re.findall(r'</(\w+)>', text)
        
        for tag in open_tags:
            if tag not in close_tags:
                issues.append(f"Unclosed SSML tag: <{tag}>")
        
        # Check for unsupported tags for specific voice types
        if voice_type == VoiceType.STANDARD:
            unsupported_in_standard = ['prosody']
            for tag in unsupported_in_standard:
                if f'<{tag}' in text:
                    issues.append(f"Tag <{tag}> may not be supported in standard voices")
        
        # Check for malformed break tags
        break_tags = re.findall(r'<break[^>]*>', text)
        for break_tag in break_tags:
            if 'time=' not in break_tag:
                issues.append(f"Break tag missing time attribute: {break_tag}")
        
        return issues
    
    def _extract_text_from_ssml(self, ssml_text: str) -> str:
        """Extract plain text from SSML for word counting"""
        # Remove all SSML tags
        text_only = re.sub(r'<[^>]+>', '', ssml_text)
        return text_only.strip()


class InstructionProcessor:
    """
    Processor for analyzing and categorizing instruction tags in scripts.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define instruction categories
        self.tts_instructions = {
            'EMPHASIS', 'STRONG_EMPHASIS', 'SHORT_PAUSE', 'MEDIUM_PAUSE', 'LONG_PAUSE',
            'SLOW', 'FAST', 'HIGH_PITCH', 'LOW_PITCH', 'LOUD', 'SOFT'
        }
        
        self.script_instructions = {
            'TRANSITION', 'SET_SCENE', 'BUILD_TENSION', 'ADD_HUMOR', 'EXPERT_INSIGHT',
            'CALL_TO_ACTION', 'NARRATOR', 'PRODUCTION'
        }
    
    def count_instructions(self, script_text: str) -> Dict[str, Any]:
        """
        Count and categorize all instructions in the script.
        
        Returns:
            Dictionary with instruction counts and analysis
        """
        try:
            # Find all instruction-like patterns
            instruction_pattern = re.compile(r'\[([^\]]+)\]', re.IGNORECASE)
            all_instructions = instruction_pattern.findall(script_text)
            
            # Categorize instructions
            tts_count = 0
            script_count = 0
            invalid_count = 0
            
            instruction_details = {
                'tts': [],
                'script': [],
                'invalid': []
            }
            
            for instruction in all_instructions:
                instruction_upper = instruction.upper()
                
                # Handle complex instructions (e.g., "NARRATOR: something")
                instruction_base = instruction_upper.split(':')[0].split()[0]
                
                if instruction_base in self.tts_instructions or instruction_upper.startswith(('PAUSE:', '/EMPHASIS', '/STRONG_EMPHASIS', '/SLOW', '/FAST')):
                    tts_count += 1
                    instruction_details['tts'].append(instruction)
                elif instruction_base in self.script_instructions or instruction_upper.startswith(('NARRATOR:', 'PRODUCTION:')):
                    script_count += 1
                    instruction_details['script'].append(instruction)
                else:
                    invalid_count += 1
                    instruction_details['invalid'].append(instruction)
            
            # Calculate instruction density
            total_words = len(script_text.split())
            instruction_density = (len(all_instructions) / total_words) * 100 if total_words > 0 else 0
            
            return {
                'total': len(all_instructions),
                'tts': tts_count,
                'script': script_count,
                'invalid': invalid_count,
                'density_percent': round(instruction_density, 2),
                'details': instruction_details,
                'analysis': {
                    'tts_heavy': tts_count > total_words * 0.05,  # More than 5% of words
                    'script_heavy': script_count > total_words * 0.03,  # More than 3% of words
                    'has_invalid': invalid_count > 0,
                    'well_structured': invalid_count == 0 and instruction_density < 10
                }
            }
            
        except Exception as e:
            self.logger.error(f"Instruction counting failed: {str(e)}", exc_info=True)
            return {
                'total': 0,
                'tts': 0,
                'script': 0,
                'invalid': 0,
                'density_percent': 0,
                'details': {'tts': [], 'script': [], 'invalid': []},
                'analysis': {'error': str(e)}
            }
    
    def suggest_instruction_improvements(self, script_text: str) -> List[str]:
        """Suggest improvements for instruction usage"""
        counts = self.count_instructions(script_text)
        suggestions = []
        
        if counts['analysis'].get('tts_heavy'):
            suggestions.append("Consider reducing TTS instructions - too many may affect natural flow")
        
        if counts['analysis'].get('script_heavy'):
            suggestions.append("Consider consolidating script instructions for cleaner generation")
        
        if counts['analysis'].get('has_invalid'):
            suggestions.append(f"Fix invalid instructions: {', '.join(counts['details']['invalid'][:5])}")
        
        if counts['density_percent'] > 15:
            suggestions.append("Very high instruction density - consider simplifying")
        
        return suggestions


class ScriptValidator:
    """
    Comprehensive script validator that assesses quality across multiple dimensions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.instruction_processor = InstructionProcessor()
    
    def validate_script(self, script_text: str) -> ProcessingResult:
        """
        Comprehensive script validation.
        
        Returns:
            ProcessingResult with ValidationResult data
        """
        try:
            # Calculate individual scores
            readability_score = self._calculate_readability_score(script_text)
            structure_score = self._calculate_structure_score(script_text)
            tts_compatibility_score = self._calculate_tts_compatibility_score(script_text)
            
            # Calculate overall score (weighted average)
            overall_score = (
                readability_score * 0.4 +
                structure_score * 0.3 +
                tts_compatibility_score * 0.3
            )
            
            # Collect issues and suggestions
            issues = []
            suggestions = []
            
            # Readability issues
            if readability_score < 0.6:
                issues.append("Low readability score - script may be hard to follow")
                suggestions.append("Use shorter sentences and simpler vocabulary")
            
            # Structure issues
            if structure_score < 0.7:
                issues.append("Poor structure - script lacks clear organization")
                suggestions.append("Add clear introduction, main content, and conclusion sections")
            
            # TTS compatibility issues
            if tts_compatibility_score < 0.8:
                issues.append("TTS compatibility issues found")
                suggestions.extend(self.instruction_processor.suggest_instruction_improvements(script_text))
            
            # Word count validation
            word_count = len(script_text.split())
            if word_count < 100:
                issues.append("Script is very short")
                suggestions.append("Consider expanding content for better podcast experience")
            elif word_count > 5000:
                issues.append("Script is very long")
                suggestions.append("Consider breaking into chapters or shortening")
            
            # Content quality checks
            content_issues = self._check_content_quality(script_text)
            issues.extend(content_issues)
            
            validation_result = ValidationResult(
                overall_score=overall_score,
                readability_score=readability_score,
                structure_score=structure_score,
                tts_compatibility_score=tts_compatibility_score,
                issues=issues,
                suggestions=suggestions
            )
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=validation_result,
                metadata={
                    'validation_method': 'comprehensive',
                    'word_count': word_count
                }
            )
            
        except Exception as e:
            self.logger.error(f"Script validation failed: {str(e)}", exc_info=True)
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=f"Validation error: {str(e)}"
            )
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score based on sentence and word complexity"""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len([s for s in sentences if s.strip()])
        
        # Syllable complexity (simplified)
        complex_words = sum(1 for word in words if len(word) > 6)
        complex_word_ratio = complex_words / len(words)
        
        # Simple readability formula (similar to Flesch Reading Ease)
        # Higher score = more readable
        readability = max(0, min(1, 1 - (avg_sentence_length / 25) - (complex_word_ratio * 2)))
        
        return readability
    
    def _calculate_structure_score(self, text: str) -> float:
        """Calculate structure score based on organization and flow"""
        score = 0.0
        
        # Check for introduction patterns
        intro_patterns = [r'\b(welcome|hello|today|this episode)\b', r'\b(we\'ll explore|let\'s discuss)\b']
        has_intro = any(re.search(pattern, text, re.IGNORECASE) for pattern in intro_patterns)
        if has_intro:
            score += 0.3
        
        # Check for conclusion patterns
        outro_patterns = [r'\b(in conclusion|to wrap up|that\'s all|thank you)\b', r'\b(until next time|see you)\b']
        has_outro = any(re.search(pattern, text, re.IGNORECASE) for pattern in outro_patterns)
        if has_outro:
            score += 0.3
        
        # Check for transitions
        transition_patterns = [r'\b(however|meanwhile|furthermore|additionally)\b', r'\b(on the other hand|speaking of)\b']
        transition_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in transition_patterns)
        if transition_count > 0:
            score += min(0.4, transition_count * 0.1)
        
        return min(1.0, score)
    
    def _calculate_tts_compatibility_score(self, text: str) -> float:
        """Calculate TTS compatibility score"""
        instruction_analysis = self.instruction_processor.count_instructions(text)
        
        score = 1.0
        
        # Penalize for invalid instructions
        if instruction_analysis['invalid'] > 0:
            score -= 0.3
        
        # Penalize for excessive instruction density
        if instruction_analysis['density_percent'] > 15:
            score -= 0.2
        elif instruction_analysis['density_percent'] > 10:
            score -= 0.1
        
        # Check for TTS-unfriendly patterns
        unfriendly_patterns = [
            r'[A-Z]{3,}',  # Multiple uppercase letters
            r'\d{4,}',     # Long numbers
            r'[^\w\s.,!?;:\'"()-]'  # Special characters
        ]
        
        for pattern in unfriendly_patterns:
            matches = len(re.findall(pattern, text))
            if matches > 5:
                score -= 0.1
        
        return max(0.0, score)
    
    def _check_content_quality(self, text: str) -> List[str]:
        """Check for content quality issues"""
        issues = []
        
        # Check for repetitive content
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) != len(set(sentences)):
            issues.append("Contains repetitive sentences")
        
        # Check for very short paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        short_paragraphs = [p for p in paragraphs if len(p.split()) < 20]
        if len(short_paragraphs) > len(paragraphs) * 0.5:
            issues.append("Many paragraphs are very short")
        
        # Check for balanced content distribution
        if paragraphs:
            paragraph_lengths = [len(p.split()) for p in paragraphs]
            if max(paragraph_lengths) > 3 * min(paragraph_lengths):
                issues.append("Unbalanced paragraph lengths")
        
        return issues


class ScriptCleaner:
    """
    Utility class for cleaning and preparing scripts for various outputs.
    """
    
    def __init__(self):
        self.tts_processor = TTSProcessor()
    
    def clean_for_tts(self, script_text: str, voice_name: str = "neural2") -> str:
        """
        Clean script for TTS processing.
        
        Args:
            script_text: Raw script text
            voice_name: TTS voice name
            
        Returns:
            TTS-ready text
        """
        result = self.tts_processor.process_script(script_text, voice_name)
        return result.data if result.is_success else script_text
    
    def clean_for_display(self, script_text: str) -> str:
        """Clean script for human reading (remove all instruction tags)"""
        # Remove all instruction tags
        cleaned = re.sub(r'\[[^\]]+\]', '', script_text)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def extract_instructions(self, script_text: str) -> List[str]:
        """Extract all instruction tags from script"""
        instruction_pattern = re.compile(r'\[([^\]]+)\]')
        return instruction_pattern.findall(script_text)