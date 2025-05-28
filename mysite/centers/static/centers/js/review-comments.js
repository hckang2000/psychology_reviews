// 리뷰 댓글 관리 JavaScript

// 디버깅을 위한 로그 함수
function debugLog(message, data = null) {
    console.log(`[ReviewComments] ${message}`, data || '');
}

// alertManager 안전 사용 함수
function safeShowAlert(message, type = 'info') {
    debugLog('Attempting to show alert:', { message, type });
    debugLog('window.alertManager exists:', !!window.alertManager);
    debugLog('window.alertManager.showAlert exists:', !!(window.alertManager && window.alertManager.showAlert));
    debugLog('window.alertManager.show exists:', !!(window.alertManager && window.alertManager.show));
    
    if (window.alertManager && typeof window.alertManager.show === 'function') {
        debugLog('Using alertManager.show');
        return window.alertManager.show(message, type);
    } else if (window.showAlert && typeof window.showAlert === 'function') {
        debugLog('Using global showAlert function');
        return window.showAlert(message, type);
    } else {
        debugLog('Falling back to alert()');
        alert(message);
    }
}

// 응답이 JSON인지 확인하는 헬퍼 함수
function isJsonResponse(response) {
    const contentType = response.headers.get('content-type');
    return contentType && contentType.includes('application/json');
}

// 안전한 JSON 파싱 함수
async function safeJsonParse(response) {
    if (!isJsonResponse(response)) {
        throw new Error(`서버에서 HTML 응답을 받았습니다. 상태: ${response.status}`);
    }
    
    const text = await response.text();
    try {
        return JSON.parse(text);
    } catch (e) {
        console.error('JSON 파싱 오류:', text);
        throw new Error('서버 응답을 파싱할 수 없습니다.');
    }
}

// 댓글 관련 JavaScript 함수들
function toggleComments(reviewId) {
    debugLog('toggleComments called', reviewId);
    const commentsSection = document.getElementById(`comments-${reviewId}`);
    const isVisible = commentsSection.style.display !== 'none';
    
    if (isVisible) {
        commentsSection.style.display = 'none';
    } else {
        commentsSection.style.display = 'block';
        // 댓글 목록 새로고침
        loadComments(reviewId);
    }
}

