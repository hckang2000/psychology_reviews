// Utility function to get query parameters from the URL
function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

console.log("Starting to load the map...");

var map;
var markers = [];
var currentCenterId = null; // 현재 선택된 센터 ID를 저장할 변수

function loadCenters(centersData) {
    console.log("Loading centers:", centersData);
    
    // Clear existing markers
    markers.forEach(marker => marker.setMap(null));
    markers = [];
    
    centersData.forEach(center => {
        const lat = parseFloat(center.lat);
        const lng = parseFloat(center.lng);
        
        if (isNaN(lat) || isNaN(lng)) {
            console.error("Invalid coordinates for center:", center);
            return;
        }
        
        console.log("Creating marker for center:", center.name, "at coordinates:", lat, lng);
        
        const marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(lat, lng),
            map: map
        });
        
        markers.push(marker);
        
        naver.maps.Event.addListener(marker, 'click', function() {
            console.log("Marker clicked for center:", center.name);
            showCenterDetails(center);
        });
    });
    
    // URL에서 center_id 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const centerId = urlParams.get('center_id');
    
    if (centerId) {
        console.log("Found center_id in URL:", centerId);
        const center = centersData.find(c => c.id === parseInt(centerId));
        if (center) {
            console.log("Found matching center:", center);
            showCenterDetails(center);
        } else {
            console.error("No matching center found for ID:", centerId);
        }
    }
}

function showCenterDetails(center) {
    console.log("Showing center details for:", center);
    
    // 현재 선택된 센터 ID 저장
    currentCenterId = center.id;
    
    // 지도 중심점 이동
    const lat = parseFloat(center.lat);
    const lng = parseFloat(center.lng);
    if (!isNaN(lat) && !isNaN(lng)) {
        const position = new naver.maps.LatLng(lat, lng);
        map.setCenter(position);
        map.setZoom(17);
    }
    
    // Bottom Sheet와 Overlay 표시
    const overlay = document.getElementById('overlay');
    const bottomSheet = document.getElementById('bottomSheet');
    
    if (overlay && bottomSheet) {
        overlay.classList.remove('hidden');
        bottomSheet.classList.remove('translate-y-full');
    }
    
    // 상담센터 정보 표시
    document.getElementById('centerName').textContent = center.name;
    document.getElementById('centerAddress').textContent = center.address;
    document.getElementById('centerPhone').textContent = center.phone;
    document.getElementById('centerDescription').textContent = center.description;
    
    // 상담사 카드 표시
    const therapistCards = document.getElementById('therapistCards');
    if (therapistCards) {
        therapistCards.innerHTML = '';
        if (center.therapists && center.therapists.length > 0) {
            center.therapists.forEach(therapist => {
                const card = document.createElement('div');
                card.className = 'swiper-slide';
                card.innerHTML = `
                    <div class="therapist-card">
                        <div class="flex flex-col items-center space-y-4">
                            <div class="therapist-photo">
                                ${therapist.photo ? 
                                    `<img src="${therapist.photo}" alt="${therapist.name}" class="w-full h-full object-cover">` :
                                    `<div class="w-full h-full flex items-center justify-center text-gray-400">No Photo</div>`
                                }
                            </div>
                            <div class="text-center">
                                <h4 class="font-medium text-lg">${therapist.name}</h4>
                                <p class="text-sm text-gray-600">경력 ${therapist.experience}년</p>
                                <p class="text-sm text-gray-600">${therapist.specialty || '전문 분야 정보 없음'}</p>
                            </div>
                        </div>
                    </div>
                `;
                therapistCards.appendChild(card);
            });
        } else {
            therapistCards.innerHTML = '<div class="text-center text-gray-500 py-4">등록된 상담사가 없습니다</div>';
        }
    }
    
    // 이미지 캐러셀 표시
    const imageCarousel = document.getElementById('imageCarousel');
    if (imageCarousel) {
        imageCarousel.innerHTML = '';
        if (center.images && center.images.length > 0) {
            center.images.forEach(image => {
                const slide = document.createElement('div');
                slide.className = 'swiper-slide';
                slide.innerHTML = `
                    <img src="${image}" alt="상담소 이미지" class="w-full h-48 object-cover rounded-lg">
                `;
                imageCarousel.appendChild(slide);
            });
        } else {
            imageCarousel.innerHTML = '<div class="text-center text-gray-500 py-4">등록된 이미지가 없습니다</div>';
        }
    }
    
    // 내부 리뷰 표시
    displayReviews(center.reviews || []);
    
    // 외부 리뷰 표시
    displayExternalReviews(center.external_reviews || []);
    
    // Swiper 초기화
    initializeSwipers();
    
    // 초기 탭 설정
    switchTab('info');
}

