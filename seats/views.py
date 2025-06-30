from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import timedelta
import json

from .models import Seat, Location

User = get_user_model()

def is_admin(user):
    return user.is_staff

# --- USER VIEWS ---

@login_required
def seat_dashboard(request):
    all_seats = Seat.objects.all()
    for seat in all_seats:
        seat.is_available()  # Update status based on reserved_until

    seats = Seat.objects.all()
    query = request.GET.get('q')
    if query:
        seats = seats.filter(
            Q(name__icontains=query) |
            Q(location__name__icontains=query)
        ).distinct()

    status_filter = request.GET.get('status')
    if status_filter:
        seats = seats.filter(status=status_filter)

    location_filter = request.GET.get('location')
    if location_filter:
        seats = seats.filter(location__name__icontains=location_filter)

    seats = seats.order_by('location__name', 'name')

    context = {
        'seats': seats,
        'query': query,
        'current_status_filter': status_filter,
        'current_location_filter': location_filter,
        'locations': Location.objects.all().order_by('name'),
    }
    return render(request, 'seats/seat_list.html', context)

@login_required
def book_seat(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)
    if request.method == 'POST':
        user_active_seat = Seat.objects.filter(
            booked_by=request.user,
            status__in=['reserved', 'pending_confirmation'],
            reserved_until__gt=timezone.now()
        ).first()

        if user_active_seat:
            messages.warning(request, f"You already have Seat {user_active_seat.name} reserved or pending confirmation. Please manage that reservation first.")
            return redirect('seats:seat_dashboard')

        if seat.is_available():
            if seat.reserve(request.user):
                my_reservations_url = reverse('seats:my_reservations')
                messages.success(request, f'Seat {seat.name} is now pending confirmation for 10 minutes! Please report to the admin. <a href="{my_reservations_url}" class="alert-link">Check your reservations here.</a>')
            else:
                messages.error(request, f"You already have a seat reserved or pending confirmation, or seat {seat.name} is no longer available.")
        else:
            messages.error(request, f'Seat {seat.name} is currently reserved or pending confirmation by someone else.')
    return redirect('seats:seat_dashboard')

@login_required
def release_seat(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)
    if request.method == 'POST':
        if seat.is_reserved_by_current_user(request.user):
            seat.release()
            messages.info(request, f"Seat {seat.name} has been released.")
        else:
            messages.error(request, f"You cannot release Seat {seat.name}.")
    return redirect('seats:seat_dashboard')

