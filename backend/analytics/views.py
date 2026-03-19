from django.db.models import Count, Q, Avg, F, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from tickets.views import SupervisorRequiredMixin
from tickets.models import Ticket
from django.utils import timezone
from datetime import timedelta
from .models import TicketMetrics
from django.template.loader import render_to_string
from django.http import HttpResponse


class SLADashboardView(LoginRequiredMixin, SupervisorRequiredMixin, TemplateView):
    template_name = 'analytics/sla_dashboard_htmx.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any necessary context (like date range)
        return context

def sla_chart_data(request):
    """Return JSON data for SLA charts (last 30 days)."""
    days = 30
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)

    # Daily aggregates
    daily_stats = (
        Ticket.objects
        .filter(created_at__date__gte=start_date)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(
            opened=Count('id'),
            resolved=Count('id', filter=Q(resolved_at__isnull=False)),
            response_breach=Count('id', filter=Q(is_response_breached=True)),
            resolution_breach=Count('id', filter=Q(is_resolution_breached=True)),
            escalated=Count('id', filter=Q(is_escalated=True)),
        )
        .order_by('date')
    )

    # Fill missing dates
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    data_dict = {item['date']: item for item in daily_stats}
    result = []
    for date in date_range:
        stats = data_dict.get(date, {})
        result.append({
            'date': date.strftime('%Y-%m-%d'),
            'opened': stats.get('opened', 0),
            'resolved': stats.get('resolved', 0),
            'response_breach': stats.get('response_breach', 0),
            'resolution_breach': stats.get('resolution_breach', 0),
            'escalated': stats.get('escalated', 0),
        })

    return JsonResponse(result, safe=False)

def sla_performance_metrics(request):
    """Return current overall metrics (last 7 days)."""
    since = timezone.now() - timedelta(days=7)
    tickets = Ticket.objects.filter(created_at__gte=since)

    total = tickets.count()
    resolved = tickets.filter(resolved_at__isnull=False).count()
    avg_response = tickets.filter(first_response_at__isnull=False).aggregate(
        avg=Avg(F('first_response_at') - F('created_at'))
    )['avg']
    avg_resolution = tickets.filter(resolved_at__isnull=False).aggregate(
        avg=Avg(F('resolved_at') - F('created_at'))
    )['avg']

    # Convert timedelta to hours
    if avg_response:
        avg_response = avg_response.total_seconds() / 3600
    if avg_resolution:
        avg_resolution = avg_resolution.total_seconds() / 3600

    return JsonResponse({
        'total_tickets': total,
        'resolved_tickets': resolved,
        'open_tickets': tickets.filter(resolved_at__isnull=True).count(),
        'avg_response_hours': round(avg_response, 2) if avg_response else None,
        'avg_resolution_hours': round(avg_resolution, 2) if avg_resolution else None,
        'response_breaches': tickets.filter(is_response_breached=True).count(),
        'resolution_breaches': tickets.filter(is_resolution_breached=True).count(),
        'escalations': tickets.filter(is_escalated=True).count(),
    })
    
def kpi_cards_partial(request):
    since = timezone.now() - timedelta(days=7)
    metrics_qs = TicketMetrics.objects.filter(ticket__created_at__gte=since)

    total = metrics_qs.count()
    resolved = metrics_qs.filter(ticket__resolved_at__isnull=False).count()
    open_tickets = total - resolved

    avg_response = metrics_qs.exclude(first_response_time__isnull=True).aggregate(
        avg=Avg('first_response_time')
    )['avg']
    if avg_response:
        avg_response = round(avg_response / 3600, 2)

    # Fix: Count True values instead of Sum
    response_breaches = metrics_qs.filter(sla_breached_response=True).count()

    context = {
        'total': total,
        'open_tickets': open_tickets,
        'avg_response': avg_response,
        'response_breaches': response_breaches,
    }
    html = render_to_string('analytics/partials/kpi_cards.html', context, request=request)
    return HttpResponse(html)

def trend_chart_partial(request):
    """Return HTML for trend chart (includes canvas and init script)."""
    days = 30
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)

    daily_stats = (
        TicketMetrics.objects
        .filter(ticket_created_at__date__gte=start_date)
        .annotate(date=TruncDate('ticket_created_at'))
        .values('date')
        .annotate(opened=Count('id'), resolved=Count('id', filter=Q(ticket__resolved_at__isnull=False)))
        .order_by('date')
    )

    # Fill missing dates
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    data_dict = {item['date']: item for item in daily_stats}
    labels = []
    opened_data = []
    resolved_data = []
    for date in date_range:
        labels.append(date.strftime('%Y-%m-%d'))
        stats = data_dict.get(date, {})
        opened_data.append(stats.get('opened', 0))
        resolved_data.append(stats.get('resolved', 0))

    context = {
        'labels': labels,
        'opened_data': opened_data,
        'resolved_data': resolved_data,
    }
    html = render_to_string('analytics/partials/trend_chart.html', context, request=request)
    return HttpResponse(html)


def breach_chart_partial(request):
    """Return HTML for breach chart (daily SLA breaches)."""
    days = 30
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)

    # Aggregate breach counts by date
    daily_stats = (
        TicketMetrics.objects
        .filter(ticket__created_at__date__gte=start_date)
        .annotate(date=TruncDate('ticket__created_at'))
        .values('date')
        .annotate(
            response_breach=Count('id', filter=Q(sla_breached_response=True)),
            resolution_breach=Count('id', filter=Q(sla_breached_resolution=True))
        )
        .order_by('date')
    )

    # Fill missing dates
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    data_dict = {item['date']: item for item in daily_stats}
    labels = []
    response_data = []
    resolution_data = []
    for date in date_range:
        labels.append(date.strftime('%Y-%m-%d'))
        stats = data_dict.get(date, {})
        response_data.append(stats.get('response_breach', 0))
        resolution_data.append(stats.get('resolution_breach', 0))

    context = {
        'labels': labels,
        'response_data': response_data,
        'resolution_data': resolution_data,
    }
    html = render_to_string('analytics/partials/breach_chart.html', context, request=request)
    return HttpResponse(html)
