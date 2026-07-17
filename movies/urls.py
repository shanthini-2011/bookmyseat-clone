from django.urls import path
from . import views

urlpatterns=[
    path('',views.movie_list,name='movie_list'),
    path('<int:movie_id>/theaters',views.theater_list,name='theater_list'),
    path('<int:movie_id>/review/',views.submit_review,name='submit_review'),
    path('theater/<int:theater_id>/seats/book/',views.book_seats,name='book_seats'),
    path('checkout/<int:theater_id>/',views.checkout_confirmation,name='checkout_confirmation'),
    path('checkout/<int:theater_id>/session/',views.create_checkout_session,name='create_checkout_session'),
    path('checkout/success/',views.payment_success,name='payment_success'),
    path('checkout/cancel/',views.payment_cancel,name='payment_cancel'),
    path('set-city/', views.set_city, name='set_city'),
    path('checkout/webhook/',views.stripe_webhook,name='stripe_webhook'),
    
    # Event routes
    path('events/', views.events_list, name='events_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/book/', views.book_event, name='book_event'),
]