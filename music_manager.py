"""
Music Manager for AdStudio Pro
Download and manage royalty-free music for your videos
"""

import os
import json
from pathlib import Path
from datetime import datetime
import subprocess
import platform


class MusicManager:
    """Manage royalty-free music for video creation"""

    # Free music categories
    CATEGORIES = {
        "upbeat": {"name": "Upbeat & Energetic", "keywords": ["upbeat", "energetic", "happy", "pop"]},
        "corporate": {"name": "Corporate & Professional", "keywords": ["corporate", "business", "professional", "clean"]},
        "cinematic": {"name": "Cinematic & Epic", "keywords": ["cinematic", "epic", "dramatic", "trailer"]},
        "chill": {"name": "Chill & Relaxing", "keywords": ["chill", "relax", "lofi", "ambient"]},
        "electronic": {"name": "Electronic & Dance", "keywords": ["electronic", "dance", "edm", "synth"]},
        "acoustic": {"name": "Acoustic & Folk", "keywords": ["acoustic", "guitar", "folk", "indie"]},
        "hiphop": {"name": "Hip Hop & Beat", "keywords": ["hiphop", "beat", "rap", "urban"]},
        "holiday": {"name": "Holiday & Seasonal", "keywords": ["holiday", "christmas", "winter", "festive"]}
    }

    def __init__(self):
        self.music_dir = Path("music")
        self.music_dir.mkdir(exist_ok=True)
        self.cache_file = self.music_dir / "music_cache.json"
        self.cache = self._load_cache()
        self.player = self._detect_player()

    def _load_cache(self):
        """Load music cache from file"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {"downloaded": [], "favorites": []}

    def _save_cache(self):
        """Save music cache to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _detect_player(self):
        """Detect available audio player"""
        if platform.system() == "Windows":
            # Try common players
            players = [
                "C:/Program Files/Windows Media Player/wmplayer.exe",
                "C:/Program Files (x86)/Windows Media Player/wmplayer.exe",
            ]
            for player in players:
                if os.path.exists(player):
                    return player
            # Use default Windows command
            return "start"
        else:
            # Linux/Mac
            for player in ["afplay", "aplay", "mpv", "ffplay"]:
                result = os.system(f"which {player} > /dev/null 2>&1")
                if result == 0:
                    return player
        return None

    def get_free_music_sources(self):
        """Get list of free music sources"""
        return {
            "pixabay": {
                "name": "Pixabay Music",
                "url": "https://pixabay.com/music/",
                "description": "Free, no attribution required",
                "direct_download": True
            },
            "freesound": {
                "name": "Freesound",
                "url": "https://freesound.org/",
                "description": "Free sounds and music, attribution required",
                "direct_download": True
            },
            "mixkit": {
                "name": "Mixkit",
                "url": "https://mixkit.co/free-stock-music/",
                "description": "Free music for videos",
                "direct_download": True
            },
            "youtube_audio": {
                "name": "YouTube Audio Library",
                "url": "https://studio.youtube.com/channel/UC/music",
                "description": "Free music from YouTube",
                "direct_download": False
            }
        }

    def list_local_music(self):
        """List all local music files"""
        audio_exts = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
        music_files = []

        for f in self.music_dir.iterdir():
            if f.suffix.lower() in audio_exts and f.name != "music_cache.json":
                # Get file info
                size_mb = f.stat().st_size / (1024 * 1024)
                duration = self._get_audio_duration(f)
                
                music_files.append({
                    "path": str(f),
                    "name": f.stem,
                    "filename": f.name,
                    "size_mb": round(size_mb, 2),
                    "duration": duration,
                    "is_favorite": str(f) in self.cache.get("favorites", [])
                })

        return sorted(music_files, key=lambda x: x["name"])

    def _get_audio_duration(self, file_path):
        """Get audio duration using ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                seconds = float(result.stdout.strip())
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{minutes}:{secs:02d}"
        except:
            pass
        return "Unknown"

    def add_to_favorites(self, music_path):
        """Add a music file to favorites"""
        if music_path not in self.cache["favorites"]:
            self.cache["favorites"].append(music_path)
            self._save_cache()
            return True
        return False

    def remove_from_favorites(self, music_path):
        """Remove a music file from favorites"""
        if music_path in self.cache["favorites"]:
            self.cache["favorites"].remove(music_path)
            self._save_cache()
            return True
        return False

    def search_music(self, query):
        """Search local music files by name"""
        music_files = self.list_local_music()
        query_lower = query.lower()
        return [m for m in music_files if query_lower in m["name"].lower()]

    def get_random_music(self, category=None):
        """Get a random music file, optionally from a category"""
        music_files = self.list_local_music()
        if not music_files:
            return None
        
        import random
        if category:
            # Filter by category keywords
            keywords = self.CATEGORIES.get(category, {}).get("keywords", [])
            filtered = [m for m in music_files if any(kw in m["name"].lower() for kw in keywords)]
            if filtered:
                return random.choice(filtered)
        
        return random.choice(music_files)

    def preview_music(self, music_path):
        """Play a preview of the music file"""
        if not self.player:
            print("No audio player found on this system")
            return False

        if not os.path.exists(music_path):
            print(f"File not found: {music_path}")
            return False

        try:
            if self.player == "start":
                # Windows - use start command
                os.startfile(music_path)
            else:
                # Linux/Mac - use detected player
                subprocess.Popen([self.player, music_path])
            return True
        except Exception as e:
            print(f"Error playing preview: {e}")
            return False

    def stop_preview(self):
        """Stop music preview"""
        if platform.system() == "Windows":
            os.system("taskkill /IM wmplayer.exe /F > /dev/null 2>&1")
        else:
            os.system("pkill afplay > /dev/null 2>&1")
            os.system("pkill mpv > /dev/null 2>&1")

    def copy_music_file(self, source_path):
        """Copy a music file to the music folder"""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source_path}")

        dest = self.music_dir / source.name
        
        # Handle duplicate names
        counter = 1
        while dest.exists():
            dest = self.music_dir / f"{source.stem}_{counter}{source.suffix}"
            counter += 1

        import shutil
        shutil.copy2(source, dest)
        
        # Add to cache
        if str(dest) not in self.cache["downloaded"]:
            self.cache["downloaded"].append(str(dest))
            self._save_cache()

        return str(dest)

    def get_music_for_video(self, duration_seconds=None, style=None):
        """Get a suitable music file for a video"""
        music_files = self.list_local_music()
        
        if not music_files:
            return None

        # Filter by style if specified
        if style:
            keywords = self.CATEGORIES.get(style, {}).get("keywords", [])
            if keywords:
                filtered = [m for m in music_files if any(kw in m["name"].lower() for kw in keywords)]
                if filtered:
                    music_files = filtered

        # If duration specified, try to find close match
        if duration_seconds:
            # Sort by duration difference
            def parse_duration(d):
                if d == "Unknown":
                    return 999
                parts = d.split(":")
                return int(parts[0]) * 60 + int(parts[1])
            
            music_files.sort(key=lambda m: abs(parse_duration(m["duration"]) - duration_seconds))

        return music_files[0] if music_files else None

    def create_music_pack(self, pack_name, music_paths):
        """Create a music pack (folder with selected tracks)"""
        pack_dir = self.music_dir / "packs" / pack_name
        pack_dir.mkdir(parents=True, exist_ok=True)

        for path in music_paths:
            if os.path.exists(path):
                dest = pack_dir / Path(path).name
                import shutil
                shutil.copy2(path, dest)

        return str(pack_dir)

    def list_music_packs(self):
        """List all music packs"""
        packs_dir = self.music_dir / "packs"
        if not packs_dir.exists():
            return []

        packs = []
        for pack_dir in packs_dir.iterdir():
            if pack_dir.is_dir():
                tracks = list(pack_dir.glob("*.mp3")) + list(pack_dir.glob("*.wav"))
                packs.append({
                    "name": pack_dir.name,
                    "path": str(pack_dir),
                    "tracks": len(tracks)
                })

        return packs

    def print_music_library(self):
        """Print formatted music library"""
        music_files = self.list_local_music()
        
        print("\n" + "=" * 70)
        print("  YOUR MUSIC LIBRARY")
        print("=" * 70)
        
        if not music_files:
            print("\n  No music files found.")
            print("  Add music to the 'music' folder to use in videos.")
            print("\n  Legal free music sources:")
            print("  • https://pixabay.com/music/")
            print("  • https://mixkit.co/free-stock-music/")
            print("  • https://freesound.org/")
            return

        print(f"\n  Total tracks: {len(music_files)}\n")
        
        for i, music in enumerate(music_files, 1):
            fav = " ★" if music["is_favorite"] else ""
            print(f"  {i:2d}. {music['name']}{fav}")
            print(f"      Duration: {music['duration']} | Size: {music['size_mb']} MB")

        print("\n" + "=" * 70)

    def print_categories(self):
        """Print available music categories"""
        print("\n" + "=" * 70)
        print("  MUSIC CATEGORIES")
        print("=" * 70)
        
        for key, cat in self.CATEGORIES.items():
            print(f"\n  {key.upper()}")
            print(f"    {cat['name']}")
            print(f"    Keywords: {', '.join(cat['keywords'])}")

        print("\n" + "=" * 70)


# Quick functions
def setup_music_folder():
    """Create the music folder structure"""
    manager = MusicManager()
    
    # Create subfolders for categories
    for category in MusicManager.CATEGORIES:
        (manager.music_dir / category).mkdir(exist_ok=True)
    
    # Create packs folder
    (manager.music_dir / "packs").mkdir(exist_ok=True)
    
    print("Music folder structure created!")
    print(f"Location: {manager.music_dir.absolute()}")
    print("\nAdd your music files to this folder.")
    
    return manager


def list_free_sources():
    """List free music sources"""
    manager = MusicManager()
    sources = manager.get_free_music_sources()
    
    print("\n" + "=" * 70)
    print("  FREE MUSIC SOURCES (Legal for Commercial Use)")
    print("=" * 70)
    
    for key, source in sources.items():
        print(f"\n  {source['name']}")
        print(f"    URL: {source['url']}")
        print(f"    {source['description']}")

    print("\n" + "=" * 70)
    print("\n  TIP: Download music and add it to the 'music' folder")


if __name__ == "__main__":
    manager = MusicManager()
    manager.print_music_library()
    manager.print_categories()
    list_free_sources()
