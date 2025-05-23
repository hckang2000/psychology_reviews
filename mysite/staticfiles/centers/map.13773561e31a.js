// Utility function to get query parameters from the URL
function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

console.log("Starting to load the map...");

var map;
var markers = [];
var currentCenterId = null; // 현재 선택된 센터 ID를 저장할 변수

// 드래그 핸들 관련 변수들
let isDragging = false;
let startY = 0;
let startTranslateY = 0;

function getTranslateY(element) {
    const style = window.getComputedStyle(element);
    const matrix = new DOMMatrixReadOnly(style.transform);
    return matrix.m42;
}

function startDrag(event) {
    const bottomSheet = document.getElementById('bottomSheet');
    if (!bottomSheet) return;
    
    isDragging = true;
    startY = event.type.startsWith('touch') ? event.touches[0].clientY : event.clientY;
    startTranslateY = getTranslateY(bottomSheet) || 0;
    bottomSheet.style.transition = 'none';
    document.body.style.userSelect = 'none';

    if (event.type.startsWith('touch')) {
        document.addEventListener('touchmove', moveDrag, { passive: false });
        document.addEventListener('touchend', endDrag);
    } else {
        document.addEventListener('mousemove', moveDrag);
        document.addEventListener('mouseup', endDrag);
    }
}

function moveDrag(event) {
    if (!isDragging) return;
    event.preventDefault();
    
    const bottomSheet = document.getElementById('bottomSheet');
    if (!bottomSheet) return;
    
    const clientY = event.type.startsWith('touch') ? event.touches[0].clientY : event.clientY;
    const deltaY = clientY - startY;
    let nextY = startTranslateY + deltaY;
    
    // 위로는 -50px까지만, 아래로는 제한 없음
    if (nextY < -50) nextY = -50;
    bottomSheet.style.transform = `translateY(${nextY}px)`;
}

function endDrag(event) {
    if (!isDragging) return;
    isDragging = false;
    
    const bottomSheet = document.getElementById('bottomSheet');
    if (!bottomSheet) return;
    
    document.body.style.userSelect = '';
    bottomSheet.style.transition = 'transform 0.3s ease-out';

    const clientY = event.type.startsWith('touch') ? event.changedTouches[0].clientY : event.clientY;
    const deltaY = clientY - startY + startTranslateY;
    
    // 150px 이상 아래로 드래그하면 닫기
    if (deltaY > 150) {
        closeBottomSheet();
    } else {
        bottomSheet.style.transform = 'translateY(0)';
    }

    if (event.type.startsWith('touch')) {
        document.removeEventListener('touchmove', moveDrag);
        document.removeEventListener('touchend', endDrag);
    } else {
        document.removeEventListener('mousemove', moveDrag);
        document.removeEventListener('mouseup', endDrag);
    }
}

function setupDragHandles() {
    const dragHandle = document.getElementById('dragHandle');
    if (!dragHandle) {
        console.error('Drag handle element not found');
        return;
    }

    // 기존 이벤트 리스너 제거
    dragHandle.removeEventListener('mousedown', startDrag);
    dragHandle.removeEventListener('touchstart', startDrag);

    // 새로운 이벤트 리스너 추가
    dragHandle.addEventListener('mousedown', startDrag);
    dragHandle.addEventListener('touchstart', startDrag, { passive: false });
}

// DOM이 로드된 후 드래그 핸들 설정
document.addEventListener('DOMContentLoaded', function() {
    setupDragHandles();
});

// 거리 계산 함수 추가
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // 지구의 반경 (km)
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// 가까운 센터 10개 찾기
function findNearestCenters(centers, centerLat, centerLng, count = 10) {
    return centers
        .map(center => ({
            ...center,
            distance: calculateDistance(centerLat, centerLng, center.lat, center.lng)
        }))
        .sort((a, b) => a.distance - b.distance)
        .slice(0, count);
}