function displayReviews(reviews, page = 1) {
    const reviewsList = document.getElementById('reviewsList');
    const noReviews = document.getElementById('noReviews');
    const paginationContainer = document.getElementById('reviewsPagination');
    
    if (!reviewsList || !noReviews || !paginationContainer) return;
    
    if (!reviews || reviews.length === 0) {
        noReviews.classList.remove('hidden');
        reviewsList.innerHTML = '';
        paginationContainer.innerHTML = '';
        return;
    }
    
    noReviews.classList.add('hidden');
    
    // 페이지당 10개씩 표시
    const itemsPerPage = 10;
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageReviews = reviews.slice(startIndex, endIndex);
    
    // 리뷰 목록 표시
    reviewsList.innerHTML = pageReviews.map(review => `
        <div class="bg-white rounded-lg shadow p-4 space-y-2">
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="font-medium">${review.title}</h4>
                    <p class="text-sm text-gray-500">${review.author} • ${formatDate(review.created_at)}</p>
                </div>
                <div class="flex items-center text-yellow-400">
                    ${generateStars(review.rating)}
                </div>
            </div>
            <p class="text-gray-700">${review.content}</p>
        </div>
    `).join('');
    
    // 페이지네이션 버튼 생성
    const totalPages = Math.ceil(reviews.length / itemsPerPage);
    if (totalPages > 1) {
        let paginationHTML = '';
        
        // 이전 페이지 버튼
        if (page > 1) {
            paginationHTML += `
                <button onclick="displayReviews(${JSON.stringify(reviews)}, ${page - 1})" 
                        class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                    이전
                </button>`;
        }
        
        // 페이지 번호 버튼
        for (let i = 1; i <= totalPages; i++) {
            if (i === page) {
                paginationHTML += `
                    <button class="px-3 py-1 bg-blue-500 text-white rounded-lg" disabled>
                        ${i}
                    </button>`;
            } else {
                paginationHTML += `
                    <button onclick="displayReviews(${JSON.stringify(reviews)}, ${i})" 
                            class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                        ${i}
                    </button>`;
            }
        }
        
        // 다음 페이지 버튼
        if (page < totalPages) {
            paginationHTML += `
                <button onclick="displayReviews(${JSON.stringify(reviews)}, ${page + 1})" 
                        class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                    다음
                </button>`;
        }
        
        paginationContainer.innerHTML = paginationHTML;
    } else {
        paginationContainer.innerHTML = '';
    }
}

