import re
import io
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking, Genre, Language, FoodItem, BookingFoodItem, Review, City
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.files.base import ContentFile
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta, datetime
from collections import OrderedDict
from django.http import JsonResponse

def get_safe_youtube_url(url):
    if not url:
        return None
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    match = re.match(youtube_regex, url)
    if match:
        video_id = match.group(6)
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

from django.core.paginator import Paginator
from django.db.models import Count, Q

def movie_list(request):
    # Prefetch genres and languages to prevent N+1 DB queries
    movies = Movie.objects.all().prefetch_related('genres', 'languages')
    
    # Filter by selected city in session
    selected_city_id = request.session.get('selected_city_id')
    if selected_city_id:
        movies = movies.filter(theaters__city_id=selected_city_id).distinct()

    # 1. Search Query
    search_query = request.GET.get('search', '').strip()
    if search_query:
        movies = movies.filter(name__icontains=search_query)
        
    # We store the pre-category-filtered query to calculate accurate facet counts
    base_movies = movies
    
    # Selected filters from request
    selected_genres = request.GET.getlist('genres')
    selected_languages = request.GET.getlist('languages')
    
    # 2. Apply Filters (using distinct() since filter joins on ManyToMany can multiply rows)
    if selected_genres:
        movies = movies.filter(genres__id__in=selected_genres).distinct()
    if selected_languages:
        movies = movies.filter(languages__id__in=selected_languages).distinct()
        
    # 3. Sorting Options
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'rating_desc':
        movies = movies.order_by('-rating')
    elif sort_by == 'rating_asc':
        movies = movies.order_by('rating')
    else:
        movies = movies.order_by('name')
        
    # 4. Pagination (6 movies per page)
    paginator = Paginator(movies, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 5. Facet Counts Calculation (Dynamic Counts)
    genre_base = base_movies
    if selected_languages:
        genre_base = genre_base.filter(languages__id__in=selected_languages)
        
    genre_counts = dict(
        Movie.genres.through.objects.filter(movie__in=genre_base)
        .values('genre_id')
        .annotate(count=Count('movie_id'))
        .values_list('genre_id', 'count')
    )
    genre_facets = [
        {
            'id': genre.id,
            'name': genre.name,
            'movie_count': genre_counts.get(genre.id, 0)
        }
        for genre in Genre.objects.all()
    ]
    
    lang_base = base_movies
    if selected_genres:
        lang_base = lang_base.filter(genres__id__in=selected_genres)
        
    lang_counts = dict(
        Movie.languages.through.objects.filter(movie__in=lang_base)
        .values('language_id')
        .annotate(count=Count('movie_id'))
        .values_list('language_id', 'count')
    )
    lang_facets = [
        {
            'id': lang.id,
            'name': lang.name,
            'movie_count': lang_counts.get(lang.id, 0)
        }
        for lang in Language.objects.all()
    ]
    
    # Preserve query parameters in pagination URLs
    query_params = request.GET.copy()
    query_params.pop('page', None)
    pagination_query_string = query_params.urlencode()
    
    context = {
        'page_obj': page_obj,
        'selected_genres': [int(x) for x in selected_genres],
        'selected_languages': [int(x) for x in selected_languages],
        'sort_by': sort_by,
        'search_query': search_query,
        'genre_facets': genre_facets,
        'lang_facets': lang_facets,
        'pagination_query_string': pagination_query_string,
    }
    return render(request, 'movies/movie_list.html', context)



def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    safe_trailer = get_safe_youtube_url(movie.trailer_url)
    
    # Date Logic for the Date Selector
    today = timezone.localtime(timezone.now()).date()
    date_param = request.GET.get('date')
    selected_date = today
    if date_param:
        try:
            parsed_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            if parsed_date >= today:
                selected_date = parsed_date
        except ValueError:
            pass
            
    available_dates = [today + timedelta(days=i) for i in range(7)]
    
    # Fetch and filter theaters
    theaters_qs = Theater.objects.filter(movie=movie)
    selected_city_id = request.session.get('selected_city_id')
    if selected_city_id:
        theaters_qs = theaters_qs.filter(city_id=selected_city_id)
        
    theaters_qs = theaters_qs.filter(time__date=selected_date).order_by('name', 'time')
    
    # Group by theater name to show all showtimes under one theater
    grouped_theaters = OrderedDict()
    for t in theaters_qs:
        if t.name not in grouped_theaters:
            grouped_theaters[t.name] = []
        grouped_theaters[t.name].append(t)
    
    # Reviews & Ratings
    reviews = Review.objects.filter(movie=movie).select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    user_review = None
    can_review = False
    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, movie=movie).first()
        can_review = True
    
    return render(request, 'movies/theater_list.html', {
        'movie': movie,
        'grouped_theaters': grouped_theaters,
        'safe_trailer': safe_trailer,
        'available_dates': available_dates,
        'selected_date': selected_date,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'user_review': user_review,
        'can_review': can_review,
    })

