# Troubleshooting Guide - Wikipedia Podcast System

## 🚨 Common Issues and Solutions

This guide covers the most frequent problems encountered during development and usage of the Wikipedia Podcast Generation System.

## 🔧 **Setup and Configuration Issues**

### **1. API Key Problems**

#### **❌ Problem**: `OPENAI_API_KEY not found`
```bash
❌ Failed to initialize OpenAI client: No API key found
```

**✅ Solution**:
1. Create `config/api_keys.env` file
2. Add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Restart the application

#### **❌ Problem**: `Google Cloud TTS credentials not found`
```bash
❌ File config/google-tts-credentials.json was not found
```

**✅ Solution**:
1. Download credentials from Google Cloud Console
2. Save as `config/google-tts-credentials.json`
3. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/config/google-tts-credentials.json"
   ```

### **2. Import Errors**

#### **❌ Problem**: `ModuleNotFoundError: No module named 'core'`
```bash
ModuleNotFoundError: No module named 'core'
```

**✅ Solution**:
1. Run from the `src/` directory:
   ```bash
   cd src/
   python main.py
   ```
2. Or add to Python path:
   ```bash
   export PYTHONPATH="/path/to/project/src:$PYTHONPATH"
   ```

#### **❌ Problem**: `ImportError: cannot import name 'PodcastScript' from 'script_formatter'`
```bash
ImportError: cannot import name 'PodcastScript' from 'script_formatter'
```

**✅ Solution**:
This indicates a migration issue. Update imports:
```python
# Change from:
from script_formatter import PodcastScript

# To:
from core.models import PodcastScript
```

## 🎵 **Audio Generation Issues**

### **3. TTS Voice Compatibility**

#### **❌ Problem**: `Voice currently does not support SSML input`
```bash
❌ Enhanced TTS error: 400 This voice currently does not support SSML input
```

**✅ Solution**:
Different Google Cloud TTS voices have different SSML support:
- **Journey voices**: Plain text only
- **Neural2 voices**: Perfect SSML only
- **Standard voices**: Forgiving SSML

Fix by disabling SSML for Journey voices:
```python
# In audio_pipeline.py
if 'Journey' in voice_config['name']:
    use_ssml = False
else:
    use_ssml = '<speak>' in text
```

#### **❌ Problem**: `Invalid SSML. Newer voices like Neural2 require valid SSML`
```bash
❌ Enhanced TTS error: 400 Invalid SSML. Newer voices like Neural2 require valid SSML
```

**✅ Solution**:
1. Check SSML syntax in `tts_processor.py`
2. Ensure proper XML formatting
3. Or disable SSML processing:
   ```python
   clean_script = ssml_processor.process_script_for_tts(script_text, use_ssml=False)
   ```

### **4. Audio File Issues**

#### **❌ Problem**: `ffmpeg not found`
```bash
⚠️ ffmpeg not found, using fallback method
```

**✅ Solution**:
Install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows (using chocolatey)
choco install ffmpeg
```

#### **❌ Problem**: `Failed to combine audio chunks`
```bash
❌ Failed to combine audio chunks
```

**✅ Solution**:
1. Check if ffmpeg is in PATH
2. Verify audio chunk files exist
3. Check file permissions
4. Fallback will use binary concatenation (lower quality)

## 📝 **Script Generation Issues**

### **5. Script Parameter Errors**

#### **❌ Problem**: `PodcastScript.__init__() got an unexpected keyword argument 'script'`
```bash
TypeError: PodcastScript.__init__() got an unexpected keyword argument 'script'
```

**✅ Solution**:
Update to new parameter names:
```python
# Old way:
script = PodcastScript(
    script="content here",
    source_article="title"
)

# New way:
script = PodcastScript(
    script_text="content here",
    source_article_id="title"
)
```

#### **❌ Problem**: `ScriptSegment.__init__() got an unexpected keyword argument 'type'`
```bash
TypeError: ScriptSegment.__init__() got an unexpected keyword argument 'type'
```

