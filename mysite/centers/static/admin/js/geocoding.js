(function($) {
    $(document).ready(function() {
        var addressField = $('#id_address');
        var latField = $('#id_latitude');
        var lngField = $('#id_longitude');
        var statusDiv = $('<div class="geocoding-status" style="margin-top: 10px;"></div>');
        
        // 상태 메시지를 표시하는 div를 추가
        addressField.after(statusDiv);
        
        // 주소 입력 필드에 변경 이벤트 리스너 추가
        addressField.on('change', function() {
            var address = $(this).val();
            if (address) {
                statusDiv.html('<span style="color: #666;">주소 변환 중...</span>');
                
                // 네이버 지도 API를 사용하여 주소를 좌표로 변환
                $.ajax({
                    url: '/centers/api/geocode/',
                    method: 'POST',
                    data: JSON.stringify({ address: address }),
                    contentType: 'application/json',
                    headers: {
                        'X-CSRFToken': django.jsi18n.get_csrf_token()
                    },
                    success: function(response) {
                        if (response.latitude && response.longitude) {
                            latField.val(response.latitude);
                            lngField.val(response.longitude);
                            statusDiv.html('<span style="color: green;">✓ 주소가 성공적으로 변환되었습니다.</span>');
                        } else {
                            statusDiv.html('<span style="color: red;">주소를 찾을 수 없습니다.</span>');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('주소 변환 중 오류 발생:', error);
                        statusDiv.html('<span style="color: red;">주소 변환 중 오류가 발생했습니다.</span>');
                    }
                });
            }
        });
    });
})(django.jQuery); 