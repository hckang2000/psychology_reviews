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
    console.log("Initializing map...");
    map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(37.5665, 126.9780), // 서울 중심
        zoom: 13
    });
}

function loadCenters(centersData, selectedCenterId) {
    console.log("Loading centers:", centersData);
    
    // Clear existing markers
    markers.forEach(marker => marker.setMap(null));
    markers = [];

    // Add markers for each center
    centersData.forEach(center => {
        console.log("Adding marker for center:", center.name, center.lat, center.lng);
        
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
        if (selectedCenterId && center.id === selectedCenterId) {
            showCenterDetails(center);
        }
    });
}

function showCenterDetails(center) {
    const bottomSheet = document.getElementById('center-info-sheet');
    const overlay = document.getElementById('overlay');
    const centerDetails = document.querySelector('#center-info-sheet .bottom-sheet-content #center-details');
    
    if (!bottomSheet || !overlay || !centerDetails) {
        console.error('필요한 요소를 찾을 수 없습니다:', {
            bottomSheet: !!bottomSheet,
            overlay: !!overlay,
            centerDetails: !!centerDetails
        });
        return;
    }
    
    // 현재 선택된 센터 ID 저장
    currentCenterId = center.id;
    
    // Create HTML content for center details
    let content = `
        <div class="center-info">
            <h2>${center.name}</h2>
            <p><strong>주소:</strong> ${center.address}</p>
            <p><strong>연락처:</strong> ${center.phone || '정보 없음'}</p>
            <p><strong>설명:</strong> ${center.description || '정보 없음'}</p>
        </div>`;

    // Add image slider if there are images
    if (center.images && center.images.length > 0) {
        content += `
        <div class="swiper-container">
            <div class="swiper-wrapper">
                ${center.images.map(image => `
                    <div class="swiper-slide">
                        <img src="${image}" alt="상담소 이미지">
                    </div>
                `).join('')}
            </div>
            <div class="swiper-button-prev"></div>
            <div class="swiper-button-next"></div>
            <div class="swiper-pagination"></div>
        </div>`;
    }

    // Show overlay and bottom sheet immediately
    overlay.classList.add('show');
    bottomSheet.classList.add('show');

    // 로그인 상태 확인을 위해 서버에 요청
    fetch('/check-auth/')
        .then(response => response.json())
        .then(data => {
            // Add review section with authentication check
            const reviewSection = `
                <div class="review-section">
                    <h3>리뷰</h3>
                    <div id="review-form-container">
                        ${data.is_authenticated ? 
                            `<button onclick="showReviewForm('${center.id}')" class="review-button">리뷰 작성하기</button>` :
                            `<div class="login-message">
                                <span>리뷰를 작성하시려면</span>
                                <a href="/accounts/login/">로그인</a>
                                <span>해주세요</span>
                            </div>`
                        }
                    </div>
                    <div class="reviews-list"></div>
                </div>`;

            content += reviewSection;
            centerDetails.innerHTML = content;

            // Initialize Swiper if there are images
            if (center.images && center.images.length > 0) {
                new Swiper('.swiper-container', {
                    loop: true,
                    navigation: {
                        nextEl: '.swiper-button-next',
                        prevEl: '.swiper-button-prev',
                    },
                    pagination: {
                        el: '.swiper-pagination',
                        clickable: true
                    },
                    observer: true,
                    observeParents: true
                });
            }

            // Load reviews for this center
            loadReviews(center.id);

            // Setup drag handles
            setupDragHandles();
        })
        .catch(error => {
            console.error('인증 상태 확인 오류:', error);
            // 오류 발생 시 비로그인 상태로 처리
            const reviewSection = `
                <div class="review-section">
                    <h3>리뷰</h3>
                    <div id="review-form-container">
                        <div class="login-message">
                            <span>리뷰를 작성하시려면</span>
                            <a href="/accounts/login/">로그인</a>
                            <span>해주세요</span>
                        </div>
                    </div>
                    <div class="reviews-list"></div>
                </div>`;

            content += reviewSection;
            centerDetails.innerHTML = content;
            
            // Initialize Swiper if there are images
            if (center.images && center.images.length > 0) {
                new Swiper('.swiper-container', {
                    loop: true,
                    navigation: {
                        nextEl: '.swiper-button-next',
                        prevEl: '.swiper-button-prev',
                    },
                    pagination: {
                        el: '.swiper-pagination',
                        clickable: true
                    },
                    observer: true,
                    observeParents: true
                });
            }

            // Load reviews for this center
            loadReviews(center.id);

            // Setup drag handles
            setupDragHandles();
        });
}

