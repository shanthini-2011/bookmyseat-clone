import queue
import threading
import time
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Global thread-safe queue to pass booking IDs from web threads to background sender
email_queue = queue.Queue()

def process_email_queue():
    # Wait for the DB to be ready before fetching
    time.sleep(5)
    from movies.models import Booking, EmailLog
    while True:
        booking_id = email_queue.get()
        try:
            booking = Booking.objects.get(id=booking_id)
            recipient = booking.user.email
            if not recipient:
                email_queue.task_done()
                continue
                
            # Log the entry as pending
            log, created = EmailLog.objects.get_or_create(
                booking=booking,
                defaults={'recipient': recipient, 'status': 'pending'}
            )
            
            success = False
            max_attempts = 3
            
            for attempt in range(1, max_attempts + 1):
                log.attempts = attempt
                log.save()
                
                try:
                    # Render the email content (Django template engine context validation)
                    html_content = render_to_string('emails/ticket_confirmation.html', {'booking': booking})
                    text_content = strip_tags(html_content)
                    
                    subject = f"Your E-Ticket Confirmation - {booking.movie.name}"
                    from_email = "tickets@bookmyseat.com"
                    
                    # Construct multi-part message (Task 6 transactional secure email)
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [recipient])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    
                    success = True
                    log.status = 'sent'
                    log.error_message = None
                    log.save()
                    break
                except Exception as ex:
                    log.error_message = str(ex)
                    log.save()
                    if attempt < max_attempts:
                        # Exponential backoff sleep (Task 6 retry logic)
                        time.sleep(2 ** attempt)
            
            if not success:
                log.status = 'failed'
                log.save()
                
        except Exception as e:
            print(f"[Email Worker Error] Task execution failed: {str(e)}")
            
        email_queue.task_done()

# Start the background email worker thread
worker_thread = threading.Thread(target=process_email_queue, daemon=True)
worker_thread.start()
