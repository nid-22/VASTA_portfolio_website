from io import BytesIO
import time

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse
from django.views.generic import RedirectView
from PIL import Image

from .admin import validate_carousel_image
from .models import (
    CareerSubmission,
    ContactSubmission,
    DailyAnalyticsMetric,
    Discipline,
    Project,
    Typology,
)
from .views import FORM_TOKEN_SALT, LegacyProjectListView, ProjectListView


def uploaded_image(width, height, name='test.png'):
    buffer = BytesIO()
    Image.new('RGB', (width, height), color='white').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


def valid_form_token():
    return signing.dumps({'issued_at': time.time() - 5}, salt=FORM_TOKEN_SALT, compress=True)


class CarouselImageFallbackTests(SimpleTestCase):
    def test_desktop_falls_back_to_cover(self):
        project = Project(cover_image='https://example.com/cover.webp')
        self.assertEqual(project.desktop_carousel_image_url, project.cover_image)

    def test_mobile_prefers_phone_then_desktop_then_cover(self):
        project = Project(
            cover_image='https://example.com/cover.webp',
            carousel_desktop_image='https://example.com/desktop.webp',
            carousel_mobile_image='https://example.com/phone.webp',
        )
        self.assertEqual(project.mobile_carousel_image_url, project.carousel_mobile_image)
        project.carousel_mobile_image = ''
        self.assertEqual(project.mobile_carousel_image_url, project.carousel_desktop_image)
        project.carousel_desktop_image = ''
        self.assertEqual(project.mobile_carousel_image_url, project.cover_image)


class HomepageRoutingTests(SimpleTestCase):
    def test_refreshed_homepage_is_at_site_root(self):
        self.assertIs(resolve('/').func.view_class, ProjectListView)

    def test_legacy_homepage_is_available_as_work(self):
        self.assertIs(resolve('/work/').func.view_class, LegacyProjectListView)

    def test_old_home_address_redirects_to_site_root(self):
        self.assertIs(resolve('/home/').func.view_class, RedirectView)
        response = self.client.get('/home/')
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_old_salem_url_redirects_to_correct_slug(self):
        response = self.client.get('/projects/box/')
        self.assertRedirects(response, '/projects/salem-residence/', status_code=301, fetch_redirect_response=False)


class OptionalProjectTextTests(SimpleTestCase):
    def test_literal_none_is_hidden(self):
        project = Project(short_description='None', long_description=' none ')
        self.assertEqual(project.display_short_description, '')
        self.assertEqual(project.display_long_description, '')

    def test_long_descriptions_are_not_character_limited(self):
        self.assertIsNone(Project._meta.get_field('long_description').max_length)


class ProjectCategoryAndCarouselTests(TestCase):
    def setUp(self):
        self.category = Typology.objects.create(name='Residential')
        self.architecture = Discipline.objects.get(name='Architecture')
        self.interior = Discipline.objects.get(name='Interior')
        self.projects = []
        for index in range(6):
            project = Project.objects.create(
                heading=f'Project {index}', project_year='2026', status='Completed',
                size='1000 sq ft', order_to_display_id=index, category=self.category,
            )
            project.disciplines.add(self.architecture)
            self.projects.append(project)

    def test_project_can_appear_in_both_filters(self):
        self.projects[0].disciplines.add(self.interior)
        response = self.client.get(reverse('project-list'))
        project = next(item for item in response.context['projects'] if item['id'] == self.projects[0].id)
        self.assertEqual(project['type'], 'Residential')
        self.assertEqual(project['filter_classes'], 'architecture interior')

    def test_carousel_first_slide_is_top_three_and_contains_six_projects(self):
        response = self.client.get(reverse('new-home'))
        carousel = response.context['carousel_projects']
        self.assertEqual(len(carousel), 6)
        self.assertIn(carousel[0].id, [project.id for project in self.projects[:3]])
        self.assertEqual({project.id for project in carousel}, {project.id for project in self.projects})

    def test_project_view_is_counted_once_per_session(self):
        url = self.projects[0].get_absolute_url()
        user_agent = 'Mozilla/5.0 Test Browser'
        self.client.get(url, HTTP_USER_AGENT=user_agent)
        self.client.get(url, HTTP_USER_AGENT=user_agent)
        metric = DailyAnalyticsMetric.objects.get(metric='project_view', label='Project 0')
        self.assertEqual(metric.count, 1)

    def test_short_description_is_metadata_not_visible_copy(self):
        project = self.projects[0]
        project.short_description = 'A concise search description for this project.'
        project.save(update_fields=['short_description'])
        response = self.client.get(project.get_absolute_url())
        self.assertContains(response, 'content="A concise search description for this project."', html=False)
        self.assertNotContains(response, '<p>A concise search description for this project.</p>', html=True)

    def test_known_bot_project_view_is_not_counted(self):
        self.client.get(self.projects[0].get_absolute_url(), HTTP_USER_AGENT='ExampleBot/1.0')
        self.assertFalse(DailyAnalyticsMetric.objects.exists())

    def test_navigation_event_is_counted(self):
        response = self.client.post(
            reverse('navigation-analytics'), {'label': 'about'},
            HTTP_USER_AGENT='Mozilla/5.0 Test Browser', HTTP_SEC_FETCH_SITE='same-origin',
        )
        self.assertEqual(response.status_code, 204)
        metric = DailyAnalyticsMetric.objects.get(metric='navigation', label='About')
        self.assertEqual(metric.count, 1)


