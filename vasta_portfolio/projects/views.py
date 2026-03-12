from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.shortcuts import redirect
from django.shortcuts import render
from .models import Project
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
from django.views.generic.edit import FormView
from django.core.mail import EmailMessage
from django.utils.encoding import smart_str

# Max portfolio upload size (bytes)
MAX_CAREER_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CAREER_MIME = {
    'application/pdf',
    'application/zip',
    'application/x-zip-compressed',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
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
        # project_images is the related_name on the ProjectImage model.
        imgs = self.object.project_images.all()
        # Provide both keys for backward compatibility in templates/code.
        context['project_images'] = imgs
        return context



class AboutView(TemplateView):
    template_name = "about.html"

class ContactView(TemplateView):
    template_name = "contact.html"

    def post(self, request, *args, **kwargs):
        # Read form fields
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', 'Website contact').strip()
        message = request.POST.get('message', '').strip()

        # Build email body
        body = f"From: {name} <{email}>\n\n{message}"

        recipient = 'design@vastarchitects.in'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'SERVER_EMAIL', None) or email or 'webmaster@localhost'

        try:
            send_mail(subject, body, from_email, [recipient], fail_silently=False)
            context = self.get_context_data(**kwargs)
            context['sent'] = True
            return render(request, self.template_name, context)
        except BadHeaderError:
            context = self.get_context_data(**kwargs)
            context['error'] = 'Invalid header found.'
            return render(request, self.template_name, context)
        except Exception as e:
            # Log exception? For now, show a generic error message in template
            context = self.get_context_data(**kwargs)
            context['error'] = 'An error occurred while sending the message. Please try again later.'
            return render(request, self.template_name, context)


@csrf_exempt
def tinymce_upload(request):
    """Simple TinyMCE image uploader that returns JSON with the file location.

    This is intentionally minimal: it saves the uploaded file to Django's
    default storage and returns the public URL in the `location` key which
    TinyMCE expects.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    filename = f"tinymce/{uuid.uuid4()}_{file.name}"
    path = default_storage.save(filename, ContentFile(file.read()))

    return JsonResponse({
        "location": default_storage.url(path)
    })


class CareersView(TemplateView):
    template_name = 'projects/careers.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        skills = request.POST.get('skills', '').strip()
        years = request.POST.get('years', '').strip()
        internship = request.POST.get('internship', '') == 'on'

        portfolio = request.FILES.get('portfolio')

        # Validate file size
        if portfolio and getattr(portfolio, 'size', 0) > MAX_CAREER_FILE_SIZE:
            ctx = self.get_context_data(**kwargs)
            ctx['error'] = f"Portfolio file is too large. Maximum allowed size is {MAX_CAREER_FILE_SIZE // (1024*1024)} MB."
            return render(request, self.template_name, ctx)

        # Validate MIME type if available
        if portfolio:
            content_type = getattr(portfolio, 'content_type', '')
            if content_type and content_type not in ALLOWED_CAREER_MIME:
                ctx = self.get_context_data(**kwargs)
                ctx['error'] = "Unsupported file format. Accepted: PDF, ZIP, DOC, DOCX."
                return render(request, self.template_name, ctx)

        recipient = 'design@vastarchitects.in'

        subject = f"Career submission from {name or 'Candidate'}"
        body_lines = [
            f"Name: {name}",
            f"Email: {email}",
            f"Skills: {skills}",
            f"Years experience: {years}",
            f"Looking for internship: {'Yes' if internship else 'No'}",
        ]
        body = "\n".join(body_lines)

        try:
            email_msg = EmailMessage(subject=subject, body=body, to=[recipient])
            # Attach portfolio file in-memory without saving to disk
            if portfolio:
                # portfolio.read() will return bytes; attach with original filename and content_type
                content = portfolio.read()
                filename = portfolio.name
                content_type = portfolio.content_type if hasattr(portfolio, 'content_type') else 'application/octet-stream'
                email_msg.attach(filename, content, content_type)

            email_msg.send(fail_silently=False)
            ctx = self.get_context_data(**kwargs)
            ctx['sent'] = True
            return render(request, self.template_name, ctx)
        except Exception as e:
            ctx = self.get_context_data(**kwargs)
            ctx['error'] = 'An error occurred while sending your application. Please try again later.'
            return render(request, self.template_name, ctx)


