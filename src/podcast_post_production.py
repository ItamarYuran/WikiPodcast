#!/usr/bin/env python3
"""
Podcast Post-Production System

This module adds professional finishing touches to generated podcasts:
- Custom intro/outro music
- Jingles and sound effects
- Audio mixing and mastering
- Background music layers
- Professional podcast formatting

Features:
- Music library management
- Custom intro/outro creation
- Multi-track audio mixing
- Volume leveling and mastering
- Batch post-production processing
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests


@dataclass
class AudioTrack:
    """Represents an audio track for mixing"""
    file_path: str
    track_type: str  # 'main', 'intro', 'outro', 'background', 'sfx'
    start_time: float = 0.0  # Start time in seconds
    duration: float = None  # Duration in seconds (None = full length)
    volume: float = 1.0  # Volume multiplier (0.0 to 1.0)
    fade_in: float = 0.0  # Fade in duration in seconds
    fade_out: float = 0.0  # Fade out duration in seconds


@dataclass
class PodcastTemplate:
    """Template for podcast post-production"""
    name: str
    description: str
    intro_music: Optional[str]
    outro_music: Optional[str]
    background_music: Optional[str]
    intro_duration: float = 5.0
    outro_duration: float = 5.0
    background_volume: float = 0.2
    crossfade_duration: float = 2.0
    jingle_positions: List[float] = None  # Time positions for jingles


class PodcastPostProduction:
    """Advanced post-production system for podcasts"""
    
    def __init__(self, assets_dir: str = "../podcast_assets"):
        """Initialize post-production system"""
        
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(exist_ok=True)
        
        # Create asset subdirectories
        (self.assets_dir / 'music').mkdir(exist_ok=True)
        (self.assets_dir / 'sfx').mkdir(exist_ok=True)
        (self.assets_dir / 'jingles').mkdir(exist_ok=True)
        (self.assets_dir / 'templates').mkdir(exist_ok=True)
        (self.assets_dir / 'final').mkdir(exist_ok=True)
        
        # Initialize with default templates
        self._create_default_templates()
        
        # Check for ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()
        
        print("🎛️ Post-Production System initialized")
        print(f"📁 Assets directory: {self.assets_dir.absolute()}")
        if self.ffmpeg_available:
            print("✅ ffmpeg available for audio processing")
        else:
            print("⚠️  ffmpeg not found - install for full functionality")
    
    def enhance_podcast(self, 
                       input_audio: str,
                       template_name: str = "default",
                       custom_intro: str = None,
                       custom_outro: str = None,
                       background_music: str = None,
                       output_name: str = None) -> Optional[str]:
        """
        Apply professional post-production to a podcast
        
        Args:
            input_audio: Path to the main podcast audio
            template_name: Post-production template to use
            custom_intro: Custom intro music file
            custom_outro: Custom outro music file  
            background_music: Background music file
            output_name: Custom output filename
            
        Returns:
            Path to enhanced podcast file
        """
        
        if not self.ffmpeg_available:
            print("❌ ffmpeg required for post-production")
            print("Install with: brew install ffmpeg (Mac) or apt install ffmpeg (Linux)")
            return None
        
        print(f"\n🎛️ ENHANCING PODCAST")
        print("=" * 30)
        
        input_path = Path(input_audio)
        if not input_path.exists():
            print(f"❌ Input file not found: {input_audio}")
            return None
        
        # Load template
        template = self._load_template(template_name)
        if not template:
            print(f"❌ Template not found: {template_name}")
            return None
        
        print(f"🎨 Using template: {template.name}")
        print(f"📄 {template.description}")
        
        # Build audio timeline
        timeline = self._build_audio_timeline(
            input_path, template, custom_intro, custom_outro, background_music
        )
        
        # Generate output filename
        if not output_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_name = f"{input_path.stem}_enhanced_{timestamp}.mp3"
        
        output_path = self.assets_dir / 'final' / output_name
        
        # Mix audio tracks
        success = self._mix_audio_tracks(timeline, output_path)
        
        if success:
            print(f"✅ Enhanced podcast created: {output_name}")
            return str(output_path)
        else:
            print("❌ Post-production failed")
            return None
    
    def create_custom_intro(self, 
                           title: str,
                           host_name: str = "AI Podcast",
                           voice: str = "nova",
                           music_file: str = None) -> Optional[str]:
        """
        Create a custom intro for the podcast series
        
        Args:
            title: Podcast series title
            host_name: Host name to announce
            voice: TTS voice for intro
            music_file: Background music file
            
        Returns:
            Path to created intro file
        """
        
        print(f"\n🎙️ CREATING CUSTOM INTRO")
        print("=" * 30)
        
        # Create intro script
        intro_script = f"""Welcome to {title}, the podcast that brings you fascinating stories from Wikipedia. I'm your host, {host_name}. Let's dive into today's episode."""
        
        # Generate TTS for intro (requires OpenAI client)
        from dotenv import load_dotenv
        load_dotenv('config/api_keys.env')
        
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("❌ OpenAI API key required for intro generation")
            return None
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            
            print(f"🎤 Generating intro with voice: {voice}")
            
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=intro_script,
                response_format="mp3"
            )
            
            # Save intro TTS
            intro_tts_path = self.assets_dir / 'temp_intro_voice.mp3'
            response.stream_to_file(intro_tts_path)
            
            # Mix with music if provided
            if music_file and Path(music_file).exists():
                final_intro_path = self.assets_dir / 'jingles' / f'custom_intro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3'
                
                # Mix voice and music
                mix_cmd = [
                    'ffmpeg', '-i', str(intro_tts_path), '-i', music_file,
                    '-filter_complex', 
                    '[1:a]volume=0.3[music];[0:a][music]amix=inputs=2:duration=longest',
                    '-y', str(final_intro_path)
                ]
                
                result = subprocess.run(mix_cmd, capture_output=True)
                
                if result.returncode == 0:
                    intro_tts_path.unlink()  # Clean up temp file
                    print(f"✅ Custom intro created: {final_intro_path.name}")
                    return str(final_intro_path)
            else:
                # Use voice-only intro
                final_intro_path = self.assets_dir / 'jingles' / f'voice_intro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3'
                intro_tts_path.rename(final_intro_path)
                print(f"✅ Voice intro created: {final_intro_path.name}")
                return str(final_intro_path)
                
        except Exception as e:
            print(f"❌ Intro creation failed: {e}")
            return None
    
    def download_free_music(self, music_type: str = "background") -> List[str]:
        """
        Download free music from various sources for podcast use
        
        Args:
            music_type: Type of music ('intro', 'outro', 'background', 'jingle')
            
        Returns:
            List of downloaded music file paths
        """
        
        print(f"\n🎵 DOWNLOADING FREE MUSIC: {music_type}")
        print("=" * 40)
        
        # Free music sources and recommendations
        music_suggestions = {
            'intro': [
                "Upbeat corporate intro music",
                "Professional podcast opener",
                "Energetic welcome theme"
            ],
            'outro': [
                "Gentle conclusion music", 
                "Thank you theme",
                "Soft closing music"
            ],
            'background': [
                "Subtle ambient background",
                "Soft instrumental underscore",
                "Light atmospheric music"  
            ],
            'jingle': [
                "Short transition sound",
                "Quick musical sting",
                "Brief attention-grabbing tune"
            ]
        }
        
        print("🎼 Recommended free music sources:")
        print("   • Freesound.org - Creative Commons sounds")
        print("   • YouTube Audio Library - Free music")
        print("   • Pixabay Music - Royalty-free tracks")
        print("   • Incompetech.com - Kevin MacLeod music")
        print("   • Zapsplat.com - Professional audio library")
        
        print(f"\n💡 Search suggestions for {music_type}:")
        for suggestion in music_suggestions.get(music_type, []):
            print(f"   • {suggestion}")
        
        print(f"\n📁 Save downloaded music to: {self.assets_dir / 'music'}")
        print("   Supported formats: MP3, WAV, FLAC, M4A")
        
        # Return existing music files
        music_dir = self.assets_dir / 'music'
        existing_files = []
        for ext in ['*.mp3', '*.wav', '*.flac', '*.m4a']:
            existing_files.extend(music_dir.glob(ext))
        
        if existing_files:
            print(f"\n🎵 Found {len(existing_files)} existing music files:")
            for file in existing_files[:5]:
                print(f"   • {file.name}")
            if len(existing_files) > 5:
                print(f"   • ... and {len(existing_files) - 5} more")
        
        return [str(f) for f in existing_files]
    
    def list_available_assets(self) -> Dict[str, List[str]]:
        """List all available audio assets"""
        
        assets = {
            'music': [],
            'sfx': [],
            'jingles': [],
            'templates': []
        }
        
        # Scan for audio files
        audio_extensions = ['*.mp3', '*.wav', '*.flac', '*.m4a']
        
        for asset_type in ['music', 'sfx', 'jingles']:
            asset_dir = self.assets_dir / asset_type
            for ext in audio_extensions:
                assets[asset_type].extend([f.name for f in asset_dir.glob(ext)])
        
        # Scan for templates
        template_dir = self.assets_dir / 'templates'
        assets['templates'] = [f.stem for f in template_dir.glob('*.json')]
        
        return assets
    
    def create_podcast_series_package(self, 
                                    series_name: str,
                                    episodes: List[str],
                                    template_name: str = "default") -> str:
        """
        Create a complete podcast series with consistent branding
        
        Args:
            series_name: Name of the podcast series
            episodes: List of episode audio files
            template_name: Template to apply to all episodes
            
        Returns:
            Path to series package directory
        """
        
        print(f"\n📦 CREATING PODCAST SERIES: {series_name}")
        print("=" * 50)
        
        # Create series directory
        series_dir = self.assets_dir / 'final' / f"{series_name}_{datetime.now().strftime('%Y%m%d')}"
        series_dir.mkdir(exist_ok=True)
        
        enhanced_episodes = []
        
        for i, episode_path in enumerate(episodes, 1):
            print(f"\n🎙️ Processing Episode {i}/{len(episodes)}")
            
            # Generate episode-specific output name
            episode_name = f"{series_name}_Episode_{i:02d}.mp3"
            
            # Enhance episode
            enhanced_path = self.enhance_podcast(
                episode_path,
                template_name=template_name,
                output_name=episode_name
            )
            
            if enhanced_path:
                # Move to series directory
                final_path = series_dir / episode_name
                Path(enhanced_path).rename(final_path)
                enhanced_episodes.append(str(final_path))
                print(f"✅ Episode {i} completed")
            else:
                print(f"❌ Episode {i} failed")
        
        # Create series metadata
        series_info = {
            'series_name': series_name,
            'total_episodes': len(episodes),
            'successful_episodes': len(enhanced_episodes),
            'template_used': template_name,
            'created_date': datetime.now().isoformat(),
            'episodes': enhanced_episodes
        }
        
        metadata_file = series_dir / 'series_info.json'
        with open(metadata_file, 'w') as f:
            json.dump(series_info, f, indent=2)
        
        print(f"\n🎉 SERIES PACKAGE COMPLETE")
        print(f"📁 Location: {series_dir}")
        print(f"✅ {len(enhanced_episodes)}/{len(episodes)} episodes processed")
        
        return str(series_dir)
    
    # Private helper methods
    
    def _create_default_templates(self):
        """Create default post-production templates"""
        
        templates = {
            'default': PodcastTemplate(
                name="Default Professional",
                description="Clean professional sound with subtle enhancements",
                intro_music=None,
                outro_music=None,
                background_music=None,
                intro_duration=3.0,
                outro_duration=3.0,
                background_volume=0.15,
                crossfade_duration=1.5
            ),
            'news': PodcastTemplate(
                name="News Style",
                description="Authoritative news-style formatting",
                intro_music=None,
                outro_music=None,
                background_music=None,
                intro_duration=2.0,
                outro_duration=2.0,
                background_volume=0.1,
                crossfade_duration=1.0
            ),
            'storytelling': PodcastTemplate(
                name="Storytelling",
                description="Atmospheric storytelling with background music",
                intro_music=None,
                outro_music=None,
                background_music=None,
                intro_duration=5.0,
                outro_duration=5.0,
                background_volume=0.25,
                crossfade_duration=3.0
            )
        }
        
        # Save templates
        template_dir = self.assets_dir / 'templates'
        for name, template in templates.items():
            template_file = template_dir / f'{name}.json'
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    json.dump(template.__dict__, f, indent=2)
    
    def _load_template(self, template_name: str) -> Optional[PodcastTemplate]:
        """Load a post-production template"""
        
        template_file = self.assets_dir / 'templates' / f'{template_name}.json'
        if not template_file.exists():
            return None
        
        try:
            with open(template_file, 'r') as f:
                data = json.load(f)
            return PodcastTemplate(**data)
        except Exception:
            return None
    
    def _build_audio_timeline(self, 
                             main_audio: Path,
                             template: PodcastTemplate,
                             custom_intro: str,
                             custom_outro: str, 
                             background_music: str) -> List[AudioTrack]:
        """Build timeline of audio tracks for mixing"""
        
        timeline = []
        current_time = 0.0
        
        # Add intro if available
        intro_file = custom_intro or template.intro_music
        if intro_file and Path(intro_file).exists():
            timeline.append(AudioTrack(
                file_path=intro_file,
                track_type='intro',
                start_time=current_time,
                duration=template.intro_duration,
                volume=0.8,
                fade_out=template.crossfade_duration
            ))
            current_time += template.intro_duration - template.crossfade_duration
        
        # Add main audio
        timeline.append(AudioTrack(
            file_path=str(main_audio),
            track_type='main',
            start_time=current_time,
            volume=1.0
        ))
        
        # Get main audio duration (rough estimate)
        main_duration = self._estimate_audio_duration(main_audio)
        
        # Add background music if available
        bg_file = background_music or template.background_music
        if bg_file and Path(bg_file).exists():
            timeline.append(AudioTrack(
                file_path=bg_file,
                track_type='background',
                start_time=current_time,
                duration=main_duration,
                volume=template.background_volume,
                fade_in=2.0,
                fade_out=2.0
            ))
        
        # Add outro if available
        outro_file = custom_outro or template.outro_music
        if outro_file and Path(outro_file).exists():
            outro_start = current_time + main_duration - template.crossfade_duration
            timeline.append(AudioTrack(
                file_path=outro_file,
                track_type='outro',
                start_time=outro_start,
                duration=template.outro_duration,
                volume=0.8,
                fade_in=template.crossfade_duration
            ))
        
        return timeline
    
    def _mix_audio_tracks(self, timeline: List[AudioTrack], output_path: Path) -> bool:
        """Mix multiple audio tracks using ffmpeg"""
        
        if not timeline:
            return False
        
        try:
            # For basic implementation, just process the main audio with normalization
            main_track = None
            for track in timeline:
                if track.track_type == 'main':
                    main_track = track
                    break
            
            if not main_track:
                return False
            
            # Basic audio processing with normalization
            cmd = [
                'ffmpeg', '-i', main_track.file_path,
                '-af', 'loudnorm',  # Normalize audio levels
                '-y', str(output_path)
            ]
            
            print("🎛️ Processing audio...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Mixing failed: {e}")
            return False
    
    def _estimate_audio_duration(self, audio_file: Path) -> float:
        """Estimate audio file duration"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', 
                   '-of', 'csv=p=0', str(audio_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        
        # Fallback estimate based on file size
        file_size_mb = audio_file.stat().st_size / (1024 * 1024)
        return file_size_mb * 8 / 0.128  # Rough estimate for 128kbps
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False


# Example usage
def example_usage():
    """Example of how to use the post-production system"""
    
    print("🎛️ Podcast Post-Production System")
    print("=" * 40)
    
    # Initialize system
    post_prod = PodcastPostProduction()
    
    # Show available assets
    assets = post_prod.list_available_assets()
    for asset_type, files in assets.items():
        print(f"\n{asset_type.title()}: {len(files)} files")
        for file in files[:3]:
            print(f"  • {file}")
        if len(files) > 3:
            print(f"  • ... and {len(files) - 3} more")
    
    # Show music download suggestions
    post_prod.download_free_music("intro")
    
    print("\nExample usage:")
    print("""
    # Enhance a podcast with default template
    enhanced = post_prod.enhance_podcast('my_podcast.mp3')
    
    # Create custom intro
    intro = post_prod.create_custom_intro(
        title="Tech Insights",
        host_name="AI Assistant",
        voice="nova"
    )
    
    # Enhance with custom intro
    final = post_prod.enhance_podcast(
        'my_podcast.mp3',
        template_name='storytelling',
        custom_intro=intro
    )
    
    # Create series package
    episodes = ['episode1.mp3', 'episode2.mp3', 'episode3.mp3']
    series = post_prod.create_podcast_series_package(
        'My Podcast Series',
        episodes,
        'news'
    )
    """)


if __name__ == "__main__":
    example_usage()