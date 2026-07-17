import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Q
from django.db.models.functions import ExtractHour
from movies.models import Booking, Movie, Theater

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # We only want superusers to connect, but for simplicity we will accept 
        # and then check permissions. Or just accept since it's a secured route.
        self.group_name = 'admin_dashboard'
        
        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        stats = await self.get_dashboard_stats()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'stats': stats
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from room group
    async def dashboard_update(self, event):
        # When a new booking is made, this gets triggered
        stats = await self.get_dashboard_stats()
        await self.send(text_data=json.dumps({
            'type': 'update_data',
            'stats': stats
        }))

    @database_sync_to_async
    def get_dashboard_stats(self):
        now = timezone.now()
        
        daily_rev = float(Booking.objects.filter(booked_at__gte=now - timedelta(days=1), status='active').aggregate(sum=Sum('price'))['sum'] or 0.00)
        weekly_rev = float(Booking.objects.filter(booked_at__gte=now - timedelta(days=7), status='active').aggregate(sum=Sum('price'))['sum'] or 0.00)
        monthly_rev = float(Booking.objects.filter(booked_at__gte=now - timedelta(days=30), status='active').aggregate(sum=Sum('price'))['sum'] or 0.00)
        
        popular_movies_qs = Movie.objects.annotate(booking_count=Count('booking', filter=Q(booking__status='active'))).order_by('-booking_count')[:5]
        popular_movies = [{'name': m.name, 'booking_count': m.booking_count} for m in popular_movies_qs]
        
        busiest_theaters = Theater.objects.annotate(
            total_seats=Count('seats'),
            booked_seats=Count('seats', filter=Q(seats__is_booked=True))
        )
        theaters_data = []
        for t in busiest_theaters:
            rate = (t.booked_seats * 100.0 / t.total_seats) if t.total_seats > 0 else 0.0
            theaters_data.append({
                'name': t.name,
                'movie': t.movie.name,
                'occupancy_rate': round(rate, 2)
            })
        theaters_data = sorted(theaters_data, key=lambda x: x['occupancy_rate'], reverse=True)[:5]
        
        peak_hours_qs = Booking.objects.annotate(hour=ExtractHour('booked_at')).values('hour').annotate(count=Count('id')).order_by('hour')
        # Format for chart (24 hours)
        hours_data = [0] * 24
        for item in peak_hours_qs:
            if item['hour'] is not None:
                hours_data[item['hour']] = item['count']
        
        total_bookings = Booking.objects.count()
        cancelled_bookings = Booking.objects.filter(status='cancelled').count()
        cancellation_rate = (cancelled_bookings * 100.0 / total_bookings) if total_bookings > 0 else 0.0
        
        return {
            'revenue': {
                'daily': daily_rev,
                'weekly': weekly_rev,
                'monthly': monthly_rev
            },
            'popular_movies': popular_movies,
            'theaters': theaters_data,
            'peak_hours': hours_data,
            'cancellation': {
                'total': total_bookings,
                'cancelled': cancelled_bookings,
                'rate': round(cancellation_rate, 2)
            }
        }
