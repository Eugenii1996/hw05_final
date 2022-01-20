from xml.etree.ElementTree import Comment
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import (
    get_object_or_404, redirect, render
)

from .models import Comment, Follow, Group, Post, User
from .forms import CommentForm, PostForm


def post_processor(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': post_processor(request, Post.objects.all()),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': post_processor(request, group.posts.all()),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists():
        following = True
    else:
        following = False
    return render(request, 'posts/profile.html', {
        'author': author,
        'following': following,
        'page_obj': post_processor(request, author.posts.all()),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': CommentForm(request.POST or None),
        'comments': Comment.objects.all().filter(post=post)
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    username = request.user.username
    return redirect('posts:profile', username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': True}
        )
    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(
            request,
            'posts/post_detail.html',
            {'form': form}
        )
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = get_object_or_404(Post, pk=post_id)
    comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    if request.user.is_authenticated:
        posts = Post.objects.filter(author__following__user=request.user)
        return render(request, 'posts/follow.html', {
            'user': request.user,
            'page_obj': post_processor(request, posts)
        })
    return redirect('posts:index')


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(
        user=user, author=author
    ).exists() or author == user:
        return redirect('posts:profile', username)
    Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', author)