def set_city(request):
    if request.method == 'POST':
        city_id = request.POST.get('city_id')
        if city_id:
            try:
                city = City.objects.get(id=city_id)
                request.session['selected_city_id'] = city.id
                request.session['selected_city_name'] = city.name
                return JsonResponse({'status': 'success', 'city': city.name})
            except City.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'City not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url='/login/')
def submit_review(request, movie_id):
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=movie_id)
        rating = int(request.POST.get('rating', 5))
        comment = request.POST.get('comment', '').strip()
        
        # Allow any authenticated user to review
        Review.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'rating': rating, 'comment': comment}
        )
    return redirect('theater_list', movie_id=movie_id)


from django.db import transaction
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import stripe
from collections import OrderedDict


# Fallback keys if not set in settings.py
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_51PxMockSecretKey')
STRIPE_WEBHOOK_SECRET = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_MockSecret')

@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater).order_by('seat_number')
    
    # Calculate locking statuses for frontend rendering
    expiry_limit = timezone.now() - timedelta(minutes=2)
    for seat in seats:
        seat.status = 'available'
        if seat.is_booked:
            seat.status = 'booked'
        elif seat.locked_by and seat.locked_at and seat.locked_at > expiry_limit:
            if seat.locked_by == request.user:
                seat.status = 'selected'
            else:
                seat.status = 'locked'

    # Organize seats by row for BookMyShow-style layout
    seat_rows = OrderedDict()
    for seat in seats:
        row_letter = seat.seat_number[0] if seat.seat_number else '?'
        if row_letter not in seat_rows:
            seat_rows[row_letter] = []
        seat_rows[row_letter].append(seat)

    if request.method == 'POST':
        selected_seat_ids = request.POST.getlist('seats')
        if not selected_seat_ids:
            return render(request, "movies/seat_selection.html", {
                'theaters': theater,
                'seats': seats,
                'seat_rows': seat_rows,
                'error': "No seat selected. Please select at least one seat."
            })
            
        try:
            # Atomic transaction block with row-level locks
            with transaction.atomic():
                locked_seats = Seat.objects.select_for_update().filter(
                    id__in=selected_seat_ids, 
                    theater=theater
                )
                
                # Check for any concurrency booking conflicts
                conflict_seats = []
                for seat in locked_seats:
                    if seat.is_booked:
                        conflict_seats.append(seat.seat_number)
                    elif seat.locked_by and seat.locked_at and seat.locked_by != request.user and seat.locked_at > expiry_limit:
                        conflict_seats.append(seat.seat_number)
                
                if conflict_seats:
                    raise ValueError(f"The following seats were booked/locked by another user: {', '.join(conflict_seats)}")
                
                # Apply temporary seat locks (2-minute timeout)
                for seat in locked_seats:
                    seat.locked_by = request.user
                    seat.locked_at = timezone.now()
                    seat.save()
            
            # Lock acquired! Proceed to checkout confirmation page
            return redirect('checkout_confirmation', theater_id=theater.id)
            
        except ValueError as e:
            return render(request, "movies/seat_selection.html", {
                'theaters': theater,
                'seats': seats,
                'seat_rows': seat_rows,
                'error': str(e)
            })
        except Exception as e:
            return render(request, "movies/seat_selection.html", {
                'theaters': theater,
                'seats': seats,
                'seat_rows': seat_rows,
                'error': "An unexpected error occurred. Please try again."
            })

    return render(request, 'movies/seat_selection.html', {
        'theaters': theater,
        'seats': seats,
        'seat_rows': seat_rows,
    })


