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

// 센터 유형에 따른 마커 아이콘 생성 함수
function getMarkerIcon(centerType) {
    let color = '#6B7280'; // 기본 회색 (gray-500)
    
    switch(centerType) {
        case 'counseling':
            color = '#3B82F6'; // 파란색 (blue-500)
            break;
        case 'clinic':
            color = '#10B981'; // 초록색 (green-500) 
            break;
        default:
            color = '#6B7280'; // 회색 (gray-500)
    }
    
    return {
        content: `
            <div style="
                background-color: ${color};
                width: 24px;
                height: 24px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                position: relative;
            "></div>
        `,
        size: new naver.maps.Size(30, 30),
        anchor: new naver.maps.Point(15, 15)
    };
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
                title: center.name,
                icon: getMarkerIcon(center.type)
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
    const reviewId = urlParams.get('review_id');
    
    if (centerId) {
        console.log("Found center_id in URL:", centerId);
        const center = centers.find(c => c.id === parseInt(centerId));
        if (center) {
            console.log("Found matching center:", center);
            showCenterDetails(center);
            
            // 리뷰 ID가 있는 경우 해당 리뷰를 modal로 표시
            if (reviewId) {
                setTimeout(() => {
                    showReviewDetail(parseInt(reviewId));
                }, 500); // bottom sheet가 열린 후 실행
            }
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
    
    // Type 배지 설정
    const typeBadge = document.getElementById('centerTypeBadge');
    
    console.log('center type:', center.type);
    console.log('typeBadge element:', typeBadge);
    
    if (typeBadge) {
        if (center.type === 'counseling') {
            typeBadge.textContent = '심리상담센터';
            typeBadge.className = 'inline-block px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded-full';
        } else if (center.type === 'clinic') {
            typeBadge.textContent = '정신건강의학과';
            typeBadge.className = 'inline-block px-3 py-1 text-sm font-medium text-white bg-green-500 rounded-full';
        } else {
            typeBadge.textContent = '미분류';
            typeBadge.className = 'inline-block px-3 py-1 text-sm font-medium text-white bg-gray-500 rounded-full';
        }
        console.log('Type badge set to:', typeBadge.textContent, typeBadge.className);
    } else {
        console.error('Type badge element not found');
    }
    
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
            // 내부리뷰 탭 전환 시 로딩 상태 표시 후 데이터 가져오기
            if (tab === 'internalReviews') {
                showReviewsLoading();
                fetchAndDisplayReviews(1);
            }
        } else {
            buttons[index]?.classList.remove('bg-blue-500', 'text-white');
            buttons[index]?.classList.add('bg-gray-200', 'text-gray-700');
            contents[index]?.classList.add('hidden');
        }
    });
}

