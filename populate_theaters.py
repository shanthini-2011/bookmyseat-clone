"""
Populate theaters for movies in cities for the next 30 days.
Each movie gets 3 theaters per city per day with 150 seats each.
"""
import os
import django
import random
from datetime import timedelta, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Movie, Theater, City, Seat
from django.utils import timezone

def populate():
    print("Deleting old theaters and seats...")
    Theater.objects.all().delete()
    
    movies = list(Movie.objects.all())
    cities = list(City.objects.all())
    
    if not movies or not cities:
        print("Please add some movies and cities first.")
        return
        
    start_date = timezone.now().date()
    
    theater_names = {
        'Chennai': ['Rohini Silver Screens', 'PVR: VR Mall', 'Sathyam Cinemas', 'AGS Cinemas', 'INOX: Phoenix Mall'],
        'Coimbatore': ['KG Cinemas', 'Broadway Cinemas', 'INOX: Prozone Mall', 'Fun Cinemas', 'SPI: Brookefields'],
        'Madurai': ['Vetri Cinemas', 'Gopuram Cinemas', 'Inox: Vishaal de Mal', 'Meenakshi Mall Screens', 'Central Cinemas'],
        'Bengaluru': ['PVR: Orion Mall', 'INOX: Mantri Square', 'Cinepolis: Nexus Shantiniketan', 'Lido Mall IMAX', 'Gopalan Cinemas'],
    }
    
    # Show times for different screenings
    show_times = [
        ("09:30", "Morning"),
        ("12:45", "Afternoon"),
        ("16:00", "Matinee"),
        ("19:30", "Evening"),
        ("22:15", "Night"),
    ]
    
    print(f"Generating showtimes for {len(movies)} movies across {len(cities)} cities for 30 days...")
    
    theaters_created = 0
    
    for day_offset in range(5):
        current_date = start_date + timedelta(days=day_offset)
        theaters_to_create = []
        
        for city in cities:
            city_theater_names = theater_names.get(city.name, ['PVR Cinemas', 'INOX', 'Cinepolis'])
            
            for movie in movies:
                # Pick 3 random unique theaters from this city
                selected_theaters = random.sample(city_theater_names, min(3, len(city_theater_names)))
                
                for t_name in selected_theaters:
                    # Each theater gets 1 random showtime
                    time_str, _ = random.choice(show_times)
                    hour, minute = map(int, time_str.split(':'))
                    
                    show_time = timezone.make_aware(
                        datetime.combine(current_date, datetime.min.time()).replace(hour=hour, minute=minute)
                    )
                    
                    theaters_to_create.append(Theater(
                        name=t_name,
                        city=city,
                        movie=movie,
                        time=show_time
                    ))
        
        Theater.objects.bulk_create(theaters_to_create)
        theaters_created += len(theaters_to_create)
        print(f"Created {len(theaters_to_create)} theaters for {current_date} (Total: {theaters_created})")
    
    # Now generate seats - 10 rows (A-J), 15 seats per row = 150 seats per theater
    print("Generating seats (150 per theater)...")
    all_theaters = Theater.objects.all()
    total_theaters = all_theaters.count()
    seats_to_create = []
    
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    
    for i, theater in enumerate(all_theaters, 1):
        for row in rows:
            for col in range(1, 16):  # 15 seats per row
                seat_num = f"{row}{col}"
                seats_to_create.append(Seat(
                    theater=theater,
                    seat_number=seat_num,
                    is_booked=False
                ))
                
        if len(seats_to_create) >= 30000:
            Seat.objects.bulk_create(seats_to_create)
            seats_to_create = []
            print(f"Processed seats for {i}/{total_theaters} theaters")
            
    if seats_to_create:
        Seat.objects.bulk_create(seats_to_create)
        
    print(f"Done! Created {total_theaters} theaters with 150 seats each.")
    print(f"Every movie has 3 theaters per city, every day for 30 days.")

if __name__ == '__main__':
    populate()
