# Wikipedia Podcast Generation System

🎙️ **Transform Wikipedia articles into professional podcasts with AI-powered script generation and text-to-speech**

## 🌟 **What This System Does**

The Wikipedia Podcast Generation System is a sophisticated pipeline that:

1. **Fetches Wikipedia articles** - Trending, featured, or specific topics
2. **Generates podcast scripts** - Using OpenAI GPT-4 with multiple styles
3. **Creates professional audio** - Google Cloud TTS with voice options
4. **Applies post-production** - Audio enhancement and effects
5. **Packages everything** - Complete podcast episodes with metadata

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.9+ 
- OpenAI API key
- Google Cloud TTS credentials (optional, for audio)
- FFmpeg (optional, for audio processing)

### **Installation**
```bash
# Clone the repository
git clone [your-repo-url]
cd wikipedia-podcast-system

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp config/api_keys.env.example config/api_keys.env
# Edit config/api_keys.env with your keys
```

### **Basic Usage**
```bash
# Interactive mode (recommended)
cd src/
python main.py

# Command line examples
python main.py --trending 5
python main.py --topic "Artificial Intelligence" --style conversational
python main.py --featured 3
```

## 🏗️ **System Architecture**

### **Current State: Hybrid Architecture (65% Migrated)**
The system is transitioning from monolithic to modular design:

```
┌─────────────────────────────────────────────────────────┐
│                 PIPELINE OVERVIEW                       │
│                                                         │
│  Wikipedia → Content → Script → Audio → Post-Prod     │
│   Fetching    Processing  Generation  Creation          │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ 21.7KB  │  │ 17.3KB  │  │ 26.5KB  │  │ 37.8KB  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────────────────┘
```

### **New Modular Components** (Implemented)
- **`core/`** - Foundation interfaces and models
- **`content_sources/`** - Pluggable content fetching
- **`script_generation/`** - Modular script creation
- **`utils/`** - Shared utilities

### **Legacy Components** (Working)
- **`interactive_menus.py`** (36.7KB) - User interface
- **`content_fetcher.py`** (21.7KB) - Wikipedia fetching
- **`pipeline.py`** (8.3KB) - Main orchestrator

## 📊 **Key Features**

### **Content Sources**
- ✅ **Wikipedia integration** - Articles, trending topics, featured content
- ✅ **Smart caching** - Avoids redundant API calls
- ✅ **Content suggestions** - Finds related topics
- ✅ **Quality scoring** - Filters low-quality content

### **Script Generation**
- ✅ **Multiple styles** - Conversational, educational, documentary, news
- ✅ **GPT-4 powered** - High-quality, natural language
- ✅ **Custom instructions** - Tailored content generation
- ✅ **Chapter editing** - Handles long articles efficiently
- ✅ **Duration targeting** - Generate scripts for specific lengths

### **Audio Generation**
- ✅ **Google Cloud TTS** - Premium voice quality
- ✅ **Multiple voices** - Journey, Neural2, Standard options
- ✅ **SSML support** - Enhanced speech synthesis
- ✅ **Chunking** - Handles long content reliably
- ✅ **Post-production** - Audio enhancement and effects

### **User Experience**
- ✅ **Interactive menus** - Intuitive command-line interface
- ✅ **Progress tracking** - Real-time status updates
- ✅ **Error handling** - Graceful failure recovery
- ✅ **Batch processing** - Generate multiple podcasts
- ✅ **Caching** - Fast access to previous work

## 🎛️ **Usage Modes**

### **1. Interactive Mode** (Recommended)
```bash
python main.py
```
- Full-featured menu system
- Step-by-step guidance
- Real-time feedback
- Easy troubleshooting

### **2. Command Line Mode**
```bash
# Generate trending topics
python main.py --trending 5 --style conversational

# Specific topic
python main.py --topic "Climate Change" --style documentary

# Featured articles
python main.py --featured 3 --style educational
```

### **3. Standalone Scripts**
```bash
# Complete podcast creation
python create_podcast.py "Machine Learning" conversational en-US-Journey-D

# Article editing only
python article_editor.py

# Audio post-production
python podcast_post_production.py
```

## 📁 **Project Structure**

```
wikipedia-podcast-system/
├── src/                           # Main application code
│   ├── core/                      # 🆕 Modular foundation
│   │   ├── models.py              # Data models
│   │   ├── interfaces.py          # Abstract interfaces
│   │   └── exceptions.py          # Error handling
│   ├── content_sources/           # 🆕 Content fetching
│   │   ├── manager.py             # Source orchestration
│   │   └── wikipedia_source.py    # Wikipedia implementation
│   ├── script_generation/         # 🆕 Script creation
│   │   ├── generators.py          # Core generation logic
│   │   └── styles.py              # Style management
│   ├── audio_pipeline.py          # 🔄 Audio generation (migrated)
│   ├── interactive_menus.py       # 📱 User interface
│   ├── content_fetcher.py         # 📰 Wikipedia fetching
│   ├── script_formatter.py        # 📝 Script generation bridge
│   ├── pipeline.py                # 🎯 Main orchestrator
│   └── main.py                    # 🚀 Entry point
├── config/                        # Configuration files
│   ├── api_keys.env               # API keys (not in git)
│   └── api_keys.env.example       # Template
├── raw_articles/                  # 💾 Cached Wikipedia content
├── processed_scripts/             # 📄 Generated scripts
├── audio_output/                  # 🎵 Generated audio files
└── docs/                          # 📚 Documentation
    ├── ARCHITECTURE.md             # System design
    ├── MIGRATION_STATUS.md         # Current progress
    └── TROUBLESHOOTING.md          # Common issues
```