// 리뷰 로딩 상태 표시 함수
function showReviewsLoading() {
    const reviewsList = document.getElementById('reviewsList');
    const noReviews = document.getElementById('noReviews');
    const paginationContainer = document.getElementById('reviewsPagination');
    
    if (reviewsList) {
        reviewsList.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span class="ml-3 text-gray-600">리뷰를 불러오는 중...</span>
            </div>
        `;
    }
    
    if (noReviews) {
        noReviews.classList.add('hidden');
    }
    
    if (paginationContainer) {
        paginationContainer.innerHTML = '';
    }
}

function fetchAndDisplayReviews(page) {
    console.log('fetchAndDisplayReviews 호출, currentCenterId:', currentCenterId, 'page:', page);
    
    // 페이지네이션 클릭 시에만 로딩 표시 (탭 전환 시에는 이미 표시됨)
    if (page > 1) {
        showReviewsLoading();
    }
    
    fetch(`/reviews/${currentCenterId}/?page=${page}`)
        .then(response => response.json())
        .then(data => {
            console.log('서버에서 받은 리뷰 데이터:', data); // 진단용
            displayReviews(data.reviews, page, data.pagination); // pagination도 전달
        })
        .catch(error => {
            console.error('리뷰 로딩 오류:', error);
            const reviewsList = document.getElementById('reviewsList');
            if (reviewsList) {
                reviewsList.innerHTML = `
                    <div class="text-center py-8 text-red-500">
                        <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                        <p>리뷰를 불러오는데 실패했습니다.</p>
                        <button onclick="fetchAndDisplayReviews(${page})" class="mt-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                            다시 시도
                        </button>
                    </div>
                `;
            }
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
        
        // 댓글 HTML 생성
        let commentsHtml = '';
        if (review.comments && review.comments.length > 0) {
            commentsHtml = `
                <div class="mt-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                    <div class="flex items-center mb-4">
                        <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center mr-3 shadow-sm">
                            <i class="fas fa-building text-white text-sm"></i>
                        </div>
                        <div class="flex items-center">
                            <span class="text-base font-semibold text-blue-800">센터 답변</span>
                            <div class="ml-2 px-2 py-1 bg-blue-200 text-blue-700 text-xs font-medium rounded-full">
                                공식
                            </div>
                        </div>
                    </div>
                    <div class="space-y-3">
                        ${review.comments.map(comment => `
                            <div class="bg-white rounded-lg p-4 shadow-sm border border-blue-150 relative">
                                <div class="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-blue-400 to-blue-600 rounded-l-lg"></div>
                                <div class="pl-3">
                                    <div class="flex justify-between items-start mb-3">
                                        <div class="flex items-center">
                                            <div class="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center mr-2">
                                                <i class="fas fa-user-tie text-blue-600 text-xs"></i>
                                            </div>
                                            <span class="text-sm font-medium text-gray-800">${comment.author}</span>
                                            <span class="text-xs text-gray-500 ml-2">${formatDate(comment.created_at)}</span>
                                            ${comment.updated_at ? `<span class="text-xs text-gray-400 ml-1">(수정됨)</span>` : ''}
                                        </div>
                                        <div class="flex items-center">
                                            <div class="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></div>
                                            <span class="text-xs text-green-600 font-medium">답변완료</span>
                                        </div>
                                    </div>
                                    <div class="bg-gray-50 rounded-lg p-3 border-l-4 border-blue-300">
                                        <p class="text-sm text-gray-700 leading-relaxed">${comment.content.replace(/\n/g, '<br>')}</p>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        return `
        <div class="bg-white rounded-lg shadow-md p-4 space-y-3 border border-gray-200 hover:shadow-lg transition-shadow duration-200">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-900 text-lg mb-1">${safeTitle}</h4>
                    <div class="flex items-center text-sm text-gray-500 mb-2">
                        <div class="w-5 h-5 bg-gray-400 rounded-full flex items-center justify-center mr-2">
                            <i class="fas fa-user text-white text-xs"></i>
                        </div>
                        <span class="mr-3">${review.author}</span>
                        <span class="text-gray-400">•</span>
                        <span class="ml-3">${formatDate(review.created_at)}</span>
                    </div>
                </div>
                <div class="flex items-center min-w-[140px] ml-4" style="min-width:140px;">
                    ${review.is_owner ? `
                        <button onclick="openEditReviewModal(${review.id}, '${safeTitle}', ${review.rating}, '${safeContent}')" 
                                class="text-gray-400 hover:text-blue-500 mr-2 p-1 rounded transition-colors" title="수정">
                            <i class="fas fa-edit text-sm"></i>
                        </button>
                        <button onclick="deleteReview(${review.id})" 
                                class="text-gray-400 hover:text-red-500 mr-3 p-1 rounded transition-colors" title="삭제">
                            <i class="fas fa-trash-alt text-sm"></i>
                        </button>
                    ` : ''}
                    <div class="flex items-center text-yellow-400 ml-auto">${generateStars(rating)}</div>
                </div>
            </div>
            <div class="bg-gray-50 rounded-lg p-3">
                <p class="text-gray-700 leading-relaxed">${safeContent}</p>
            </div>
            ${commentsHtml}
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
        
        // URL 파라미터가 있으면 제거 (재발생 방지)
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('center_id') || urlParams.has('review_id')) {
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
        
        // 세션 스토리지 정리
        sessionStorage.removeItem('selectedCenterId');
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
    // 센터 답변이 포함된 새로운 스타일로 리뷰 목록 새로고침
    fetchAndDisplayReviews(1);
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
            
            // 리뷰 목록 새로고침 - 센터 답변이 포함된 새로운 스타일 적용
            fetchAndDisplayReviews(1);
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
        
        // URL에서 center_id 파라미터 확인 (기존 기능 유지)
        const urlParams = new URLSearchParams(window.location.search);
        const centerId = urlParams.get('center_id');
        
        // 세션 스토리지에서 센터 ID 확인 (새로운 기능)
        const sessionCenterId = sessionStorage.getItem('selectedCenterId');
        
        let targetCenterId = centerId || sessionCenterId;
        
        if (targetCenterId) {
            const center = centersData.find(c => c.id === parseInt(targetCenterId));
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
        // URL 파라미터나 세션 스토리지에 센터 ID가 있는 경우에는 마커 재로딩 방지
        const urlParams = new URLSearchParams(window.location.search);
        const hasUrlCenterId = urlParams.has('center_id');
        const hasSessionCenterId = sessionStorage.getItem('selectedCenterId');
        
        // 파라미터가 없고 bottom sheet가 닫혀있을 때만 마커 업데이트
        const bottomSheet = document.getElementById('bottomSheet');
        const isBottomSheetClosed = !bottomSheet || bottomSheet.classList.contains('translate-y-full');
        
        if (!hasUrlCenterId && !hasSessionCenterId && isBottomSheetClosed && typeof centersData !== 'undefined') {
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
    const reviewId = urlParams.get('review_id');
    const sessionCenterId = sessionStorage.getItem('selectedCenterId');
    
    let targetCenterId = centerId || sessionCenterId;
    
    if (targetCenterId) {
        const center = centersData.find(c => c.id === parseInt(targetCenterId));
        if (center) {
            showCenterDetails(center);
            
            // 리뷰 ID가 있는 경우 해당 리뷰를 modal로 표시
            if (reviewId) {
                setTimeout(() => {
                    showReviewDetail(parseInt(reviewId));
                }, 500); // bottom sheet가 열린 후 실행
            }
            
            // 세션 스토리지와 URL 파라미터 정리
            if (sessionCenterId) {
                sessionStorage.removeItem('selectedCenterId');
            }
            if (centerId) {
                // URL에서 파라미터 제거 (뒤로 가기 시 재발생 방지)
                const newUrl = window.location.pathname;
                window.history.replaceState({}, document.title, newUrl);
            }
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

// 리뷰 상세보기 함수
function showReviewDetail(reviewId) {
    fetch(`/centers/api/review/${reviewId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const review = data.review;
                
                // 모달에 데이터 설정
                document.getElementById('reviewDetailTitle').textContent = review.title;
                document.getElementById('reviewDetailAuthor').textContent = review.author;
                document.getElementById('reviewDetailDate').textContent = formatDate(review.created_at);
                document.getElementById('reviewDetailContentText').textContent = review.content;
                document.getElementById('reviewDetailCenter').textContent = review.center_name;
                
                // 별점 표시
                const ratingContainer = document.getElementById('reviewDetailRating');
                ratingContainer.innerHTML = generateStars(review.rating);
                
                // 모달 표시
                document.getElementById('reviewDetailModal').classList.remove('hidden');
            } else {
                console.error('리뷰를 가져오는데 실패했습니다:', data.error);
            }
        })
        .catch(error => {
            console.error('리뷰 상세 정보 요청 중 오류 발생:', error);
        });
}

// 리뷰 상세보기 모달 닫기 함수
function closeReviewDetailModal() {
    document.getElementById('reviewDetailModal').classList.add('hidden');
}