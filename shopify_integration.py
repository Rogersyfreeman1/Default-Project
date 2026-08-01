"""
Shopify Integration for AdStudio Pro
Connect your Shopify store and create promo videos automatically
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
import subprocess
from PIL import Image, ImageDraw, ImageFont
import platform


class ShopifyStore:
    """Connect to your Shopify store and fetch products"""

    def __init__(self):
        self.config_file = Path("shopify_config.json")
        self.config = self._load_config()
        self.cache_dir = Path("shopify_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.font_path = self._find_font()

    def _load_config(self):
        """Load Shopify configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Save Shopify configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def _find_font(self):
        """Find system font"""
        if platform.system() == "Windows":
            fonts = [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibrib.ttf",
            ]
        else:
            fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        for f in fonts:
            if os.path.exists(f):
                return f
        return None

    def setup(self, store_url, access_token):
        """
        Setup Shopify connection
        
        Args:
            store_url: Your Shopify store URL (e.g., your-store.myshopify.com)
            access_token: Shopify API access token
        
        Returns:
            True if connection successful
        """
        # Clean up URL
        store_url = store_url.replace("https://", "").replace("http://", "")
        store_url = store_url.rstrip("/")
        
        if not store_url.endswith(".myshopify.com"):
            store_url = f"{store_url}.myshopify.com"

        self.config["store_url"] = store_url
        self.config["access_token"] = access_token
        self.config["setup_date"] = datetime.now().isoformat()
        self._save_config()

        # Test connection
        return self.test_connection()

    def test_connection(self):
        """Test Shopify API connection"""
        if not self.config.get("store_url") or not self.config.get("access_token"):
            return False

        try:
            products = self._fetch_products(limit=1)
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def _fetch_products(self, limit=50, page=1):
        """Fetch products from Shopify API"""
        if not self.config.get("store_url") or not self.config.get("access_token"):
            raise ValueError("Shopify not configured. Run setup() first.")

        url = f"https://{self.config['store_url']}/admin/api/2024-01/products.json"
        headers = {
            "X-Shopify-Access-Token": self.config["access_token"],
            "Content-Type": "application/json"
        }
        params = {
            "limit": min(limit, 250),
            "page": page
        }

        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 401:
            raise Exception("Invalid access token")
        elif response.status_code == 404:
            raise Exception("Store not found. Check your store URL.")
        elif response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        return response.json().get("products", [])

    def get_products(self, limit=50, collection=None, product_type=None):
        """
        Get products from your store
        
        Args:
            limit: Number of products to fetch (max 250)
            collection: Filter by collection title
            product_type: Filter by product type
        
        Returns:
            List of product dictionaries
        """
        products = self._fetch_products(limit=limit)
        
        formatted_products = []
        for p in products:
            # Get main image
            images = p.get("images", [])
            main_image = images[0]["src"] if images else None
            
            # Get price
            variants = p.get("variants", [])
            price = variants[0]["price"] if variants else "0.00"
            compare_price = variants[0].get("compare_at_price") if variants else None
            
            formatted_products.append({
                "id": p["id"],
                "title": p["title"],
                "description": p.get("body_html", ""),
                "vendor": p.get("vendor", ""),
                "product_type": p.get("product_type", ""),
                "status": p.get("status", "active"),
                "price": price,
                "compare_at_price": compare_price,
                "image": main_image,
                "images": [img["src"] for img in images],
                "tags": p.get("tags", []),
                "url": f"https://{self.config['store_url']}/products/{p['handle']}",
                "handle": p.get("handle", "")
            })

        # Apply filters
        if collection:
            # Note: Collection filtering would need additional API call
            pass
        
        if product_type:
            formatted_products = [
                p for p in formatted_products 
                if p["product_type"].lower() == product_type.lower()
            ]

        return formatted_products

    def get_product(self, product_id):
        """Get single product by ID"""
        if not self.config.get("store_url") or not self.config.get("access_token"):
            raise ValueError("Shopify not configured.")

        url = f"https://{self.config['store_url']}/admin/api/2024-01/products/{product_id}.json"
        headers = {
            "X-Shopify-Access-Token": self.config["access_token"],
        }

        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Product not found: {response.status_code}")

        p = response.json().get("product", {})
        images = p.get("images", [])
        variants = p.get("variants", [])
        
        return {
            "id": p["id"],
            "title": p["title"],
            "description": p.get("body_html", ""),
            "vendor": p.get("vendor", ""),
            "product_type": p.get("product_type", ""),
            "price": variants[0]["price"] if variants else "0.00",
            "compare_at_price": variants[0].get("compare_at_price") if variants else None,
            "image": images[0]["src"] if images else None,
            "images": [img["src"] for img in images],
            "tags": p.get("tags", []),
            "url": f"https://{self.config['store_url']}/products/{p['handle']}"
        }

    def download_product_images(self, product, save_dir=None):
        """Download all images for a product"""
        if save_dir is None:
            save_dir = self.cache_dir / f"product_{product['id']}"
        else:
            save_dir = Path(save_dir)
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = []
        for i, img_url in enumerate(product.get("images", [])):
            try:
                response = requests.get(img_url, timeout=30)
                if response.status_code == 200:
                    # Get file extension from URL
                    ext = ".jpg"
                    if ".png" in img_url.lower():
                        ext = ".png"
                    elif ".webp" in img_url.lower():
                        ext = ".webp"
                    
                    filename = f"product_{i+1}{ext}"
                    filepath = save_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded.append(str(filepath))
                    print(f"  Downloaded: {filename}")
            except Exception as e:
                print(f"  Error downloading image {i+1}: {e}")

        return downloaded

    def search_products(self, query, limit=20):
        """Search products by title"""
        products = self.get_products(limit=100)
        
        query_lower = query.lower()
        results = [
            p for p in products
            if query_lower in p["title"].lower()
            or query_lower in p.get("product_type", "").lower()
            or query_lower in " ".join(p.get("tags", [])).lower()
        ]
        
        return results[:limit]

    def get_collections(self):
        """Get all collections from store"""
        if not self.config.get("store_url") or not self.config.get("access_token"):
            return []

        url = f"https://{self.config['store_url']}/admin/api/2024-01/collections.json"
        headers = {
            "X-Shopify-Access-Token": self.config["access_token"],
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                collections = response.json().get("collections", [])
                return [{"id": c["id"], "title": c["title"]} for c in collections]
        except:
            pass
        
        return []

    def get_product_types(self):
        """Get unique product types from store"""
        products = self.get_products(limit=250)
        types = set(p["product_type"] for p in products if p["product_type"])
        return sorted(list(types))

    def print_products(self, products):
        """Print formatted product list"""
        print("\n" + "=" * 70)
        print("  YOUR SHOPIFY PRODUCTS")
        print("=" * 70)
        
        if not products:
            print("\n  No products found.")
            return

        print(f"\n  Total products: {len(products)}\n")
        
        for i, p in enumerate(products, 1):
            has_image = "✓" if p["image"] else "✗"
            print(f"  {i:2d}. [{has_image}] {p['title']}")
            print(f"      Price: ${p['price']} | Type: {p['product_type'] or 'N/A'}")
            if p["compare_at_price"]:
                print(f"      Compare at: ${p['compare_at_price']}")

        print("\n" + "=" * 70)

    def is_configured(self):
        """Check if Shopify is configured"""
        return bool(self.config.get("store_url") and self.config.get("access_token"))


class ProductVideoCreator:
    """Create promotional videos from Shopify products"""

    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp_frames")
        self.temp_dir.mkdir(exist_ok=True)
        self.font_path = self._find_font()
        self.shopify = ShopifyStore()

    def _find_font(self):
        """Find system font"""
        if platform.system() == "Windows":
            fonts = [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        else:
            fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        for f in fonts:
            if os.path.exists(f):
                return f
        return None

    def _get_font(self, size):
        """Get font with size"""
        if self.font_path:
            return ImageFont.truetype(self.font_path, size)
        return ImageFont.load_default()

    def _download_image(self, url, save_path):
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"Error downloading: {e}")
        return False

    def _create_product_frame(self, product, width, height, show_price=True, 
                               show_discount=False, bg_color=(0, 0, 0)):
        """Create a single frame for a product"""
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Download and add product image
        if product.get("image"):
            temp_img_path = self.temp_dir / f"temp_product_{product['id']}.jpg"
            if self._download_image(product["image"], temp_img_path):
                try:
                    product_img = Image.open(temp_img_path).convert('RGB')
                    
                    # Resize to fit
                    max_img_height = height * 0.6
                    max_img_width = width * 0.8
                    
                    img_ratio = product_img.width / product_img.height
                    if img_ratio > (max_img_width / max_img_height):
                        new_w = int(max_img_width)
                        new_h = int(max_img_width / img_ratio)
                    else:
                        new_h = int(max_img_height)
                        new_w = int(max_img_height * img_ratio)
                    
                    product_img = product_img.resize((new_w, new_h), Image.LANCZOS)
                    
                    # Center image
                    paste_x = (width - new_w) // 2
                    paste_y = 80
                    img.paste(product_img, (paste_x, paste_y))
                    
                    text_y = paste_y + new_h + 40
                except Exception as e:
                    print(f"Error loading product image: {e}")
                    text_y = 100
            else:
                text_y = 100
        else:
            text_y = 100

        # Add product title
        title_font = self._get_font(60)
        title = product["title"]
        
        # Word wrap title
        words = title.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=title_font)
            if bbox[2] - bbox[0] > width - 100:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        
        # Draw title
        for line in lines[:2]:  # Max 2 lines
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, text_y), line, fill='white', font=title_font)
            text_y += 70

        # Add price
        if show_price and product.get("price"):
            price_font = self._get_font(80)
            price_text = f"${product['price']}"
            
            if show_discount and product.get("compare_at_price"):
                # Show discount
                try:
                    original = float(product["compare_at_price"])
                    current = float(product["price"])
                    discount = int((1 - current/original) * 100)
                    price_text = f"SALE ${product['price']} ({discount}% OFF)"
                except:
                    pass
            
            bbox = draw.textbbox((0, 0), price_text, font=price_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            
            # Draw price with glow
            for offset in [-2, -1, 0, 1, 2]:
                draw.text((x+offset, text_y), price_text, fill=(0, 0, 0), font=price_font)
            draw.text((x, text_y), price_text, fill=(255, 215, 0), font=price_font)

        return img

    def create_product_video(self, product, platform="instagram_reels",
                              duration=5, show_price=True, show_discount=True,
                              bg_color=(20, 20, 30), bg_music=None):
        """
        Create promotional video for a single product
        """
        from ad_studio import AdStudio
        studio = AdStudio()
        template = studio.PLATFORMS.get(platform, studio.PLATFORMS["youtube"])
        w, h = template["width"], template["height"]
        fps = template["fps"]

        # Create frame
        frame = self._create_product_frame(product, w, h, show_price, show_discount, bg_color)

        # Generate frames
        frames_count = fps * duration
        for i in range(frames_count):
            frame.save(self.temp_dir / f"frame_{i:06d}.png")

        # Create video
        output_path = self.output_dir / f"product_{product['id']}_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%06d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p"
        ]

        if bg_music and os.path.exists(bg_music):
            cmd.extend([
                "-stream_loop", "-1",
                "-i", bg_music,
                "-t", str(duration),
                "-c:a", "aac",
                "-shortest"
            ])

        cmd.append(str(output_path))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup
        for f in self.temp_dir.glob("frame_*.png"):
            f.unlink()
        for f in self.temp_dir.glob("temp_product_*.jpg"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        return str(output_path)

    def create_multi_product_video(self, products, platform="instagram_reels",
                                    duration_per_product=4, show_price=True,
                                    show_discount=True, transition="fade",
                                    bg_color=(20, 20, 30), bg_music=None):
        """
        Create video showcasing multiple products
        """
        from ad_studio import AdStudio
        studio = AdStudio()
        template = studio.PLATFORMS.get(platform, studio.PLATFORMS["youtube"])
        w, h = template["width"], template["height"]
        fps = template["fps"]

        # Create frames for each product
        all_frames = []
        for idx, product in enumerate(products):
            print(f"  Creating frame for: {product['title']}")
            frame = self._create_product_frame(product, w, h, show_price, show_discount, bg_color)
            
            frames_count = fps * duration_per_product
            for i in range(frames_count):
                frame.save(self.temp_dir / f"frame_{len(all_frames):06d}.png")
                all_frames.append(1)

        # Create video
        output_path = self.output_dir / f"products_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%06d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p"
        ]

        if bg_music and os.path.exists(bg_music):
            total_duration = len(products) * duration_per_product
            cmd.extend([
                "-stream_loop", "-1",
                "-i", bg_music,
                "-t", str(total_duration),
                "-c:a", "aac",
                "-shortest"
            ])

        cmd.append(str(output_path))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Cleanup
        for f in self.temp_dir.glob("frame_*.png"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        return str(output_path)

    def create_sale_video(self, products, platform="instagram_reels",
                          sale_text="SALE", duration_per_product=3,
                          bg_music=None):
        """
        Create sale/promotional video
        """
        from ad_studio import AdStudio
        studio = AdStudio()
        template = studio.PLATFORMS.get(platform, studio.PLATFORMS["youtube"])
        w, h = template["width"], template["height"]
        fps = template["fps"]

        # Sale colors
        sale_colors = [(220, 20, 60), (255, 69, 0)]

        frames = []

        # Title frame
        title_img = Image.new('RGB', (w, h), sale_colors[0])
        draw = ImageDraw.Draw(title_img)
        
        title_font = self._get_font(120)
        bbox = draw.textbbox((0, 0), sale_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (w - text_width) // 2
        y = (h - 120) // 2
        
        for offset in [-3, -2, -1, 0, 1, 2, 3]:
            draw.text((x+offset, y), sale_text, fill=(0, 0, 0), font=title_font)
        draw.text((x, y), sale_text, fill='white', font=title_font)
        
        for i in range(fps * 2):  # 2 seconds title
            title_img.save(self.temp_dir / f"frame_{len(frames):06d}.png")
            frames.append(1)

        # Product frames
        for product in products:
            print(f"  Adding: {product['title']}")
            frame = self._create_product_frame(
                product, w, h, 
                show_price=True, 
                show_discount=True,
                bg_color=sale_colors[1]
            )
            
            for i in range(fps * duration_per_product):
                frame.save(self.temp_dir / f"frame_{len(frames):06d}.png")
                frames.append(1)

        # Create video
        output_path = self.output_dir / f"sale_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(self.temp_dir / "frame_%06d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p"
        ]

        if bg_music and os.path.exists(bg_music):
            total_duration = 2 + len(products) * duration_per_product
            cmd.extend([
                "-stream_loop", "-1",
                "-i", bg_music,
                "-t", str(total_duration),
                "-c:a", "aac",
                "-shortest"
            ])

        cmd.append(str(output_path))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        for f in self.temp_dir.glob("frame_*.png"):
            f.unlink()

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        return str(output_path)


# Quick functions
def setup_shopify(store_url, access_token):
    """Quick Shopify setup"""
    store = ShopifyStore()
    success = store.setup(store_url, access_token)
    if success:
        print("Shopify connected successfully!")
        products = store.get_products(limit=5)
        print(f"Found {len(products)} products")
        store.print_products(products)
    else:
        print("Connection failed. Check your credentials.")
    return store


def quick_product_video(product_id, platform="instagram_reels"):
    """Quick video for single product"""
    store = ShopifyStore()
    if not store.is_configured():
        print("Shopify not configured. Run setup_shopify() first.")
        return
    
    product = store.get_product(product_id)
    creator = ProductVideoCreator()
    return creator.create_product_video(product, platform)


if __name__ == "__main__":
    print("Shopify Integration for AdStudio Pro")
    print("=" * 50)
    
    store = ShopifyStore()
    if store.is_configured():
        print(f"Connected to: {store.config['store_url']}")
        products = store.get_products(limit=10)
        store.print_products(products)
    else:
        print("Not configured yet.")
        print("\nTo setup, run:")
        print('  setup_shopify("your-store.myshopify.com", "your-access-token")')
