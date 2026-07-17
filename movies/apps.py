import os
import threading
import time
import sys
from django.apps import AppConfig

def cleanup_expired_locks():
    # Wait for the database and server bootup to complete
    time.sleep(5)
    while True:
        try:
            from django.utils import timezone
            from datetime import timedelta
            from movies.models import Seat
            
            expiry_limit = timezone.now() - timedelta(minutes=2)
            # Find and clear seats that are expired and not permanently booked
            expired_seats = Seat.objects.filter(locked_at__lt=expiry_limit, is_booked=False)
            if expired_seats.exists():
                expired_count = expired_seats.count()
                expired_seats.update(locked_by=None, locked_at=None)
                print(f"[Lock Manager] Released {expired_count} expired seat reservation locks.")
        except Exception as e:
            # Silence exceptions during DB setups or migrations
            pass
        time.sleep(5)

class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'

    def ready(self):
        # Start background lock manager if running the server
        if 'runserver' in sys.argv or os.environ.get('RUN_MAIN') == 'true' or 'gunicorn' in sys.argv:
            threading.Thread(target=cleanup_expired_locks, daemon=True).start()
            # Import email worker to start the async daemon email queue loop (Task 6 non-blocking background queue)
            import movies.email_worker


