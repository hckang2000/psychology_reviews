// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing sidebar');
    
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const body = document.body;

    console.log('Elements found:', {
        sidebarToggle: !!sidebarToggle,
        sidebar: !!sidebar,
        overlay: !!overlay
    });

    function toggleSidebar() {
        console.log('Toggling sidebar');
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
        body.classList.toggle('sidebar-open');
    }

    if (sidebarToggle && sidebar && overlay) {
        sidebarToggle.addEventListener('click', function(e) {
            console.log('Sidebar toggle clicked');
            e.preventDefault();
            toggleSidebar();
        });

        overlay.addEventListener('click', function(e) {
            console.log('Overlay clicked');
            e.preventDefault();
            toggleSidebar();
        });
    } else {
        console.error('Some sidebar elements are missing:', {
            sidebarToggle: !!sidebarToggle,
            sidebar: !!sidebar,
            overlay: !!overlay
        });
    }

    // Close sidebar when pressing Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('active')) {
            console.log('Escape key pressed - closing sidebar');
            toggleSidebar();
        }
    });
}); 