function loadCenters(centers) {
    if (!map) {
        console.error('Map is not initialized yet');
        return;
    }

    // 기존 마커 제거
    markers.forEach(marker => marker.setMap(null));
    markers = [];
    
    // 지도의 현재 중심점 가져오기
    const center = map.getCenter();
    const centerLat = center.y;
    const centerLng = center.x;
    
    // 가까운 센터 10개 찾기
    const nearestCenters = findNearestCenters(centers, centerLat, centerLng);
    
    // 각 센터에 대한 마커 생성
    nearestCenters.forEach(center => {
        try {
            // 필수 데이터 검증
            if (!center.id || !center.name || !center.lat || !center.lng) {
                console.warn(`Invalid center data: ${JSON.stringify(center)}`);
                return;
            }

            // 마커 생성
            const marker = new naver.maps.Marker({
                position: new naver.maps.LatLng(center.lat, center.lng),
                map: map,
                title: center.name
            });

            // 마커 클릭 이벤트
            naver.maps.Event.addListener(marker, 'click', function() {
                showCenterDetails(center);
            });

            markers.push(marker);
        } catch (error) {
            console.error(`Error creating marker for center ${center.id}:`, error);
        }
    });
    
    // URL에서 center_id 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const centerId = urlParams.get('center_id');
    
    if (centerId) {
        console.log("Found center_id in URL:", centerId);
        const center = centers.find(c => c.id === parseInt(centerId));
        if (center) {
            console.log("Found matching center:", center);
            showCenterDetails(center);
        } else {
            console.error("No matching center found for ID:", centerId);
        }
    }
}

function createTherapistCard(therapist) {
    const card = document.createElement('div');
    card.className = 'swiper-slide';
    card.innerHTML = `
        <div class="therapist-card">
            <div class="therapist-photo">
                ${therapist.photo ? 
                    `<img src="${therapist.photo}" alt="${therapist.name}" class="w-full h-full object-cover">` :
                    `<div class="w-full h-full flex items-center justify-center bg-gray-200 text-gray-500">
                        <span>사진 없음</span>
                    </div>`
                }
            </div>
            <div class="therapist-info">
                <h4 class="therapist-name">${therapist.name}</h4>
                <p class="therapist-experience">경력 ${therapist.experience}년</p>
                <p class="therapist-specialty">${therapist.specialty || '전문 분야 정보 없음'}</p>
                <div class="therapist-description hidden">${therapist.description || ''}</div>
            </div>
        </div>
    `;
    
    // 카드 클릭 이벤트 리스너 추가
    const therapistCard = card.querySelector('.therapist-card');
    therapistCard.addEventListener('click', () => {
        showTherapistModal({
            photo: therapist.photo || '',
            name: therapist.name,
            experience: therapist.experience,
            specialty: therapist.specialty || '전문 분야 정보 없음',
            description: therapist.description || ''
        });
    });
    
    return card;
}

