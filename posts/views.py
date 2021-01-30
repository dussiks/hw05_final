from shutil import get_archive_formats
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow, Comment


PER_PAGE = settings.PER_PAGE


def index(request):
    """Return defined in PER_PAGE amount of posts per page beginning
    from last.
    """
    posts_list = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(posts_list, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "index.html", context)


def group_posts(request, slug):
    """Return defined in PER_PAGE amount of posts per page
    in group beginning from last.
    """
    group = get_object_or_404(Group, slug=slug)
    group_posts = Post.objects.select_related(
                        'author', 'group'
                    ).filter(
                        group=group
                    )
    paginator = Paginator(group_posts, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "group": group,
        "page": page,
        "paginator": paginator,
    }
    return render(request, "group.html", context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('index')
    context = {'form': form, 'is_edit': False}
    return render(request, 'posts/new.html', context)


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    author_posts = Post.objects.select_related(
                        'author', 'group'
                    ).filter(
                        author=author
                    )
    posts_count = author.posts.count()
    paginator = Paginator(author_posts, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    followers_count = author.following.count()
    followings_count = author.follower.count()
    is_following = (request.user.is_authenticated and
                    Follow.objects.filter(author=author, user=user).exists())
    context = {
        "page": page,
        "author": author,
        "paginator": paginator,
        "posts_count": posts_count,
        "followers_count": followers_count,
        "followings_count": followings_count,
        "is_following": is_following,
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=author, id=post_id)
    comments_list = Comment.objects.select_related(
                            'author', 'post'
                        ).filter(
                            post=post
                        )
    posts_count = author.posts.count()
    followers_count = author.following.count()
    followings_count = author.follower.count()
    form = CommentForm(request.POST or None)
    context = {
        "post": post,
        "posts_count": posts_count,
        "followers_count": followers_count,
        "followings_count": followings_count,
        "author": author,
        "comments_list": comments_list,
        "form": form,
    }
    return render(request, 'post.html', context)


def post_edit(request, username, post_id):
    post_author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author=post_author, id=post_id)
    if request.user != post_author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    context = {
        "form": form,
        "is_edit": True,
        "post": post,
    }
    return render(request, 'posts/new.html', context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    posts_list = Post.objects.select_related(
                        'author', 'group'
                    ).filter(
                        author__following__user=user
                    )
    paginator = Paginator(posts_list, PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=user).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception=None):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404,
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
