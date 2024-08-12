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
    var map = new naver.maps.Map('map', {
        center: new naver.maps.LatLng(37.5665, 126.9780), // Default center
        zoom: 10
    });

    centers.forEach(function (center) {
        var marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(center.lat, center.lng),
            map: map,
            title: center.name
        });

        naver.maps.Event.addListener(marker, 'click', function () {
            displayCenterInfo(center);
        });

        // If the current center matches the selectedCenterId, trigger it
        if (selectedCenterId && center.id == selectedCenterId) {
            displayCenterInfo(center);
        }
    });
}

function displayCenterInfo(center) {
    // Display center information
    var centerInfoDiv = document.getElementById('center-info');
    centerInfoDiv.innerHTML = `
        <div class="info-box">
            <h2>${center.name}</h2>
            <p><strong>Address:</strong> ${center.address}</p>
            <p><strong>Contact:</strong> ${center.contact}</p>
            <p><strong>Website:</strong> <a href="${center.url}" target="_blank">${center.url}</a></p>
            <p><strong>Operating Hours:</strong> ${center.operating_hours}</p>
            <p><strong>Description:</strong> ${center.description}</p>
            ${center.isAuthenticated ? 
                '<button id="write-review-btn" class="btn">Write a Review</button>' :
                '<p><a href="/accounts/login/">Log in</a> to write a review.</p>'
            }
        </div>
    `;

    // Add event listener to the "Write a Review" button
    var writeReviewBtn = document.getElementById('write-review-btn');
    if (writeReviewBtn) {
        writeReviewBtn.addEventListener('click', function () {
            var formContainer = document.getElementById('review-form-container');
            formContainer.style.display = 'block';
            // Ensure that the review is for the correct center
            document.getElementById('review-form').action = `/reviews/${center.id}/add/`;
        });
    }

    // Load reviews for the selected center
    fetch(`/reviews/${center.id}/`)
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
    // Check if the write-review-btn exists before adding an event listener
    var writeReviewBtn = document.getElementById('write-review-btn');
    if (writeReviewBtn) {
        writeReviewBtn.addEventListener('click', function () {
            var formContainer = document.getElementById('review-form-container');
            if (formContainer.style.display === 'none') {
                formContainer.style.display = 'block';
            } else {
                formContainer.style.display = 'none';
            }
        });
    }
});