function displayExternalReviews(reviews, page = 1) {
    const externalReviewsList = document.getElementById('externalReviewsList');
    const noExternalReviews = document.getElementById('noExternalReviews');
    const paginationContainer = document.getElementById('externalReviewsPagination');
    
    if (!externalReviewsList || !noExternalReviews || !paginationContainer) {
        console.warn('External reviews DOM elements not found');
        return;
    }
    
    if (!reviews || reviews.length === 0) {
        noExternalReviews.classList.remove('hidden');
        externalReviewsList.innerHTML = '';
        paginationContainer.innerHTML = '';
        return;
    }
    
    noExternalReviews.classList.add('hidden');
    
    // 페이지당 10개씩 표시
    const itemsPerPage = 10;
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageReviews = reviews.slice(startIndex, endIndex);
    
    // 외부 리뷰 목록 표시
    externalReviewsList.innerHTML = pageReviews.map(review => `
        <div class="bg-white rounded-lg shadow p-4 space-y-2">
            <a href="${review.url}" target="_blank" rel="noopener noreferrer" 
               class="block hover:text-blue-600 transition-colors">
                <h4 class="font-medium">${review.title}</h4>
            </a>
            <p class="text-sm text-gray-700">${truncateText(review.summary, 200)}</p>
            <div class="flex justify-between items-center text-sm text-gray-500">
                <span>${review.source}</span>
                <span>${formatDate(review.created_at)}</span>
            </div>
        </div>
    `).join('');
    
    // 페이지네이션 버튼 생성
    const totalPages = Math.ceil(reviews.length / itemsPerPage);
    if (totalPages > 1) {
        let paginationHTML = '';
        
        // 이전 페이지 버튼
        if (page > 1) {
            paginationHTML += `
                <button onclick="displayExternalReviews(${JSON.stringify(reviews)}, ${page - 1})" 
                        class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                    이전
                </button>`;
        }
        
        // 페이지 번호 버튼
        for (let i = 1; i <= totalPages; i++) {
            if (i === page) {
                paginationHTML += `
                    <button class="px-3 py-1 bg-blue-500 text-white rounded-lg" disabled>
                        ${i}
                    </button>`;
            } else {
                paginationHTML += `
                    <button onclick="displayExternalReviews(${JSON.stringify(reviews)}, ${i})" 
                            class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                        ${i}
                    </button>`;
            }
        }
        
        // 다음 페이지 버튼
        if (page < totalPages) {
            paginationHTML += `
                <button onclick="displayExternalReviews(${JSON.stringify(reviews)}, ${page + 1})" 
                        class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                    다음
                </button>`;
        }
        
        paginationContainer.innerHTML = paginationHTML;
    } else {
        paginationContainer.innerHTML = '';
    }
}

// 유틸리티 함수들
function generateStars(rating) {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function initializeSwipers() {
    // 상담사 카드 Swiper
    new Swiper('.therapist-swiper-container', {
        slidesPerView: 'auto',
        spaceBetween: 16,
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        breakpoints: {
            320: { slidesPerView: 1.2 },
            640: { slidesPerView: 2.2 },
            1024: { slidesPerView: 3.2 }
        }
    });
    
    // 이미지 캐러셀 Swiper
    new Swiper('.image-carousel .swiper-container', {
        slidesPerView: 1,
        spaceBetween: 16,
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        }
    });
}

// 탭 전환 기능
function switchTab(tabName) {
    const tabs = ['info', 'internalReviews', 'externalReviews'];
    const buttons = tabs.map(tab => document.getElementById(`${tab}Tab`));
    const contents = tabs.map(tab => document.getElementById(`${tab}Content`));
    
    tabs.forEach((tab, index) => {
        if (tab === tabName) {
            buttons[index]?.classList.add('bg-blue-500', 'text-white');
            buttons[index]?.classList.remove('bg-gray-200', 'text-gray-700');
            contents[index]?.classList.remove('hidden');
        } else {
            buttons[index]?.classList.remove('bg-blue-500', 'text-white');
            buttons[index]?.classList.add('bg-gray-200', 'text-gray-700');
            contents[index]?.classList.add('hidden');
        }
    });
}

// 초기 탭 설정
document.addEventListener('DOMContentLoaded', () => {
    const infoTab = document.getElementById('infoTab');
    if (infoTab) {
        infoTab.click();
    }
});