function closeBottomSheet() {
    const bottomSheet = document.getElementById('center-info-sheet');
    const overlay = document.getElementById('overlay');
    
    // Hide bottom sheet and overlay with transition
    bottomSheet.classList.remove('show');
    overlay.classList.remove('show');
    
    // Reset transform
    bottomSheet.style.transform = '';
    
    currentCenterId = null;
}

function setupDragHandles() {
    const bottomSheet = document.getElementById('center-info-sheet');
    const dragHandle = document.querySelector('.drag-handle');
    const overlay = document.getElementById('overlay');
    
    if (!dragHandle) return;
    
    let startY;
    let startTransform = 0;

    // Handle overlay click
    overlay.addEventListener('click', closeBottomSheet);

    // Touch events
    dragHandle.addEventListener('touchstart', (e) => {
        startY = e.touches[0].clientY;
        const transform = bottomSheet.style.transform;
        if (transform) {
            startTransform = parseInt(transform.replace('translateY(', '').replace('px)', ''));
        }
        bottomSheet.style.transition = 'none';
    });
    
    dragHandle.addEventListener('touchmove', (e) => {
        const currentY = e.touches[0].clientY;
        const diff = currentY - startY;
        
        if (diff > 0) { // Only allow dragging down
            bottomSheet.style.transform = `translateY(${startTransform + diff}px)`;
        }
    });
    
    dragHandle.addEventListener('touchend', () => {
        bottomSheet.style.transition = 'transform 0.3s ease-in-out';
        const transform = bottomSheet.style.transform;
        if (transform) {
            const currentY = parseInt(transform.replace('translateY(', '').replace('px)', ''));
            
            if (currentY > 100) { // If dragged down more than 100px
                closeBottomSheet();
            } else {
                bottomSheet.style.transform = '';
            }
        }
    });

    // Mouse events (desktop support)
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
        
        if (diff > 0) { // Only allow dragging down
            bottomSheet.style.transform = `translateY(${startTransform + diff}px)`;
        }
    }
    
    function handleMouseUp() {
        const transform = bottomSheet.style.transform;
        if (transform) {
            const currentY = parseInt(transform.replace('translateY(', '').replace('px)', ''));
            
            if (currentY > 100) { // If dragged down more than 100px
                closeBottomSheet();
            } else {
                bottomSheet.style.transform = '';
            }
        }
        
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    }
}

