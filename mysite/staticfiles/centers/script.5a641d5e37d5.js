// iOS Safari 뷰포트 높이 문제 해결 - 통합 버전
function setViewportHeight() {
    // 실제 뷰포트 높이 계산
    let vh = window.innerHeight * 0.01;
    // CSS 변수로 설정
    document.documentElement.style.setProperty('--vh', `${vh}px`);
    
    // iOS Safari 전용 추가 처리
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        // 주소창 숨김/표시 감지를 위한 추가 처리
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.style.height = `${window.innerHeight}px`;
        }
    }
}

// iOS 디바이스 감지
function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

// 뷰포트 높이 설정 초기화
setViewportHeight();

// 기본 이벤트 리스너
window.addEventListener('resize', setViewportHeight);
window.addEventListener('orientationchange', setViewportHeight);

// iOS Safari에서 추가 이벤트 리스너
if (isIOS()) {
    window.addEventListener('focusin', setViewportHeight);   // 키보드 올라올 때
    window.addEventListener('focusout', setViewportHeight);  // 키보드 내려갈 때
    window.addEventListener('scroll', setViewportHeight);    // 스크롤 할 때
    window.addEventListener('touchmove', setViewportHeight); // 터치 이동할 때
}

// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing sidebar');
    
    const sidebarToggle = document.querySelector('.hamburger-button');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    console.log('Elements found:', {
        sidebarToggle: !!sidebarToggle,
        sidebar: !!sidebar,
        overlay: !!overlay
    });
    
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
        document.body.classList.toggle('sidebar-open');
    }
    
    if (sidebarToggle && sidebar && overlay) {
        sidebarToggle.addEventListener('click', function(e) {
            console.log('Sidebar toggle clicked');
            e.preventDefault();
            e.stopPropagation();
            toggleSidebar();
        });
        
        overlay.addEventListener('click', function(e) {
            console.log('Overlay clicked');
            e.preventDefault();
            toggleSidebar();
        });
        
        // ESC 키를 눌렀을 때 사이드바 닫기
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('active')) {
                toggleSidebar();
            }
        });
    } else {
        console.error('Some sidebar elements are missing:', {
            sidebarToggle: !!sidebarToggle,
            sidebar: !!sidebar,
            overlay: !!overlay
        });
    }
    
    // 로딩 스피너 제어
    const loadingSpinner = document.querySelector('.loading-spinner');
    
    if (loadingSpinner) {
        // 페이지 로딩 완료
        window.addEventListener('load', () => {
            loadingSpinner.classList.remove('active');
        });

        // AJAX 요청 시 로딩 스피너 표시
        const originalFetch = window.fetch;
        window.fetch = function() {
            loadingSpinner.classList.add('active');
            return originalFetch.apply(this, arguments)
                .then(response => {
                    loadingSpinner.classList.remove('active');
                    return response;
                })
                .catch(error => {
                    loadingSpinner.classList.remove('active');
                    throw error;
                });
        };
    }
});

// 검색 관련 기능
document.addEventListener('DOMContentLoaded', function() {
    const searchToggleBtn = document.querySelector('.search-toggle-btn');
    const searchContainer = document.querySelector('.search-container');
    const searchCloseBtn = document.querySelector('.search-close-btn');
    const searchInput = document.querySelector('.search-input');

    // 검색창 토글 함수
    function toggleSearch() {
        searchContainer.classList.toggle('active');
        if (searchContainer.classList.contains('active')) {
            searchInput.focus();
        }
    }

    // 검색창 닫기 함수
    function closeSearch() {
        searchContainer.classList.remove('active');
        searchInput.value = ''; // 입력값 초기화
    }

    // 이벤트 리스너 등록
    if (searchToggleBtn) {
        searchToggleBtn.addEventListener('click', toggleSearch);
    }

    if (searchCloseBtn) {
        searchCloseBtn.addEventListener('click', closeSearch);
    }

    // ESC 키로 검색창 닫기
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && searchContainer.classList.contains('active')) {
            closeSearch();
        }
    });

    // 검색창 외부 클릭시 닫기
    document.addEventListener('click', function(e) {
        const isClickInside = searchContainer.contains(e.target) || 
                            searchToggleBtn.contains(e.target);
        
        if (!isClickInside && searchContainer.classList.contains('active')) {
            closeSearch();
        }
    });
}); 