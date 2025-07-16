# Wikipedia Podcast Generation System - Architecture Documentation

## 🏗️ System Overview

The Wikipedia Podcast Generation System is a sophisticated pipeline that converts Wikipedia articles into professional podcast episodes. The system is currently undergoing a major architectural transition from a monolithic to a modular design.

## 📊 Current System Statistics

- **Total Files**: 12 Python files in `/src`
- **Total Lines**: 5,548 lines of code
- **Total Size**: 220.5 KB
- **Classes**: 17 classes
- **Functions**: 9 standalone functions
- **Methods**: 129 methods across all classes
- **Executable Scripts**: 5 entry points

## 🔄 Architecture Evolution

### Current State: Hybrid Architecture
The system operates with both **legacy monolithic components** and **new modular components** running in parallel, with compatibility bridges connecting them.

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYBRID ARCHITECTURE                         │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │  Legacy System  │ ←→ │  New Modular    │                   │
│  │   (Working)     │    │   (Partial)     │                   │
│  └─────────────────┘    └─────────────────┘                   │
│          │                        │                           │
│          └────────────────────────┼──────────────────────────┘
│                                   │
│                    ┌─────────────────┐
│                    │ Compatibility   │
│                    │    Bridges      │
│                    └─────────────────┘
```

## 🎯 Core Components

### 1. **Content Pipeline** (Working)
- **Entry Point**: `main.py` (4.5 KB)
- **Orchestrator**: `pipeline.py` (8.3 KB)
- **Content Fetching**: `content_fetcher.py` (21.7 KB)
- **Content Processing**: `content_pipeline.py` (17.3 KB)

### 2. **Script Generation** (Hybrid)
- **Main Engine**: `script_formatter.py` (26.5 KB) - Compatibility bridge
- **Backend**: `core/script_generation/` - New modular system
- **Legacy Support**: Maintains old interface while using new backend

### 3. **Audio Generation** (Recently Modernized)
- **Main Engine**: `audio_pipeline.py` (37.8 KB) - Now uses new interface
- **TTS Processing**: `tts_processor.py` (10.2 KB)
- **Post-Production**: `podcast_post_production.py` (21.7 KB)

### 4. **User Interface** (Legacy)
- **Interactive System**: `interactive_menus.py` (36.7 KB)
- **Command Line**: `main.py` with argument parsing
- **Diagnostic Tools**: `api_diagnostic.py` (1.1 KB)

### 5. **Utilities** (Legacy)
- **Article Editing**: `article_editor.py` (8.0 KB)
- **Standalone Creator**: `create_podcast.py` (26.7 KB)

## 🏛️ New Modular Architecture (Target)

### Core Modules (Implemented)
```
src/
├── core/                           # Foundation layer
│   ├── models.py                   # Data models (14KB)
│   ├── interfaces.py               # Abstract interfaces (8KB)
│   └── exceptions.py               # Error handling (7KB)
│
├── content_sources/                # Content fetching
│   ├── interfaces.py               # Content source contracts
│   ├── manager.py                  # Source orchestration
│   └── wikipedia_source.py         # Wikipedia implementation
│
├── script_generation/              # Script creation
│   ├── generators.py               # Core generation (29KB)
│   ├── styles.py                   # Style management (15KB)
│   └── processors.py               # TTS processing stubs
│
└── utils/                          # Utility functions
    ├── http_client.py              # HTTP utilities
    ├── filesystem.py               # File operations
    └── async_utils.py              # Async utilities