function loadReviews(centerId, page = 1) {
    // Fetch reviews from the server
    fetch(`/reviews/${centerId}/?page=${page}`)
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
                            <span>${new Date(review.created_at).toLocaleDateString('ko-KR')}</span>
                        </div>
                        <div class="review-content">${review.content || review.summary || ''}</div>
                    `;
                    reviewsList.appendChild(reviewItem);
                });

                // 페이지네이션 UI 추가
                if (data.pagination.total_pages > 1) {
                    const paginationContainer = document.createElement('div');
                    paginationContainer.className = 'pagination-container';
                    
                    let paginationHTML = '<div class="pagination">';
                    
                    // 이전 페이지 버튼
                    if (data.pagination.has_previous) {
                        paginationHTML += `
                            <button onclick="loadReviews(${centerId}, ${data.pagination.previous_page})" 
                                    class="pagination-button">
                                이전
                            </button>`;
                    }
                    
                    // 페이지 번호들
                    for (let i = 1; i <= data.pagination.total_pages; i++) {
                        if (i === data.pagination.current_page) {
                            paginationHTML += `
                                <button class="pagination-button current" disabled>
                                    ${i}
                                </button>`;
                        } else {
                            paginationHTML += `
                                <button onclick="loadReviews(${centerId}, ${i})" 
                                        class="pagination-button">
                                    ${i}
                                </button>`;
                        }
                    }
                    
                    // 다음 페이지 버튼
                    if (data.pagination.has_next) {
                        paginationHTML += `
                            <button onclick="loadReviews(${centerId}, ${data.pagination.next_page})" 
                                    class="pagination-button">
                                다음
                            </button>`;
                    }
                    
                    paginationHTML += '</div>';
                    paginationContainer.innerHTML = paginationHTML;
                    reviewsList.appendChild(paginationContainer);
                }
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
            console.error('리뷰 로딩 오류:', error);
            const reviewSection = document.querySelector('.review-section');
            const reviewsList = document.createElement('div');
            reviewsList.className = 'reviews-list';
            reviewsList.innerHTML = '<p>리뷰를 불러오는데 실패했습니다.</p>';
            reviewSection.appendChild(reviewsList);
        });
}

function showReviewForm(centerId) {
    const reviewSection = document.querySelector('.review-section');
    const reviewsList = reviewSection.querySelector('.reviews-list');
    
    // Hide reviews list temporarily
    if (reviewsList) {
        reviewsList.style.display = 'none';
    }
    
    reviewSection.innerHTML = `
        <h3>리뷰 작성</h3>
        <form class="review-form" onsubmit="submitReview(event)">
            <input type="text" name="title" placeholder="제목을 입력해주세요" required>
            <textarea name="content" placeholder="리뷰 내용을 입력해주세요" required></textarea>
            <button type="submit">작성 완료</button>
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
        <div id="review-form-container">
            <button onclick="showReviewForm()" class="review-button">리뷰 작성하기</button>
        </div>
        <div class="reviews-list"></div>
    `;
    
    // Reload reviews
    loadReviews(currentCenterId);
}

function submitReview(event) {
    event.preventDefault();
    
    if (!currentCenterId) {
        alert('리뷰를 작성할 상담소가 선택되지 않았습니다.');
        return;
    }
    
    const form = event.target;
    const title = form.querySelector('[name="title"]').value;
    const content = form.querySelector('[name="content"]').value;
    
    // Get CSRF token
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        alert('보안 토큰을 찾을 수 없습니다. 페이지를 새로고침하고 다시 시도해주세요.');
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
            return response.text().then(text => {
                console.error('서버 응답 오류:', text.substring(0, 200) + '...');
                throw new Error('로그인이 필요하거나 서버에서 오류가 발생했습니다.');
            });
        }
        
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || '리뷰 작성에 실패했습니다.');
            });
        }
        
        return response.json();
    })
    .then(data => {
        alert('리뷰가 성공적으로 등록되었습니다.');
        // Reset review section to original state
        const reviewSection = document.querySelector('.review-section');
        reviewSection.innerHTML = `
            <h3>리뷰</h3>
            <div id="review-form-container">
                <button onclick="showReviewForm()">리뷰 작성하기</button>
            </div>
            <div class="reviews-list"></div>
        `;
        // Reload reviews
        loadReviews(currentCenterId);
    })
    .catch(error => {
        console.error('리뷰 제출 오류:', error);
        alert('리뷰 작성 중 오류가 발생했습니다: ' + error.message);
        
        // 오류 발생 시 리뷰 폼을 다시 표시
        const reviewSection = document.querySelector('.review-section');
        reviewSection.innerHTML = `
            <h3>리뷰 작성</h3>
            <form class="review-form" onsubmit="submitReview(event)">
                <input type="text" name="title" placeholder="제목을 입력해주세요" required>
                <textarea name="content" placeholder="리뷰 내용을 입력해주세요" required></textarea>
                <button type="submit">작성 완료</button>
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