import os
import sys
import django
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Movie, Theater, Seat, Genre, Language, FoodItem
from django.utils.timezone import make_aware
from django.core.files.base import ContentFile

def populate():
    print("=" * 50)
    print("Populating BookMySeat with real movie data...")
    print("=" * 50)
    
    # Genres
    genre_names = ['Action', 'Thriller', 'Sci-Fi', 'Comedy', 'Drama', 'Horror', 'Romance', 'Adventure']
    genres = {}
    for g in genre_names:
        obj, _ = Genre.objects.get_or_create(name=g)
        genres[g] = obj
    print(f"[✓] {len(genres)} genres ready")
    
    # Languages
    lang_names = ['Tamil', 'English', 'Hindi', 'Telugu', 'Malayalam', 'Kannada']
    languages = {}
    for l in lang_names:
        obj, _ = Language.objects.get_or_create(name=l)
        languages[l] = obj
    print(f"[✓] {len(languages)} languages ready")
    
    # Movies Data
    movies_data = [
        {
            'name': 'Vikram',
            'rating': 8.4,
            'cast': 'Kamal Haasan, Fahadh Faasil, Vijay Sethupathi, Narain',
            'desc': 'A special investigator uncovers a series of murders and discovers a sinister conspiracy far deeper than he imagined. Packed with intense action and unexpected twists.',
            'genres': ['Action', 'Thriller'],
            'langs': ['Tamil', 'Hindi', 'Telugu'],
            'trailer': 'https://www.youtube.com/watch?v=OKBMCL-frPU',
            'theaters': ['PVR IMAX Screen 1', 'Sathyam Cinemas'],
        },
        {
            'name': 'Jailer',
            'rating': 7.9,
            'cast': 'Rajinikanth, Mohanlal, Shivarajkumar, Jackie Shroff',
            'desc': 'A retired jailer goes on a dangerous manhunt after his son is targeted by a powerful drug cartel. Superstar Rajinikanth delivers a power-packed performance.',
            'genres': ['Action', 'Comedy'],
            'langs': ['Tamil', 'Telugu', 'Hindi'],
            'trailer': 'https://www.youtube.com/watch?v=wCkVYB1mvf0',
            'theaters': ['INOX Multiplex', 'PVR Gold Screen'],
        },
        {
            'name': 'Leo',
            'rating': 7.5,
            'cast': 'Vijay, Trisha, Sanjay Dutt, Arjun Sarja',
            'desc': 'A mild-mannered cafe owner is forced to confront his dark past when a ruthless gang threatens his family. A gripping tale of identity and vengeance.',
            'genres': ['Action', 'Thriller'],
            'langs': ['Tamil', 'Telugu', 'Hindi'],
            'trailer': 'https://www.youtube.com/watch?v=aBE3RSXK1os',
            'theaters': ['Rohini Silver Screen', 'AGS Cinemas IMAX'],
        },
        {
            'name': 'KGF Chapter 2',
            'rating': 8.3,
            'cast': 'Yash, Sanjay Dutt, Raveena Tandon, Srinidhi Shetty',
            'desc': 'Rocky\'s reign over Kolar Gold Fields is challenged by Adheera, a ruthless adversary. The saga of power, ambition, and legacy continues in this blockbuster sequel.',
            'genres': ['Action', 'Drama'],
            'langs': ['Kannada', 'Hindi', 'Tamil', 'Telugu'],
            'trailer': 'https://www.youtube.com/watch?v=JKa05nyUmuQ',
            'theaters': ['PVR Orion Mall', 'INOX Forum Mall'],
        },
        {
            'name': 'RRR',
            'rating': 8.0,
            'cast': 'Jr NTR, Ram Charan, Alia Bhatt, Ajay Devgn',
            'desc': 'A fictional tale of two legendary Indian revolutionaries, Alluri Sitarama Raju and Komaram Bheem, and their battle against the British Empire.',
            'genres': ['Action', 'Drama', 'Adventure'],
            'langs': ['Telugu', 'Hindi', 'Tamil'],
            'trailer': 'https://www.youtube.com/watch?v=f_vbAtFSEc0',
            'theaters': ['AMB Cinemas', 'Prasads Multiplex'],
        },
        {
            'name': 'Interstellar',
            'rating': 9.0,
            'cast': 'Matthew McConaughey, Anne Hathaway, Jessica Chastain, Michael Caine',
            'desc': 'A team of explorers travel through a wormhole in space to ensure humanity\'s survival. Christopher Nolan\'s magnum opus pushes the boundaries of science fiction.',
            'genres': ['Sci-Fi', 'Drama', 'Adventure'],
            'langs': ['English', 'Hindi', 'Tamil'],
            'trailer': 'https://www.youtube.com/watch?v=zSWdZVtXT7E',
            'theaters': ['PVR IMAX Delhi', 'Cinepolis VR Mall'],
        },
        {
            'name': 'The Dark Knight',
            'rating': 9.2,
            'cast': 'Christian Bale, Heath Ledger, Aaron Eckhart, Morgan Freeman',
            'desc': 'Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice when the menacing Joker wreaks havoc on Gotham.',
            'genres': ['Action', 'Thriller', 'Drama'],
            'langs': ['English', 'Hindi'],
            'trailer': 'https://www.youtube.com/watch?v=EXeTwQWrcwY',
            'theaters': ['PVR Director\'s Cut', 'INOX Insignia'],
        },
        {
            'name': 'Ponniyin Selvan',
            'rating': 7.8,
            'cast': 'Vikram, Aishwarya Rai, Jayam Ravi, Karthi, Trisha',
            'desc': 'An epic historical drama set in the Chola dynasty. A tale of palace intrigue, war, and loyalty unfolds in ancient South India.',
            'genres': ['Drama', 'Action', 'Adventure'],
            'langs': ['Tamil', 'Hindi', 'Telugu', 'Malayalam'],
            'trailer': 'https://www.youtube.com/watch?v=OwYGikLMHEI',
            'theaters': ['Sathyam IMAX', 'PVR ECR'],
        },
    ]

    for mdata in movies_data:
        m, created = Movie.objects.get_or_create(name=mdata['name'], defaults={
            'rating': mdata['rating'],
            'cast': mdata['cast'],
            'description': mdata['desc'],
            'trailer_url': mdata['trailer'],
        })
        
        if created:
            # Create a simple colored placeholder image using Pillow
            try:
                from PIL import Image, ImageDraw, ImageFont
                import hashlib
                
                # Generate unique color from movie name
                hash_val = int(hashlib.md5(mdata['name'].encode()).hexdigest()[:6], 16)
                r = (hash_val >> 16) & 0xFF
                g = (hash_val >> 8) & 0xFF
                b = hash_val & 0xFF
                # Make colors more vibrant
                r = min(255, r + 60)
                g = min(255, g + 40)
                b = min(255, b + 80)
                
                img = Image.new('RGB', (400, 600), (r, g, b))
                draw = ImageDraw.Draw(img)
                
                # Add gradient overlay
                for y in range(600):
                    alpha = int(y / 600 * 180)
                    draw.line([(0, y), (400, y)], fill=(alpha//3, alpha//4, alpha//2))
                
                # Add movie name text
                try:
                    font = ImageFont.truetype("arial.ttf", 32)
                except:
                    font = ImageFont.load_default()
                
                # Draw text with shadow
                text = mdata['name']
                draw.text((22, 502), text, fill=(0, 0, 0), font=font)
                draw.text((20, 500), text, fill=(255, 255, 255), font=font)
                
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                buffer.seek(0)
                m.image.save(f"{mdata['name'].replace(' ', '_')}.jpg", ContentFile(buffer.read()), save=True)
                print(f"  [✓] Created poster for {mdata['name']}")
            except Exception as e:
                print(f"  [!] Failed to create poster for {mdata['name']}: {e}")
            
            for g_name in mdata['genres']:
                m.genres.add(genres[g_name])
            for l_name in mdata['langs']:
                m.languages.add(languages[l_name])
        else:
            print(f"  [~] {mdata['name']} already exists, skipping")
            continue
            
        # Create theaters and seats (rows A-J, 13 seats each = 130 seats per theater)
        for t_name in mdata['theaters']:
            for day_offset in range(1, 4):  # 3 days of shows
                for hour in [10, 14, 18, 21]:  # 4 showtimes per day
                    t_time = datetime.now() + timedelta(days=day_offset, hours=hour - datetime.now().hour)
                    t, t_created = Theater.objects.get_or_create(
                        name=t_name,
                        movie=m,
                        time=make_aware(t_time.replace(hour=hour, minute=0, second=0)),
                    )
                    if t_created:
                        # Create seats: rows A-J, 13 seats each
                        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
                        for row in rows:
                            for num in range(1, 14):
                                Seat.objects.create(theater=t, seat_number=f"{row}{num}")
        
        print(f"  [✓] {mdata['name']} - theaters and seats created")
    
    # Food & Beverages Data
    print("\n" + "=" * 50)
    print("Adding Food & Beverage items...")
    print("=" * 50)
    
    food_data = [
        {'name': 'Large Popcorn', 'price': 5.99, 'category': 'snacks'},
        {'name': 'Regular Popcorn', 'price': 3.99, 'category': 'snacks'},
        {'name': 'Nachos with Salsa', 'price': 4.49, 'category': 'snacks'},
        {'name': 'Coca-Cola (Large)', 'price': 3.49, 'category': 'drinks'},
        {'name': 'Pepsi (Large)', 'price': 3.49, 'category': 'drinks'},
        {'name': 'Mineral Water', 'price': 1.99, 'category': 'drinks'},
        {'name': 'Popcorn + Coke Combo', 'price': 7.99, 'category': 'combos'},
        {'name': 'Family Combo (2 Popcorn + 2 Drinks)', 'price': 14.99, 'category': 'combos'},
    ]
    
    for fd in food_data:
        fi, created = FoodItem.objects.get_or_create(
            name=fd['name'],
            defaults={'price': fd['price'], 'category': fd['category']}
        )
        if created:
            print(f"  [✓] Added {fd['name']} - ${fd['price']}")
    
    print("\n" + "=" * 50)
    print("✅ Data population complete!")
    print(f"   Movies: {Movie.objects.count()}")
    print(f"   Theaters: {Theater.objects.count()}")
    print(f"   Seats: {Seat.objects.count()}")
    print(f"   Food Items: {FoodItem.objects.count()}")
    print("=" * 50)

if __name__ == '__main__':
    populate()
