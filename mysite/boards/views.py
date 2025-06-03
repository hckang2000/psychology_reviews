from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from .models import Post, Comment, EventPost
from .forms import PostForm, CommentForm, EventPostForm

def board_list(request, board_type):
    if board_type == 'event':
        # 이벤트 게시판은 EventPost와 조인하여 가져오기
        posts = Post.objects.filter(board_type=board_type).select_related('event_detail').order_by('-created_at')
    else:
        posts = Post.objects.filter(board_type=board_type)
    
    paginator = Paginator(posts, 10)  # 한 페이지에 10개씩
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    
    context = {
        'posts': posts,
        'board_type': board_type,
        'is_anonymous': board_type == 'anonymous',
        'is_event': board_type == 'event'
    }
    return render(request, 'boards/post_list.html', context)

@login_required
def post_create(request, board_type):
    # 이벤트 게시판은 superuser만 접근 가능
    if board_type == 'event' and not request.user.is_superuser:
        messages.error(request, '이벤트 등록은 관리자만 가능합니다.')
        return redirect('boards:event_board')
    
    if board_type == 'event':
        # 이벤트 게시글 처리
        if request.method == 'POST':
            form = EventPostForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    # Post 생성
                    post = Post.objects.create(
                        title=form.cleaned_data['title'],
                        content=form.cleaned_data['content'],
                        author=request.user,
                        board_type=board_type
                    )
                    
                    # EventPost 생성
                    event_post = form.save(commit=False)
                    event_post.post = post
                    event_post.save()
                    
                messages.success(request, '이벤트가 등록되었습니다.')
                return redirect('boards:event_board')
        else:
            form = EventPostForm()
        
        return render(request, 'boards/event_form.html', {
            'form': form,
            'board_type': board_type
        })
    else:
        # 일반 게시글 처리
        if request.method == 'POST':
            form = PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.board_type = board_type
                post.save()
                messages.success(request, '게시글이 작성되었습니다.')
                
                # 게시판 타입에 따른 리다이렉트
                if board_type == 'free':
                    url_name = 'boards:free_board'
                elif board_type == 'anonymous':
                    url_name = 'boards:anonymous_board'
                else:
                    url_name = 'boards:free_board'  # 기본값
                    
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
    
    # 이벤트 게시글인 경우 EventPost 정보도 가져오기
    event_detail = None
    if post.board_type == 'event':
        try:
            event_detail = post.event_detail
        except EventPost.DoesNotExist:
            event_detail = None
    
    context = {
        'post': post,
        'comment_form': comment_form,
        'is_anonymous': post.board_type == 'anonymous',
        'is_event': post.board_type == 'event',
        'event_detail': event_detail
    }
    return render(request, 'boards/post_detail.html', context)

@login_required
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # 이벤트 게시글은 superuser만 수정 가능
    if post.board_type == 'event' and not request.user.is_superuser:
        messages.error(request, '이벤트 수정은 관리자만 가능합니다.')
        return redirect('boards:post_detail', pk=post.pk)
    
    # 일반 게시글은 작성자만 수정 가능
    if post.board_type != 'event' and request.user != post.author:
        messages.error(request, '자신의 게시글만 수정할 수 있습니다.')
        return redirect('boards:post_detail', pk=post.pk)
    
    if post.board_type == 'event':
        # 이벤트 게시글 수정
        try:
            event_detail = post.event_detail
        except EventPost.DoesNotExist:
            messages.error(request, '이벤트 정보를 찾을 수 없습니다.')
            return redirect('boards:post_detail', pk=post.pk)
        
        if request.method == 'POST':
            form = EventPostForm(request.POST, instance=event_detail)
            if form.is_valid():
                with transaction.atomic():
                    # Post 업데이트
                    post.title = form.cleaned_data['title']
                    post.content = form.cleaned_data['content']
                    post.save()
                    
                    # EventPost 업데이트
                    form.save()
                    
                messages.success(request, '이벤트가 수정되었습니다.')
                return redirect('boards:post_detail', pk=post.pk)
        else:
            # 기존 데이터로 폼 초기화
            initial_data = {
                'title': post.title,
                'content': post.content
            }
            form = EventPostForm(instance=event_detail, initial=initial_data)
        
        return render(request, 'boards/event_form.html', {
            'form': form,
            'post': post,
            'board_type': post.board_type
        })
    else:
        # 일반 게시글 수정
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
    
    # 이벤트 게시글은 superuser만 삭제 가능
    if post.board_type == 'event' and not request.user.is_superuser:
        messages.error(request, '이벤트 삭제는 관리자만 가능합니다.')
        return redirect('boards:post_detail', pk=post.pk)
    
    # 일반 게시글은 작성자만 삭제 가능
    if post.board_type != 'event' and request.user != post.author:
        messages.error(request, '자신의 게시글만 삭제할 수 있습니다.')
        return redirect('boards:post_detail', pk=post.pk)
    
    board_type = post.board_type
    post.delete()  # EventPost는 CASCADE로 자동 삭제
    messages.success(request, '게시글이 삭제되었습니다.')
    
    # 게시판 타입에 따른 리다이렉트
    if board_type == 'free':
        return redirect('boards:free_board')
    elif board_type == 'anonymous':
        return redirect('boards:anonymous_board')
    elif board_type == 'event':
        return redirect('boards:event_board')
    else:
        return redirect('boards:free_board')

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
