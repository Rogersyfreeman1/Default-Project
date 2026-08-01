"""
AdStudio Pro - Professional Video Studio CLI
Easy-to-use menu for creating amazing ad videos
"""

import os
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ad_studio import AdStudio
from music_manager import MusicManager
from shopify_integration import ShopifyStore, ProductVideoCreator


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    clear()
    print("=" * 60)
    print("     LASSY ADCRAFT STUDIO")
    print("     Professional Video Generator for Ads")
    print("=" * 60)
    print("  Create stunning videos for your social media ads")
    print("=" * 60)
    print()


def print_main_menu():
    print("MAIN MENU")
    print("-" * 60)
    print("  1.  Create Video from Images")
    print("  2.  Create Text-Only Video")
    print("  3.  Use Ad Template (Sale, Launch, etc.)")
    print("  4.  Batch Create Multiple Videos")
    print("  5.  Shopify Store (Auto-create from products)")
    print("  6.  Music Manager (Add & Preview Music)")
    print("  7.  View Templates & Platforms")
    print("  8.  View Output Folder")
    print("  9.  Help & Tutorials")
    print("  10. Exit")
    print()


def select_platform():
    studio = AdStudio()
    print("\nSELECT PLATFORM")
    print("-" * 60)
    platforms = list(studio.PLATFORMS.items())
    for i, (key, p) in enumerate(platforms, 1):
        print(f"  {i}. {p['name']} ({p['width']}x{p['height']})")

    while True:
        try:
            choice = int(input("\nEnter number: ")) - 1
            if 0 <= choice < len(platforms):
                return platforms[choice][0]
        except ValueError:
            pass
        print("Invalid choice. Try again.")


def select_transition():
    studio = AdStudio()
    print("\nSELECT TRANSITION")
    print("-" * 60)
    transitions = list(studio.TRANSITIONS.items())
    for i, (key, name) in enumerate(transitions, 1):
        print(f"  {i}. {name} ({key})")

    while True:
        try:
            choice = int(input("\nEnter number (or 1 for none): ")) - 1
            if 0 <= choice < len(transitions):
                return transitions[choice][0]
        except ValueError:
            pass
        print("Invalid choice. Try again.")


def select_text_animation():
    studio = AdStudio()
    print("\nSELECT TEXT ANIMATION")
    print("-" * 60)
    animations = list(studio.TEXT_ANIMATIONS.items())
    for i, (key, name) in enumerate(animations, 1):
        print(f"  1. {name} ({key})")

    while True:
        try:
            choice = int(input("\nEnter number (or 1 for none): ")) - 1
            if 0 <= choice < len(animations):
                return animations[choice][0]
        except ValueError:
            pass
        print("Invalid choice. Try again.")


def create_from_images():
    print("\n" + "=" * 60)
    print("  CREATE VIDEO FROM IMAGES")
    print("=" * 60)

    # Get images folder
    folder = input("\nPath to images folder: ").strip().strip('"')
    if not os.path.exists(folder):
        print("Folder not found!")
        return

    # Get all images
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    images = sorted([str(f) for f in Path(folder).iterdir() if f.suffix.lower() in image_exts])

    if not images:
        print("No images found in folder!")
        return

    print(f"\nFound {len(images)} images:")
    for i, img in enumerate(images[:10], 1):
        print(f"  {i}. {Path(img).name}")
    if len(images) > 10:
        print(f"  ... and {len(images) - 10} more")

    # Get settings
    platform = select_platform()
    transition = select_transition()
    animation = select_text_animation()

    while True:
        try:
            duration = float(input("\nSeconds per image (default 3): ") or "3")
            if duration > 0:
                break
        except ValueError:
            pass
        print("Enter a positive number.")

    # Get texts
    print("\nAdd text overlays? (images without text will have no overlay)")
    add_texts = input("Add texts? (y/n): ").lower() == 'y'
    texts = None

    if add_texts:
        texts = []
        print("\nEnter text for each image (press Enter for no text, type 'done' when finished):")
        for i, img in enumerate(images):
            text = input(f"  Image {i+1} ({Path(img).name}): ")
            if text.lower() == 'done':
                break
            texts.append(text)

        if not texts:
            texts = None

    # Get extras
    logo = input("\nPath to logo image (or Enter to skip): ").strip().strip('"') or None
    if logo and not os.path.exists(logo):
        print("Logo not found, skipping...")
        logo = None

    music = input("Path to background music (or Enter to skip): ").strip().strip('"') or None
    if music and not os.path.exists(music):
        print("Music not found, skipping...")
        music = None

    watermark = input("Watermark text (or Enter to skip): ").strip() or None

    # Create video
    print("\n" + "=" * 60)
    print("  CREATING YOUR VIDEO...")
    print("=" * 60)

    try:
        studio = AdStudio()
        output = studio.create_slideshow(
            images=images,
            texts=texts or [""] * len(images),
            platform=platform,
            duration_per_slide=duration,
            transition=transition,
            text_animation=animation,
            bg_music=music,
            logo=logo,
            watermark=watermark
        )
        print("\n" + "=" * 60)
        print("  VIDEO CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n  Saved to: {output}")
    except Exception as e:
        print(f"\nError: {e}")


