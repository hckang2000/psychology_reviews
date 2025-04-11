// Utility function to get query parameters from the URL
function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

console.log("Starting to load the map...");

var map;
var markers = [];
var currentCenterId = null; // 현재 선택된 센터 ID를 저장할 변수

function initMap() {
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(37.5665, 126.9780), // 서울 중심
        zoom: 13
    });
}

var centers = [
    // The centers data will be dynamically passed from Django
];

function loadCenters(centers, selectedCenterId) {
    // Clear existing markers
    markers.forEach(marker => marker.setMap(null));
    markers = [];

    // Add markers for each center
    centers.forEach(center => {
        const marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(center.lat, center.lng),
            map: map
        });

        // Add click event to marker
        naver.maps.Event.addListener(marker, 'click', function() {
            showCenterDetails(center);
        });

        markers.push(marker);

        // If this is the selected center, show its details
        if (center.id === selectedCenterId) {
            showCenterDetails(center);
        }
    });
}

function showCenterDetails(center) {
    const bottomSheet = document.getElementById('center-info-sheet');
    const centerDetails = document.getElementById('center-details');
    
    // 현재 선택된 센터 ID 저장
    currentCenterId = center.id;
    
    // Create HTML content for center details
    let content = `
        <div class="center-details">
            <div class="bottom-sheet-header">
                <div class="drag-handle"></div>
                <button class="close-button" onclick="closeBottomSheet()">×</button>
            </div>
            <h2>${center.name}</h2>
            <p><strong>주소:</strong> ${center.address}</p>
            <p><strong>연락처:</strong> ${center.contact}</p>
            <p><strong>운영시간:</strong> ${center.operating_hours}</p>
            <p><strong>웹사이트:</strong> <a href="${center.url}" target="_blank">${center.url}</a></p>
            <p>${center.description}</p>
    `;

    // Add image slider if there are images
    if (center.images && center.images.length > 0) {
        content += `
            <div class="image-slider">
                <img src="${center.images[0]}" alt="${center.name}">
            </div>
        `;
    }

    // Add review section
    content += `
            <div class="review-section">
                <h3>리뷰</h3>
                ${center.isAuthenticated ? 
                    '<button onclick="showReviewForm()">리뷰 작성하기</button>' :
                    '<p><a href="/login">로그인</a>하여 리뷰를 작성해보세요.</p>'
                }
            </div>
        </div>
    `;

    centerDetails.innerHTML = content;
    bottomSheet.classList.add('active');

    // Load reviews for this center
    loadReviews(center.id);

    // 드래그 이벤트 설정
    setupDragHandles();
}

// 드래그 핸들 설정 함수
function setupDragHandles() {
    const bottomSheet = document.getElementById('center-info-sheet');
    const dragHandle = document.querySelector('.drag-handle');
    
    if (!dragHandle) return;
    
    let startY;
    let startTransform = 0;
    
    // 터치 이벤트
    dragHandle.addEventListener('touchstart', (e) => {
        startY = e.touches[0].clientY;
        const transform = bottomSheet.style.transform;
        if (transform) {
            startTransform = parseInt(transform.replace('translateY(', '').replace('px)', ''));
        }
    });
    
    dragHandle.addEventListener('touchmove', (e) => {
        const currentY = e.touches[0].clientY;
        const diff = currentY - startY;
        
        if (diff > 0) { // 아래로 드래그만 허용
            bottomSheet.style.transform = `translateY(${startTransform + diff}px)`;
        }
    });
    
    dragHandle.addEventListener('touchend', () => {
        const transform = bottomSheet.style.transform;
        if (transform) {
            const currentY = parseInt(transform.replace('translateY(', '').replace('px)', ''));
            
            if (currentY > 100) { // 100px 이상 드래그하면 닫기
                closeBottomSheet();
            } else {
                bottomSheet.style.transform = '';
            }
        }
    });
    
    // 마우스 이벤트 (데스크톱 지원)
    dragHandle.addEventListener('mousedown', (e) => {
        startY = e.clientY;
        const transform = bottomSheet.style.transform;
        if (transform) {
            startTransform = parseInt(transform.replace('translateY(', '').replace('px)', ''));
        }
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    });
    
    function handleMouseMove(e) {
        const currentY = e.clientY;
        const diff = currentY - startY;
        
        if (diff > 0) { // 아래로 드래그만 허용
            bottomSheet.style.transform = `translateY(${startTransform + diff}px)`;
        }
    }
    
    function handleMouseUp() {
        const transform = bottomSheet.style.transform;
        if (transform) {
            const currentY = parseInt(transform.replace('translateY(', '').replace('px)', ''));
            
            if (currentY > 100) { // 100px 이상 드래그하면 닫기
                closeBottomSheet();
            } else {
                bottomSheet.style.transform = '';
            }
        }
        
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    }
}