**✅ Solution**:
Update to new parameter names:
```python
# Old way:
segment = ScriptSegment(
    type="main_content",
    content="text"
)

# New way:
segment = ScriptSegment(
    segment_type="main_content",
    content="text"
)
```

### **6. Cache and File Issues**

#### **❌ Problem**: `Script file not found in cache`
```bash
❌ Script file not found: Bible_20250714_1950.json
```

**✅ Solution**:
1. Check cache directories exist:
   ```bash
   ls -la ../processed_scripts/
   ls -la processed_scripts/
   ```
2. Generate script first before trying to create audio
3. Check file permissions

#### **❌ Problem**: `Could not load script from cache`
```bash
❌ Error loading script from cache: JSON decode error
```

**✅ Solution**:
1. Check file is valid JSON:
   ```bash
   cat ../processed_scripts/conversational/script_file.json | python -m json.tool
   ```
2. Delete corrupted cache file and regenerate
3. Check disk space

## 🌐 **Network and API Issues**

### **7. Wikipedia API Problems**

#### **❌ Problem**: `Wikipedia API rate limit exceeded`
```bash
❌ Rate limit exceeded for Wikipedia API
```

**✅ Solution**:
1. Add delays between requests
2. Use cached articles when possible
3. Implement exponential backoff

#### **❌ Problem**: `Article not found on Wikipedia`
```bash
❌ Could not find Wikipedia article for: [topic]
```

**✅ Solution**:
1. Check spelling and capitalization
2. Use article suggestions:
   ```python
   suggestions = content_fetcher.suggest_titles(topic, 5)
   ```
3. Try alternative search terms

### **8. OpenAI API Issues**

#### **❌ Problem**: `OpenAI API quota exceeded`
```bash
❌ You have exceeded your OpenAI API quota
```

**✅ Solution**:
1. Check usage on OpenAI dashboard
2. Upgrade plan or wait for quota reset
3. Optimize prompts to use fewer tokens

#### **❌ Problem**: `OpenAI API timeout`
```bash
❌ Request timed out
```

**✅ Solution**:
1. Retry with exponential backoff
2. Break large requests into smaller chunks
3. Check network connectivity

## 💾 **Data and Storage Issues**

### **9. File Permission Problems**

#### **❌ Problem**: `Permission denied when saving files`
```bash
❌ Permission denied: /path/to/file
```

**✅ Solution**:
1. Check directory permissions:
   ```bash
   ls -la ../processed_scripts/
   ```
2. Create directories if missing:
   ```bash
   mkdir -p ../processed_scripts/conversational
   mkdir -p ../raw_articles
   mkdir -p audio_output
   ```
3. Fix permissions:
   ```bash
   chmod 755 ../processed_scripts/
   ```

### **10. Disk Space Issues**

#### **❌ Problem**: `No space left on device`
```bash
❌ No space left on device
```

**✅ Solution**:
1. Check disk usage:
   ```bash
   df -h
   ```
2. Clean up old cache files:
   ```bash
   # Clean old audio files
   find audio_output/ -name "*.mp3" -mtime +30 -delete
   
   # Clean old scripts
   find ../processed_scripts/ -name "*.json" -mtime +30 -delete
   ```
3. Implement cache size limits

## 🔍 **Debugging and Development Issues**

### **11. Analysis Errors**

#### **❌ Problem**: `Analysis Error: argument of type 'X' is not iterable`
```bash
❌ Analysis Error: argument of type 'Subscript' is not iterable
```

**✅ Solution**:
1. Check for syntax errors in the file
2. Look for malformed import statements
3. Verify variable types in conditional statements

#### **❌ Problem**: `Relative import failures`
```bash
❌ ImportError: attempted relative import with no known parent package
```

**✅ Solution**:
1. Use absolute imports:
   ```python
   # Instead of:
   from .manager import ContentSourceManager
   
   # Use:
   from content_sources.manager import ContentSourceManager
   ```
