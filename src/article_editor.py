import openai
import re
import time
from typing import List, Tuple
import json
import os

class ChapterEditor:
    def __init__(self, api_key: str):
        """Initialize the chapter editor with OpenAI API key."""
        self.client = openai.OpenAI(api_key=api_key)
        
    def split_into_chapters(self, article: str) -> List[Tuple[str, str]]:
        """
        Split article into chapters based on headers or natural breaks.
        Returns list of (title, content) tuples.
        """
        # Pattern to match markdown headers (# ## ###) or numbered sections
        header_pattern = r'^(#{1,3}\s+.*|^\d+\.?\s+[A-Z][^.\n]*|^[A-Z][A-Z\s]+$)'
        
        # Split by headers
        sections = re.split(f'({header_pattern})', article, flags=re.MULTILINE)
        
        chapters = []
        current_title = "Introduction"
        current_content = ""
        
        for i, section in enumerate(sections):
            if re.match(header_pattern, section, re.MULTILINE):
                # Save previous chapter if it has content
                if current_content.strip():
                    chapters.append((current_title, current_content.strip()))
                
                # Start new chapter
                current_title = section.strip()
                current_content = ""
            else:
                current_content += section
        
        # Add the last chapter
        if current_content.strip():
            chapters.append((current_title, current_content.strip()))
        
        # If no clear chapters found, split by paragraphs (every ~500 words)
        if len(chapters) <= 1:
            chapters = self._split_by_length(article)
        
        return chapters
    
    def _split_by_length(self, text: str, max_words: int = 500) -> List[Tuple[str, str]]:
        """Split text into chunks of approximately max_words."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), max_words):
            chunk_words = words[i:i + max_words]
            chunk_text = ' '.join(chunk_words)
            title = f"Section {len(chunks) + 1}"
            chunks.append((title, chunk_text))
        
        return chunks
    
    def edit_chapter(self, title: str, content: str, instructions: str) -> str:
        """Edit a single chapter using OpenAI API."""
        prompt = f"""
You are an expert editor. Please edit the following chapter according to these instructions:

INSTRUCTIONS: {instructions}

CHAPTER TITLE: {title}

CHAPTER CONTENT:
{content}

Please provide only the edited content, maintaining the same structure and format. Do not include explanations or commentary, just the improved text.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional editor. Edit the provided text according to the given instructions. Return only the edited content without explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error editing chapter '{title}': {str(e)}")
            return content  # Return original content if editing fails
    
    def edit_article_by_chapters(self, article: str, instructions: str, delay: float = 1.0) -> str:
        """
        Edit an entire article by processing each chapter separately.
        
        Args:
            article: The full article text
            instructions: Editing instructions to apply to each chapter
            delay: Delay between API calls to avoid rate limits
        
        Returns:
            The fully edited article
        """
        print("Splitting article into chapters...")
        chapters = self.split_into_chapters(article)
        print(f"Found {len(chapters)} chapters to edit")
        
        edited_chapters = []
        
        for i, (title, content) in enumerate(chapters, 1):
            print(f"Editing chapter {i}/{len(chapters)}: {title}")
            
            edited_content = self.edit_chapter(title, content, instructions)
            edited_chapters.append((title, edited_content))
            
            # Add delay to respect rate limits
            if i < len(chapters):  # Don't delay after the last chapter
                time.sleep(delay)
        
        # Reassemble the article
        print("Reassembling edited article...")
        final_article = ""
        
        for title, content in edited_chapters:
            # Add the title back if it looks like a header
            if title != "Introduction" and not title.startswith("Section "):
                if not title.startswith('#'):
                    final_article += f"\n\n## {title}\n\n"
                else:
                    final_article += f"\n\n{title}\n\n"
            
            final_article += content + "\n"
        
        return final_article.strip()
    
    def save_progress(self, chapters: List[Tuple[str, str]], filename: str):
        """Save editing progress to a JSON file."""
        progress_data = {
            "chapters": [{"title": title, "content": content} for title, content in chapters],
            "timestamp": time.time()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def load_progress(self, filename: str) -> List[Tuple[str, str]]:
        """Load editing progress from a JSON file."""
        with open(filename, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        return [(chapter["title"], chapter["content"]) for chapter in progress_data["chapters"]]


# Example usage functions
def edit_long_article(article_text: str, editing_instructions: str, api_key: str) -> str:
    """
    Main function to edit a long article chapter by chapter.
    
    Args:
        article_text: The full article to edit
        editing_instructions: Instructions for how to edit each chapter
        api_key: OpenAI API key
    
    Returns:
        The fully edited article
    """
    editor = ChapterEditor(api_key)
    return editor.edit_article_by_chapters(article_text, editing_instructions)


def edit_article_from_file(input_file: str, output_file: str, instructions: str, api_key: str):
    """
    Edit an article from a file and save the result.
    
    Args:
        input_file: Path to input article file
        output_file: Path to save edited article
        instructions: Editing instructions
        api_key: OpenAI API key
    """
    # Read the article
    with open(input_file, 'r', encoding='utf-8') as f:
        article = f.read()
    
    print(f"Loaded article from {input_file}")
    print(f"Article length: {len(article)} characters")
    
    # Edit the article
    editor = ChapterEditor(api_key)
    edited_article = editor.edit_article_by_chapters(article, instructions)
    
    # Save the result
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(edited_article)
    
    print(f"Edited article saved to {output_file}")


if __name__ == "__main__":
    # Example usage
    API_KEY = "your-openai-api-key-here"
    
    # Example 1: Edit from string
    sample_article = """
    # Introduction
    This is a sample article with multiple sections.
    
    ## Chapter 1: Getting Started
    This chapter covers the basics of our topic.
    
    ## Chapter 2: Advanced Concepts
    Here we dive deeper into complex ideas.
    
    ## Conclusion
    Final thoughts and summary.
    """
    
    instructions = "Improve clarity, fix grammar, and enhance readability while maintaining the original meaning."
    
    # Uncomment to test:
    # edited = edit_long_article(sample_article, instructions, API_KEY)
    # print(edited)
    
    # Example 2: Edit from file
    # edit_article_from_file("input_article.txt", "edited_article.txt", instructions, API_KEY)