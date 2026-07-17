from django.contrib import admin
from .models import Movie, Theater, Seat, Booking, Genre, Language, EmailLog, FoodItem, BookingFoodItem, Review, Event, EventBooking, City

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'cast', 'description']
    filter_horizontal = ('genres', 'languages')

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'movie', 'time']
    list_filter = ['city', 'movie']

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater', 'seat_number', 'is_booked']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'seat', 'movie', 'theater', 'booked_at']

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['booking', 'recipient', 'status', 'attempts', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['recipient', 'booking__id']

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_available']
    list_filter = ['category', 'is_available']

@admin.register(BookingFoodItem)
class BookingFoodItemAdmin(admin.ModelAdmin):
    list_display = ['booking', 'food_item', 'quantity']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'date', 'location', 'ticket_price')
    list_filter = ('category', 'date')
    search_fields = ('name', 'location')

@admin.register(EventBooking)
class EventBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'quantity', 'total_price', 'booked_at', 'status')
    list_filter = ('status', 'booked_at', 'event')
    search_fields = ('user__username', 'event__name')