function setupDragHandles() {
    const bottomSheet = document.getElementById('bottomSheet');
    const dragHandle = document.getElementById('dragHandle');
    const overlay = document.getElementById('overlay');
    
    if (!bottomSheet || !dragHandle || !overlay) {
        console.error('Required elements not found for drag functionality');
        return;
    }

    let startY = 0;
    let currentY = 0;
    let initialHeight = 0;
    let isDragging = false;
    
    // 드래그 관련 기본 동작 방지
    dragHandle.addEventListener('dragstart', (e) => e.preventDefault());
    dragHandle.addEventListener('drop', (e) => e.preventDefault());
    
    function handleStart(event) {
        if (event.button === 2) return; // 우클릭 방지
        
        isDragging = true;
        startY = event.type.includes('mouse') ? event.clientY : event.touches[0].clientY;
        initialHeight = bottomSheet.offsetHeight;
        
        // 드래그 시작시 트랜지션 제거
        bottomSheet.style.transition = 'none';
        
        // 이벤트 캡처링 사용
        if (event.type.includes('mouse')) {
            document.addEventListener('mousemove', handleMove, { capture: true });
            document.addEventListener('mouseup', handleEnd, { capture: true });
        } else {
            document.addEventListener('touchmove', handleMove, { capture: true, passive: false });
            document.addEventListener('touchend', handleEnd, { capture: true });
        }
        
        event.preventDefault();
        event.stopPropagation();
    }
    
    function handleMove(event) {
        if (!isDragging) return;
        
        event.preventDefault();
        event.stopPropagation();
        
        const clientY = event.type.includes('mouse') ? event.clientY : event.touches[0].clientY;
        currentY = clientY - startY;
        
        // 위로 드래그할 때는 최대 85vh까지만
        if (currentY < 0) {
            currentY = Math.max(currentY, -(window.innerHeight * 0.85 - initialHeight));
        }
        
        // RAF를 사용하여 성능 최적화
        requestAnimationFrame(() => {
            bottomSheet.style.transform = `translateY(${currentY}px)`;
        });
    }
    
    function handleEnd(event) {
        if (!isDragging) return;
        
        isDragging = false;
        
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        
        // 트랜지션 다시 추가
        bottomSheet.style.transition = 'transform 0.3s ease-out';
        
        // 150px 이상 아래로 드래그하면 닫기
        if (currentY > 150) {
            closeBottomSheet();
        } else {
            // 원래 위치로 돌아가기
            bottomSheet.style.transform = 'translateY(0)';
        }
        
        // 이벤트 리스너 제거
        document.removeEventListener('mousemove', handleMove, { capture: true });
        document.removeEventListener('touchmove', handleMove, { capture: true });
        document.removeEventListener('mouseup', handleEnd, { capture: true });
        document.removeEventListener('touchend', handleEnd, { capture: true });
    }
    
    // 이벤트 리스너 등록
    dragHandle.addEventListener('mousedown', handleStart, { passive: false });
    dragHandle.addEventListener('touchstart', handleStart, { passive: false });
    
    // 전역 이벤트 방지
    document.addEventListener('dragstart', (e) => {
        if (isDragging) e.preventDefault();
    }, { capture: true });
    
    document.addEventListener('selectstart', (e) => {
        if (isDragging) e.preventDefault();
    }, { capture: true });
}

function closeBottomSheet() {
    const bottomSheet = document.getElementById('bottomSheet');
    const overlay = document.getElementById('overlay');
    
    if (bottomSheet && overlay) {
        bottomSheet.classList.add('translate-y-full');
        overlay.classList.add('hidden');
    }
}

function openBottomSheet(center) {
    const bottomSheet = document.getElementById('bottomSheet');
    if (bottomSheet) {
        bottomSheet.classList.remove('translate-y-full');
        // 센터 정보 업데이트
        updateCenterInfo(center);
        // 리뷰 데이터 로드
        loadReviews(center.id);
    }
}