function updateTherapistCards(therapists) {
    const therapistCards = document.getElementById('therapistCards');
    if (therapistCards) {
        therapistCards.innerHTML = '';
        if (therapists && therapists.length > 0) {
            therapists.forEach(therapist => {
                const card = createTherapistCard(therapist);
                therapistCards.appendChild(card);
            });
        } else {
            therapistCards.innerHTML = '<div class="text-center text-gray-500 py-4">등록된 상담사가 없습니다</div>';
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
    
    // 설명 텍스트에서 이스케이프된 따옴표를 원래 따옴표로 변환
    const description = center.description
        .replace(/\\"/g, '"')  // \" 를 " 로 변환
        .replace(/\\'/g, "'")  // \' 를 ' 로 변환
        .replace(/\\\\/g, "\\");  // \\ 를 \ 로 변환
    document.getElementById('centerDescription').textContent = description;
    
    // 상담사 카드 업데이트
    updateTherapistCards(center.therapists);
    
    // Swiper 초기화
    if (window.therapistSwiper) {
        window.therapistSwiper.update();
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
    
    // 내부 리뷰 표시 (항상 서버에서 첫 페이지 fetch)
    fetchAndDisplayReviews(1);
    
    // 외부 리뷰 표시
    displayExternalReviews(center.external_reviews || []);
    
    // Swiper 초기화
    initializeSwipers();
    
    // 초기 탭 설정
    switchTab('info');
}

function fetchAndDisplayReviews(page) {
    console.log('fetchAndDisplayReviews 호출, currentCenterId:', currentCenterId, 'page:', page);
    fetch(`/reviews/${currentCenterId}/?page=${page}`)
        .then(response => response.json())
        .then(data => {
            console.log('서버에서 받은 리뷰 데이터:', data); // 진단용
            displayReviews(data.reviews, page, data.pagination); // pagination도 전달
        })
        .catch(error => {
            alert('리뷰를 불러오는데 실패했습니다.');
        });
}

function displayReviews(reviews, page = 1, pagination = null) {
    console.log('displayReviews 호출, reviews:', reviews);
    const reviewsList = document.getElementById('reviewsList');
    const noReviews = document.getElementById('noReviews');
    const paginationContainer = document.getElementById('reviewsPagination');
    
    if (!reviewsList || !noReviews || !paginationContainer) return;
    
    if (!reviews || reviews.length === 0) {
        console.log('displayReviews: reviews가 비어있음. reviews:', reviews); // 진단용
        noReviews.classList.remove('hidden');
        reviewsList.innerHTML = '';
        paginationContainer.innerHTML = '';
        return;
    }
    
    noReviews.classList.add('hidden');
    
    const pageReviews = reviews;
    
    // 리뷰 목록 표시
    reviewsList.innerHTML = pageReviews.map(review => {
        const rating = (review.rating !== undefined && review.rating !== null) ? Number(review.rating) : 5;
        const safeTitle = String(review.title).replace(/'/g, "&#39;");
        const safeContent = String(review.content).replace(/'/g, "&#39;");
        return `
        <div class="bg-white rounded-lg shadow p-4 space-y-2">
            <div class="flex justify-between items-start">
                <div>
                        <h4 class="font-medium">${safeTitle}</h4>
                    <p class="text-sm text-gray-500">${review.author} • ${formatDate(review.created_at)}</p>
                </div>
                    <div class="flex items-center min-w-[120px] ml-4" style="min-width:120px;">
                        ${review.is_owner ? `
                            <button onclick="openEditReviewModal(${review.id}, '${safeTitle}', ${review.rating}, '${safeContent}')" class="text-gray-500 hover:text-blue-500 mr-2" title="수정">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button onclick="deleteReview(${review.id})" class="text-gray-500 hover:text-red-500 mr-2" title="삭제">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        ` : ''}
                        <span class="flex items-center text-yellow-400 ml-auto">${generateStars(rating)}</span>
                </div>
            </div>
                <p class="text-gray-700">${safeContent}</p>
        </div>
        `;
    }).join('');
    
    // 페이지네이션 버튼 생성 (pagination 정보 활용)
    if (pagination && pagination.total_pages > 1) {
        let paginationHTML = '';
        if (pagination.has_previous) {
            paginationHTML += `
                <button onclick="fetchAndDisplayReviews(${pagination.previous_page})" 
                        class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                    이전
                </button>`;
        }
        for (let i = 1; i <= pagination.total_pages; i++) {
            if (i === pagination.current_page) {
                paginationHTML += `
                    <button class="px-3 py-1 bg-blue-500 text-white rounded-lg" disabled>
                        ${i}
                    </button>`;
            } else {
                paginationHTML += `
                    <button onclick="fetchAndDisplayReviews(${i})" 
                            class="px-3 py-1 bg-gray-200 rounded-lg hover:bg-gray-300">
                        ${i}
                    </button>`;
            }
        }
        if (pagination.has_next) {
            paginationHTML += `
                <button onclick="fetchAndDisplayReviews(${pagination.next_page})" 
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
    rating = Number(rating) || 0;
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= rating) {
            stars += '<span class="text-yellow-400">★</span>';
        } else {
            stars += '<span class="text-gray-300">☆</span>';
        }
    }
    return stars;
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
            // 내부리뷰 탭 전환 시 항상 서버에서 최신 리뷰 목록을 받아와서 렌더링
            if (tab === 'internalReviews') {
                fetchAndDisplayReviews(1);
            }
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

function closeBottomSheet() {
    const bottomSheet = document.getElementById('bottomSheet');
    const overlay = document.getElementById('overlay');
    if (bottomSheet && overlay) {
        bottomSheet.classList.add('translate-y-full');
        bottomSheet.style.transform = '';
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
                reviewsList.innerHTML = data.reviews.map(review => {
                    // rating이 undefined/null이면 5점으로 fallback (임시)
                    const rating = (review.rating !== undefined && review.rating !== null) ? Number(review.rating) : 5;
                    return `
                    <div class="bg-white rounded-lg shadow p-4 space-y-2">
                        <div class="flex justify-between items-start">
                            <div>
                                <h4 class="font-medium">${review.title}</h4>
                                <p class="text-sm text-gray-500">${review.author} • ${formatDate(review.created_at)}</p>
                            </div>
                            <div class="flex items-center text-yellow-400">
                                    ${generateStars(rating)}
                            </div>
                        </div>
                        <p class="text-gray-700">${review.content}</p>
                    </div>
                    `;
                }).join('');
                
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

function showReviewModal() {
    const reviewModal = document.getElementById('reviewModal');
    if (reviewModal) {
        reviewModal.classList.remove('hidden');
        document.getElementById('reviewCenterId').value = currentCenterId;
        document.getElementById('rating').value = 5; // 기본값 5점

        // 별점 버튼 새로 생성 및 이벤트 리스너 fresh하게 등록
        const starRatingDiv = document.getElementById('starRating');
        starRatingDiv.innerHTML = '';
        for (let i = 1; i <= 5; i++) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'text-2xl';
            btn.dataset.rating = i;
            btn.textContent = '★';
            btn.addEventListener('click', function() {
                document.getElementById('rating').value = i;
                // 별점 UI 업데이트
                Array.from(starRatingDiv.children).forEach((starBtn, idx) => {
                    starBtn.textContent = idx < i ? '★' : '☆';
                });
            });
            starRatingDiv.appendChild(btn);
        }
    }
}

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

function submitReview(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const rating = formData.get('rating');
    if (!rating) {
        alert('평점을 선택해주세요.');
        return;
    }
    
    if (!currentCenterId) {
        alert('리뷰를 작성할 상담소가 선택되지 않았습니다.');
        return;
    }
    
    const title = formData.get('title');
    const content = formData.get('content');
    
    if (!title || !content) {
        alert('제목과 내용을 모두 입력해주세요.');
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
            fetch(`/reviews/${currentCenterId}/`)
                .then(response => response.json())
                .then(data => {
                    const reviewsList = document.getElementById('reviewsList');
                    if (reviewsList && data.reviews) {
                        reviewsList.innerHTML = data.reviews.map(review => {
                            // rating이 undefined/null이면 5점으로 fallback (임시)
                            const rating = (review.rating !== undefined && review.rating !== null) ? Number(review.rating) : 5;
                            return `
                                <div class="bg-white rounded-lg shadow p-4 space-y-2">
                                    <div class="flex justify-between items-start">
                                        <div>
                                            <h4 class="font-medium">${review.title}</h4>
                                            <p class="text-sm text-gray-500">${review.author} • ${formatDate(review.created_at)}</p>
                                        </div>
                                        <div class="flex items-center text-yellow-400">
                                            ${generateStars(rating)}
                                        </div>
                                    </div>
                                    <p class="text-gray-700">${review.content}</p>
                                </div>
                            `;
                        }).join('');
                        
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

    // 별점 버튼 이벤트 리스너 최초 1회만 등록
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
});

// 현재 위치 가져오기 함수
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by your browser'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
            },
            (error) => {
                console.warn('위치 정보를 가져오는데 실패했습니다:', error.message);
                // 위치 정보 가져오기 실패 시 서울시청 좌표 반환
                resolve({
                    lat: 37.5665,
                    lng: 126.9780
                });
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    });
}

// 지도 초기화 함수 수정
async function initializeMap(initialLat, initialLng, initialZoom) {
    console.log("Initializing map...");
    
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

    try {
        // 현재 위치 가져오기
        const currentLocation = await getCurrentLocation();
        console.log("Current location:", currentLocation);
        
        // URL에서 center_id 파라미터가 있는 경우 해당 센터의 좌표 사용
        const urlParams = new URLSearchParams(window.location.search);
        const centerId = urlParams.get('center_id');
        
        if (centerId) {
            const center = centersData.find(c => c.id === parseInt(centerId));
            if (center) {
                initialLat = parseFloat(center.lat);
                initialLng = parseFloat(center.lng);
                initialZoom = 15;
            }
        } else {
            // center_id가 없는 경우 현재 위치 사용
            initialLat = currentLocation.lat;
            initialLng = currentLocation.lng;
            initialZoom = 15;
        }
    } catch (error) {
        console.warn('위치 정보를 가져오는데 실패했습니다:', error);
        // 실패 시 기본값(서울시청) 사용
        initialLat = 37.5665;
        initialLng = 126.9780;
        initialZoom = 13;
    }
    
    // 지도 초기화
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

    // 지도 이벤트 리스너 추가
    naver.maps.Event.addListener(map, 'idle', function() {
        // 지도 이동이나 확대/축소가 끝났을 때 마커 업데이트
        if (typeof centersData !== 'undefined') {
            loadCenters(centersData);
        }
    });

    // 센터 데이터 로드
    if (typeof centersData !== 'undefined') {
        loadCenters(centersData);
    }

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