def create_text_video():
    print("\n" + "=" * 60)
    print("  CREATE TEXT-ONLY VIDEO")
    print("=" * 60)

    # Get platform
    platform = select_platform()
    transition = select_transition()
    animation = select_text_animation()

    # Get texts
    print("\nEnter text for each slide:")
    print("(Type 'done' when finished)")
    texts = []
    while True:
        text = input(f"  Slide {len(texts)+1}: ")
        if text.lower() == 'done':
            break
        if text:
            texts.append(text)

    if not texts:
        print("No texts entered!")
        return

    # Get settings
    while True:
        try:
            duration = float(input("\nSeconds per slide (default 3): ") or "3")
            if duration > 0:
                break
        except ValueError:
            pass
        print("Enter a positive number.")

    while True:
        try:
            font_size = int(input("Font size (default 100): ") or "100")
            if 20 <= font_size <= 200:
                break
        except ValueError:
            pass
        print("Enter a number between 20-200.")

    # Colors
    print("\nBackground colors:")
    print("  1. Black")
    print("  2. White")
    print("  3. Dark Blue")
    print("  4. Red Gradient")
    print("  5. Custom RGB")
    color_choice = input("Select (1-5): ").strip()

    gradient_colors = None
    bg_color = (0, 0, 0)
    text_color = 'white'

    if color_choice == '2':
        bg_color = (255, 255, 255)
        text_color = 'black'
    elif color_choice == '3':
        bg_color = (0, 20, 50)
    elif color_choice == '4':
        gradient_colors = [(220, 20, 60), (255, 69, 0)]
    elif color_choice == '5':
        try:
            rgb = input("Enter RGB as R,G,B: ").strip().split(',')
            bg_color = tuple(int(x) for x in rgb)
        except:
            bg_color = (0, 0, 0)

    # Extras
    music = input("\nPath to background music (or Enter to skip): ").strip().strip('"') or None
    if music and not os.path.exists(music):
        music = None

    # Create video
    print("\n" + "=" * 60)
    print("  CREATING YOUR VIDEO...")
    print("=" * 60)

    try:
        studio = AdStudio()
        output = studio.create_text_video(
            texts=texts,
            platform=platform,
            duration_per_text=duration,
            bg_color=bg_color,
            text_color=text_color,
            font_size=font_size,
            animation=animation,
            transition=transition,
            bg_music=music,
            gradient_colors=gradient_colors
        )
        print("\n" + "=" * 60)
        print("  VIDEO CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n  Saved to: {output}")
    except Exception as e:
        print(f"\nError: {e}")


