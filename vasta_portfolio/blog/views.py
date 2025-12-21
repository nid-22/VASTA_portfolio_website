from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Blog


class BlogListView(ListView):
	model = Blog
	template_name = 'blog/index.html'
	context_object_name = 'articles'
	paginate_by = 12

	def get_queryset(self):
		return Blog.objects.filter(is_active=True).order_by('-created_date')


class BlogDetailView(DetailView):
	model = Blog
	template_name = 'blog/detail.html'
	context_object_name = 'article'

	def get_object(self, queryset=None):
		return get_object_or_404(Blog, slug=self.kwargs.get('slug'), is_active=True)