```

## 🔗 Data Flow Architecture

### Current Pipeline Flow
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Wikipedia     │ ── │   Content       │ ── │   Script        │
│   Fetching      │    │   Processing    │    │   Generation    │
│                 │    │                 │    │                 │
│ content_fetcher │    │content_pipeline │    │script_formatter │
│     (21.7KB)    │    │    (17.3KB)     │    │    (26.5KB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Post-Prod     │ ── │   Audio         │ ── │   TTS           │
│   Enhancement   │    │   Generation    │    │   Processing    │
│                 │    │                 │    │                 │
│podcast_post_prod│    │audio_pipeline   │    │ tts_processor   │
│    (21.7KB)     │    │    (37.8KB)     │    │    (10.2KB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎛️ Interface Patterns

### Legacy Interface (Current)
```python
# Old style - direct class instantiation
content_fetcher = WikipediaContentFetcher()
script_formatter = PodcastScriptFormatter()
```

### New Interface (Target)
```python
# New style - dependency injection with interfaces
content_manager = ContentSourceManager()
script_generator = ScriptGeneratorImpl(config)
```

## 📦 Component Responsibilities

### **Large Components** (>20KB)
1. **`audio_pipeline.py`** (37.8KB) - Audio generation with Google Cloud TTS
2. **`interactive_menus.py`** (36.7KB) - User interface system
3. **`create_podcast.py`** (26.7KB) - Standalone podcast creator
4. **`script_formatter.py`** (26.5KB) - Script generation bridge
5. **`podcast_post_production.py`** (21.7KB) - Audio enhancement
6. **`content_fetcher.py`** (21.7KB) - Wikipedia content fetching

### **Medium Components** (10-20KB)
1. **`content_pipeline.py`** (17.3KB) - Content processing orchestration
2. **`tts_processor.py`** (10.2KB) - SSML and TTS optimization

### **Small Components** (<10KB)
1. **`pipeline.py`** (8.3KB) - Main system orchestrator
2. **`article_editor.py`** (8.0KB) - Chapter-based editing
3. **`main.py`** (4.5KB) - CLI entry point
4. **`api_diagnostic.py`** (1.1KB) - Diagnostic utilities

## 🔧 Configuration Management

### Current Configuration
- **API Keys**: `config/api_keys.env`
- **Hardcoded Settings**: Scattered throughout legacy components
- **Cache Directories**: `../raw_articles/`, `../processed_scripts/`

### Target Configuration
- **Centralized**: `config_management/config_manager.py`
- **Environment-based**: Different configs for dev/prod
- **Type-safe**: Using dataclasses and validation

## 🚀 Execution Models

### **Interactive Mode** (Primary)
```bash
python main.py  # Launches interactive_menus.py
```

### **Command Line Mode**
```bash
python main.py --trending 5
python main.py --topic "AI" --style conversational
```

### **Standalone Scripts**
```bash
python create_podcast.py "Machine Learning" conversational
python article_editor.py  # Direct article editing
python podcast_post_production.py  # Audio enhancement
```

## 🔄 Migration Strategy

### **Completed Migrations**
- ✅ **`audio_pipeline.py`** - Now uses `core.models.PodcastScript`
- ✅ **Core foundation** - `core/models.py`, `core/interfaces.py`
- ✅ **Script generation backend** - `script_generation/generators.py`

### **In Progress**
- 🔄 **`script_formatter.py`** - Compatibility bridge active
- 🔄 **Configuration management** - Partially centralized

### **Pending Migrations**
- ❌ **`interactive_menus.py`** - Still uses legacy imports
- ❌ **`content_fetcher.py`** - Large monolithic component
- ❌ **`pipeline.py`** - Orchestration layer needs updating

## 🛠️ Development Patterns

### **Error Handling**
- **Legacy**: Basic try/catch with print statements
- **New**: Structured exceptions in `core/exceptions.py`

### **Data Models**
- **Legacy**: Simple dataclasses or dictionaries
- **New**: Rich domain models with validation

### **Dependency Management**
- **Legacy**: Direct imports and instantiation
- **New**: Dependency injection with interfaces

## 🎯 Quality Metrics

### **Code Organization**
- **Cohesion**: High - Components have clear responsibilities
- **Coupling**: Medium - Some tight coupling in legacy components
- **Testability**: Low - Limited test coverage currently

### **Performance Characteristics**
- **Startup Time**: ~2-3 seconds (loading OpenAI, Google Cloud clients)
- **Memory Usage**: ~50-100MB for typical operations
- **I/O Patterns**: Heavy file caching, API rate limiting

## 🔮 Future Architecture Vision

### **Target State**: Fully Modular
```
┌─────────────────────────────────────────────────────────────────┐
│                    MODULAR ARCHITECTURE                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Content   │  │   Script    │  │   Audio     │            │
│  │   Sources   │  │ Generation  │  │ Pipeline    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                 │
│         └─────────────────┼─────────────────┘                 │
│                           │                                   │
│                  ┌─────────────┐                              │
│                  │    Core     │                              │
│                  │ Foundation  │                              │
│                  └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### **Benefits of Full Migration**
- **Maintainability**: Clear separation of concerns
- **Testability**: Mockable interfaces
- **Extensibility**: Plugin architecture for new sources
- **Reliability**: Structured error handling
- **Performance**: Optimized data flow

## 📝 Development Guidelines

### **Adding New Features**
1. **Check existing interfaces** in `core/interfaces.py`
2. **Use dependency injection** rather than direct instantiation
3. **Add proper error handling** using `core/exceptions.py`
4. **Follow the modular patterns** in `script_generation/`

### **Modifying Existing Code**
1. **Prefer migrating to new interface** over extending legacy
2. **Use compatibility bridges** for gradual migration
3. **Update documentation** when changing interfaces
4. **Test both legacy and new paths** during transition

### **Integration Points**
- **External APIs**: OpenAI, Google Cloud TTS, Wikipedia
- **File System**: Caching in `raw_articles/`, `processed_scripts/`
- **Configuration**: Environment variables and config files
- **User Interface**: CLI arguments and interactive menus

This architecture supports both immediate productivity (legacy system works) and long-term maintainability (new system is cleaner and more extensible).