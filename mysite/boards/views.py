from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from .models import Post, Comment
from .forms import PostForm, CommentForm

def board_list(request, board_type):
    posts = Post.objects.filter(board_type=board_type)
    paginator = Paginator(posts, 10)  # 한 페이지에 10개씩
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts,
        'board_type': board_type,
        'is_anonymous': board_type == 'anonymous'
    }
    return render(request, 'boards/post_list.html', context)

@login_required
def post_create(request, board_type):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.board_type = board_type
            post.save()
            messages.success(request, '게시글이 작성되었습니다.')
            url_name = 'boards:free_board' if board_type == 'free' else 'boards:anonymous_board'
            return redirect(url_name)
    else:
        form = PostForm()
    
    return render(request, 'boards/post_form.html', {
        'form': form,
        'board_type': board_type
    })

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comment_form = CommentForm()
    
    context = {
        'post': post,
        'comment_form': comment_form,
        'is_anonymous': post.board_type == 'anonymous'
    }
    return render(request, 'boards/post_detail.html', context)

@login_required
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if request.user != post.author:
        messages.error(request, '자신의 게시글만 수정할 수 있습니다.')
        return redirect('boards:post_detail', pk=post.pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, '게시글이 수정되었습니다.')
            return redirect('boards:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'boards/post_form.html', {
        'form': form,
        'post': post
    })

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if request.user != post.author:
        messages.error(request, '자신의 게시글만 삭제할 수 있습니다.')
        return redirect('boards:post_detail', pk=post.pk)
    
    board_type = post.board_type
    post.delete()
    messages.success(request, '게시글이 삭제되었습니다.')
    return redirect('boards:board_list', board_type=board_type)

@login_required
def comment_create(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                author=request.user,
                post=post,
                content=content
            )
            messages.success(request, '댓글이 작성되었습니다.')
            
            # AJAX 요청인지 확인
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'author': comment.author.username if post.board_type == 'free' else '익명',
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y.%m.d %H:%i')
                })
            
    return redirect('boards:post_detail', pk=post_pk)

@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    
    if request.user != comment.author:
        messages.error(request, '자신의 댓글만 삭제할 수 있습니다.')
        return redirect('boards:post_detail', pk=post_pk)
    
    comment.delete()
    messages.success(request, '댓글이 삭제되었습니다.')
    
    # AJAX 요청인지 확인
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('boards:post_detail', pk=post_pk)
