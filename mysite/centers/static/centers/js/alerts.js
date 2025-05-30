/**
 * ==========================================================================
 * Alert Messages JavaScript
 * ==========================================================================
 */

class AlertManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // 알림 컨테이너 생성
        this.createContainer();
        
        // 페이지 로드 시 Django 메시지들 처리
        document.addEventListener('DOMContentLoaded', () => {
            this.processDjangoMessages();
            this.processExistingAlerts();
        });
    }

    createContainer() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'alert-container';
            document.body.appendChild(this.container);
        }
    }

    processDjangoMessages() {
        // 숨겨진 Django 메시지 컨테이너 찾기
        const djangoMessages = document.querySelector('.django-messages');
        
        if (djangoMessages) {
            const alerts = djangoMessages.querySelectorAll('.alert');
            
            alerts.forEach(alert => {
                const text = alert.textContent.trim();
                const classList = Array.from(alert.classList);
                
                // 메시지 타입 결정
                let type = 'info';
                if (classList.includes('alert-success')) type = 'success';
                else if (classList.includes('alert-error') || classList.includes('alert-danger')) type = 'error';
                else if (classList.includes('alert-warning')) type = 'warning';
                
                // 새로운 스타일로 표시
                this.show(text, type);
            });
            
            // 원본 메시지 컨테이너 제거
            djangoMessages.remove();
        }
    }

    convertExistingMessages() {
        // Django messages를 찾아서 새로운 스타일로 변환
        const existingMessages = document.querySelectorAll('.alert:not(.alert-container .alert)');
        
        existingMessages.forEach(message => {
            const text = message.textContent.trim();
            const classList = Array.from(message.classList);
            
            // 메시지 타입 결정
            let type = 'info';
            if (classList.includes('alert-success')) type = 'success';
            else if (classList.includes('alert-error') || classList.includes('alert-danger')) type = 'error';
            else if (classList.includes('alert-warning')) type = 'warning';
            
            // 기존 메시지 숨기기
            message.style.display = 'none';
            
            // 새로운 스타일로 표시
            this.show(text, type);
        });
    }

    processExistingAlerts() {
        // 페이지에 이미 있는 알림들에 자동 사라짐 기능 추가
        const alerts = this.container.querySelectorAll('.alert');
        alerts.forEach(alert => {
            this.addAutoHide(alert);
        });
    }

    show(message, type = 'info', duration = 5000) {
        this.createContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        
        alert.innerHTML = `
            <div class="alert-icon"></div>
            <div class="alert-content">${message}</div>
            <button class="alert-close" aria-label="닫기">&times;</button>
            <div class="alert-progress"></div>
        `;
        
        // 닫기 버튼 이벤트
        const closeBtn = alert.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            this.hide(alert);
        });
        
        // 컨테이너에 추가
        this.container.appendChild(alert);
        
        // 자동 숨김 설정
        this.addAutoHide(alert, duration);
        
        return alert;
    }

    addAutoHide(alert, duration = 5000) {
        // 진행률 바 애니메이션 시작
        const progressBar = alert.querySelector('.alert-progress');
        if (progressBar) {
            progressBar.style.animationDuration = `${duration}ms`;
        }
        
        // 자동 숨김 타이머
        const timer = setTimeout(() => {
            this.hide(alert);
        }, duration);
        
        // 마우스 호버 시 타이머 일시정지
        alert.addEventListener('mouseenter', () => {
            clearTimeout(timer);
            if (progressBar) {
                progressBar.style.animationPlayState = 'paused';
            }
        });
        
        // 마우스 떠날 때 타이머 재시작
        alert.addEventListener('mouseleave', () => {
            const remainingTime = this.getRemainingTime(progressBar);
            if (remainingTime > 0) {
                setTimeout(() => {
                    this.hide(alert);
                }, remainingTime);
                
                if (progressBar) {
                    progressBar.style.animationPlayState = 'running';
                }
            }
        });
    }

    getRemainingTime(progressBar) {
        if (!progressBar) return 0;
        
        const computedStyle = window.getComputedStyle(progressBar);
        const animationDuration = parseFloat(computedStyle.animationDuration) * 1000;
        const currentWidth = progressBar.offsetWidth;
        const totalWidth = progressBar.parentElement.offsetWidth;
        
        return (currentWidth / totalWidth) * animationDuration;
    }

    hide(alert) {
        alert.classList.add('fade-out');
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 300);
    }

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// 전역 인스턴스 생성
window.alertManager = new AlertManager();

// 편의 함수들
window.showAlert = (message, type, duration) => window.alertManager.show(message, type, duration);
window.showSuccess = (message, duration) => window.alertManager.success(message, duration);
window.showError = (message, duration) => window.alertManager.error(message, duration);
window.showWarning = (message, duration) => window.alertManager.warning(message, duration);
window.showInfo = (message, duration) => window.alertManager.info(message, duration);

// 폼 제출 관련 알림 처리
document.addEventListener('DOMContentLoaded', function() {
    // 폼 제출 시 로딩 상태 표시
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.textContent;
                submitBtn.textContent = '처리 중...';
                submitBtn.disabled = true;
                
                // 3초 후에도 응답이 없으면 버튼 복원 (안전장치)
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                    }
                }, 3000);
            }
        });
    });
}); 