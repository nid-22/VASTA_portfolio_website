from django.urls import path
from django.views.generic import RedirectView
from .views import (
    AboutView,
    CareersView,
    ContactView,
    LegacyProjectListView,
    ProjectDetailView,
    ProjectListView,
    navigation_analytics,
    tinymce_upload,
)



# In your urls.py within the same app
from django.urls import path


urlpatterns = [
    path('', ProjectListView.as_view(), name='new-home'),
    path(
        'home/',
        RedirectView.as_view(pattern_name='new-home', permanent=False),
        name='home-redirect',
    ),
    path('work/', LegacyProjectListView.as_view(), name='project-list'),
    path('tinymce/upload/', tinymce_upload, name='tinymce_upload'),
    path(
        'projects/box/',
        RedirectView.as_view(url='/projects/salem-residence/', permanent=True),
        name='salem-old-url',
    ),
    path('projects/<slug:slug>/', ProjectDetailView.as_view(), name='project_detail'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('careers/', CareersView.as_view(), name='careers'),
    path('analytics/navigation/', navigation_analytics, name='navigation-analytics'),
]