function loadComments(reviewId) {
    debugLog('loadComments called', reviewId);
    fetch(`/reviews/${reviewId}/comments/`)
        .then(response => {
            debugLog('loadComments response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return safeJsonParse(response);
        })
        .then(data => {
            debugLog('loadComments data received:', data);
            if (data.success) {
                updateCommentsDisplay(reviewId, data.comments);
            } else {
                console.error('댓글 로딩 실패:', data.error);
                alert(data.error || '댓글을 불러오는데 실패했습니다.');
            }
        })
        .catch(error => {
            console.error('댓글 로딩 오류:', error);
            alert(`댓글 로딩 중 오류가 발생했습니다: ${error.message}`);
        });
}

function updateCommentsDisplay(reviewId, comments) {
    debugLog('updateCommentsDisplay called', { reviewId, commentsCount: comments.length });
    const commentsList = document.getElementById(`comments-list-${reviewId}`);
    commentsList.innerHTML = '';
    
    comments.forEach(comment => {
        const commentHtml = createCommentHTML(comment);
        commentsList.insertAdjacentHTML('beforeend', commentHtml);
    });
}

function createCommentHTML(comment) {
    const editActions = comment.can_edit ? `
        <div class="comment-actions">
            <button class="edit-comment-btn" onclick="editComment(${comment.id})">
                ✏️ 수정
            </button>
            <button class="delete-comment-btn" onclick="deleteComment(${comment.id})">
                🗑️ 삭제
            </button>
        </div>
    ` : '';
    
    return `
        <div class="comment-item" data-comment-id="${comment.id}">
            <div class="comment-header">
                <span class="comment-author">🏢 ${comment.author}</span>
                <span class="comment-date">${comment.created_at}</span>
                ${editActions}
            </div>
            <div class="comment-content" id="comment-content-${comment.id}">
                ${comment.content.replace(/\n/g, '<br>')}
            </div>
            <div class="comment-edit-form" id="comment-edit-form-${comment.id}" style="display: none;">
                <textarea class="comment-edit-textarea" id="comment-edit-textarea-${comment.id}">${comment.content}</textarea>
                <div class="comment-edit-actions">
                    <button class="save-comment-btn" onclick="saveComment(${comment.id})">
                        💾 저장
                    </button>
                    <button class="cancel-edit-btn" onclick="cancelEdit(${comment.id})">
                        ❌ 취소
                    </button>
                </div>
            </div>
        </div>
    `;
}

function addComment(reviewId) {
    debugLog('addComment called', reviewId);
    const textarea = document.getElementById(`comment-textarea-${reviewId}`);
    const content = textarea.value.trim();
    
    if (!content) {
        alert('댓글 내용을 입력해주세요.');
        return;
    }
    
    debugLog('Sending comment request', { reviewId, content });
    
    fetch(`/reviews/${reviewId}/comments/add/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => {
        debugLog('addComment response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return safeJsonParse(response);
    })
    .then(data => {
        debugLog('addComment data received:', data);
        if (data.success) {
            textarea.value = '';
            loadComments(reviewId);
            // 알림 표시
            safeShowAlert('댓글이 성공적으로 작성되었습니다.', 'success');
        } else {
            alert(data.error || '댓글 작성에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('댓글 작성 오류:', error);
        alert(`댓글 작성 중 오류가 발생했습니다: ${error.message}`);
    });
}

function editComment(commentId) {
    debugLog('editComment called', commentId);
    const contentDiv = document.getElementById(`comment-content-${commentId}`);
    const editForm = document.getElementById(`comment-edit-form-${commentId}`);
    
    contentDiv.style.display = 'none';
    editForm.style.display = 'block';
}

function cancelEdit(commentId) {
    debugLog('cancelEdit called', commentId);
    const contentDiv = document.getElementById(`comment-content-${commentId}`);
    const editForm = document.getElementById(`comment-edit-form-${commentId}`);
    
    contentDiv.style.display = 'block';
    editForm.style.display = 'none';
}

function saveComment(commentId) {
    debugLog('saveComment called', commentId);
    const textarea = document.getElementById(`comment-edit-textarea-${commentId}`);
    const content = textarea.value.trim();
    
    if (!content) {
        alert('댓글 내용을 입력해주세요.');
        return;
    }
    
    fetch(`/comments/${commentId}/update/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => {
        debugLog('saveComment response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return safeJsonParse(response);
    })
    .then(data => {
        debugLog('saveComment data received:', data);
        if (data.success) {
            const contentDiv = document.getElementById(`comment-content-${commentId}`);
            const editForm = document.getElementById(`comment-edit-form-${commentId}`);
            
            contentDiv.innerHTML = content.replace(/\n/g, '<br>');
            contentDiv.style.display = 'block';
            editForm.style.display = 'none';
            
            // 알림 표시
            safeShowAlert('댓글이 성공적으로 수정되었습니다.', 'success');
        } else {
            alert(data.error || '댓글 수정에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('댓글 수정 오류:', error);
        alert(`댓글 수정 중 오류가 발생했습니다: ${error.message}`);
    });
}

function deleteComment(commentId) {
    debugLog('deleteComment called', commentId);
    if (!confirm('정말로 이 댓글을 삭제하시겠습니까?')) {
        return;
    }
    
    fetch(`/comments/${commentId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        debugLog('deleteComment response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return safeJsonParse(response);
    })
    .then(data => {
        debugLog('deleteComment data received:', data);
        if (data.success) {
            const commentItem = document.querySelector(`[data-comment-id="${commentId}"]`);
            commentItem.remove();
            
            // 알림 표시
            safeShowAlert('댓글이 성공적으로 삭제되었습니다.', 'success');
        } else {
            alert(data.error || '댓글 삭제에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('댓글 삭제 오류:', error);
        alert(`댓글 삭제 중 오류가 발생했습니다: ${error.message}`);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 페이지 로드 시 디버깅 정보 출력
document.addEventListener('DOMContentLoaded', function() {
    debugLog('DOM Content Loaded');
    debugLog('window.alertManager available:', !!window.alertManager);
    debugLog('window.showAlert available:', !!window.showAlert);
    
    // alertManager가 로드될 때까지 기다리는 함수
    function waitForAlertManager(attempts = 0) {
        if (window.alertManager && typeof window.alertManager.show === 'function') {
            debugLog('AlertManager is ready!');
            return;
        }
        
        if (attempts < 10) {
            debugLog(`Waiting for alertManager... attempt ${attempts + 1}`);
            setTimeout(() => waitForAlertManager(attempts + 1), 100);
        } else {
            debugLog('AlertManager not found after 10 attempts, will use fallback');
        }
    }
    
    waitForAlertManager();
}); 