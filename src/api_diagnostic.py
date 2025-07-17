from content_sources.manager import ContentSourceManager
from script_generation import create_script_generator

# Load a simple article first
manager = ContentSourceManager(); fetcher = manager.get_source('wikipedia')
cached_articles = fetcher.list_cached_articles()

# Find the "5" article you were trying to use
article_5 = None
for cached in cached_articles:
    if cached['title'] == '5':
        article_5 = fetcher.load_cached_article(cached['filename'])
        break

if article_5:
    print(f"✅ Loaded article: {article_5.title}")
    print(f"📊 Word count: {article_5.word_count}")
    
    # Now test script generation
    formatter = create_script_generator()
    
    print("🧪 Testing script generation...")
    try:
        script = formatter.format_article_to_script(article_5, "conversational")
        if script:
            print("✅ Script generated successfully!")
        else:
            print("❌ Script generation returned None")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Could not find article '5'")