@login_required(login_url='/login/')
def checkout_confirmation(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    expiry_limit = timezone.now() - timedelta(minutes=2)
    
    # Query seats locked by the current user
    locked_seats = Seat.objects.filter(
        theater=theater, 
        locked_by=request.user, 
        locked_at__gt=expiry_limit,
        is_booked=False
    )
    
    if not locked_seats.exists():
        return render(request, "movies/seat_selection.html", {
            'theaters': theater,
            'seats': Seat.objects.filter(theater=theater),
            'seat_rows': {},
            'error': "Your seat locks have expired. Please select your seats again."
        })
        
    # Calculate pricing and lock countdown
    seat_price = 15.00
    total_price = len(locked_seats) * seat_price
    oldest_lock = min([s.locked_at for s in locked_seats])
    elapsed = (timezone.now() - oldest_lock).total_seconds()
    remaining_seconds = max(0, int(120 - elapsed))
    
    # Food & Beverages (Feature 2)
    food_items = FoodItem.objects.filter(is_available=True)
    
    context = {
        'theater': theater,
        'seats': locked_seats,
        'total_price': total_price,
        'remaining_seconds': remaining_seconds,
        'food_items': food_items,
    }
    return render(request, 'movies/checkout_confirmation.html', context)


@login_required(login_url='/login/')
def create_checkout_session(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)
    expiry_limit = timezone.now() - timedelta(minutes=2)
    locked_seats = Seat.objects.filter(
        theater=theater, 
        locked_by=request.user, 
        locked_at__gt=expiry_limit,
        is_booked=False
    )
    
    if not locked_seats.exists():
        return redirect('book_seats', theater_id=theater.id)
        
    seat_price = 15.00
    seat_names = ", ".join([s.seat_number for s in locked_seats])
    seat_ids = ",".join([str(s.id) for s in locked_seats])
    
    # Calculate food total from POST data
    food_total = 0.0
    food_data = {}
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('food_qty_'):
                food_id = key.replace('food_qty_', '')
                qty = int(value) if value.isdigit() and int(value) > 0 else 0
                if qty > 0:
                    try:
                        fi = FoodItem.objects.get(id=food_id, is_available=True)
                        food_total += float(fi.price) * qty
                        food_data[food_id] = qty
                    except FoodItem.DoesNotExist:
                        pass
    
    try:
        line_items = [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Ticket for {theater.movie.name}',
                    'description': f'{theater.name} - Seats: {seat_names}',
                },
                'unit_amount': int(seat_price * 100),
            },
            'quantity': len(locked_seats),
        }]
        
        # Add food items as separate line items
        if food_total > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Food & Beverages',
                        'description': 'F&B Add-ons',
                    },
                    'unit_amount': int(food_total * 100),
                },
                'quantity': 1,
            })
        
        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('payment_cancel')) + f'?theater_id={theater.id}',
            client_reference_id=str(request.user.id),
            metadata={
                'seat_ids': seat_ids,
                'theater_id': str(theater.id),
                'movie_id': str(theater.movie.id),
                'price': str(seat_price),
                'food_data': str(food_data) if food_data else '',
            }
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return render(request, 'movies/checkout_confirmation.html', {
            'theater': theater,
            'seats': locked_seats,
            'total_price': len(locked_seats) * seat_price,
            'remaining_seconds': 60,
            'food_items': FoodItem.objects.filter(is_available=True),
            'error': f"Stripe integration error: {str(e)}"
        })


