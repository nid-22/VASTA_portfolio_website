import logging
import re
import time

from django.db import DatabaseError, transaction
from django.db.models import F
from django.utils import timezone

from .models import DailyAnalyticsMetric


BOT_PATTERN = re.compile(
    r'bot|spider|crawler|slurp|bingpreview|headless|python-requests|curl|wget|uptime|monitor',
    re.IGNORECASE,
)


def is_probable_bot(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return not user_agent or bool(BOT_PATTERN.search(user_agent))


def record_metric(metric, label):
    label = str(label).strip()[:160]
    if not label:
        return False
    try:
        with transaction.atomic():
            item, created = DailyAnalyticsMetric.objects.select_for_update().get_or_create(
                date=timezone.localdate(), metric=metric, label=label,
                defaults={'count': 1},
            )
            if not created:
                DailyAnalyticsMetric.objects.filter(pk=item.pk).update(count=F('count') + 1)
        return True
    except DatabaseError:
        # Analytics must never prevent a page, enquiry or application from working.
        logging.exception('Unable to record internal analytics metric')
        return False


def record_once_per_session(request, metric, label):
    if is_probable_bot(request):
        return False
    key = f'{timezone.localdate().isoformat()}:{metric}:{label}'
    seen = request.session.get('analytics_seen', [])
    if key in seen:
        return False
    if not record_metric(metric, label):
        return False
    request.session['analytics_seen'] = [*seen[-99:], key]
    return True


def navigation_is_rate_limited(request, label):
    now = time.time()
    key = f'analytics_navigation_{label}'
    previous = request.session.get(key, 0)
    request.session[key] = now
    return now - previous < 2