## 🔧 **Configuration**

### **API Keys** (`config/api_keys.env`)
```bash
# Required for script generation
OPENAI_API_KEY=sk-your-openai-key-here

# Optional for audio generation
GOOGLE_APPLICATION_CREDENTIALS=config/google-tts-credentials.json

# Future integrations
ELEVENLABS_API_KEY=your-elevenlabs-key-here
```

### **System Settings**
- **Cache directories**: `../raw_articles/`, `../processed_scripts/`
- **Audio output**: `audio_output/`
- **Default voice**: `en-US-Journey-D`
- **Default style**: `conversational`

## 🎨 **Available Styles**

| Style | Description | Best For |
|-------|-------------|----------|
| **Conversational** | Natural, engaging dialogue | General audience |
| **Educational** | Structured, informative | Learning content |
| **Documentary** | Professional, authoritative | Serious topics |
| **News** | Concise, factual reporting | Current events |
| **Storytelling** | Narrative, dramatic | Historical topics |
| **Comedy** | Light-hearted, entertaining | Fun topics |

## 🎤 **Voice Options**

### **Google Cloud TTS Voices**
- **Journey Series** (Premium): `en-US-Journey-D`, `en-US-Journey-F`
- **Neural2 Series** (High Quality): `en-US-Neural2-A`, `en-US-Neural2-C`
- **Standard Series** (Basic): `en-US-Standard-A`, `en-US-Standard-C`

### **Voice Compatibility**
- **Journey**: Plain text only (no SSML)
- **Neural2**: Requires perfect SSML
- **Standard**: Forgiving SSML support

## 📈 **Performance Characteristics**

### **Typical Processing Times**
- **Article fetching**: 1-3 seconds
- **Script generation**: 30-60 seconds (depends on length)
- **Audio generation**: 1-2 minutes (depends on voice and length)
- **Post-production**: 30-60 seconds

### **Resource Usage**
- **Memory**: 50-100MB during processing
- **Storage**: ~1MB per script, ~5-10MB per audio file
- **Network**: Wikipedia API, OpenAI API, Google Cloud TTS

## 🔄 **Migration Status**

The system is **65% migrated** to the new modular architecture:

- ✅ **Core foundation** - Complete
- ✅ **Script generation** - Complete  
- ✅ **Audio pipeline** - Complete
- 🔄 **Configuration** - In progress
- ❌ **Interactive menus** - Pending
- ❌ **Content fetching** - Pending

See [MIGRATION_STATUS.md](docs/MIGRATION_STATUS.md) for detailed progress.

## 🐛 **Common Issues**

### **Quick Fixes**
- **Import errors**: Run from `src/` directory
- **API key issues**: Check `config/api_keys.env`
- **Audio generation fails**: Verify Google Cloud credentials
- **SSML errors**: Disable SSML for Journey voices

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for comprehensive solutions.

## 🛣️ **Development Roadmap**

### **Phase 1: Complete Migration** (Current)
- [ ] Fix utility import errors
- [ ] Migrate interactive menu system
- [ ] Complete content fetcher migration
- [ ] Centralize configuration management

### **Phase 2: Enhanced Features**
- [ ] Multiple content sources (news, RSS, custom text)
- [ ] Advanced audio processing (music, sound effects)
- [ ] Batch processing workflows
- [ ] Quality metrics and validation

### **Phase 3: Production Ready**
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [ ] Monitoring and logging
- [ ] Docker containerization

## 🤝 **Contributing**

### **Development Setup**
```bash
# Clone and setup
git clone [repo-url]
cd wikipedia-podcast-system
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Check code style
flake8 src/
```

### **Architecture Guidelines**
- **Use new modular interfaces** in `core/`
- **Follow dependency injection** patterns
- **Add proper error handling** with `core/exceptions.py`
- **Update documentation** when changing interfaces

### **Adding New Features**
1. **Check existing interfaces** in `core/interfaces.py`
2. **Create new components** following modular patterns
3. **Add compatibility bridges** for gradual migration
4. **Update tests and documentation**

## 📊 **System Metrics**

### **Current Codebase**
- **Total files**: 12 Python files
- **Lines of code**: 5,548 lines
- **Total size**: 220.5 KB
- **Classes**: 17 classes
- **Methods**: 129 methods

### **Component Sizes**
- **Largest**: `audio_pipeline.py` (37.8KB)
- **User interface**: `interactive_menus.py` (36.7KB)  
- **Content fetching**: `content_fetcher.py` (21.7KB)
- **Script generation**: `script_formatter.py` (26.5KB)

## 🔒 **Security**

### **API Key Management**
- **Never commit API keys** to version control
- **Use environment variables** for configuration
- **Rotate keys regularly** if compromised
- **Limit API key permissions** to required services only

### **Data Privacy**
- **No personal data** is collected or stored
- **Wikipedia content** is public domain
- **Generated scripts** are stored locally
- **Audio files** contain no identifying information

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **OpenAI** for GPT-4 and text-to-speech APIs
- **Google Cloud** for premium TTS voices
- **Wikipedia** for open access to knowledge
- **Python community** for excellent libraries

## 📞 **Support**

- **Documentation**: See `docs/` directory
- **Issues**: Create GitHub issue with reproduction steps
- **Troubleshooting**: Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

**Status**: 🟢 Active Development | **Version**: 2.0-beta | **Migration**: 65% Complete

Transform your Wikipedia exploration into engaging podcast content with professional quality and minimal effort.