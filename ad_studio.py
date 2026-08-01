"""
AdStudio Pro - Professional Video Generator for Ads
Full-featured video creation with transitions, music, animations
"""

import os
import subprocess
import json
import math
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import platform
import random


class AdStudio:
    """Professional Video Studio for Creating Ad Videos"""

    # Platform Templates
    PLATFORMS = {
        "instagram_reels": {"width": 1080, "height": 1920, "fps": 30, "name": "Instagram Reels"},
        "tiktok": {"width": 1080, "height": 1920, "fps": 30, "name": "TikTok"},
        "youtube": {"width": 1920, "height": 1080, "fps": 30, "name": "YouTube"},
        "youtube_shorts": {"width": 1080, "height": 1920, "fps": 30, "name": "YouTube Shorts"},
        "instagram_post": {"width": 1080, "height": 1080, "fps": 30, "name": "Instagram Post"},
        "facebook": {"width": 1920, "height": 1080, "fps": 30, "name": "Facebook"},
        "twitter": {"width": 1280, "height": 720, "fps": 30, "name": "Twitter"},
        "linkedin": {"width": 1920, "height": 1080, "fps": 30, "name": "LinkedIn"},
        "pinterest": {"width": 1000, "height": 1500, "fps": 30, "name": "Pinterest"},
    }

    # Ad Templates
    TEMPLATES = {
        "sale": {
            "name": "Flash Sale",
            "bg_colors": [(220, 20, 60), (255, 69, 0)],
            "text_color": "white",
            "accent_color": (255, 215, 0),
            "texts": ["FLASH SALE", "50% OFF", "LIMITED TIME", "SHOP NOW"],
            "font_size": 100
        },
        "product_launch": {
            "name": "Product Launch",
            "bg_colors": [(20, 20, 40), (50, 50, 100)],
            "text_color": "white",
            "accent_color": (0, 200, 255),
            "texts": ["NEW ARRIVAL", "JUST LAUNCHED", "BE THE FIRST", "GET IT NOW"],
            "font_size": 90
        },
        "discount": {
            "name": "Mega Discount",
            "bg_colors": [(0, 150, 0), (50, 200, 50)],
            "text_color": "white",
            "accent_color": (255, 255, 0),
            "texts": ["MEGA SALE", "UP TO 70% OFF", "TODAY ONLY", "HURRY!"],
            "font_size": 100
        },
        "black_friday": {
            "name": "Black Friday",
            "bg_colors": [(10, 10, 10), (40, 40, 40)],
            "text_color": "white",
            "accent_color": (255, 215, 0),
            "texts": ["BLACK FRIDAY", "BIGGEST SALE", "SAVE BIG", "DON'T MISS OUT"],
            "font_size": 100
        },
        "summer": {
            "name": "Summer Vibes",
            "bg_colors": [(255, 165, 0), (255, 99, 71)],
            "text_color": "white",
            "accent_color": (255, 255, 100),
            "texts": ["SUMMER SALE", "SUNNY DEALS", "HOT OFFERS", "ENJOY NOW"],
            "font_size": 95
        },
        "elegant": {
            "name": "Elegant Premium",
            "bg_colors": [(20, 20, 30), (60, 40, 80)],
            "text_color": "white",
            "accent_color": (212, 175, 55),
            "texts": ["EXCLUSIVE", "PREMIUM COLLECTION", "LUXURY LIVING", "DISCOVER NOW"],
            "font_size": 85
        },
        "minimal": {
            "name": "Minimal Clean",
            "bg_colors": [(255, 255, 255), (240, 240, 240)],
            "text_color": "black",
            "accent_color": (50, 50, 50),
            "texts": ["NEW", "SIMPLE", "ELEGANT", "SHOP"],
            "font_size": 120
        },
        "fitness": {
            "name": "Fitness Motivation",
            "bg_colors": [(0, 0, 0), (139, 0, 0)],
            "text_color": "white",
            "accent_color": (255, 69, 0),
            "texts": ["NO PAIN", "NO GAIN", "PUSH HARDER", "GET FIT NOW"],
            "font_size": 100
        },
        "food": {
            "name": "Food & Restaurant",
            "bg_colors": [(139, 69, 19), (210, 105, 30)],
            "text_color": "white",
            "accent_color": (255, 215, 0),
            "texts": ["TODAY'S SPECIAL", "FRESH & TASTY", "ORDER NOW", "FREE DELIVERY"],
            "font_size": 90
        },
        "tech": {
            "name": "Tech & Gadgets",
            "bg_colors": [(0, 20, 40), (0, 50, 100)],
            "text_color": "white",
            "accent_color": (0, 200, 255),
            "texts": ["FUTURE IS HERE", "TECH REVOLUTION", "UPGRADE NOW", "INNOVATION"],
            "font_size": 95
        }
    }

    # Transition Types
    TRANSITIONS = {
        "none": "No transition",
        "fade": "Fade in/out",
        "slide_left": "Slide from right",
        "slide_right": "Slide from left",
        "slide_up": "Slide from bottom",
        "slide_down": "Slide from top",
        "zoom": "Zoom in",
        "zoom_out": "Zoom out",
        "dissolve": "Dissolve blend",
        "wipe": "Wipe transition"
    }

    # Animation Types for Text
    TEXT_ANIMATIONS = {
        "none": "No animation",
        "fade_in": "Fade in",
        "fade_out": "Fade out",
        "slide_left": "Slide from left",
        "slide_right": "Slide from right",
        "typewriter": "Typewriter effect",
        "bounce": "Bounce in",
        "scale_up": "Scale up"
    }

    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp_frames")
        self.temp_dir.mkdir(exist_ok=True)
        self.music_dir = Path("music")
        self.music_dir.mkdir(exist_ok=True)
        self.font_path = self._find_font()
        self.assets_dir = Path("assets")
        self.assets_dir.mkdir(exist_ok=True)

    def _find_font(self):
        """Find system font"""
        if platform.system() == "Windows":
            fonts = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/calibrib.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/tahomabd.ttf",
            ]
        else:
            fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        for f in fonts:
            if os.path.exists(f):
                return f
        return None

    def _get_font(self, size, bold=True):
        """Get font with specified size"""
        if bold and self.font_path:
            # Try bold version
            bold_path = self.font_path.replace(".ttf", "bd.ttf")
            if os.path.exists(bold_path):
                return ImageFont.truetype(bold_path, size)
        if self.font_path:
            return ImageFont.truetype(self.font_path, size)
        return ImageFont.load_default()

    def _create_gradient(self, width, height, color1, color2, direction='vertical'):
        """Create a gradient background"""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return img

    def _draw_text_with_effects(self, draw, text, position, font, 
                                 text_color='white', shadow=True, 
                                 outline=True, glow=False, glow_color=(255, 215, 0)):
        """Draw text with professional effects"""
        x, y = position
        
        # Glow effect
        if glow:
            for offset in range(8, 0, -1):
                glow_alpha = int(50 - offset * 5)
                for dx in range(-offset, offset+1):
                    for dy in range(-offset, offset+1):
                        draw.text((x+dx, y+dy), text, fill=glow_color, font=font)
        
        # Shadow
        if shadow:
            for offset in [3, 2, 1]:
                draw.text((x+offset, y+offset), text, fill=(0, 0, 0), font=font)
                draw.text((x+offset, y), text, fill=(0, 0, 0), font=font)
                draw.text((x, y+offset), text, fill=(0, 0, 0), font=font)
        
        # Outline
        if outline:
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), text, fill=(0, 0, 0), font=font)
        
        # Main text
        draw.text((x, y), text, fill=text_color, font=font)

    def _center_text(self, draw, text, font, width, y=None):
        """Get centered text position"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        if y is None:
            y = (width - text_height) // 2  # Will be overridden
        return x, y, text_width, text_height

    def _apply_transition(self, frame1, frame2, transition_type, progress):
        """Apply transition between two frames"""
        if transition_type == "none" or progress < 0 or progress > 1:
            return frame2 if progress >= 0.5 else frame1
        
        w, h = frame1.size
        
        if transition_type == "fade":
            return Image.blend(frame1, frame2, progress)
        
        elif transition_type == "slide_left":
            offset = int(w * progress)
            result = Image.new('RGB', (w, h))
            result.paste(frame1, (-offset, 0))
            result.paste(frame2, (w - offset, 0))
            return result
        
        elif transition_type == "slide_right":
            offset = int(w * progress)
            result = Image.new('RGB', (w, h))
            result.paste(frame1, (offset, 0))
            result.paste(frame2, (-w + offset, 0))
            return result
        
        elif transition_type == "slide_up":
            offset = int(h * progress)
            result = Image.new('RGB', (w, h))
            result.paste(frame1, (0, offset))
            result.paste(frame2, (0, -h + offset))
            return result
        
        elif transition_type == "slide_down":
            offset = int(h * progress)
            result = Image.new('RGB', (w, h))
            result.paste(frame1, (0, -offset))
            result.paste(frame2, (0, h - offset))
            return result
        
        elif transition_type == "zoom":
            scale = 0.5 + progress * 0.5
            new_w, new_h = int(w * scale), int(h * scale)
            img2 = frame2.resize((new_w, new_h), Image.LANCZOS)
            result = Image.new('RGB', (w, h))
            paste_x = (w - new_w) // 2
            paste_y = (h - new_h) // 2
            result.paste(img2, (paste_x, paste_y))
            return result
        
        elif transition_type == "dissolve":
            return Image.blend(frame1, frame2, progress)
        
        elif transition_type == "wipe":
            result = frame1.copy()
            draw = ImageDraw.Draw(result)
            x = int(w * progress)
            draw.rectangle([x, 0, w, h], fill=None)
            result = Image.composite(frame2, result, Image.new('L', (w, h), int(255 * progress)))
            return result
        
        return frame2

    def _create_text_animation_frame(self, text, width, height, progress,
                                      font_size=100, text_color='white',
                                      animation='fade_in', bg_color=(0, 0, 0),
                                      accent_color=(255, 215, 0)):
        """Create a single animated text frame"""
        # Create background
        if isinstance(bg_color, tuple) and len(bg_color) == 2:
            img = self._create_gradient(width, height, bg_color[0], bg_color[1])
        else:
            img = Image.new('RGB', (width, height), bg_color)
        
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size)
        
        # Calculate text position
        x, y, text_w, text_h = self._center_text(draw, text, font, width)
        y = (height - text_h) // 2
        
        # Apply animation
        alpha = 1.0
        offset_x, offset_y = 0, 0
        
        if animation == 'fade_in':
            alpha = progress
        elif animation == 'fade_out':
            alpha = 1 - progress
        elif animation == 'slide_left':
            offset_x = int(width * (1 - progress))
        elif animation == 'slide_right':
            offset_x = -int(width * (1 - progress))
        elif animation == 'typewriter':
            chars_to_show = int(len(text) * progress)
            text = text[:chars_to_show]
        elif animation == 'bounce':
            if progress < 0.6:
                alpha = progress / 0.6
                offset_y = int(height * 0.3 * (1 - progress / 0.6))
            else:
                bounce = math.sin((progress - 0.6) * 5) * 20
                offset_y = int(bounce)
        elif animation == 'scale_up':
            scale = 0.3 + progress * 0.7
            font = self._get_font(int(font_size * scale))
            x, y, text_w, text_h = self._center_text(draw, text, font, width)
            y = (height - text_h) // 2
        
        if alpha < 1.0:
            # Create text layer with alpha
            txt_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            txt_draw = ImageDraw.Draw(txt_layer)
            
            # Get color tuple
            if isinstance(text_color, tuple):
                color_rgb = text_color
            elif text_color == 'white':
                color_rgb = (255, 255, 255)
            elif text_color == 'black':
                color_rgb = (0, 0, 0)
            elif text_color.startswith('#'):
                color_rgb = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            else:
                color_rgb = (255, 255, 255)  # Default white
            
            txt_draw.text((x + offset_x, y + offset_y), text, 
                         fill=(*color_rgb, int(255 * alpha)),
                         font=font)
            img = Image.alpha_composite(img.convert('RGBA'), txt_layer).convert('RGB')
        else:
            self._draw_text_with_effects(draw, text, (x + offset_x, y + offset_y), 
                                         font, text_color, glow=True, glow_color=accent_color)
        
        return img

    def create_slideshow(self, images, texts, platform="instagram_reels",
                         duration_per_slide=3, transition="fade",
                         transition_duration=0.5, text_animation="fade_in",
                         bg_music=None, logo=None, logo_position="bottom_right",
                         watermark=None):
        """
        Create professional slideshow video with all effects

        Args:
            images: List of image paths
            texts: List of text overlays
            platform: Target platform
            duration_per_slide: Seconds per slide
            transition: Transition type
            transition_duration: Transition duration in seconds
            text_animation: Text animation type
            bg_music: Path to background music file
            logo: Path to logo image
            logo_position: Logo position (top_left, top_right, bottom_left, bottom_right)
            watermark: Watermark text

        Returns:
            Path to generated video
        """
        template = self.PLATFORMS.get(platform, self.PLATFORMS["youtube"])
        w, h = template["width"], template["height"]
        fps = template["fps"]

        # Clean temp
        for f in self.temp_dir.glob("*"):
            f.unlink()

        frame_num = 0
        frames_per_slide = int(fps * duration_per_slide)
        transition_frames = int(fps * transition_duration)

        # Load and prepare images
        prepared_images = []
        for img_path in images:
            try:
                img = Image.open(img_path).convert('RGB')
                img = self._resize_to_fit(img, w, h)
                prepared_images.append(img)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                prepared_images.append(Image.new('RGB', (w, h), (30, 30, 30)))

        # Load logo if provided
        logo_img = None
        if logo and os.path.exists(logo):
            try:
                logo_img = Image.open(logo).convert('RGBA')
                logo_size = min(w // 6, h // 6)
                logo_img = logo_img.resize((logo_size, logo_size), Image.LANCZOS)
            except:
                pass

        # Generate frames
        prev_frame = None
        for slide_idx, (img, text) in enumerate(zip(prepared_images, texts)):
            # Create slide frame with text
            slide_frame = img.copy()
            draw = ImageDraw.Draw(slide_frame)
            
            if text:
                font = self._get_font(80)
                x, y, tw, th = self._center_text(draw, text, font, w)
                y = h - 250  # Position text near bottom
                self._draw_text_with_effects(draw, text, (x, y), font,
                                            glow=True, glow_color=(255, 215, 0))

            # Add logo
            if logo_img:
                slide_frame = self._add_logo(slide_frame, logo_img, logo_position)

            # Add watermark
            if watermark:
                wm_font = self._get_font(30)
                wm_draw = ImageDraw.Draw(slide_frame)
                wm_draw.text((20, h - 50), watermark, fill=(255, 255, 255, 180), font=wm_font)

            # Write frames with transition
            for frame_idx in range(frames_per_slide):
                if frame_idx < transition_frames and prev_frame is not None:
                    # During transition
                    progress = frame_idx / transition_frames
                    final_frame = self._apply_transition(prev_frame, slide_frame, transition, progress)
                else:
                    final_frame = slide_frame

                # Text animation
                if text and frame_idx < fps:  # Animate text for first second
                    anim_progress = frame_idx / fps
                    anim_frame = self._create_text_animation_frame(
                        text, w, h, anim_progress, font_size=80,
                        animation=text_animation, bg_color=None
                    )
                    # Blend animation with slide
                    if text_animation in ['slide_left', 'slide_right']:
                        offset = int(w * (1 - min(1, anim_progress * 2)))
                        if text_animation == 'slide_left':
                            final_frame.paste(anim_frame, (offset, 0))
                        else:
                            final_frame.paste(anim_frame, (-offset, 0))
                    else:
                        final_frame = Image.blend(final_frame, anim_frame, min(0.7, anim_progress))

                final_frame.save(self.temp_dir / f"frame_{frame_num:06d}.png")
                frame_num += 1

            prev_frame = slide_frame
            print(f"  Slide {slide_idx + 1}/{len(images)} processed")

        # Create video with FFmpeg
        output_path = self.output_dir / f"video_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%06d.png"),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p"
        ]

        # Add audio if provided
        if bg_music and os.path.exists(bg_music):
            duration = len(images) * duration_per_slide
            cmd.extend([
                "-stream_loop", "-1",
                "-i", bg_music,
                "-t", str(duration),
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest"
            ])

        cmd.append(str(output_path))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup
        for f in self.temp_dir.glob("*"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        print(f"\nVideo saved: {output_path}")
        return str(output_path)

    def create_from_template(self, template_name, platform="instagram_reels",
                             images=None, custom_texts=None, duration_per_slide=3,
                             transition="fade", text_animation="fade_in",
                             bg_music=None, logo=None):
        """
        Create video using predefined ad template

        Args:
            template_name: Template name (sale, product_launch, discount, etc.)
            platform: Target platform
            images: Optional list of product images
            custom_texts: Custom text for each slide
            duration_per_slide: Seconds per slide
            transition: Transition type
            text_animation: Text animation type
            bg_music: Background music path
            logo: Logo image path

        Returns:
            Path to generated video
        """
        template = self.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        texts = custom_texts or template["texts"]
        w, h = self.PLATFORMS[platform]["width"], self.PLATFORMS[platform]["height"]

        # If images provided, use them
        if images:
            return self.create_slideshow(
                images=images,
                texts=texts[:len(images)],
                platform=platform,
                duration_per_slide=duration_per_slide,
                transition=transition,
                text_animation=text_animation,
                bg_music=bg_music,
                logo=logo
            )

        # Otherwise create template-based video with gradient backgrounds
        template_dir = Path("template_cache")
        template_dir.mkdir(exist_ok=True)
        
        temp_images = []
        for i, color in enumerate(template["bg_colors"]):
            img = self._create_gradient(w, h, color, template["bg_colors"][(i+1) % len(template["bg_colors"])])
            temp_path = template_dir / f"template_{template_name}_{i}.png"
            img.save(temp_path)
            temp_images.append(str(temp_path))

        # Cycle through images if we have more texts than images
        while len(temp_images) < len(texts):
            temp_images.extend(temp_images[:len(texts) - len(temp_images)])

        return self.create_slideshow(
            images=temp_images[:len(texts)],
            texts=texts,
            platform=platform,
            duration_per_slide=duration_per_slide,
            transition=transition,
            text_animation=text_animation,
            bg_music=bg_music,
            logo=logo
        )

    def create_text_video(self, texts, platform="instagram_reels",
                          duration_per_text=3, bg_color=(0, 0, 0),
                          text_color='white', font_size=100,
                          animation="fade_in", transition="fade",
                          bg_music=None, gradient_colors=None):
        """
        Create video with only animated text slides
        """
        template = self.PLATFORMS.get(platform, self.PLATFORMS["youtube"])
        w, h = template["width"], template["height"]
        fps = template["fps"]

        # Clean temp
        for f in self.temp_dir.glob("*"):
            f.unlink()

        frame_num = 0
        frames_per_text = int(fps * duration_per_text)
        transition_frames = int(fps * 0.5)

        # Create text frames
        text_frames = []
        for text in texts:
            if gradient_colors:
                img = self._create_gradient(w, h, gradient_colors[0], gradient_colors[1])
            else:
                img = Image.new('RGB', (w, h), bg_color)
            
            draw = ImageDraw.Draw(img)
            font = self._get_font(font_size)
            x, y, tw, th = self._center_text(draw, text, font, w)
            y = (h - th) // 2
            self._draw_text_with_effects(draw, text, (x, y), font, text_color, glow=True)
            text_frames.append(img)

        # Generate frames
        prev_frame = None
        for text_idx, text_frame in enumerate(text_frames):
            for frame_idx in range(frames_per_text):
                if frame_idx < transition_frames and prev_frame is not None:
                    progress = frame_idx / transition_frames
                    final_frame = self._apply_transition(prev_frame, text_frame, transition, progress)
                else:
                    final_frame = text_frame

                # Text animation
                if frame_idx < fps:
                    anim_progress = frame_idx / fps
                    text = texts[text_idx]
                    anim_frame = self._create_text_animation_frame(
                        text, w, h, anim_progress, font_size, text_color,
                        animation, bg_color
                    )
                    final_frame = Image.blend(final_frame, anim_frame, min(0.8, anim_progress))

                final_frame.save(self.temp_dir / f"frame_{frame_num:06d}.png")
                frame_num += 1

            prev_frame = text_frame
            print(f"  Slide {text_idx + 1}/{len(texts)} processed")

        # Create video
        output_path = self.output_dir / f"text_video_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%06d.png"),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p"
        ]

        if bg_music and os.path.exists(bg_music):
            duration = len(texts) * duration_per_text
            cmd.extend([
                "-stream_loop", "-1",
                "-i", bg_music,
                "-t", str(duration),
                "-c:a", "aac",
                "-shortest"
            ])

        cmd.append(str(output_path))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        for f in self.temp_dir.glob("*"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        print(f"\nVideo saved: {output_path}")
        return str(output_path)

    def _resize_to_fit(self, img, target_w, target_h):
        """Resize image to fit target dimensions"""
        img_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if img_ratio > target_ratio:
            new_w = target_w
            new_h = int(target_w / img_ratio)
        else:
            new_h = target_h
            new_w = int(target_h * img_ratio)

        img = img.resize((new_w, new_h), Image.LANCZOS)
        bg = Image.new('RGB', (target_w, target_h), (0, 0, 0))
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        bg.paste(img, (paste_x, paste_y))
        return bg

    def _add_logo(self, frame, logo, position="bottom_right"):
        """Add logo to frame"""
        margin = 30
        
        if position == "top_left":
            pos = (margin, margin)
        elif position == "top_right":
            pos = (frame.width - logo.width - margin, margin)
        elif position == "bottom_left":
            pos = (margin, frame.height - logo.height - margin)
        else:  # bottom_right
            pos = (frame.width - logo.width - margin, frame.height - logo.height - margin)

        frame.paste(logo, pos, logo if logo.mode == 'RGBA' else None)
        return frame

    def list_templates(self):
        """List all available templates"""
        print("\n" + "="*50)
        print("AVAILABLE AD TEMPLATES")
        print("="*50)
        for key, template in self.TEMPLATES.items():
            print(f"\n{key.upper()}")
            print(f"  Name: {template['name']}")
            print(f"  Colors: {template['bg_colors']}")
            print(f"  Default texts: {', '.join(template['texts'])}")

    def list_platforms(self):
        """List all available platforms"""
        print("\n" + "="*50)
        print("AVAILABLE PLATFORMS")
        print("="*50)
        for key, platform in self.PLATFORMS.items():
            print(f"\n{platform['name']}")
            print(f"  ID: {key}")
            print(f"  Resolution: {platform['width']}x{platform['height']}")

    def list_transitions(self):
        """List all available transitions"""
        print("\n" + "="*50)
        print("AVAILABLE TRANSITIONS")
        print("="*50)
        for key, name in self.TRANSITIONS.items():
            print(f"  {key}: {name}")

    def list_animations(self):
        """List all available text animations"""
        print("\n" + "="*50)
        print("AVAILABLE TEXT ANIMATIONS")
        print("="*50)
        for key, name in self.TEXT_ANIMATIONS.items():
            print(f"  {key}: {name}")

    def batch_create(self, configs):
        """
        Create multiple videos at once

        Args:
            configs: List of configuration dictionaries

        Returns:
            List of output paths
        """
        results = []
        for i, config in enumerate(configs):
            print(f"\nCreating video {i+1}/{len(configs)}...")
            try:
                if 'template' in config:
                    output = self.create_from_template(**config)
                else:
                    output = self.create_slideshow(**config)
                results.append({"success": True, "path": output, "config": config})
            except Exception as e:
                results.append({"success": False, "error": str(e), "config": config})
                print(f"Error: {e}")
        return results


# Quick functions for beginners
def quick_sale_video(images=None, platform="instagram_reels"):
    """Quick flash sale video"""
    studio = AdStudio()
    return studio.create_from_template("sale", platform, images=images)

def quick_product_launch(images=None, platform="instagram_reels"):
    """Quick product launch video"""
    studio = AdStudio()
    return studio.create_from_template("product_launch", platform, images=images)

def quick_discount_video(images=None, platform="instagram_reels"):
    """Quick discount video"""
    studio = AdStudio()
    return studio.create_from_template("discount", platform, images=images)

def quick_text_video(texts, platform="instagram_reels"):
    """Quick text-only video"""
    studio = AdStudio()
    return studio.create_text_video(texts, platform)


if __name__ == "__main__":
    print("AdStudio Pro - Professional Video Generator")
    print("="*50)
    studio = AdStudio()
    studio.list_templates()
    studio.list_platforms()
    studio.list_transitions()
    studio.list_animations()
