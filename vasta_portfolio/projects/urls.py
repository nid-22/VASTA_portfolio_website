from django.urls import path
from .views import (
    AboutView,
    CareersView,
    ContactView,
    LegacyProjectListView,
    ProjectDetailView,
    ProjectListView,
    tinymce_upload,
)



# In your urls.py within the same app
from django.urls import path


urlpatterns = [
    path('', LegacyProjectListView.as_view(), name='project-list'),
    path('home/', ProjectListView.as_view(), name='new-home'),
    path('tinymce/upload/', tinymce_upload, name='tinymce_upload'),
    path('projects/<slug:slug>/', ProjectDetailView.as_view(), name='project_detail'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('careers/', CareersView.as_view(), name='careers'),
]