2. Run from correct directory (`src/`)

### **12. Memory and Performance Issues**

#### **❌ Problem**: `System running out of memory`
```bash
❌ MemoryError: Unable to allocate array
```

**✅ Solution**:
1. Process large articles in chunks
2. Clear cache periodically
3. Use generators instead of loading all data at once

#### **❌ Problem**: `Application startup is slow`
```bash
⏳ Taking 30+ seconds to start
```

**✅ Solution**:
1. Lazy load components
2. Cache API client initialization
3. Optimize import statements

## 🛠️ **Development Workflow Issues**

### **13. Git and Version Control**

#### **❌ Problem**: `Accidentally committed API keys`
```bash
❌ API keys exposed in git history
```

**✅ Solution**:
1. Remove from git history:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch config/api_keys.env'
   ```
2. Update `.gitignore`
3. Rotate compromised keys

#### **❌ Problem**: `Merge conflicts in generated files`
```bash
❌ Merge conflict in processed_scripts/
```

**✅ Solution**:
1. Generated files should be in `.gitignore`
2. Resolve by regenerating content
3. Don't commit large generated files

### **14. Testing and Validation**

#### **❌ Problem**: `Script generation produces poor quality`
```bash
❌ Generated script is repetitive or incoherent
```

**✅ Solution**:
1. Adjust prompt engineering
2. Use different OpenAI model
3. Implement quality checks
4. Use custom instructions for better results

## 🚀 **Quick Diagnostic Commands**

### **System Health Check**
```bash
# Check Python environment
python --version
pip list | grep -E "(openai|google|requests)"

# Check file structure
ls -la ../processed_scripts/
ls -la ../raw_articles/
ls -la audio_output/

# Test API connections
python -c "from openai import OpenAI; print('OpenAI OK')"
python -c "from google.cloud import texttospeech; print('Google TTS OK')"
```

### **Clean Reset**
```bash
# Clear all caches
rm -rf ../processed_scripts/*
rm -rf ../raw_articles/*
rm -rf audio_output/*

# Restart with clean state
python main.py
```

### **Test Specific Components**
```bash
# Test content fetching
python -c "from src.content_fetcher import WikipediaContentFetcher; f = WikipediaContentFetcher(); print(f.fetch_article('Python'))"

# Test script generation
python -c "from src.script_formatter import PodcastScriptFormatter; f = PodcastScriptFormatter(); print(f.get_available_styles())"
```

## 📞 **Getting Help**

### **When to Create an Issue**
1. **Reproducible bugs** - provide steps to reproduce
2. **Feature requests** - describe use case and expected behavior
3. **Documentation gaps** - point out unclear or missing information

### **Information to Include**
- **System information**: OS, Python version, dependencies
- **Error messages**: Full stack traces
- **Configuration**: Relevant config files (without API keys)
- **Steps to reproduce**: Minimal example that triggers the issue

### **Before Reporting**
1. Check this troubleshooting guide
2. Search existing issues
3. Try with a clean environment
4. Test with minimal configuration

## 🔄 **Emergency Recovery**

### **If Everything Breaks**
1. **Stop the application**
2. **Backup current state**:
   ```bash
   cp -r src/ src_backup/
   cp -r config/ config_backup/
   ```
3. **Revert to last known good state**:
   ```bash
   git checkout HEAD~1
   ```
4. **Gradually reapply changes**
5. **Test after each change**

### **Nuclear Option - Complete Reset**
```bash
# Back up API keys
cp config/api_keys.env ~/api_keys_backup.env

# Clean everything
git clean -fdx
git reset --hard HEAD

# Restore API keys
cp ~/api_keys_backup.env config/api_keys.env

# Restart fresh
python main.py
```

This troubleshooting guide covers the most common issues. For complex problems, consider creating a minimal reproduction case and seeking help from the development team.