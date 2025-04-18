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