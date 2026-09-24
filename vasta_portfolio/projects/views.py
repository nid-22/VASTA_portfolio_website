import hmac
import logging
import os
import random
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import BadHeaderError, EmailMessage
from django.core.validators import URLValidator, validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .analytics import is_probable_bot, navigation_is_rate_limited, record_metric, record_once_per_session
from .models import CareerSubmission, ContactSubmission, DailyAnalyticsMetric, Project


MAX_CAREER_FILE_SIZE = 10 * 1024 * 1024
MIN_FORM_COMPLETION_SECONDS = 3
FORM_TOKEN_MAX_AGE_SECONDS = 2 * 60 * 60
FORM_TOKEN_SALT = 'vasta-public-form-timing-v1'
RATE_LIMIT_WINDOW_SECONDS = 60 * 60
RATE_LIMITS = {'contact': 5, 'careers': 3}


def _monitor_cursor(request, name):
    try:
        return max(0, int(request.GET.get(name, 0)))
    except (TypeError, ValueError):
        return 0


@require_GET
def submission_monitor(request):
    """Return only submission counts and cursors for the private notifier."""
    expected_token = os.environ.get('SUBMISSION_MONITOR_TOKEN', '')
    authorization = request.headers.get('Authorization', '')
    supplied_token = authorization.removeprefix('Bearer ').strip()
    if not expected_token or not supplied_token or not hmac.compare_digest(expected_token, supplied_token):
        return JsonResponse({'detail': 'Not found.'}, status=404)

    after_contact = _monitor_cursor(request, 'after_contact')
    after_career = _monitor_cursor(request, 'after_career')
    contact_queryset = ContactSubmission.objects.order_by('pk')
    career_queryset = CareerSubmission.objects.order_by('pk')
    latest_contact = contact_queryset.values_list('pk', flat=True).last() or 0
    latest_career = career_queryset.values_list('pk', flat=True).last() or 0

    return JsonResponse({
        'contact': {
            'new_count': contact_queryset.filter(pk__gt=after_contact).count(),
            'latest_id': latest_contact,
        },
        'career': {
            'new_count': career_queryset.filter(pk__gt=after_career).count(),
            'latest_id': latest_career,
        },
        'checked_at': timezone.now().isoformat(),
    })


def form_email_enabled():
    value = getattr(settings, 'FORM_EMAIL_ENABLED', os.environ.get('FORM_EMAIL_ENABLED', 'False'))
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes')


def update_email_status(submission, status, error=''):
    submission.email_status = status
    submission.email_error = error[:2000]
    submission.email_sent_at = timezone.now() if status == submission.EmailStatus.SENT else None
    submission.save(update_fields=('email_status', 'email_error', 'email_sent_at', 'updated_at'))


def form_timing_token():
    return signing.dumps({'issued_at': time.time()}, salt=FORM_TOKEN_SALT, compress=True)


def form_timing_is_valid(token):
    try:
        payload = signing.loads(token, salt=FORM_TOKEN_SALT, max_age=FORM_TOKEN_MAX_AGE_SECONDS)
        return time.time() - float(payload['issued_at']) >= MIN_FORM_COMPLETION_SECONDS
    except (signing.BadSignature, signing.SignatureExpired, KeyError, TypeError, ValueError):
        return False