@login_required
def my_reservations(request):
    user_reserved_seats = Seat.objects.filter(
        booked_by=request.user,
        status__in=['reserved', 'pending_confirmation'],
        reserved_until__gt=timezone.now()
    ).order_by('name')

    for seat in user_reserved_seats:
        seat.is_available()

    user_reserved_seats = Seat.objects.filter(
        booked_by=request.user,
        status__in=['reserved', 'pending_confirmation'],
        reserved_until__gt=timezone.now()
    ).order_by('name')

    return render(request, 'seats/my_reservations.html', {'user_reserved_seats': user_reserved_seats})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def confirm_booking(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('barcode') or data.get('manual_code')
        if not code:
            return JsonResponse({'message': 'No code provided.'}, status=400)

        seat = (
            Seat.objects
            .filter(
                Q(booked_by__username__iexact=code) | Q(name__iexact=code),
                status='pending_confirmation',
                reserved_until__gt=timezone.now()
            )
            .select_related('booked_by')
            .first()
        )

        if seat:
            seat.status = 'reserved'
            seat.is_confirmed = True
            seat.reserved_until = timezone.now() + timedelta(hours=4)
            seat.save()
            return JsonResponse({'message': f'Booking confirmed for {seat.booked_by.username if seat.booked_by else ""} (Seat {seat.name})!'})
        else:
            return JsonResponse({'message': 'No pending booking found for this code.'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)
# --- ADMIN CHECK-IN VIEWS ---

@login_required
@user_passes_test(is_admin)
def admin_checkin_dashboard(request):
    # For manual entry via GET
    query = request.GET.get('q', '').strip()
    recent_scans = []
    confirmed = False

    if query:
        seat = (
            Seat.objects
            .filter(
                status='pending_confirmation',
                booked_by__username__iexact=query,
                reserved_until__gt=timezone.now()
            )
            .select_related('booked_by', 'location')
            .order_by('-reserved_until')
            .first()
        )
        if seat:
            seat.status = 'reserved'
            seat.is_confirmed = True
            seat.reserved_until = timezone.now() + timedelta(hours=4)
            seat.save()
            messages.success(request, f"Seat {seat.name} for user {seat.booked_by.get_full_name() or seat.booked_by.username} confirmed!")
            confirmed = True
        else:
            messages.error(request, f"No pending seat found for user ID '{query}'.")
        return redirect('seats:admin_checkin_dashboard')

    # Stats for charts
    total_seats = Seat.objects.count()
    available_seats = Seat.objects.filter(status='available').count()
    reserved_seats = Seat.objects.filter(status='reserved').count()
    pending_seats = Seat.objects.filter(status='pending_confirmation').count()

    seat_status_counts = (
        Seat.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    seats = (
        Seat.objects
        .filter(
            status='pending_confirmation',
            reserved_until__gt=timezone.now()
        )
        .select_related('booked_by', 'location')
        .order_by('-reserved_until')[:10]
    )

    for seat in seats:
        recent_scans.append({
            "user_id": seat.booked_by.username if seat.booked_by else "",
            "name": seat.booked_by.get_full_name() if seat.booked_by else "",
            "seat": seat.name,
            "status": seat.status,
        })

    context = {
        'recent_scans': recent_scans,
        'total_seats': total_seats,
        'available_seats': available_seats,
        'reserved_seats': reserved_seats,
        'pending_seats': pending_seats,
        'seat_status_counts': list(seat_status_counts),
    }
    return render(request, 'seats/admin_checkin_dashboard.html', context)

# --- ADMIN ANALYTICS DASHBOARD ---

@login_required
@user_passes_test(is_admin)
def seat_analytics_dashboard(request):
    total_seats = Seat.objects.count()
    available_seats = Seat.objects.filter(status='available').count()
    reserved_seats = Seat.objects.filter(status='reserved').count()
    pending_seats = Seat.objects.filter(status='pending_confirmation').count()
    
    status_distribution = list(
        Seat.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    location_distribution = list(
        Location.objects.annotate(seat_count=Count('seats'))
        .values('name', 'seat_count')
    )
    today = timezone.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    reservations_per_day = []
    for date in dates:
        count = Seat.objects.filter(
            reserved_until__date=date,
            status__in=['reserved', 'pending_confirmation']
        ).count()
        reservations_per_day.append(count)
    # Dummy recent activities (replace with ActivityLog if available)
    recent_activities = [
        {'user': '22A91A6164', 'action': 'Booked', 'timestamp': timezone.now(), 'seat': 'CL-001'},
        {'user': '22A91A6123', 'action': 'Released', 'timestamp': timezone.now(), 'seat': 'CL-002'},
        {'user': '22A91A6142', 'action': 'Confirmed', 'timestamp': timezone.now(), 'seat': 'CL-003'},
    ]
    context = {
        'total_seats': total_seats,
        'available_seats': available_seats,
        'reserved_seats': reserved_seats,
        'pending_seats': pending_seats,
        'status_distribution': status_distribution,
        'location_distribution': location_distribution,
        'dates': [d.strftime('%b %d') for d in dates],
        'reservations_per_day': reservations_per_day,
        'recent_activities': recent_activities,
    }
    return render(request, 'seats/admin_dashboard.html', context)

# --- BARCODE CONFIRMATION ENDPOINT (AJAX) ---

@csrf_exempt
def confirm_entry(request):
    if request.method == "POST":
        data = json.loads(request.body)
        barcode = data.get('barcode')
        # Try to find a pending seat for this barcode (user ID or seat name)
        seat = (
            Seat.objects
            .filter(
                Q(booked_by__username__iexact=barcode) | Q(name__iexact=barcode),
                status='pending_confirmation',
                reserved_until__gt=timezone.now()
            )
            .select_related('booked_by', 'location')
            .order_by('-reserved_until')
            .first()
        )
        if seat:
            seat.status = 'reserved'
            seat.is_confirmed = True
            seat.reserved_until = timezone.now() + timedelta(hours=4)
            seat.save()
            return JsonResponse({'message': f"Entry confirmed for {seat.booked_by.username if seat.booked_by else ''} (Seat {seat.name})!"})
        else:
            return JsonResponse({'message': 'No pending seat found for this barcode.'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
