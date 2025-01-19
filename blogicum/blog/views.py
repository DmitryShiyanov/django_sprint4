from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest, HttpResponse, Http404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy, reverse
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from blog import constants

from .forms import AddComment, NewPost, ProfileEdit
from .models import Category, Comment, Post
from .moduls import annotate_comments, filter_posts

User = get_user_model()


def index(request):
    paginator = Paginator(annotate_comments(filter_posts(Post.objects)),
                          constants.POSTS_LIMIT)
    return render(
        request,
        template_name=constants.BLOG_INDEX,
        context={'page_obj': paginator.get_page(request.GET.get('page'))})


# def post_detail(request, post_id):
#     post = get_object_or_404(Post.objects.filter((Q(is_published=True) & Q(
#         category__is_published=True)) | Q(author=request.user.id)), id=post_id)
#     form = AddComment(
#         request.POST or None,
#         files=request.FILES or None
#     )
#     if form.is_valid():
#         instance = form.save(commit=False)
#         instance.post_id = post_id
#         instance.save()
#         return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
#     return render(
#         request,
#         template_name=constants.BLOG_DETAIL,
#         context={'post': post, 'form': form, 'comment': post.comments.all()})


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    post_list = annotate_comments(
        filter_posts(category.posts.all()))
    paginator = Paginator(post_list, constants.POSTS_LIMIT)
    return render(request, template_name=constants.BLOG_CATEGORY,
                  context={'category': category,
                           'page_obj': paginator.get_page(
                               request.GET.get('page'))})


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = annotate_comments(profile.posts.all())
    if username != request.user.username:
        posts = filter_posts(posts).order_by('-pub_date')
    paginator = Paginator(posts, constants.POSTS_LIMIT)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, template_name=constants.BLOG_PROFILE,
                  context={'page_obj': page_obj, 'profile': profile})


@login_required
def edit_profile(request):
    user = request.user
    form = ProfileEdit(request.POST or None, instance=user)
    if request.method != 'POST':
        return render(request, constants.BLOG_USER, context={'form': form})
    if not form.is_valid():
        return render(request, constants.BLOG_USER, context={'form': form})
    form.save()
    return redirect(constants.BLOG_PROFILE_NAME, username=user.username)


@login_required
def create_post(request):
    form = NewPost(request.POST or None, files=request.FILES or None)
    user = request.user
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = user
        instance.save()
        return redirect(constants.BLOG_PROFILE_NAME,
                        username=user.username)
    return render(request, constants.BLOG_CREATE, context={'form': form})


@login_required
def edit_post(request, post_id):
    user = request.user
    instance = get_object_or_404(Post, id=post_id)
    if instance.author.username != user.username:
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)

    form = NewPost(request.POST or None, files=request.FILES or None,
                   instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = user
        instance.save()
        return redirect(constants.BLOG_PROFILE_NAME, username=user.username)
    return render(request, constants.BLOG_CREATE, context={'form': form})


@login_required
def add_comment(request, post_id):
    form = AddComment(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)

    return render(request, constants.BLOG_COMMENT, context={'form': form})


@login_required
def edit_comment(request, post_id, comment_id):
    instance = get_object_or_404(Comment, id=comment_id, author=request.user)

    form = AddComment(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)

    return render(request, constants.BLOG_COMMENT,
                  context={'form': form, 'comment': instance})


@login_required
def delete_post(request, post_id):
    instance = get_object_or_404(Post, pk=post_id)
    if instance.author.username != request.user.username:
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
    if request.method == 'POST':
        instance.delete()
        return redirect(constants.BLOG_PROFILE_NAME,
                        username=request.user.username)
    form = NewPost(instance=instance)
    return render(request, constants.BLOG_CREATE,
                  context={'form': form, 'post': instance})


@login_required
def delete_comment(request, post_id, comment_id):
    instance = get_object_or_404(Comment, pk=comment_id,
                                 author=request.user.id)
    if request.method == 'POST':
        instance.delete()
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
    return render(request, constants.BLOG_COMMENT,
                  context={'comment': instance})


def post_detail(request, post_id):
    template_name = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.filter(
            pk=post_id,
            
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    )
    if not post.is_published and post.author != request.user:
        raise Http404('Пост  не существует')
    form = AddComment()
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template_name, context)

# class OnlyAuthorMixin(UserPassesTestMixin):

#     def test_func(self):
#         object = self.get_object()
#         if isinstance(object, HttpResponse):
#             return False
#         return object.author == self.request.user

# class EditPostView(LoginRequiredMixin, UpdateView):
#     model = Post
#     form_class = NewPost
#     template_name = 'blog/create.html'
#     pk_url_kwarg = 'post_id'

#     def get_object(self, queryset=None):
#         post_id = self.kwargs['post_id']
#         post = Post.objects.get(id=post_id)
#         if post.author != self.request.user:
#             raise PermissionDenied
#         return post
    
#     def get_success_url(self):
#         return reverse('blog:post_detail', kwargs={'post_id': self.object.id})
    
#     def dispatch(self,request, *args, **kwargs):
#         try:
#             return super().dispatch(request, *args, **kwargs)
#         except PermissionDenied:
#             return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


# class PostDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
#     model = Post
#     template_name = 'blog/create.html'
#     pk_url_kwarg = 'post_id'
    
#     def get_object(self, queryset=None):
#         post_id = self.kwargs['post_id']
#         post = Post.objects.get(id=post_id)
#         if post.author != self.request.user:
#             return reverse('blog:profile', kwargs={'username': self.request.user.username})
#         return post
    
#     def get_success_url(self):
#         return reverse('blog:profile', kwargs={'username': self.request.user.username})
