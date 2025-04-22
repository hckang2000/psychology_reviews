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