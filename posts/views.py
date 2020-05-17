from django.shortcuts import render,get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.select_related('author').order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_posts_list = Post.objects.filter(group=group).order_by('-pub_date').all()
    paginator = Paginator(group_posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'page': page, 'paginator': paginator, 'group': group})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            Post.objects.create(author=request.user, **form.cleaned_data)
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    form = PostForm()
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    profile_posts_list = Post.objects.prefetch_related('author').filter(author=user_profile).order_by('-pub_date').all()
    follows = Follow
    
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=user_profile).exists()
    else:
        following = False

    paginator = Paginator(profile_posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
       
    return render(request, 'profile.html', {'page': page, 'paginator': paginator, 
                    'username': username, 'user_profile': user_profile, 'following': following})


def post_view(request, username, post_id):
    user_profile = get_object_or_404(User, username=username)  
    post = get_object_or_404(Post.objects.select_related('author'), author=user_profile, pk=post_id)
    counter_posts = Post.objects.filter(author=user_profile).count()
    form = CommentForm()
    items = Comment.objects.filter(post=post)
    return render(request, 'post.html', {'username': username, 'user_profile': user_profile, 
                    'post': post, 'counter': counter_posts, 'form': form, 'items': items})


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)
    if post.author != request.user != author:
        return redirect(post_view, username=username, post_id=post_id)
        
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
        if form.is_valid():
            form.save()
            return redirect(post_view, username=username, post_id=post_id)
        return render(request, 'new_post.html', {'form': form, 'post': post})
        
    form = PostForm(instance=post)
    return render(request, 'new_post.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)  
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(author=request.user, post=post, **form.cleaned_data)
            return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path':request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def follow_index(request):
    follow_list = Follow.objects.select_related('author').filter(user=request.user)
    post_list = Post.objects.prefetch_related('author').filter(author__in=[follow.author for follow in follow_list]).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    form = CommentForm(request.POST)
    return render(request, "follow.html", {'page': page, 'paginator':paginator, 'form':form, 'post': post_list})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user).exists()
    
    if author != request.user and follow == False:
        Follow.objects.create(user=request.user, author=author)
        return redirect('profile', username=author.username)

    return redirect('profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_list = Follow.objects.select_related('author').filter(user=request.user)
    for follow in follow_list:
        if follow.author == author:
            follow.delete()
            return redirect('profile', username=author.username)
    