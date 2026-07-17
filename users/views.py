from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .forms import UserRegisterForm, UserUpdateForm
from django.shortcuts import render,redirect
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from movies.models import Movie , Booking, EventBooking

def home(request):
    selected_city_id = request.session.get('selected_city_id')
    if selected_city_id:
        movies = Movie.objects.filter(theaters__city_id=selected_city_id).distinct()
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'movies': movies})
def register(request):
    if request.method == 'POST':
        form=UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data.get('username')
            password=form.cleaned_data.get('password1')
            user=authenticate(username=username,password=password)
            login(request,user)
            return redirect('profile')
    else:
        form=UserRegisterForm()
    return render(request,'users/register.html',{'form':form})

def login_view(request):
    if request.method == 'POST':
        form=AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request,user)
            return redirect('/')
    else:
        form=AuthenticationForm()
    return render(request,'users/login.html',{'form':form})

@login_required
def profile(request):
    bookings= Booking.objects.filter(user=request.user)
    event_bookings = EventBooking.objects.filter(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)

    return render(request, 'users/profile.html', {'u_form': u_form,'bookings':bookings, 'event_bookings': event_bookings})

@login_required
def reset_password(request):
    if request.method == 'POST':
        form=PasswordChangeForm(user=request.user,data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form=PasswordChangeForm(user=request.user)
    return render(request,'users/reset_password.html',{'form':form})


from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import ExtractHour
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from movies.models import Movie, Theater, Seat, Booking, EmailLog

@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    # Try fetching compiled stats from the cache to prevent DB load (Task 4 caching)
    stats = cache.get('admin_dashboard_stats')
    
    if not stats:
        now = timezone.now()
        
        # 1. Total Revenue metrics (daily, weekly, monthly) using database-level aggregations
        daily_rev = Booking.objects.filter(
            booked_at__gte=now - timedelta(days=1), 
            status='active'
        ).aggregate(sum=Sum('price'))['sum'] or 0.00
        
        weekly_rev = Booking.objects.filter(
            booked_at__gte=now - timedelta(days=7), 
            status='active'
        ).aggregate(sum=Sum('price'))['sum'] or 0.00
        
        monthly_rev = Booking.objects.filter(
            booked_at__gte=now - timedelta(days=30), 
            status='active'
        ).aggregate(sum=Sum('price'))['sum'] or 0.00
        
        # 2. Most Popular Movies (ranked by ticket bookings)
        popular_movies = Movie.objects.annotate(
            booking_count=Count('booking', filter=Q(booking__status='active'))
        ).order_by('-booking_count')[:5]
        
        # 3. Busiest Theaters (calculated via occupancy rates)
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
                'time': t.time,
                'occupancy_rate': round(rate, 2)
            })
        theaters_data = sorted(theaters_data, key=lambda x: x['occupancy_rate'], reverse=True)[:5]
        
        # 4. Peak Booking Hours
        peak_hours = Booking.objects.annotate(
            hour=ExtractHour('booked_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # 5. Cancellation Rates
        total_bookings = Booking.objects.count()
        cancelled_bookings = Booking.objects.filter(status='cancelled').count()
        cancellation_rate = (cancelled_bookings * 100.0 / total_bookings) if total_bookings > 0 else 0.0
        
        # 6. Email Monitoring Logs (Task 6 monitoring logs)
        total_emails = EmailLog.objects.count()
        sent_emails = EmailLog.objects.filter(status='sent').count()
        failed_emails = EmailLog.objects.filter(status='failed').count()
        pending_emails = EmailLog.objects.filter(status='pending').count()
        recent_failures = EmailLog.objects.filter(status='failed').order_by('-updated_at')[:10]
        
        stats = {
            'revenue': {
                'daily': daily_rev,
                'weekly': weekly_rev,
                'monthly': monthly_rev
            },
            'popular_movies': popular_movies,
            'theaters': theaters_data,
            'peak_hours': peak_hours,
            'cancellation': {
                'total': total_bookings,
                'cancelled': cancelled_bookings,
                'rate': round(cancellation_rate, 2)
            },
            'emails': {
                'total': total_emails,
                'sent': sent_emails,
                'failed': failed_emails,
                'pending': pending_emails,
                'recent_failures': recent_failures
            }
        }
        # Save to cache for 5 minutes
        cache.set('admin_dashboard_stats', stats, 300)
        
    return render(request, 'users/admin_dashboard.html', {'stats': stats})