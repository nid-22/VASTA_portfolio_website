from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from .admin import validate_carousel_image
from .models import Project


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
