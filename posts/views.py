from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse


from .forms import CommentForm, PostForm
from .models import Group, Post, Follow
from yatube.settings import POST_ON_PAGE


User = get_user_model()


def index(request):
    posts = Post.objects.all()

    paginator = Paginator(posts, POST_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    paginator = Paginator(posts, POST_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'posts': page})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post_object = form.save(commit=False)
        post_object.author = request.user
        post_object.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form, 'edit': False})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.all()

    follow = False
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()

    paginator = Paginator(user_posts, POST_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'posts': page,
        'author': author,
        'follow': follow,
    }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'post.html', {
        'post': post,
        'author': post.author,
        'comments': comments,
        'form': form
    }
    )


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect(
            reverse('post', kwargs={'username': username, 'post_id': post_id})
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect(reverse(
            'post', kwargs={'username': username, 'post_id': post_id}
        ))
    return render(
        request,
        'new_post.html', {'form': form, 'post': post, 'edit': True}
    )


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment_object = form.save(commit=False)
        comment_object.author = request.user
        comment_object.post = post
        comment_object.save()
    return redirect(reverse(
        'post', kwargs={'username': username, 'post_id': post_id}
    ))


@login_required()
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(posts, POST_ON_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author).exists()
    if request.user != author and not follow:
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect(reverse('profile', kwargs={'username': username}))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    get_object_or_404(Follow, user=request.user, author=author).delete()
    return redirect(reverse('profile', kwargs={'username': username}))


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)