function loadReviews(centerId) {
    // Fetch reviews from the server
    fetch(`/reviews/${centerId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('리뷰를 불러오는데 실패했습니다.');
            }
            return response.json();
        })
        .then(data => {
            const reviewsList = document.createElement('div');
            reviewsList.className = 'reviews-list';
            
            if (data.reviews && data.reviews.length > 0) {
                data.reviews.forEach(review => {
                    const reviewItem = document.createElement('div');
                    reviewItem.className = 'review-item';
                    reviewItem.innerHTML = `
                        <h3>${review.title}</h3>
                        <div class="review-meta">
                            <span>${review.author || '익명'}</span> • 
                            <span>${new Date(review.created_at).toLocaleDateString()}</span>
                        </div>
                        <div class="review-content">${review.content || review.summary || ''}</div>
                    `;
                    reviewsList.appendChild(reviewItem);
                });
            } else {
                reviewsList.innerHTML = '<p>아직 작성된 리뷰가 없습니다.</p>';
            }
            
            // Add reviews list after the review section
            const reviewSection = document.querySelector('.review-section');
            const existingReviewsList = reviewSection.querySelector('.reviews-list');
            
            if (existingReviewsList) {
                existingReviewsList.remove();
            }
            
            reviewSection.appendChild(reviewsList);
        })
        .catch(error => {
            console.error('Error loading reviews:', error);
            const reviewSection = document.querySelector('.review-section');
            const reviewsList = document.createElement('div');
            reviewsList.className = 'reviews-list';
            reviewsList.innerHTML = '<p>리뷰를 불러오는데 실패했습니다.</p>';
            reviewSection.appendChild(reviewsList);
        });
}

function showReviewForm() {
    const reviewSection = document.querySelector('.review-section');
    const reviewsList = reviewSection.querySelector('.reviews-list');
    
    // Hide reviews list temporarily
    if (reviewsList) {
        reviewsList.style.display = 'none';
    }
    
    reviewSection.innerHTML = `
        <h3>리뷰 작성</h3>
        <form class="review-form" onsubmit="submitReview(event)">
            <input type="text" name="title" placeholder="제목" required>
            <textarea name="content" placeholder="리뷰 내용" required></textarea>
            <button type="submit">제출하기</button>
            <button type="button" onclick="cancelReviewForm()">취소</button>
        </form>
    `;
}

function cancelReviewForm() {
    const reviewSection = document.querySelector('.review-section');
    const reviewsList = reviewSection.querySelector('.reviews-list');
    
    // Show reviews list again
    if (reviewsList) {
        reviewsList.style.display = 'block';
    }
    
    // Reset review section to original state
    reviewSection.innerHTML = `
        <h3>리뷰</h3>
        <button onclick="showReviewForm()">리뷰 작성하기</button>
    `;
    
    // Reload reviews
    loadReviews(currentCenterId);
}

function submitReview(event) {
    event.preventDefault();
    
    if (!currentCenterId) {
        alert('리뷰를 작성할 센터가 선택되지 않았습니다.');
        return;
    }
    
    const form = event.target;
    const title = form.querySelector('[name="title"]').value;
    const content = form.querySelector('[name="content"]').value;
    
    // Get CSRF token
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        alert('CSRF 토큰을 찾을 수 없습니다. 페이지를 새로고침하고 다시 시도해주세요.');
        return;
    }
    
    // Submit review to server
    fetch(`/reviews/${currentCenterId}/add/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            title: title,
            content: content
        })
    })
    .then(response => {
        // 응답이 JSON이 아닌 경우 처리
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // 응답이 HTML인 경우 (오류 페이지)
            return response.text().then(text => {
                console.error('서버 응답이 JSON이 아닙니다:', text.substring(0, 200) + '...');
                throw new Error('서버에서 JSON 응답을 반환하지 않았습니다. 로그인이 필요할 수 있습니다.');
            });
        }
        
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || '리뷰 제출에 실패했습니다.');
            });
        }
        
        return response.json();
    })
    .then(data => {
        alert('리뷰가 제출되었습니다.');
        // Reset review section to original state
        const reviewSection = document.querySelector('.review-section');
        reviewSection.innerHTML = `
            <h3>리뷰</h3>
            <button onclick="showReviewForm()">리뷰 작성하기</button>
        `;
        // Reload reviews
        loadReviews(currentCenterId);
    })
    .catch(error => {
        console.error('Error submitting review:', error);
        alert('리뷰 제출 중 오류가 발생했습니다: ' + error.message);
        
        // 오류 발생 시 리뷰 폼을 다시 표시
        const reviewSection = document.querySelector('.review-section');
        reviewSection.innerHTML = `
            <h3>리뷰 작성</h3>
            <form class="review-form" onsubmit="submitReview(event)">
                <input type="text" name="title" placeholder="제목" required>
                <textarea name="content" placeholder="리뷰 내용" required></textarea>
                <button type="submit">제출하기</button>
                <button type="button" onclick="cancelReviewForm()">취소</button>
            </form>
        `;
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

// 닫기 버튼 기능 추가
function closeBottomSheet() {
    const bottomSheet = document.getElementById('center-info-sheet');
    bottomSheet.classList.remove('active');
    bottomSheet.style.transform = '';
    currentCenterId = null; // 현재 선택된 센터 ID 초기화
}

// Initialize map when the page loads
document.addEventListener('DOMContentLoaded', initMap);