def create_from_template():
    print("\n" + "=" * 60)
    print("  USE AD TEMPLATE")
    print("=" * 60)

    # Select template
    studio = AdStudio()
    templates = list(studio.TEMPLATES.items())

    print("\nAvailable Templates:")
    print("-" * 60)
    for i, (key, t) in enumerate(templates, 1):
        print(f"  {i}. {t['name']} ({key})")

    while True:
        try:
            choice = int(input("\nSelect template (1-{}): ".format(len(templates)))) - 1
            if 0 <= choice < len(templates):
                template_key = templates[choice][0]
                break
        except ValueError:
            pass
        print("Invalid choice.")

    template = templates[choice][1]
    print(f"\nTemplate: {template['name']}")
    print(f"Default texts: {', '.join(template['texts'])}")

    # Platform
    platform = select_platform()

    # Images (optional)
    use_images = input("\nUse custom images? (y/n): ").lower() == 'y'
    images = None

    if use_images:
        folder = input("Path to images folder: ").strip().strip('"')
        if os.path.exists(folder):
            image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            images = sorted([str(f) for f in Path(folder).iterdir() if f.suffix.lower() in image_exts])
            print(f"Found {len(images)} images")
        else:
            print("Folder not found, using template defaults...")

    # Custom texts?
    use_custom = input("\nUse custom texts? (y/n): ").lower() == 'y'
    custom_texts = None

    if use_custom:
        print("\nEnter custom texts (press Enter for default, 'done' to finish):")
        custom_texts = []
        for i, default_text in enumerate(template['texts']):
            text = input(f"  Slide {i+1} [{default_text}]: ").strip()
            if text.lower() == 'done':
                break
            custom_texts.append(text if text else default_text)

    # Settings
    transition = select_transition()
    animation = select_text_animation()

    while True:
        try:
            duration = float(input("\nSeconds per slide (default 3): ") or "3")
            if duration > 0:
                break
        except ValueError:
            pass

    # Extras
    logo = input("\nPath to logo (or Enter to skip): ").strip().strip('"') or None
    if logo and not os.path.exists(logo):
        logo = None

    music = input("Path to music (or Enter to skip): ").strip().strip('"') or None
    if music and not os.path.exists(music):
        music = None

    # Create video
    print("\n" + "=" * 60)
    print("  CREATING YOUR TEMPLATE VIDEO...")
    print("=" * 60)

    try:
        output = studio.create_from_template(
            template_name=template_key,
            platform=platform,
            images=images,
            custom_texts=custom_texts,
            duration_per_slide=duration,
            transition=transition,
            text_animation=animation,
            bg_music=music,
            logo=logo
        )
        print("\n" + "=" * 60)
        print("  VIDEO CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n  Saved to: {output}")
    except Exception as e:
        print(f"\nError: {e}")


def batch_create():
    print("\n" + "=" * 60)
    print("  BATCH CREATE MULTIPLE VIDEOS")
    print("=" * 60)
    print("\n  This will create multiple videos at once.")
    print("  Enter details for each video:")

    configs = []
    while True:
        print(f"\n--- Video {len(configs)+1} ---")
        print("  1. From images")
        print("  2. From template")
        print("  3. Finish batch")

        choice = input("  Select (1-3): ").strip()

        if choice == '3':
            break

        platform = select_platform()

        if choice == '1':
            folder = input("  Images folder: ").strip().strip('"')
            if os.path.exists(folder):
                texts = input("  Texts (comma-separated): ").strip().split(',')
                configs.append({
                    'images': [str(f) for f in Path(folder).iterdir() 
                              if f.suffix.lower() in {'.jpg', '.jpeg', '.png'}],
                    'texts': texts,
                    'platform': platform
                })

        elif choice == '2':
            studio = AdStudio()
            templates = list(studio.TEMPLATES.keys())
            print("  Templates:", ", ".join(templates))
            template = input("  Template name: ").strip()
            if template in templates:
                configs.append({
                    'template': template,
                    'platform': platform
                })

    if not configs:
        print("No videos to create!")
        return

    print(f"\nCreating {len(configs)} videos...")
    studio = AdStudio()
    results = studio.batch_create(configs)

    success = sum(1 for r in results if r['success'])
    print(f"\nDone! {success}/{len(configs)} videos created successfully.")