function updateCenterInfo(center) {
    const centerNameElement = document.getElementById('centerName');
    const centerAddressElement = document.getElementById('centerAddress');
    const centerPhoneElement = document.getElementById('centerPhone');
    
    if (centerNameElement) centerNameElement.textContent = center.name;
    if (centerAddressElement) centerAddressElement.textContent = center.address;
    if (centerPhoneElement) centerPhoneElement.textContent = center.phone;
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
    // Set current center ID
    currentCenterId = centerId;
    
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

// 리뷰 목록을 새로고침하는 함수
function refreshReviews(centerId) {
    fetch(`/reviews/${centerId}/`)
        .then(response => response.json())
        .then(data => {
            const reviewsList = document.getElementById('reviewsList');
            if (reviewsList && data.reviews) {
                reviewsList.innerHTML = data.reviews.map(review => `
                    <div class="bg-white rounded-lg shadow p-4 space-y-2">
                        <div class="flex justify-between items-start">
                            <div>
                                <h4 class="font-medium">${review.title}</h4>
                                <p class="text-sm text-gray-500">${review.author} • ${formatDate(review.created_at)}</p>
                            </div>
                            <div class="flex items-center text-yellow-400">
                                ${generateStars(review.rating)}
                            </div>
                        </div>
                        <p class="text-gray-700">${review.content}</p>
                    </div>
                `).join('');
                
                // "작성된 리뷰가 없습니다" 메시지 처리
                const noReviews = document.getElementById('noReviews');
                if (noReviews) {
                    if (data.reviews.length > 0) {
                        noReviews.classList.add('hidden');
                    } else {
                        noReviews.classList.remove('hidden');
                    }
                }
            }
        })
        .catch(error => {
            console.error('리뷰 목록 새로고침 실패:', error);
        });
}

function submitReview(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    if (!currentCenterId) {
        alert('리뷰를 작성할 상담소가 선택되지 않았습니다.');
        return;
    }
    
    const title = formData.get('title');
    const content = formData.get('content');
    const rating = formData.get('rating');
    
    if (!title || !content || !rating) {
        alert('제목, 내용, 평점을 모두 입력해주세요.');
        return;
    }
    
    fetch(`/reviews/${currentCenterId}/add/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            title: title,
            content: content,
            rating: parseInt(rating)
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || '리뷰 작성에 실패했습니다.');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('리뷰가 성공적으로 등록되었습니다.');
            closeReviewModal();
            
            // 내부리뷰 탭으로 전환
            switchTab('internalReviews');
            
            // 리뷰 목록 새로고침
            refreshReviews(currentCenterId);
        } else {
            throw new Error(data.error || '리뷰 작성에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('리뷰 제출 오류:', error);
        alert(error.message);
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

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded");
    
    // centersData 확인
    console.log("Raw Centers Data:", centersData);
    if (!Array.isArray(centersData)) {
        console.error("centersData is not an array!");
        return;
    }

    // URL에서 center_id 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const centerId = urlParams.get('center_id');
    console.log("Center ID from URL:", centerId);

    let initialLat = 37.5665;  // 기본 위도 (서울시청)
    let initialLng = 126.9780; // 기본 경도 (서울시청)
    let initialZoom = 13;      // 기본 줌 레벨

    // 선택된 센터가 있는 경우 해당 좌표로 설정
    if (centerId) {
        const centerIdNum = parseInt(centerId);
        console.log("Parsed Center ID:", centerIdNum);

        const center = centersData.find(c => c.id === centerIdNum);
        console.log("Found center:", center);
        
        if (center) {
            const lat = parseFloat(center.lat);
            const lng = parseFloat(center.lng);
            console.log("Parsed coordinates:", { lat, lng });
            
            if (!isNaN(lat) && !isNaN(lng)) {
                initialLat = lat;
                initialLng = lng;
                initialZoom = 15;
                console.log("Using center coordinates:", initialLat, initialLng);
            }
        }
    }

    // 네이버 지도 API가 로드되었는지 확인
    if (typeof naver === 'undefined' || typeof naver.maps === 'undefined') {
        console.error("Naver Maps API is not loaded yet!");
        // API가 로드될 때까지 대기
        const checkNaverMaps = setInterval(function() {
            if (typeof naver !== 'undefined' && typeof naver.maps !== 'undefined') {
                clearInterval(checkNaverMaps);
                initializeMap(initialLat, initialLng, initialZoom);
            }
        }, 100);
    } else {
        // API가 이미 로드된 경우 바로 초기화
        initializeMap(initialLat, initialLng, initialZoom);
    }
});

// 지도 초기화 함수
function initializeMap(initialLat, initialLng, initialZoom) {
    // 지도 초기화
    console.log("Initializing map with coordinates:", initialLat, initialLng);
    
    // 지도 컨테이너의 크기 설정
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }
    
    // 명시적으로 지도 컨테이너 크기 설정
    const headerHeight = 60;
    const windowHeight = window.innerHeight;
    mapContainer.style.height = `${windowHeight - headerHeight}px`;
    mapContainer.style.width = '100%';
    
    map = new naver.maps.Map(mapContainer, {
        center: new naver.maps.LatLng(initialLat, initialLng),
        zoom: initialZoom,
        scaleControl: false,
        mapDataControl: false,
        zoomControl: true,
        zoomControlOptions: {
            position: naver.maps.Position.RIGHT_CENTER
        }
    });

    // 윈도우 크기 변경 시 지도 크기 조정
    window.addEventListener('resize', function() {
        const newHeight = window.innerHeight - headerHeight;
        mapContainer.style.height = `${newHeight}px`;
        mapContainer.style.width = '100%';
        map.setSize(new naver.maps.Size(window.innerWidth, newHeight));
    });

    // 센터 데이터 로드
    loadCenters(centersData);

    // 선택된 센터가 있는 경우 상세 정보 표시
    const urlParams = new URLSearchParams(window.location.search);
    const centerId = urlParams.get('center_id');
    if (centerId) {
        const center = centersData.find(c => c.id === parseInt(centerId));
        if (center) {
            showCenterDetails(center);
        }
    }

    // 검색 폼 이벤트 리스너 설정
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const searchInput = document.getElementById('search-input');
            const searchTerm = searchInput.value.trim();
            if (searchTerm) {
                window.location.href = `/search/?q=${encodeURIComponent(searchTerm)}`;
            }
        });
    }
}

function goHome() {
    // 초기 지도 중심점과 줌 레벨로 이동
    map.setCenter(new naver.maps.LatLng(37.5665, 126.9780)); // 서울 시청 좌표
    map.setZoom(13);
    
    // 모든 마커 다시 표시
    loadCenters(centersData);
    
    // 바텀 시트 닫기
    const bottomSheet = document.querySelector('.bottom-sheet');
    if (bottomSheet) {
        bottomSheet.classList.remove('active');
    }
}

// 홈 버튼 이벤트 리스너
document.addEventListener('DOMContentLoaded', function() {
    const homeButton = document.getElementById('home-button');
    if (homeButton) {
        homeButton.addEventListener('click', goHome);
    }
});

// MindScanner 로고 클릭 이벤트 리스너
document.addEventListener('DOMContentLoaded', function() {
    const logo = document.querySelector('.logo');
    if (logo) {
        logo.addEventListener('click', function() {
            // 초기 지도 중심점과 줌 레벨로 이동
            map.setCenter(new naver.maps.LatLng(37.5665, 126.9780)); // 서울 시청 좌표
            map.setZoom(13);
            
            // 모든 마커 다시 표시
            loadCenters(centersData);
            
            // 바텀 시트 닫기
            const bottomSheet = document.querySelector('.bottom-sheet');
            if (bottomSheet) {
                bottomSheet.classList.remove('active');
            }
            
            // 검색 폼 초기화
            const searchForm = document.getElementById('search-form');
            if (searchForm) {
                searchForm.style.display = 'none';
            }
            
            // 검색 입력창 초기화
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = '';
            }
        });
    }
});

// 리뷰 모달 표시 함수
function showReviewModal() {
    const reviewModal = document.getElementById('reviewModal');
    if (reviewModal) {
        reviewModal.classList.remove('hidden');
        document.getElementById('reviewCenterId').value = currentCenterId;
        
        // 별점 버튼 이벤트 설정
        const starButtons = document.querySelectorAll('#starRating button');
        starButtons.forEach(button => {
            button.addEventListener('click', function() {
                const rating = this.dataset.rating;
                document.getElementById('rating').value = rating;
                
                // 별점 UI 업데이트
                starButtons.forEach(btn => {
                    const btnRating = btn.dataset.rating;
                    btn.textContent = btnRating <= rating ? '★' : '☆';
                });
            });
        });
    }
}

// 리뷰 모달 닫기 함수
function closeReviewModal() {
    const reviewModal = document.getElementById('reviewModal');
    if (reviewModal) {
        reviewModal.classList.add('hidden');
        // 폼 초기화
        document.getElementById('reviewForm').reset();
        // 별점 UI 초기화
        document.querySelectorAll('#starRating button').forEach(btn => {
            btn.textContent = '☆';
        });
    }
}