class CarouselImageValidationTests(SimpleTestCase):
    def test_accepts_suitable_desktop_image(self):
        image = uploaded_image(1920, 1080)
        self.assertIs(
            validate_carousel_image(
                image,
                minimum_size=(1920, 1080),
                orientation='landscape',
                label='Desktop carousel image',
            ),
            image,
        )

    def test_rejects_landscape_image_for_phone(self):
        with self.assertRaisesMessage(ValidationError, 'must be a portrait image'):
            validate_carousel_image(
                uploaded_image(1920, 1350),
                minimum_size=(1080, 1350),
                orientation='portrait',
                label='Phone carousel image',
            )

    def test_rejects_small_desktop_image(self):
        with self.assertRaisesMessage(ValidationError, 'must be at least 1920 × 1080 px'):
            validate_carousel_image(
                uploaded_image(1600, 900),
                minimum_size=(1920, 1080),
                orientation='landscape',
                label='Desktop carousel image',
            )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='contact@vastarchitects.in',
    FORM_EMAIL_ENABLED=True,
)
class ContactViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_contact_submission_emails_callback_details(self):
        response = self.client.post(reverse('contact'), {
            'form_token': valid_form_token(),
            'name': 'Asha Rao',
            'phone': '+91 98765 43210',
            'email': 'asha@example.com',
            'project_type': 'architecture-interiors',
            'project_location': 'Bengaluru',
            'call_time': 'Weekday mornings',
            'message': 'We are planning a family home on a 40 × 60 site.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enquiry received')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['design@vastarchitects.in'])
        self.assertEqual(mail.outbox[0].from_email, 'contact@vastarchitects.in')
        self.assertIn('Phone: +91 98765 43210', mail.outbox[0].body)
        self.assertIn('Project type: Architecture + interiors', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].reply_to, ['asha@example.com'])
        submission = ContactSubmission.objects.get()
        self.assertEqual(submission.name, 'Asha Rao')
        self.assertEqual(submission.phone, '+91 98765 43210')
        self.assertEqual(submission.project_type, 'architecture-interiors')
        self.assertEqual(submission.email_status, ContactSubmission.EmailStatus.SENT)

    def test_contact_submission_requires_callback_details(self):
        response = self.client.post(reverse('contact'), {
            'form_token': valid_form_token(),
            'name': '',
            'phone': '',
            'project_type': '',
            'message': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter your name.')
        self.assertContains(response, 'Please enter a phone number so we can call you.')
        self.assertContains(response, 'Please choose a project type.')
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_submission_is_discarded(self):
        response = self.client.post(reverse('contact'), {
            'form_token': valid_form_token(), 'website': 'spam.example',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enquiry received')
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(ContactSubmission.objects.exists())

    def test_too_fast_submission_is_rejected(self):
        response = self.client.post(reverse('contact'), {
            'form_token': signing.dumps({'issued_at': time.time()}, salt=FORM_TOKEN_SALT),
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Please wait a moment', status_code=400)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(FORM_EMAIL_ENABLED=False)
    def test_contact_submission_is_saved_when_email_is_disabled(self):
        response = self.client.post(reverse('contact'), {
            'form_token': valid_form_token(),
            'name': 'Database Test',
            'phone': '+91 98765 43210',
            'email': 'database@example.com',
            'project_type': 'architecture',
            'message': 'Save this enquiry without trying SMTP.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enquiry received')
        self.assertEqual(len(mail.outbox), 0)
        submission = ContactSubmission.objects.get()
        self.assertEqual(submission.email_status, ContactSubmission.EmailStatus.DISABLED)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='contact@vastarchitects.in',
    FORM_EMAIL_ENABLED=True,
)
class CareersViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_portfolio_link_can_be_used_instead_of_upload(self):
        response = self.client.post(reverse('careers'), {
            'form_token': valid_form_token(),
            'name': 'Asha Rao',
            'email': 'asha@example.com',
            'portfolio_link': 'https://example.com/portfolio',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Application received')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['design@vastarchitects.in'])
        self.assertEqual(mail.outbox[0].from_email, 'contact@vastarchitects.in')
        self.assertEqual(mail.outbox[0].reply_to, ['asha@example.com'])
        self.assertIn('Portfolio link: https://example.com/portfolio', mail.outbox[0].body)
        submission = CareerSubmission.objects.get()
        self.assertEqual(submission.name, 'Asha Rao')
        self.assertEqual(submission.portfolio_link, 'https://example.com/portfolio')
        self.assertEqual(submission.email_status, CareerSubmission.EmailStatus.SENT)

    def test_word_document_is_rejected(self):
        upload = SimpleUploadedFile(
            'portfolio.docx', b'not a pdf',
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        response = self.client.post(reverse('careers'), {
            'form_token': valid_form_token(),
            'name': 'Asha Rao', 'email': 'asha@example.com', 'portfolio': upload,
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Only PDF portfolios are accepted.', status_code=400)
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_pdf_signature_is_rejected(self):
        upload = SimpleUploadedFile('portfolio.pdf', b'not a pdf', content_type='application/pdf')
        response = self.client.post(reverse('careers'), {
            'form_token': valid_form_token(),
            'name': 'Asha Rao', 'email': 'asha@example.com', 'portfolio': upload,
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'does not appear to be a valid PDF', status_code=400)

    def test_rate_limit_blocks_fourth_careers_submission(self):
        data = {
            'form_token': valid_form_token(), 'name': 'Asha Rao',
            'email': 'asha@example.com', 'portfolio_link': 'https://example.com/portfolio',
        }
        for _ in range(3):
            self.assertEqual(self.client.post(reverse('careers'), data).status_code, 200)
        response = self.client.post(reverse('careers'), data)
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, 'Too many applications', status_code=429)

    @override_settings(FORM_EMAIL_ENABLED=False)
    def test_pdf_application_is_saved_when_email_is_disabled(self):
        portfolio = SimpleUploadedFile(
            'portfolio.pdf',
            b'%PDF-1.4\nVASTA test portfolio',
            content_type='application/pdf',
        )
        response = self.client.post(reverse('careers'), {
            'form_token': valid_form_token(),
            'name': 'Database Test',
            'email': 'database@example.com',
            'portfolio': portfolio,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Application received')
        self.assertEqual(len(mail.outbox), 0)
        submission = CareerSubmission.objects.get()
        self.assertEqual(submission.portfolio_filename, 'portfolio.pdf')
        self.assertEqual(bytes(submission.portfolio_data), b'%PDF-1.4\nVASTA test portfolio')
        self.assertEqual(submission.email_status, CareerSubmission.EmailStatus.DISABLED)


class CareerSubmissionAdminTests(TestCase):
    def setUp(self):
        self.submission = CareerSubmission.objects.create(
            name='Portfolio Test',
            email='portfolio@example.com',
            portfolio_filename='private-portfolio.pdf',
            portfolio_content_type='application/pdf',
            portfolio_data=b'%PDF-1.4\nprivate',
        )
        self.url = reverse(
            'admin:projects_careersubmission_download_portfolio',
            args=(self.submission.pk,),
        )

    def test_portfolio_download_requires_admin_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response['Location'])

    def test_admin_can_download_private_portfolio(self):
        user = get_user_model().objects.create_superuser(
            username='portfolio-admin',
            email='admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'%PDF-1.4\nprivate')
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('private-portfolio.pdf', response['Content-Disposition'])