def shopify_manager():
    """Shopify Store Manager"""
    store = ShopifyStore()
    
    while True:
        print("\n" + "=" * 60)
        print("  SHOPIFY STORE MANAGER")
        print("=" * 60)
        
        if store.is_configured():
            print(f"  Connected to: {store.config['store_url']}")
            print("  " + "-" * 56)
        
        print("  1.  Setup / Change Store Connection")
        print("  2.  View All Products")
        print("  3.  Search Products")
        print("  4.  Create Video from Single Product")
        print("  5.  Create Video from Multiple Products")
        print("  6.  Create Sale / Promo Video")
        print("  7.  View Collections")
        print("  8.  Back to Main Menu")
        print()
        
        choice = input("  Select (1-8): ").strip()
        
        if choice == '1':
            print("\n  Setup Shopify Connection")
            print("  " + "-" * 56)
            print("  You need:")
            print("  1. Your store URL (e.g., your-store.myshopify.com)")
            print("  2. An Admin API access token")
            print()
            print("  How to get access token:")
            print("  1. Go to your Shopify Admin")
            print("  2. Settings > Apps and sales channels")
            print("  3. Develop apps > Create an app")
            print("  4. Configure Admin API scopes")
            print("  5. Install app and copy access token")
            print()
            
            store_url = input("  Store URL: ").strip()
            access_token = input("  Access Token: ").strip()
            
            if store_url and access_token:
                if store.setup(store_url, access_token):
                    print("\n  Connected successfully!")
                    products = store.get_products(limit=5)
                    print(f"  Found {len(products)} products")
                else:
                    print("\n  Connection failed. Check credentials.")
            else:
                print("  Please enter both URL and token.")
        
        elif choice == '2':
            if not store.is_configured():
                print("  Please setup Shopify first (option 1)")
                continue
            
            try:
                products = store.get_products(limit=50)
                store.print_products(products)
            except Exception as e:
                print(f"  Error: {e}")
        
        elif choice == '3':
            if not store.is_configured():
                print("  Please setup Shopify first (option 1)")
                continue
            
            query = input("  Search term: ").strip()
            if query:
                products = store.search_products(query)
                store.print_products(products)
        
        elif choice == '4':
            if not store.is_configured():
                print("  Please setup Shopify first (option 1)")
                continue
            
            try:
                products = store.get_products(limit=50)
                store.print_products(products)
                
                idx = int(input("\n  Select product number: ")) - 1
                if 0 <= idx < len(products):
                    product = products[idx]
                    
                    print("\n  Select platform:")
                    from ad_studio import AdStudio
                    studio = AdStudio()
                    platforms = list(studio.PLATFORMS.keys())
                    for i, p in enumerate(platforms, 1):
                        print(f"    {i}. {p}")
                    
                    plat_idx = int(input("  Platform number: ")) - 1
                    platform = platforms[plat_idx] if 0 <= plat_idx < len(platforms) else "instagram_reels"
                    
                    duration = int(input("  Duration in seconds (default 5): ") or "5")
                    
                    print("\n  Creating product video...")
                    creator = ProductVideoCreator()
                    output = creator.create_product_video(product, platform, duration)
                    print(f"\n  Video saved: {output}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif choice == '5':
            if not store.is_configured():
                print("  Please setup Shopify first (option 1)")
                continue
            
            try:
                products = store.get_products(limit=50)
                store.print_products(products)
                
                print("\n  Enter product numbers (comma-separated, e.g., 1,3,5)")
                selection = input("  Select products: ").strip()
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                
                selected = [products[i] for i in indices if 0 <= i < len(products)]
                
                if selected:
                    print(f"\n  Selected {len(selected)} products")
                    
                    from ad_studio import AdStudio
                    studio = AdStudio()
                    platforms = list(studio.PLATFORMS.keys())
                    for i, p in enumerate(platforms, 1):
                        print(f"    {i}. {p}")
                    
                    plat_idx = int(input("  Platform number: ")) - 1
                    platform = platforms[plat_idx] if 0 <= plat_idx < len(platforms) else "instagram_reels"
                    
                    print("\n  Creating multi-product video...")
                    creator = ProductVideoCreator()
                    output = creator.create_multi_product_video(selected, platform)
                    print(f"\n  Video saved: {output}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif choice == '6':
            if not store.is_configured():
                print("  Please setup Shopify first (option 1)")
                continue
            
            try:
                products = store.get_products(limit=50)
                store.print_products(products)
                
                print("\n  Enter product numbers (comma-separated)")
                selection = input("  Select products: ").strip()
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                
                selected = [products[i] for i in indices if 0 <= i < len(products)]
                
                if selected:
                    sale_text = input("  Sale text (default 'SALE'): ").strip() or "SALE"
                    
                    from ad_studio import AdStudio
                    studio = AdStudio()
                    platforms = list(studio.PLATFORMS.keys())
                    for i, p in enumerate(platforms, 1):
                        print(f"    {i}. {p}")
                    
                    plat_idx = int(input("  Platform number: ")) - 1
                    platform = platforms[plat_idx] if 0 <= plat_idx < len(platforms) else "instagram_reels"
                    
                    print("\n  Creating sale video...")
                    creator = ProductVideoCreator()
                    output = creator.create_sale_video(selected, platform, sale_text)
                    print(f"\n  Video saved: {output}")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif choice == '7':
            if not store.is_configured():
                print("  Please setup Shopify first (option 1)")
                continue
            
            try:
                collections = store.get_collections()
                if collections:
                    print("\n  Your Collections:")
                    for c in collections:
                        print(f"    • {c['title']} (ID: {c['id']})")
                else:
                    print("  No collections found.")
            except Exception as e:
                print(f"  Error: {e}")
        
        elif choice == '8':
            break
        
        input("\n  Press Enter to continue...")


def music_manager():
    """Music Manager submenu"""
    manager = MusicManager()
    
    while True:
        print("\n" + "=" * 60)
        print("  MUSIC MANAGER")
        print("=" * 60)
        print("  1. View Music Library")
        print("  2. Add Music from Computer")
        print("  3. Preview Music")
        print("  4. View Free Music Sources")
        print("  5. View Music Categories")
        print("  6. Music Packs")
        print("  7. Auto-select Music for Video")
        print("  8. Back to Main Menu")
        print()
        
        choice = input("  Select (1-8): ").strip()
        
        if choice == '1':
            manager.print_music_library()
        
        elif choice == '2':
            print("\n  Add music from your computer:")
            source = input("  Enter path to music file: ").strip().strip('"')
            if os.path.exists(source):
                try:
                    dest = manager.copy_music_file(source)
                    print(f"  Music added to: {dest}")
                except Exception as e:
                    print(f"  Error: {e}")
            else:
                print("  File not found!")
        
        elif choice == '3':
            music_files = manager.list_local_music()
            if not music_files:
                print("  No music files found. Add some music first!")
            else:
                print("\n  Your music:")
                for i, m in enumerate(music_files, 1):
                    print(f"  {i}. {m['name']} ({m['duration']})")
                
                try:
                    idx = int(input("\n  Select number to preview: ")) - 1
                    if 0 <= idx < len(music_files):
                        print(f"  Playing: {music_files[idx]['name']}...")
                        print("  (Press Ctrl+C to stop)")
                        manager.preview_music(music_files[idx]['path'])
                except (ValueError, IndexError):
                    print("  Invalid selection")
        
        elif choice == '4':
            list_free_sources()
        
        elif choice == '5':
            manager.print_categories()
        
        elif choice == '6':
            packs = manager.list_music_packs()
            if packs:
                print("\n  Your Music Packs:")
                for pack in packs:
                    print(f"  • {pack['name']} ({pack['tracks']} tracks)")
            else:
                print("  No music packs yet.")
                print("  Create one by copying music to music/packs/[pack_name]/")
        
        elif choice == '7':
            print("\n  Auto-select music for your video:")
            print("  Available styles:")
            styles = list(MusicManager.CATEGORIES.keys())
            for i, style in enumerate(styles, 1):
                print(f"  {i}. {style.title()}")
            
            try:
                style_idx = int(input("\n  Select style: ")) - 1
                style = styles[style_idx] if 0 <= style_idx < len(styles) else None
            except (ValueError, IndexError):
                style = None
            
            duration = input("  Video duration in seconds (or Enter to skip): ").strip()
            duration = int(duration) if duration.isdigit() else None
            
            music = manager.get_music_for_video(duration, style)
            if music:
                print(f"\n  Recommended: {music['name']} ({music['duration']})")
                print(f"  Path: {music['path']}")
            else:
                print("  No music found. Add music to your library first!")
        
        elif choice == '8':
            break
        
        input("\n  Press Enter to continue...")


def view_info():
    studio = AdStudio()
    print("\n" + "=" * 60)
    print("  TEMPLATES & PLATFORMS")
    print("=" * 60)
    studio.list_templates()
    studio.list_platforms()
    studio.list_transitions()
    studio.list_animations()


def view_output():
    output_dir = Path("output")
    if output_dir.exists():
        files = list(output_dir.glob("*.mp4"))
        if files:
            print("\n" + "=" * 60)
            print("  OUTPUT VIDEOS")
            print("=" * 60)
            for f in sorted(files, key=os.path.getmtime, reverse=True):
                size_kb = f.stat().st_size / 1024
                print(f"  {f.name} ({size_kb:.0f} KB)")
        else:
            print("\n  No videos yet.")
    else:
        print("\n  Output folder doesn't exist yet.")


def show_help():
    print("\n" + "=" * 60)
    print("  HELP & TUTORIALS")
    print("=" * 60)
    print("""
  QUICK START:
  ─────────────────────────────────────────────────────────────
  1. Put your images in a folder
  2. Choose "Create Video from Images"
  3. Select platform, transition, animation
  4. Your video will be saved in "output" folder

  TEMPLATES:
  ─────────────────────────────────────────────────────────────
  Use pre-made templates for:
  • Flash Sales - Quick promotional videos
  • Product Launches - New product announcements
  • Black Friday - Special event videos
  • And more!

  MUSIC:
  ─────────────────────────────────────────────────────────────
  Add background music to make videos engaging!
  
  1. Go to "Music Manager" (option 5)
  2. Add music from your computer
  3. Or download free music from legal sources
  
  FREE MUSIC SOURCES (No Copyright Issues):
  • https://pixabay.com/music/ - Free, no attribution
  • https://mixkit.co/free-stock-music/ - Free for videos
  • https://freesound.org/ - Free sounds & music
  • YouTube Audio Library - Free music

  TIPS:
  ─────────────────────────────────────────────────────────────
  • Use high-quality images (1080px+ wide)
  • Keep text short and readable
  • For vertical videos (TikTok, Reels), use tall images
  • Add your logo for brand recognition
  • Use background music for engagement
  • Match music style to your video content

  KEYBOARD SHORTCUTS:
  ─────────────────────────────────────────────────────────────
  • Press Enter to accept default values
  • Type 'done' to finish entering lists
  • Type 'skip' to skip optional steps
""")


def main():
    while True:
        print_banner()
        print_main_menu()

        choice = input("Select option (1-10): ").strip()

        if choice == '1':
            create_from_images()
        elif choice == '2':
            create_text_video()
        elif choice == '3':
            create_from_template()
        elif choice == '4':
            batch_create()
        elif choice == '5':
            shopify_manager()
        elif choice == '6':
            music_manager()
        elif choice == '7':
            view_info()
        elif choice == '8':
            view_output()
        elif choice == '9':
            show_help()
        elif choice == '10':
            print("\nThank you for using Lassy AdCraft Studio!")
            break
        else:
            print("\nInvalid option. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
