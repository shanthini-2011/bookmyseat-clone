"""Populate default events for all cities."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from movies.models import Event, City
from django.utils import timezone
from datetime import timedelta
import random

EVENTS_DATA = [
    # Comedy
    {'name': 'Zakir Khan Live - Haq Se Single', 'category': 'comedy', 'desc': 'India\'s most loved comedian brings his hilarious storytelling to your city.', 'price': 799, 'img': 'https://storage.googleapis.com/a1aa/image/wQXDIlqv4XoxGtNEO9XkSKBZYe9IuDePUWEcd0WwqcNzY5nTA.jpg'},
    {'name': 'Biswa Kalyan Rath - Sahi Galat', 'category': 'comedy', 'desc': 'Sharp observational comedy that makes you think and laugh.', 'price': 699, 'img': 'https://storage.googleapis.com/a1aa/image/wQXDIlqv4XoxGtNEO9XkSKBZYe9IuDePUWEcd0WwqcNzY5nTA.jpg'},
    {'name': 'Comicstaan Live Tour', 'category': 'comedy', 'desc': 'Your favorite Comicstaan comedians together on one stage!', 'price': 999, 'img': 'https://storage.googleapis.com/a1aa/image/wQXDIlqv4XoxGtNEO9XkSKBZYe9IuDePUWEcd0WwqcNzY5nTA.jpg'},

    # Music
    {'name': 'Anirudh Ravichander Live', 'category': 'music', 'desc': 'The rockstar of South Indian music - live concert with all hit songs.', 'price': 1499, 'img': 'https://storage.googleapis.com/a1aa/image/t52p8goZiO6QDBfid8wRyReanID18f5AxbszVhfPgESGklfcC.jpg'},
    {'name': 'AR Rahman - Infinite Love Tour', 'category': 'music', 'desc': 'Oscar-winning maestro AR Rahman performs his iconic compositions live.', 'price': 2499, 'img': 'https://storage.googleapis.com/a1aa/image/t52p8goZiO6QDBfid8wRyReanID18f5AxbszVhfPgESGklfcC.jpg'},
    {'name': 'Prateek Kuhad - Cold/Mess Tour', 'category': 'music', 'desc': 'Indie sensation performs acoustics under the stars.', 'price': 899, 'img': 'https://storage.googleapis.com/a1aa/image/t52p8goZiO6QDBfid8wRyReanID18f5AxbszVhfPgESGklfcC.jpg'},

    # Theatre
    {'name': 'Mughal-E-Azam - The Musical', 'category': 'theatre', 'desc': 'A spectacular Bollywood musical adapted from the legendary film.', 'price': 1299, 'img': 'https://storage.googleapis.com/a1aa/image/lAqCOht0TCaeSSLzw2ZGlPmDwvIEI3RtqajPoTYQN0ZOs8zJA.jpg'},
    {'name': 'Hamlet - Shakespeare Festival', 'category': 'theatre', 'desc': 'Classic Shakespeare brought to life by India\'s finest actors.', 'price': 599, 'img': 'https://storage.googleapis.com/a1aa/image/lAqCOht0TCaeSSLzw2ZGlPmDwvIEI3RtqajPoTYQN0ZOs8zJA.jpg'},
    {'name': 'Aadukalam - Tamil Stage Play', 'category': 'theatre', 'desc': 'The cult Tamil film adapted as a gripping stage performance.', 'price': 499, 'img': 'https://storage.googleapis.com/a1aa/image/lAqCOht0TCaeSSLzw2ZGlPmDwvIEI3RtqajPoTYQN0ZOs8zJA.jpg'},

    # Sports
    {'name': 'IPL 2026 - CSK vs MI', 'category': 'sports', 'desc': 'The biggest rivalry in cricket! Watch it live at the stadium.', 'price': 1999, 'img': 'https://storage.googleapis.com/a1aa/image/EyIkuIxpLaLyHBDEuu5hezeydhw0mOSjKWX71bUiuTBiY5nTA.jpg'},
    {'name': 'ISL - Chennaiyin FC vs Bengaluru FC', 'category': 'sports', 'desc': 'South Indian football derby - electrifying atmosphere guaranteed.', 'price': 499, 'img': 'https://storage.googleapis.com/a1aa/image/EyIkuIxpLaLyHBDEuu5hezeydhw0mOSjKWX71bUiuTBiY5nTA.jpg'},
    {'name': 'Pro Kabaddi League - Finals', 'category': 'sports', 'desc': 'The ultimate kabaddi showdown live at the arena!', 'price': 799, 'img': 'https://storage.googleapis.com/a1aa/image/EyIkuIxpLaLyHBDEuu5hezeydhw0mOSjKWX71bUiuTBiY5nTA.jpg'},
]

VENUES = {
    'Chennai': ['Jawaharlal Nehru Indoor Stadium', 'Music Academy', 'Sir Mutha Venkatasubba Rao Concert Hall', 'MA Chidambaram Stadium'],
    'Madurai': ['Tamukkam Grounds', 'Gandhi Museum Auditorium', 'Madurai Club Ground', 'Vandiyur Park Arena'],
    'Bengaluru': ['Palace Grounds', 'MLR Convention Centre', 'Chowdiah Memorial Hall', 'M Chinnaswamy Stadium'],
    'Coimbatore': ['Codissia Trade Fair Complex', 'PSG Kalyana Mandapam', 'Brookefields Convention Centre', 'Nehru Stadium'],
}

def populate():
    cities = City.objects.all()
    if not cities.exists():
        print('[ERROR] No cities found! Run populate_theaters.py first.')
        return

    now = timezone.now()
    created = 0

    for city in cities:
        city_venues = VENUES.get(city.name, ['City Convention Hall', 'Town Auditorium', 'Community Arena'])
        for evt_data in EVENTS_DATA:
            # Create 2 upcoming events per category per city
            for i in range(2):
                days_ahead = random.randint(3, 45)
                hour = random.choice([10, 14, 17, 19, 20])
                event_date = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=0, second=0, microsecond=0)
                venue = random.choice(city_venues)

                name_suffix = f" - {city.name}" if i == 0 else f" - {city.name} (Show {i+1})"

                Event.objects.get_or_create(
                    name=evt_data['name'] + name_suffix,
                    defaults={
                        'category': evt_data['category'],
                        'description': evt_data['desc'],
                        'ticket_price': evt_data['price'],
                        'date': event_date,
                        'location': venue,
                        'city': city,
                        'image': '',  # We'll use URL in template
                    }
                )
                created += 1

    print(f'[DONE] Created {created} events across {cities.count()} cities.')
    for city in cities:
        count = Event.objects.filter(city=city).count()
        print(f'  {city.name}: {count} events')

if __name__ == '__main__':
    populate()
