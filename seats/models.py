from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Library Section/Room'
        verbose_name_plural = 'Library Sections/Rooms'

    def __str__(self):
        return self.name

class Seat(models.Model):
    name = models.CharField(max_length=50, unique=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='seats')
    status = models.CharField(
        max_length=20,
        default='available',
        choices=[
            ('available', 'Available'),
            ('reserved', 'Reserved'), # Confirmed Reserved
            ('pending_confirmation', 'Pending Confirmation'),
        ]
    )
    booked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reserved_until = models.DateTimeField(null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['location__name', 'name']
        verbose_name = 'Seat'
        verbose_name_plural = 'Seats'

    def __str__(self):
        return f"{self.name} ({self.location.name})"

    def is_available(self):
        # Auto-release if expired
        if self.status in ['reserved', 'pending_confirmation'] and \
           self.reserved_until and timezone.now() >= self.reserved_until:
            self.status = 'available'
            self.booked_by = None
            self.reserved_until = None
            self.is_confirmed = False
            self.save()
            return True
        return self.status == 'available'

    def reserve(self, user):
        """
        Reserve this seat for a user, only if:
        - The seat is available (or expired)
        - The user does NOT already have an active reservation (pending or confirmed)
        """
        with transaction.atomic():
            # Double-check: user cannot have more than one active seat
            if Seat.objects.filter(
                booked_by=user,
                status__in=['reserved', 'pending_confirmation'],
                reserved_until__gt=timezone.now()
            ).exists():
                return False
            # Check if this seat is available (will also auto-release expired)
            if self.is_available():
                self.status = 'pending_confirmation'
                self.booked_by = user
                self.reserved_until = timezone.now() + timedelta(minutes=10)
                self.is_confirmed = False
                self.save()
                return True
        return False

    def release(self):
        if self.status in ['reserved', 'pending_confirmation']:
            self.status = 'available'
            self.booked_by = None
            self.reserved_until = None
            self.is_confirmed = False
            self.save()
            return True
        return False

    def confirm_booking(self):
        """
        Confirm a pending booking (admin action).
        """
        if self.status == 'pending_confirmation':
            self.status = 'reserved'
            self.is_confirmed = True
            self.reserved_until = timezone.now() + timedelta(hours=4) # Example: 4 hours from confirmation
            self.save()
            return True
        return False

    def is_reserved_by_current_user(self, user):
        return self.booked_by == user and \
               self.status in ['reserved', 'pending_confirmation'] and \
               self.reserved_until and \
               timezone.now() < self.reserved_until
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('book', 'Seat Booked'),
        ('release', 'Seat Released'),
        ('confirm', 'Seat Confirmed'),
        ('checkin', 'Checked In'),
        ('checkout', 'Checked Out'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} seat {self.seat.name}"
