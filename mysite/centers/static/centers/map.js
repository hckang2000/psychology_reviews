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
    console.log("displayCenterInfo called with center: ", center);
    var centerInfoDiv = document.getElementById('center-info');
    
    // Update HTML content directly without extra wrappers
    centerInfoDiv.innerHTML = `
        <div id="center-info-content">
            <h2>${center.name}</h2>
            <p><strong>Address:</strong> ${center.address}</p>
            <p><strong>Contact:</strong> ${center.contact}</p>
            <p><strong>Website:</strong> <a href="${center.url}" target="_blank">${center.url}</a></p>
            <p><strong>Operating Hours:</strong> ${center.operating_hours}</p>
            <p><strong>Description:</strong> ${center.description}</p>
        </div>
        ${center.isAuthenticated ? 
            '<button class="write-review-btn" onclick="showReviewForm()">Write a Review</button>' :
            '<p><a href="/accounts/login/">Log in</a> to write a review.</p>'
        }
    `;

    // Add event listener to the "Write a Review" button if present
    var writeReviewBtn = document.querySelector('.write-review-btn');
    if (writeReviewBtn) {
        writeReviewBtn.addEventListener('click', function () {
            var formContainer = document.getElementById('review-form-container');
            formContainer.style.display = 'block';
            // Ensure that the review is for the correct center
            document.getElementById('review-form').action = `/reviews/${center.id}/add/`;
        });
    }

    // Load reviews for the selected center
    displayCenterReviews(center.id);
}

function showReviewForm() {
    document.getElementById('review-form-container').style.display = 'block';
}

function displayCenterReviews(centerId) {
    fetch(`/reviews/${centerId}/`)
        .then(response => response.json())
        .then(data => {
            console.log("Reviews data: ", data);
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