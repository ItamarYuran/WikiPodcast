#!/usr/bin/env python3
"""
Wikipedia to Podcast Pipeline - Main Entry Point

This script orchestrates the entire pipeline:
1. Fetches Wikipedia content (trending, featured, or specific topics)
2. Generates podcast scripts in various styles
3. Provides interactive menu for different operations
4. Manages the entire workflow from content to scripts

Usage:
    python main.py                    # Interactive mode
    python main.py --trending 5       # Generate 5 trending articles
    python main.py --topic "AI"       # Generate script for specific topic
    python main.py --featured 3       # Generate 3 featured articles
"""

import argparse
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from pipeline import PodcastPipeline
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all pipeline modules are in the same directory")
    sys.exit(1)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Wikipedia to Podcast Pipeline")
    parser.add_argument("--trending", type=int, metavar="COUNT", 
                       help="Generate scripts for COUNT trending articles")
    parser.add_argument("--featured", type=int, metavar="COUNT",
                       help="Generate scripts for COUNT featured articles")
    parser.add_argument("--topic", type=str, metavar="TOPIC",
                       help="Generate script for specific Wikipedia topic")
    parser.add_argument("--style", type=str, default="conversational",
                       help="Podcast style (default: conversational)")
    parser.add_argument("--duration", type=str, default="medium",
                       choices=["short", "medium", "long", "full"],
                       help="Target podcast duration (short=5min, medium=10min, long=15min, full=complete)")
    parser.add_argument("--custom", type=str, 
                       help="Custom instructions for script generation")
    parser.add_argument("--voice", type=str, default="nova",
                       help="OpenAI voice for audio generation (nova, onyx, shimmer, etc.)")
    parser.add_argument("--audio", action="store_true",
                       help="Generate complete podcast with audio (topic → script → audio)")
    parser.add_argument("--no-audio", action="store_true",
                       help="Generate script only, skip audio generation")
    
    return parser.parse_args()


def run_command_line_mode(pipeline, args):
    """Execute command line operations"""
    if args.trending:
        pipeline.fetch_and_generate_trending(args.trending, args.style)
    elif args.featured:
        pipeline.fetch_and_generate_featured(args.featured, args.style)
    elif args.topic:
        # Decide whether to generate audio
        generate_audio = args.audio or (not args.no_audio and pipeline.openai_client)
        
        if generate_audio:
            pipeline.generate_complete_podcast(args.topic, args.style, args.voice, args.custom, True, args.duration)
        else:
            pipeline.generate_single_topic(args.topic, args.style, args.custom, args.duration)
    else:
        # No command line args, run interactive mode
        return False
    
    return True


def run_interactive_mode(pipeline):
    """Run the interactive menu system"""
    pipeline.show_status()
    pipeline.interactive_mode()


def main():
    """Main entry point"""
    print("🎙️  Wikipedia Podcast Pipeline Starting...")
    print("=" * 50)
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Initialize pipeline
        pipeline = PodcastPipeline()
        
        # Run command line mode or interactive mode
        if not run_command_line_mode(pipeline, args):
            run_interactive_mode(pipeline)
            
    except KeyboardInterrupt:
        print("\n\n👋 Pipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline Error: {e}")
        print("Check your API keys and internet connection")
        sys.exit(1)


if __name__ == "__main__":
    main()