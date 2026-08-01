# AI Video Generator for Social Media Ads

## Quick Start (2 Steps)

### Step 1: Double-click "Start Video Generator.bat"
This will install all required packages and start the program.

### Step 2: Follow the menu
- Choose option 1 to create a video from images
- Choose option 2 to create a text-only video

---

## How to Use

### Option 1: Create Video from Images

1. Put your images in a folder (e.g., `my_images`)
2. Run the program and select option 1
3. Enter the folder path
4. Choose your platform (TikTok, Instagram, YouTube, etc.)
5. Your video will be saved in the `output` folder

### Option 2: Create Text Video

1. Run the program and select option 2
2. Choose your platform
3. Type your text for each slide
4. Your video will be saved in the `output` folder

---

## Supported Platforms

| Platform | Resolution | Best For |
|----------|------------|----------|
| Instagram Reels | 1080x1920 | Short vertical videos |
| TikTok | 1080x1920 | Short vertical videos |
| YouTube | 1920x1080 | Long horizontal videos |
| Instagram Post | 1080x1080 | Square posts |
| Facebook | 1920x1080 | Horizontal videos |
| Twitter | 1280x720 | Short clips |

---

## Example: Quick Video

```python
from video_generator import quick_video

# Create a video from images in a folder
quick_video("my_images", "tiktok")

# Create a video with text overlays
quick_video("my_images", "youtube", ["Hello", "Welcome", "Subscribe"])
```

---

## Tips

- Use high-quality images (at least 1080px wide)
- Keep text short and readable
- For vertical videos (TikTok, Reels), use tall images
- Videos are saved in `output` folder

---

## Requirements

- Python 3.7 or higher
- Internet connection (for first-time package installation)

---

## Need Help?

If you get an error:
1. Make sure Python is installed
2. Try running "Start Video Generator.bat" as administrator
3. Check that your images are in a valid format (JPG, PNG)