def client_fingerprint(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip_address = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    raw_value = f"{ip_address}|{request.META.get('HTTP_USER_AGENT', '')}"
    return salted_hmac('vasta-form-rate-limit', raw_value).hexdigest()


def rate_limit_exceeded(request, form_name):
    key = f'public-form:{form_name}:{client_fingerprint(request)}'
    if cache.add(key, 1, RATE_LIMIT_WINDOW_SECONDS):
        return False
    try:
        attempts = cache.incr(key)
    except ValueError:
        cache.set(key, 1, RATE_LIMIT_WINDOW_SECONDS)
        attempts = 1
    return attempts > RATE_LIMITS[form_name]


class ProtectedFormView(TemplateView):
    form_name = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_token'] = form_timing_token()
        return context

    def bot_submission(self, request):
        return bool(request.POST.get('website', '').strip())

    def timing_error(self, request):
        return not form_timing_is_valid(request.POST.get('form_token', ''))


class ProjectListView(ListView):
    model = Project
    template_name = 'projects/index.html'

    def get_queryset(self):
        return (
            Project.objects.filter(is_active=True, is_deleted=False)
            .select_related('category')
            .prefetch_related('disciplines')
            .order_by('order_to_display_id')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_objects = list(context['object_list'])
        context['projects'] = [
            {
                'id': project.id,
                'project_name': project.heading,
                'cover_image': project.cover_image or None,
                'type': project.category_label,
                'filter_classes': project.discipline_filter_classes,
                'get_absolute_url': project.get_absolute_url,
            }
            for project in project_objects
        ]

        top_projects = project_objects[:3]
        pool = project_objects[3:]
        sample_size = min(3, len(pool))
        random_projects = random.sample(pool, sample_size) if sample_size else []
        previous_ids = self.request.session.get('homepage_random_project_ids', [])
        if len(pool) > sample_size and sample_size and [p.pk for p in random_projects] == previous_ids:
            for _ in range(5):
                candidate = random.sample(pool, sample_size)
                if [p.pk for p in candidate] != previous_ids:
                    random_projects = candidate
                    break
        self.request.session['homepage_random_project_ids'] = [p.pk for p in random_projects]

        if top_projects:
            first_project = random.choice(top_projects)
            remaining_projects = [project for project in top_projects if project.pk != first_project.pk]
            remaining_projects.extend(random_projects)
            random.shuffle(remaining_projects)
            context['carousel_projects'] = [first_project, *remaining_projects]
        else:
            context['carousel_projects'] = []
        return context


class LegacyProjectListView(ProjectListView):
    template_name = 'projects/index_legacy.html'


class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/work-single.html'

    def get_queryset(self):
        return super().get_queryset().select_related('category').prefetch_related('disciplines', 'project_images')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        record_once_per_session(request, DailyAnalyticsMetric.PROJECT_VIEW, self.object.heading)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_images'] = self.object.project_images.all()
        return context


class AboutView(TemplateView):
    template_name = 'about.html'


class ContactView(ProtectedFormView):
    template_name = 'contact.html'
    form_name = 'contact'
    project_type_choices = dict(ContactSubmission.PROJECT_TYPE_CHOICES)

    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if self.bot_submission(request):
            context = self.get_context_data(**kwargs)
            context['sent'] = True
            return render(request, self.template_name, context)
        if self.timing_error(request):
            return self.render_form_error(request, kwargs, 'Please wait a moment and try again.', is_ajax, 400)
        if rate_limit_exceeded(request, self.form_name):
            return self.render_form_error(request, kwargs, 'Too many enquiries were submitted from this connection. Please try again later.', is_ajax, 429)

        fields = {name: request.POST.get(name, '').strip() for name in (
            'name', 'phone', 'email', 'project_type', 'project_location', 'call_time', 'message'
        )}
        field_errors = {}
        limits = {'name': 100, 'phone': 30, 'email': 254, 'project_location': 150, 'call_time': 100, 'message': 3000}
        for field, maximum in limits.items():
            if len(fields[field]) > maximum:
                field_errors[field] = f'Please keep this field under {maximum} characters.'
        if not fields['name']:
            field_errors['name'] = 'Please enter your name.'
        if not fields['phone']:
            field_errors['phone'] = 'Please enter a phone number so we can call you.'
        elif len(''.join(character for character in fields['phone'] if character.isdigit())) < 7:
            field_errors['phone'] = 'Please enter a valid phone number.'
        if fields['email']:
            try:
                validate_email(fields['email'])
            except ValidationError:
                field_errors['email'] = 'Please enter a valid email address.'
        if fields['project_type'] not in self.project_type_choices:
            field_errors['project_type'] = 'Please choose a project type.'
        if not fields['message']:
            field_errors['message'] = 'Please tell us a little about your project.'
        if field_errors:
            if is_ajax:
                return HttpResponse('\n'.join(field_errors.values()), status=400)
            context = self.get_context_data(**kwargs)
            context['field_errors'] = field_errors
            return render(request, self.template_name, context)

        try:
            submission = ContactSubmission.objects.create(
                name=fields['name'],
                phone=fields['phone'],
                email=fields['email'],
                project_type=fields['project_type'],
                project_location=fields['project_location'],
                preferred_call_time=fields['call_time'],
                message=fields['message'],
            )
        except Exception:
            logging.exception('Error saving contact submission')
            return self.render_form_error(
                request,
                kwargs,
                'We could not save your enquiry. Please try again later.',
                is_ajax,
                500,
            )

        record_metric(DailyAnalyticsMetric.FORM_SUBMISSION, 'Contact enquiry')
        subject = f"New website enquiry — {fields['name']}"
        body = '\n'.join([
            'A new project enquiry was submitted through vastarchitects.in.', '',
            f"Name: {fields['name']}", f"Phone: {fields['phone']}",
            f"Email: {fields['email'] or 'Not provided'}",
            f"Project type: {self.project_type_choices[fields['project_type']]}",
            f"Project location: {fields['project_location'] or 'Not provided'}",
            f"Preferred time to call: {fields['call_time'] or 'Not provided'}", '',
            'About the project:', fields['message'],
        ])
        recipient = os.environ.get('CONTACT_RECIPIENT_EMAIL', 'design@vastarchitects.in')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None) or 'contact@vastarchitects.in'
        if form_email_enabled():
            try:
                EmailMessage(
                    subject,
                    body,
                    from_email,
                    [recipient],
                    reply_to=[fields['email']] if fields['email'] else None,
                ).send(fail_silently=False)
                update_email_status(submission, ContactSubmission.EmailStatus.SENT)
            except BadHeaderError as exc:
                logging.exception('BadHeaderError sending contact email')
                update_email_status(submission, ContactSubmission.EmailStatus.FAILED, str(exc))
            except Exception as exc:
                logging.exception('Error sending contact email')
                update_email_status(submission, ContactSubmission.EmailStatus.FAILED, str(exc))
        else:
            update_email_status(
                submission,
                ContactSubmission.EmailStatus.DISABLED,
                'Email delivery is disabled; the enquiry is saved in Django Admin.',
            )

        if is_ajax:
            return HttpResponse('OK')
        context = self.get_context_data(**kwargs)
        context['sent'] = True
        return render(request, self.template_name, context)

    def render_form_error(self, request, kwargs, message, is_ajax=False, status=400):
        if is_ajax:
            return HttpResponse(message, status=status)
        context = self.get_context_data(**kwargs)
        context['error'] = message
        return render(request, self.template_name, context, status=status)


@csrf_exempt
def tinymce_upload(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    filename = f'tinymce/{uuid.uuid4()}_{uploaded_file.name}'
    path = default_storage.save(filename, ContentFile(uploaded_file.read()))
    return JsonResponse({'location': default_storage.url(path)})


class CareersView(ProtectedFormView):
    template_name = 'projects/careers.html'
    form_name = 'careers'

    def post(self, request, *args, **kwargs):
        if self.bot_submission(request):
            context = self.get_context_data(**kwargs)
            context['sent'] = True
            return render(request, self.template_name, context)
        if self.timing_error(request):
            return self.render_error(request, kwargs, 'Please wait a moment and try again.', 400)
        if rate_limit_exceeded(request, self.form_name):
            return self.render_error(request, kwargs, 'Too many applications were submitted from this connection. Please try again later.', 429)

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        skills = request.POST.get('skills', '').strip()
        years = request.POST.get('years', '').strip()
        portfolio_link = request.POST.get('portfolio_link', '').strip()
        internship = request.POST.get('internship', '') == 'on'
        portfolio = request.FILES.get('portfolio')
        field_errors = {}

        if not name:
            field_errors['name'] = 'Please enter your name.'
        elif len(name) > 100:
            field_errors['name'] = 'Please keep your name under 100 characters.'
        try:
            validate_email(email)
        except ValidationError:
            field_errors['email'] = 'Please enter a valid email address.'
        if len(email) > 254:
            field_errors['email'] = 'Please keep your email under 254 characters.'
        if len(skills) > 500:
            field_errors['skills'] = 'Please keep the skills summary under 500 characters.'
        if years:
            try:
                if not 0 <= int(years) <= 80:
                    raise ValueError
            except ValueError:
                field_errors['years'] = 'Please enter a number from 0 to 80.'
        if len(portfolio_link) > 500:
            field_errors['portfolio_link'] = 'Please keep the portfolio link under 500 characters.'
        elif portfolio_link:
            try:
                URLValidator(schemes=['http', 'https'])(portfolio_link)
            except ValidationError:
                field_errors['portfolio_link'] = 'Please enter a complete http or https link.'
        if not portfolio and not portfolio_link:
            field_errors['portfolio'] = 'Please upload a PDF portfolio or add a portfolio link.'
        if portfolio:
            if portfolio.size > MAX_CAREER_FILE_SIZE:
                field_errors['portfolio'] = 'The PDF must be 10 MB or smaller.'
            elif len(portfolio.name) > 255:
                field_errors['portfolio'] = 'The PDF filename is too long.'
            elif Path(portfolio.name).suffix.lower() != '.pdf':
                field_errors['portfolio'] = 'Only PDF portfolios are accepted.'
            elif getattr(portfolio, 'content_type', '') not in ('', 'application/pdf'):
                field_errors['portfolio'] = 'Only PDF portfolios are accepted.'
            else:
                header = portfolio.read(5)
                portfolio.seek(0)
                if header != b'%PDF-':
                    field_errors['portfolio'] = 'This file does not appear to be a valid PDF.'
        if field_errors:
            context = self.get_context_data(**kwargs)
            context['field_errors'] = field_errors
            return render(request, self.template_name, context, status=400)

        portfolio_data = portfolio.read() if portfolio else None
        if portfolio:
            portfolio.seek(0)
        try:
            submission = CareerSubmission.objects.create(
                name=name,
                email=email,
                skills=skills,
                years_experience=int(years) if years else None,
                seeking_internship=internship,
                portfolio_link=portfolio_link,
                portfolio_filename=portfolio.name if portfolio else '',
                portfolio_content_type=(getattr(portfolio, 'content_type', '') or 'application/pdf') if portfolio else '',
                portfolio_data=portfolio_data,
            )
        except Exception:
            logging.exception('Error saving careers submission')
            return self.render_error(
                request,
                kwargs,
                'We could not save your application. Please try again later.',
                500,
            )

        record_metric(DailyAnalyticsMetric.FORM_SUBMISSION, 'Careers application')
        body = '\n'.join([
            f'Name: {name}', f'Email: {email}', f'Skills: {skills or "Not provided"}',
            f'Years experience: {years or "Not provided"}',
            f"Looking for internship: {'Yes' if internship else 'No'}",
            f'Portfolio link: {portfolio_link or "Not provided"}',
        ])
        recipient = os.environ.get('CAREERS_RECIPIENT_EMAIL', 'design@vastarchitects.in')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'contact@vastarchitects.in'
        if form_email_enabled():
            try:
                email_message = EmailMessage(
                    subject=f'Career submission from {name}', body=body, from_email=from_email,
                    to=[recipient], reply_to=[email],
                )
                if portfolio_data:
                    email_message.attach(
                        submission.portfolio_filename,
                        portfolio_data,
                        submission.portfolio_content_type,
                    )
                email_message.send(fail_silently=False)
                update_email_status(submission, CareerSubmission.EmailStatus.SENT)
            except Exception as exc:
                logging.exception('Error sending careers email')
                update_email_status(submission, CareerSubmission.EmailStatus.FAILED, str(exc))
        else:
            update_email_status(
                submission,
                CareerSubmission.EmailStatus.DISABLED,
                'Email delivery is disabled; the application is saved in Django Admin.',
            )

        context = self.get_context_data(**kwargs)
        context['sent'] = True
        return render(request, self.template_name, context)

    def render_error(self, request, kwargs, message, status):
        context = self.get_context_data(**kwargs)
        context['error'] = message
        return render(request, self.template_name, context, status=status)


@csrf_exempt
def navigation_analytics(request):
    allowed_labels = {'work', 'about', 'journal', 'contact', 'careers', 'instagram'}
    if request.method != 'POST' or is_probable_bot(request):
        return HttpResponse(status=204)
    if request.META.get('HTTP_SEC_FETCH_SITE', 'same-origin') not in ('same-origin', 'same-site', 'none'):
        return HttpResponse(status=403)
    label = request.POST.get('label', '').strip().lower()
    if label not in allowed_labels or navigation_is_rate_limited(request, label):
        return HttpResponse(status=204)
    record_metric(DailyAnalyticsMetric.NAVIGATION, label.title())
    return HttpResponse(status=204)
