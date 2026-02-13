#!/usr/bin/env python3
"""
Parent Map HK - Image Caching Script
Automatically fetches external images and caches them to Cloudinary
"""

import os
import json
import requests
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

WORKSPACE = Path("/root/.openclaw/workspace/parent-map-hk")

def get_cloudinary_url(public_id, transformations="w_600,h_400,c_fill,q_auto,f_auto"):
    """Generate Cloudinary URL with transformations"""
    return f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/{transformations}/{public_id}"

def upload_to_cloudinary(image_url, public_id):
    """Upload image from URL to Cloudinary"""
    try:
        result = cloudinary.uploader.upload(
            image_url,
            public_id=public_id,
            folder="places",
            overwrite=True,
            resource_type="image"
        )
        return result.get('secure_url')
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

def extract_image_from_website(website_url):
    """Try to extract Open Graph image from website"""
    try:
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(website_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Try Twitter card image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
        # Try first large image
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', img.get('data-src', ''))
            if src and ('logo' not in src.lower() and 'icon' not in src.lower()):
                if src.startswith('http'):
                    return src
                elif src.startswith('/'):
                    parsed = urlparse(website_url)
                    return f"{parsed.scheme}://{parsed.netloc}{src}"
        
        return None
    except Exception as e:
        print(f"❌ Failed to extract image: {e}")
        return None

def process_place(place):
    """Process a single place - find and cache image"""
    place_id = place.get('id', '').replace('-', '_')
    name = place.get('name', '')
    website = place.get('website', '')
    
    print(f"\n📍 Processing: {name}")
    
    # Check if already has local image
    local_path = WORKSPACE / "images" / "places" / f"{place_id}.jpg"
    if local_path.exists():
        print(f"  ✓ Local image exists")
        return {
            'local': f"/images/places/{place_id}.jpg",
            'cloudinary': None,
            'fallback': None
        }
    
    # Try to extract image from website
    if website:
        print(f"  🔍 Extracting from: {website}")
        image_url = extract_image_from_website(website)
        
        if image_url:
            print(f"  ✓ Found image: {image_url[:60]}...")
            cloudinary_url = upload_to_cloudinary(image_url, f"places/{place_id}")
            
            if cloudinary_url:
                print(f"  ✓ Uploaded to Cloudinary")
                return {
                    'local': None,
                    'cloudinary': get_cloudinary_url(f"places/{place_id}"),
                    'fallback': None
                }
    
    print(f"  ⚠️ No image found")
    return {
        'local': None,
        'cloudinary': None,
        'fallback': f"/images/placeholder-{place.get('category', 'playhouse')}.svg"
    }

def main():
    """Main entry point"""
    print("=" * 60)
    print("☁️ Cloudinary Image Caching")
    print("=" * 60)
    
    # Check configuration
    if not os.getenv("CLOUDINARY_CLOUD_NAME"):
        print("❌ Cloudinary not configured. Please set CLOUDINARY_CLOUD_NAME")
        return
    
    print(f"Cloud: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
    
    # Load locations
    locations_file = WORKSPACE / "data" / "locations.json"
    with open(locations_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    locations = data.get('locations', [])
    print(f"\n📊 Total locations: {len(locations)}")
    
    # Process top 10 locations first
    top_locations = locations[:10]
    print(f"Processing top {len(top_locations)} locations...")
    
    updated_count = 0
    for place in top_locations:
        images = process_place(place)
        if images['local'] or images['cloudinary']:
            place['images'] = images
            updated_count += 1
    
    # Save updated data
    if updated_count > 0:
        with open(locations_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Updated {updated_count} locations with images")
    
    print("\n✅ Done")

if __name__ == "__main__":
    main()
