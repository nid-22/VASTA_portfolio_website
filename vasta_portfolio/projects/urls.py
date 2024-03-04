from django.urls import path
from .views import ProjectListView, ProjectDetailView, AboutView, ContactView



# In your urls.py within the same app
from django.urls import path


urlpatterns = [
    path('projects/all/', ProjectListView.as_view(), name='project-list'),
    path('projects/<slug:slug>/', ProjectDetailView.as_view(), name='project_detail'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
]
