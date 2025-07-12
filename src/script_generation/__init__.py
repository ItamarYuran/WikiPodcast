"""
Script Generation Package

This package handles all aspects of podcast script generation:
- Content processing and preparation
- Script generation with various styles
- TTS optimization and processing
- Instruction processing and validation
- Caching and persistence

The package is organized into focused modules:
- generators: Core script generation logic
- styles: Style definitions and templates
- processors: TTS processing and optimization
- cache: Script caching and persistence
- validators: Script validation and quality checks
"""

from script_generation.generators import (
    ScriptGeneratorImpl,
    ChapterBasedGenerator,
    ConversationalGenerator
)

from script_generation.styles import (
    StyleManager,
    StyleTemplate
)

# These will be created next
# from script_generation.processors import (
#     TTSProcessor,
#     InstructionProcessor,
#     ScriptCleaner
# )

# from script_generation.cache import (
#     ScriptCache,
#     CacheManager
# )

# from script_generation.validators import (
#     ScriptValidator,
#     QualityChecker,
#     InstructionValidator
# )

__version__ = "1.0.0"
__all__ = [
    # Generators
    "ScriptGeneratorImpl",
    "ChapterBasedGenerator", 
    "ConversationalGenerator",
    
    # Styles
    "StyleManager",
    "StyleTemplate",
    
    # TODO: Add when processors are created
    # "TTSProcessor",
    # "InstructionProcessor", 
    # "ScriptCleaner",
    # "ScriptCache",
    # "CacheManager",
    # "ScriptValidator",
    # "QualityChecker",
    # "InstructionValidator"
]

# Convenience factory function
def create_script_generator(config=None):
    """Create a configured script generator instance"""
    from script_generation.generators import ScriptGeneratorImpl
    return ScriptGeneratorImpl(config)