from io import BytesIO

from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import resolve, reverse
from django.views.generic import RedirectView
from PIL import Image

from .admin import validate_carousel_image
from .models import Project
from .views import LegacyProjectListView, ProjectListView


def uploaded_image(width, height, name='test.png'):
    buffer = BytesIO()
    Image.new('RGB', (width, height), color='white').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


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


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ContactViewTests(SimpleTestCase):
    def test_contact_submission_emails_callback_details(self):
        response = self.client.post(reverse('contact'), {
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
        self.assertEqual(mail.outbox[0].to, ['vast.architects@gmail.com'])
        self.assertEqual(mail.outbox[0].from_email, 'design@vastarchitects.in')
        self.assertIn('Phone: +91 98765 43210', mail.outbox[0].body)
        self.assertIn('Project type: Architecture + interiors', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].reply_to, ['asha@example.com'])

    def test_contact_submission_requires_callback_details(self):
        response = self.client.post(reverse('contact'), {
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
