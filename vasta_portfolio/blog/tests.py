from django.test import TestCase
from django.urls import reverse

from .admin import BlogAdminForm
from .models import Blog


class BlogLayoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.article = Blog.objects.create(
            title='What is in a detail?',
            slug='what-is-in-a-detail',
            content='<p>Article body</p>',
            cover_image='blog/cover_images/detail.png',
            content_width='standard',
        )

    def test_blog_card_has_visible_title_but_no_date(self):
        response = self.client.get(reverse('blog:list'))
        self.assertContains(response, '<h3>What is in a detail?</h3>', html=True)
        self.assertNotContains(response, 'work-info')
        self.assertNotContains(response, 'September')

    def test_article_uses_selected_width_without_repeating_cover(self):
        response = self.client.get(self.article.get_absolute_url())
        self.assertContains(response, 'blog-width-standard')
        self.assertContains(response, 'Article body')
        self.assertContains(response, '<time datetime=', count=1)
        self.assertNotContains(response, 'blog/cover_images/detail.png')

    def test_admin_editor_exposes_image_layouts(self):
        config = BlogAdminForm.base_fields['content'].widget.mce_attrs
        self.assertTrue(config['image_caption'])
        self.assertIn('essay-image-pair', str(config['table_class_list']))
        self.assertIn('essay-float-left', str(config['image_class_list']))
        self.assertIn('essay-float-right', str(config['image_class_list']))