@login_required(login_url='/login/')
def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('profile')
        
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        metadata = getattr(session, 'metadata', {})
        
        # StripeObject might not have a .get method
        meta_type = metadata.get('type') if hasattr(metadata, 'get') else getattr(metadata, 'type', None)
        
        if meta_type == 'event':
            finalize_event_booking(session)
            
            event_id = metadata.get('event_id') if hasattr(metadata, 'get') else getattr(metadata, 'event_id', None)
            user_id = getattr(session, 'client_reference_id', request.user.id)
            
            booking_obj = EventBooking.objects.filter(
                user_id=user_id, 
                event_id=event_id
            ).last()
            
            if booking_obj:
                return render(request, 'events/event_success.html', {'booking': booking_obj})
            else:
                return redirect('events_list')
        else:
            # Movie Finalization
            result = finalize_booking(session)
            if not result or result.get('status') == 'error':
                return render(request, 'movies/payment_success.html', {'refunded': True, 'message': 'An unexpected error occurred while finalizing your booking.'})
            if result and result.get('status') == 'refunded':
                return render(request, 'movies/payment_success.html', {'refunded': True, 'message': result.get('message')})
            return render(request, 'movies/payment_success.html')

    except Exception as e:
        print(f"ERROR in payment_success: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return render(request, 'movies/payment_success.html')


@login_required(login_url='/login/')
def payment_cancel(request):
    theater_id = request.GET.get('theater_id')
    if theater_id:
        # Release the user's locks immediately
        Seat.objects.filter(theater_id=theater_id, locked_by=request.user).update(locked_by=None, locked_at=None)
        return redirect('book_seats', theater_id=theater_id)
    return redirect('/')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
        
    # Process secure completed checkout session
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = getattr(session, 'metadata', {})
        if metadata.get('type') == 'event':
            finalize_event_booking(session)
        else:
            finalize_booking(session)
        
    return HttpResponse(status=200)


def generate_qr_code(booking):
    """Generate a QR code for a booking and save it to the booking's qr_code field."""
    qr_data = (
        f"BookMySeat E-Ticket\n"
        f"Booking ID: #{booking.id}\n"
        f"Movie: {booking.movie.name}\n"
        f"Theater: {booking.theater.name}\n"
        f"Seat: {booking.seat.seat_number}\n"
        f"Time: {booking.theater.time.strftime('%d %b, %Y - %H:%M')}\n"
        f"Payment: {booking.payment_intent_id or 'N/A'}"
    )
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#050816", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    filename = f"qr_booking_{booking.id}.png"
    booking.qr_code.save(filename, ContentFile(buffer.read()), save=True)


def finalize_booking(session):
    # Idempotency check: check if booking already exists for this payment intent ID
    payment_intent_id = getattr(session, 'payment_intent', None)
    if payment_intent_id and Booking.objects.filter(payment_intent_id=payment_intent_id).exists():
        return {'status': 'already_processed'}
        
    user_id = getattr(session, 'client_reference_id', None)
    metadata = getattr(session, 'metadata', None)
    if not metadata:
        return {'status': 'error'}
        
    seat_ids_str = metadata.get('seat_ids', '') if hasattr(metadata, 'get') else getattr(metadata, 'seat_ids', '')
    theater_id = metadata.get('theater_id', None) if hasattr(metadata, 'get') else getattr(metadata, 'theater_id', None)
    movie_id = metadata.get('movie_id', None) if hasattr(metadata, 'get') else getattr(metadata, 'movie_id', None)
    price_val = float(metadata.get('price', 15.00) if hasattr(metadata, 'get') else getattr(metadata, 'price', 15.00))
    
    if not (user_id and seat_ids_str and theater_id and movie_id):
        return {'status': 'error'}
        
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        theater = Theater.objects.get(id=theater_id)
        movie = Movie.objects.get(id=movie_id)
        seat_ids = [int(sid) for sid in seat_ids_str.split(',') if sid.strip()]
        
        with transaction.atomic():
            seats = Seat.objects.select_for_update().filter(id__in=seat_ids)
            
            # Check for concurrency conflict (seat booked by another user's payment)
            already_booked = False
            for seat in seats:
                if Booking.objects.filter(seat=seat).exists():
                    already_booked = True
                    break
                    
            if already_booked:
                if payment_intent_id:
                    stripe.Refund.create(payment_intent=payment_intent_id)
                return {'status': 'refunded', 'message': 'The seat was booked by someone else while your payment was processing. We have refunded your payment.'}
                
            for seat in seats:
                # Mark as permanently booked and clear lock attributes
                seat.is_booked = True
                seat.locked_by = None
                seat.locked_at = None
                seat.save()
                
                booking = Booking.objects.create(
                    user=user,
                    seat=seat,
                    movie=movie,
                    theater=theater,
                    price=price_val,
                    payment_intent_id=payment_intent_id
                )
                
                # Add F&B Items if any
                food_data_str = metadata.get('food_data', '') if hasattr(metadata, 'get') else getattr(metadata, 'food_data', '')
                if food_data_str:
                    try:
                        import ast
                        food_data_dict = ast.literal_eval(food_data_str)
                        for food_id, qty in food_data_dict.items():
                            try:
                                fi = FoodItem.objects.get(id=int(food_id))
                                BookingFoodItem.objects.create(booking=booking, food_item=fi, quantity=qty)
                            except FoodItem.DoesNotExist:
                                pass
                    except Exception as fe:
                        print(f"[F&B Error] Failed to parse food data: {fe}")

                # Generate QR Code (Feature 1)
                try:
                    generate_qr_code(booking)
                except Exception as qr_err:
                    print(f"[QR Error] Failed to generate QR: {qr_err}")
                
                # Trigger background email task (Task 6)
                enqueue_ticket_email(booking.id)
            
            # TRIGGER CHANNELS DASHBOARD UPDATE (Task 4)
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'admin_dashboard',
                    {
                        'type': 'dashboard_update'
                    }
                )
            except Exception as e:
                print(f"WebSocket update failed: {e}")
                
        return {'status': 'success'}

    except Exception as e:
        print(f"[Webhook Error] Booking finalization failed: {str(e)}")


