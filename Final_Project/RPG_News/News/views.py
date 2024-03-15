from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


import django_filters
import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

#from .forms import PostForm
from .models import *
from django.http import HttpResponse
from django.views import View
#from .tasks import hello, shared_task, printer
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.utils import timezone
from .forms import PostForm, CommentForm
from RPG_News.settings import EMAIL_HOST_USER, SITE_URL, DEFAULT_FROM_EMAIL
from django.core.mail import EmailMultiAlternatives
# Create your views here.


class NewsList(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    ordering = '-time_in'
    paginate_by = 1


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_author'] = not self.request.user.groups.filter(name='authors').exists()
        context['current_time'] = timezone.now()
        return context
    
def author_now(request):
    user = request.user
    author_group = Group.objects.get(name='authors')
    if not user.groups.filter(name='authors').exists():
        user.groups.add(author_group)
    return redirect('post_list')

class NewsDetail(DeleteView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'

    def get_object(self, *args, **kwargs):
        obj = cache.get(f'post-{self.kwargs["pk"]}', None)

        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)
    
        return obj


class NewsCreate(CreateView):
    model = Post
    template_name = 'post_create.html'
    context_object_name = 'posts'
    permission_required = ('News.add_post')
    fields='__all__'
    uccess_url = reverse_lazy('post')
    
    

class NewsUpload(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_edit.html'
    context_object_name = 'posts'
    permission_required = ('News.change_post')
    success_url = reverse_lazy('post_list')


class NewsDelete(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    context_object_name = 'posts'
    success_url = reverse_lazy('post_list')

class CommentDetailView(DetailView):
    model = Comment
    template_name = 'comment/comment.html'
    context_object_name = 'comment'

class CommentCreateView(CreateView, LoginRequiredMixin):
    model = Comment
    model_search = Post
    form_class = CommentForm
    template_name = 'comment/comment_create.html'
    context_object_name = 'comment'



    def form_valid(self, form):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=post_id)
        
        comment = form.save(commit=False)
        comment.post = post
        comment.author = self.request.user
        comment.save()

        recipient_email = post.author.user.email
        html_context = render_to_string(
            'email/new_comment.html',
            {
                'text': comment.text,
                'link': f'{SITE_URL}/comment/{comment.pk}',
                'title': post.title,
                'author': comment.author,
                'preview': comment.preview(),
            }
        )

        msg = EmailMultiAlternatives(
            subject=f'Новый отклик на ваш пост',
            body='',
            from_email=DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        msg.attach_alternative(html_context, 'text/html')
        msg.send()

        return super().form_valid(form)
    
    
class CommentUpdateView(UpdateView):
    model = Comment
    model_search = Comment
    template_name = 'comment/comment_edit.html'


    def get_object(self, **kwargs):
        my_id = self.kwargs.get('pk')
        return Comment.objects.get(pk=my_id)
    

class CommentDeleteView(DeleteView):
    template_name = 'comment/coment_delete.html'
    queryset = Comment.objects.all()
    success_url = reverse_lazy('post_list')


@login_required
def comment_accept(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if not comment.accept:
        comment.acccept = True
        comment.save()

        author_response = comment.author
        post = comment.post
        category = post.category
        text_sub = ''
        category_name = ''

        recipient_email = author_response.email
        html_context = render_to_string(
            'email/new_comment.html',
            {
                'cat': category_name,
                'link': f'{SITE_URL}/comment/{comment.pk}',
                'preview': comment.preview(),
                'text_sub': text_sub,

            }
        )

        msg = EmailMultiAlternatives(
            subject=f'Одобрение отклика',
            body='',
            from_email=EMAIL_HOST_USER,
            to=[recipient_email],
        )
        msg.attach_alternative(html_context, 'text/html')
        msg.send()
    return redirect(f'/comment/{comment_id}')