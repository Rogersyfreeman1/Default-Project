"""
Video Generator CLI - Easy-to-use interface
Run this script to create videos without coding
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from video_generator import VideoGenerator


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    print("=" * 50)
    print("     AI VIDEO GENERATOR FOR SOCIAL MEDIA ADS")
    print("=" * 50)
    print()


def print_menu():
    print("MAIN MENU:")
    print("-" * 30)
    print("1. Create video from images folder")
    print("2. Create text-only video")
    print("3. View available platforms")
    print("4. View output folder")
    print("5. Exit")
    print()


def get_platform_choice():
    generator = VideoGenerator()
    templates = generator.get_templates()

    print("\nSelect platform:")
    print("-" * 30)
    platforms = list(templates.keys())
    for i, (key, template) in enumerate(templates.items(), 1):
        print(f"{i}. {template['name']} ({template['width']}x{template['height']})")

    while True:
        try:
            choice = int(input("\nEnter number (1-6): ")) - 1
            if 0 <= choice < len(platforms):
                return platforms[choice]
            print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a number.")


def create_from_images():
    """Create video from images in a folder"""
    print("\n--- CREATE VIDEO FROM IMAGES ---\n")

    # Get folder path
    folder = input("Enter path to images folder: ").strip()
    if not folder:
        print("No folder specified. Using current directory.")
        folder = "."

    if not os.path.exists(folder):
        print(f"Error: Folder '{folder}' not found!")
        return

    # Get platform
    platform = get_platform_choice()

    # Get duration
    while True:
        try:
            duration = float(input("\nSeconds per image (default 3): ") or "3")
            if duration > 0:
                break
            print("Duration must be positive.")
        except ValueError:
            print("Please enter a number.")

    # Ask for texts
    add_texts = input("\nAdd text overlays? (y/n): ").lower() == 'y'
    texts = None

    if add_texts:
        print("\nEnter text for each image (press Enter for no text):")
        texts = []
        while True:
            text = input(f"Text for image {len(texts) + 1} (or 'done' to finish): ")
            if text.lower() == 'done':
                break
            texts.append(text)

        if not texts:
            texts = None

    # Create video
    try:
        generator = VideoGenerator()
        output = generator.create_from_folder(
            folder_path=folder,
            platform=platform,
            duration_per_slide=duration,
            texts=texts
        )
        print(f"\nSuccess! Video saved to: {output}")
    except Exception as e:
        print(f"\nError: {e}")


def create_text_video():
    """Create text-only video"""
    print("\n--- CREATE TEXT VIDEO ---\n")

    # Get platform
    platform = get_platform_choice()

    # Get texts
    print("\nEnter text for each slide (type 'done' when finished):")
    texts = []
    while True:
        text = input(f"Slide {len(texts) + 1}: ")
        if text.lower() == 'done':
            break
        if text:
            texts.append(text)

    if not texts:
        print("No texts entered. Returning to menu.")
        return

    # Get duration
    while True:
        try:
            duration = float(input("\nSeconds per slide (default 3): ") or "3")
            if duration > 0:
                break
            print("Duration must be positive.")
        except ValueError:
            print("Please enter a number.")

    # Get colors
    bg_input = input("\nBackground color (R,G,B) or press Enter for black: ").strip()
    if bg_input:
        try:
            bg_color = tuple(map(int, bg_input.split(',')))
        except:
            bg_color = (0, 0, 0)
    else:
        bg_color = (0, 0, 0)

    # Create video
    try:
        generator = VideoGenerator()
        output = generator.create_text_video(
            texts=texts,
            platform=platform,
            duration_per_text=duration,
            bg_color=bg_color
        )
        print(f"\nSuccess! Video saved to: {output}")
    except Exception as e:
        print(f"\nError: {e}")


def view_platforms():
    """Display available platforms"""
    generator = VideoGenerator()
    templates = generator.get_templates()

    print("\n--- AVAILABLE PLATFORMS ---\n")
    for key, template in templates.items():
        print(f"{template['name']}:")
        print(f"  ID: {key}")
        print(f"  Resolution: {template['width']}x{template['height']}")
        print(f"  Max Duration: {template['max_duration']} seconds")
        print()


def view_output():
    """Open output folder"""
    output_dir = Path("output")
    if output_dir.exists():
        files = list(output_dir.glob("*.mp4"))
        if files:
            print(f"\n--- OUTPUT VIDEOS ({len(files)} found) ---\n")
            for f in sorted(files, key=os.path.getmtime, reverse=True):
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  {f.name} ({size_mb:.1f} MB)")
        else:
            print("\nNo videos generated yet.")
    else:
        print("\nOutput folder doesn't exist yet.")

    print()


def main():
    while True:
        clear_screen()
        print_banner()
        print_menu()

        choice = input("Enter your choice (1-5): ").strip()

        if choice == '1':
            create_from_images()
        elif choice == '2':
            create_text_video()
        elif choice == '3':
            view_platforms()
        elif choice == '4':
            view_output()
        elif choice == '5':
            print("\nThank you for using Video Generator!")
            break
        else:
            print("\nInvalid choice. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
