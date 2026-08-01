"""
AI Video Generator for Social Media Ads - Simple Version
Uses FFmpeg directly for reliable video creation
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import platform


class VideoGenerator:
    """Simple video generator using FFmpeg"""

    TEMPLATES = {
        "instagram_reels": {"width": 1080, "height": 1920, "name": "Instagram Reels"},
        "tiktok": {"width": 1080, "height": 1920, "name": "TikTok"},
        "youtube": {"width": 1920, "height": 1080, "name": "YouTube"},
        "instagram_post": {"width": 1080, "height": 1080, "name": "Instagram Post"},
        "facebook": {"width": 1920, "height": 1080, "name": "Facebook"},
        "twitter": {"width": 1280, "height": 720, "name": "Twitter"}
    }

    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp_frames")
        self.temp_dir.mkdir(exist_ok=True)
        self.font_path = self._find_font()

    def _find_font(self):
        """Find a system font"""
        if platform.system() == "Windows":
            fonts = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "C:/Windows/Fonts/tahoma.ttf",
            ]
        else:
            fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        for f in fonts:
            if os.path.exists(f):
                return f
        return None

    def _create_text_frame(self, text, width, height, bg_color=(0, 0, 0), text_color='white', font_size=80):
        """Create a single frame with text"""
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        if self.font_path:
            font = ImageFont.truetype(self.font_path, font_size)
        else:
            font = ImageFont.load_default()

        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw text with outline
        for offset in [-2, -1, 0, 1, 2]:
            draw.text((x+offset, y), text, fill='black', font=font)
            draw.text((x, y+offset), text, fill='black', font=font)
        draw.text((x, y), text, fill=text_color, font=font)

        return img

    def _create_image_frame(self, image_path, width, height):
        """Create a frame from an image, resized to fit"""
        img = Image.open(image_path).convert('RGB')
        
        # Calculate resize to fit while maintaining aspect ratio
        img_ratio = img.width / img.height
        target_ratio = width / height

        if img_ratio > target_ratio:
            new_width = width
            new_height = int(width / img_ratio)
        else:
            new_height = height
            new_width = int(height * img_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)

        # Center on black background
        bg = Image.new('RGB', (width, height), (0, 0, 0))
        paste_x = (width - new_width) // 2
        paste_y = (height - new_height) // 2
        bg.paste(img, (paste_x, paste_y))

        return bg

    def _images_to_video(self, images, output_path, fps=30, duration_per_image=3):
        """Convert images to video using FFmpeg"""
        template = self.TEMPLATES.get("youtube")  # Default template
        
        # Create frames directory
        for i, img_path in enumerate(images):
            frame = self._create_image_frame(img_path, template["width"], template["height"])
            frame.save(self.temp_dir / f"frame_{i:04d}.png")
            
            # Duplicate frames for duration
            for j in range(1, int(fps * duration_per_image)):
                frame.save(self.temp_dir / f"frame_{i:04d}_{j:04d}.png")

        # Use FFmpeg to create video
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return output_path

    def create_text_video(self, texts, platform="instagram_reels", 
                          duration_per_text=3, bg_color=(0, 0, 0), 
                          text_color='white', font_size=80):
        """Create video with text slides"""
        template = self.TEMPLATES.get(platform, self.TEMPLATES["youtube"])
        
        # Clean temp directory
        for f in self.temp_dir.glob("*"):
            f.unlink()

        # Create frames for each text
        frame_num = 0
        fps = 30
        frames_per_text = int(fps * duration_per_text)

        for text in texts:
            frame = self._create_text_frame(
                text, template["width"], template["height"],
                bg_color, text_color, font_size
            )
            
            for i in range(frames_per_text):
                frame.save(self.temp_dir / f"frame_{frame_num:04d}.png")
                frame_num += 1

        # Output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"text_video_{platform}_{timestamp}.mp4"

        # Create video with FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp files
        for f in self.temp_dir.glob("*"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        print(f"Video saved to: {output_path}")
        return str(output_path)

    def create_from_folder(self, folder_path, platform="instagram_reels",
                           duration_per_slide=3, texts=None):
        """Create video from images in a folder"""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Get images
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        images = sorted([str(f) for f in folder.iterdir() if f.suffix.lower() in image_exts])
        
        if not images:
            raise ValueError(f"No images found in {folder_path}")

        print(f"Found {len(images)} images")

        if texts is None:
            texts = [""] * len(images)
        while len(texts) < len(images):
            texts.append("")

        template = self.TEMPLATES.get(platform, self.TEMPLATES["youtube"])
        
        # Clean temp
        for f in self.temp_dir.glob("*"):
            f.unlink()

        # Create frames
        frame_num = 0
        fps = 30
        frames_per_slide = int(fps * duration_per_slide)

        for img_path, text in zip(images, texts):
            if text:
                # Create image with text overlay
                frame = self._create_image_frame(img_path, template["width"], template["height"])
                draw = ImageDraw.Draw(frame)
                
                if self.font_path:
                    font = ImageFont.truetype(self.font_path, 70)
                else:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                x = (template["width"] - text_width) // 2
                y = template["height"] - 200
                
                # Draw text with outline
                for offset in [-2, -1, 0, 1, 2]:
                    draw.text((x+offset, y), text, fill='black', font=font)
                    draw.text((x, y+offset), text, fill='black', font=font)
                draw.text((x, y), text, fill='white', font=font)
            else:
                frame = self._create_image_frame(img_path, template["width"], template["height"])

            for i in range(frames_per_slide):
                frame.save(self.temp_dir / f"frame_{frame_num:04d}.png")
                frame_num += 1

        # Output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"video_{platform}_{timestamp}.mp4"

        # Create video
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up
        for f in self.temp_dir.glob("*"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        print(f"Video saved to: {output_path}")
        return str(output_path)


def quick_video(images_folder, platform="instagram_reels", texts=None):
    """One-line video creation"""
    generator = VideoGenerator()
    return generator.create_from_folder(images_folder, platform, texts=texts)


if __name__ == "__main__":
    print("AI Video Generator")
    print("=" * 40)
    print("\nAvailable platforms:")
    generator = VideoGenerator()
    for key, template in generator.get_templates().items():
        print(f"  - {key}: {template['width']}x{template['height']}")
