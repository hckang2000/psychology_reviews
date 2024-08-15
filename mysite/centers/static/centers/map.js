console.log("Starting to load the map...");

var map = new naver.maps.Map('map', {
    center: new naver.maps.LatLng(37.5665, 126.9780),
    zoom: 10
});

console.log("Map loaded successfully.");

var centers = [
    // The centers data will be dynamically passed from Django
];

function loadCenters(centers, selectedCenterId = null) {
    centers.forEach(function (center) {
        var marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(center.lat, center.lng),
            map: map,
            title: center.name
        });

        naver.maps.Event.addListener(marker, 'click', function () {
            displayCenterInfo(center);
            displayCenterReviews(center.id);
        });

        if (selectedCenterId && center.id == selectedCenterId) {
            map.setCenter(new naver.maps.LatLng(center.lat, center.lng));
            displayCenterInfo(center);
            displayCenterReviews(center.id);
        }
    });
}

function displayCenterInfo(center) {
    var centerInfoDiv = document.getElementById('center-info');
    centerInfoDiv.innerHTML = `
        <div class="info-box">
            <h2>${center.name}</h2>
            <p><strong>Address:</strong> ${center.address}</p>
            <p><strong>Contact:</strong> ${center.contact}</p>
            <p><strong>Website:</strong> <a href="${center.url}" target="_blank">${center.url}</a></p>
            <p><strong>Operating Hours:</strong> ${center.operating_hours}</p>
            <p><strong>Description:</strong> ${center.description}</p>
        </div>
    `;
}

function displayCenterReviews(centerId) {
    fetch(`/reviews/${centerId}/`)
        .then(response => response.json())
        .then(data => {
            var reviewsDiv = document.getElementById('reviews');
            reviewsDiv.innerHTML = '';
            data.reviews.forEach(review => {
                var reviewDiv = document.createElement('div');
                reviewDiv.className = 'review';
                reviewDiv.innerHTML = `<h3>${review.title}</h3><p>${review.summary}</p><p><small>${review.date}</small></p>`;
                if (review.url) {
                    reviewDiv.innerHTML += `<a href="${review.url}" target="_blank">Read more</a>`;
                }
                reviewsDiv.appendChild(reviewDiv);
            });
        });
}

document.addEventListener('DOMContentLoaded', function () {
    var selectedCenterId = getQueryParam('center_id');  // Get the center_id from the URL
    loadCenters(centers, selectedCenterId);
});