from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

def validate_youtube_url(value):
    if value and not ('youtube.com' in value or 'youtu.be' in value):
        raise ValidationError('Only YouTube URLs are allowed (e.g., youtube.com or youtu.be).')

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    image = models.ImageField(upload_to="movies/")
    rating = models.DecimalField(max_digits=3, decimal_places=1, db_index=True)
    cast = models.TextField()
    description = models.TextField(blank=True, null=True) # optional
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    languages = models.ManyToManyField(Language, related_name='movies', blank=True)
    trailer_url = models.URLField(max_length=500, blank=True, null=True, validators=[validate_youtube_url])

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    image = models.ImageField(upload_to='cities/', blank=True, null=True)

    def __str__(self):
        return self.name

class Theater(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='theaters')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='theaters')
    time = models.DateTimeField(db_index=True)

    def __str__(self):
        city_name = self.city.name if self.city else "Unknown City"
        return f'{self.name} ({city_name}) - {self.movie.name} at {self.time}'

class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='locked_seats')
    locked_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=150.0)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('cancelled', 'Cancelled')], default='active')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def __str__(self):
        return f'Booking by {self.user.username} for {self.seat.seat_number} at {self.theater.name}'

class EmailLog(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='email_logs')
    recipient = models.EmailField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending')
    attempts = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class FoodItem(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image_url = models.URLField(max_length=500, blank=True)
    category = models.CharField(max_length=20, choices=[('snacks', 'Snacks'), ('drinks', 'Drinks'), ('combos', 'Combos')], default='snacks')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class BookingFoodItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='food_items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.food_item.name} for {self.booking.id}'

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f'{self.user.username} rated {self.movie.name} {self.rating}/5'

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('comedy', 'Standup Comedy'),
        ('music', 'Music Concerts'),
        ('theatre', 'Theatre Plays'),
        ('sports', 'Sports & Leagues'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='comedy')
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

class EventBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('cancelled', 'Cancelled')], default='active')

    def __str__(self):
        return f'{self.quantity} tickets for {self.event.name} by {self.user.username}'