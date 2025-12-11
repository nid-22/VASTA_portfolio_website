from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.shortcuts import render
from .models import Project
# Create your views here.

class ProjectListView(ListView):
    model = Project
    template_name = 'projects/index.html'

    def get_queryset(self):
        # Order projects by the order_to_display_id field so the template shows them in that order
        return Project.objects.all().order_by('order_to_display_id')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Modify the context to include your custom data
        context['projects'] = [
            {
                'id':project.id,
                'project_name': project.heading,
                'cover_image': project.cover_image.url if project.cover_image else None,
                'type': project.typology.name,
                'get_absolute_url': project.get_absolute_url,
                'grid_shape': project.grid_shape,
            }
            for project in context['object_list']
        ]
        return context



class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/work-single.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['process_images'] = self.object.process_images.all()  # Assuming 'process_images' is the related_name for ProcessImages
        return context



class AboutView(TemplateView):
    template_name = "about.html"

class ContactView(TemplateView):
    template_name = "contact.html"


