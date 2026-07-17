import os
import django
import urllib.request
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Event

# Unsplash Source URLs for dummy images
IMAGE_URLS = {
    'comedy': 'https://images.unsplash.com/photo-1585699324551-f6c309eedeca?q=80&w=800&auto=format&fit=crop',
    'music': 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?q=80&w=800&auto=format&fit=crop',
    'theatre': 'https://images.unsplash.com/photo-1516280440542-5f80fc520268?q=80&w=800&auto=format&fit=crop',
    'sports': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?q=80&w=800&auto=format&fit=crop',
}

def update_event_images():
    # Ensure media/events dir exists
    os.makedirs('media/events', exist_ok=True)
    
    # Download images and save temporarily
    image_contents = {}
    for cat, url in IMAGE_URLS.items():
        print(f"Downloading image for {cat}...")
        try:
            # We use a user agent to avoid 403 Forbidden
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                image_contents[cat] = response.read()
        except Exception as e:
            print(f"Failed to download {cat} image: {e}")
            return
            
    events = Event.objects.all()
    print(f"Found {events.count()} events. Updating images...")
    
    for event in events:
        if event.category in image_contents:
            file_name = f"{event.category}_placeholder.jpg"
            event.image.save(file_name, ContentFile(image_contents[event.category]), save=True)
            
    print("Successfully updated all event images!")

if __name__ == '__main__':
    update_event_images()