def enqueue_ticket_email(booking_id):
    # Send email synchronously to avoid background thread flakiness
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from .models import Booking
        
        booking = Booking.objects.get(id=booking_id)
        recipient = booking.user.email
        if not recipient:
            return
            
        html_content = render_to_string('emails/ticket_confirmation.html', {'booking': booking})
        text_content = strip_tags(html_content)
        subject = f"Your E-Ticket Confirmation - {booking.movie.name}"
        from_email = "tickets@bookmyseat.com"
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [recipient])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"Successfully sent confirmation email to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")

from .models import Event, EventBooking

def events_list(request):
    events = Event.objects.all().order_by('date')
    
    # Filter by selected city in session
    selected_city_id = request.session.get('selected_city_id')
    if selected_city_id:
        events = events.filter(city_id=selected_city_id)
        
    category = request.GET.get('category')
    if category:
        events = events.filter(category=category)
    return render(request, 'events/events_list.html', {'events': events, 'category': category})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'events/event_detail.html', {'event': event})

@login_required(login_url='login')
def book_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            line_items = [{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Ticket for {event.name}',
                        'description': f'{event.get_category_display()} - {event.location}',
                    },
                    'unit_amount': int(event.ticket_price * 100),
                },
                'quantity': quantity,
            }]
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('events_list')),
                client_reference_id=str(request.user.id),
                metadata={
                    'type': 'event',
                    'event_id': str(event.id),
                    'quantity': str(quantity),
                    'price': str(event.ticket_price),
                }
            )
            return redirect(session.url, code=303)
        except Exception as e:
            # Fallback in case of error
            print(f"Stripe Event Error: {e}")
            return redirect('events_list')
    
    return redirect('event_detail', event_id=event.id)

def finalize_event_booking(session):
    payment_intent_id = getattr(session, 'payment_intent', None)
    
    # We don't have a payment_intent_id column in EventBooking currently, so we can't easily check idempotency via DB.
    # However, since events don't have strict seating constraints, double booking isn't as fatal as movies.
    # Still, let's use the session id as a lightweight check if we can, or just trust the webhook idempotency.
    # Actually, let's just create the booking.
    
    user_id = getattr(session, 'client_reference_id', None)
    metadata = getattr(session, 'metadata', None)
    if not metadata:
        return {'status': 'error'}
        
    event_id = metadata.get('event_id') if hasattr(metadata, 'get') else getattr(metadata, 'event_id', None)
    quantity_str = metadata.get('quantity') if hasattr(metadata, 'get') else getattr(metadata, 'quantity', '1')
    
    if not (user_id and event_id):
        return {'status': 'error'}
        
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        event = Event.objects.get(id=event_id)
        quantity = int(quantity_str)
        
        # Check if booking exists (very naive check based on time to prevent double-firing in 5 seconds)
        recent_booking = EventBooking.objects.filter(
            user=user, 
            event=event, 
            quantity=quantity
        ).order_by('-booked_at').first()
        
        from django.utils import timezone
        import datetime
        
        if recent_booking and (timezone.now() - recent_booking.booked_at) < datetime.timedelta(seconds=10):
            return {'status': 'already_processed'}
            
        total_price = event.ticket_price * quantity
        
        booking = EventBooking.objects.create(
            user=user,
            event=event,
            quantity=quantity,
            total_price=total_price,
            status='active'
        )
        return booking
        
    except Exception as e:
        print(f'Error finalizing event booking: {e}')
        return {'status': 'error'}
