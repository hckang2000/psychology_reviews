// Utility function to get query parameters from the URL
function getQueryParam(param) {
    var urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

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
        console.log('Adding marker for center:', center.name); // Log each marker creation
        var marker = new naver.maps.Marker({
            position: new naver.maps.LatLng(center.lat, center.lng),
            map: map,
            title: center.name
        });

        naver.maps.Event.addListener(marker, 'click', function () {
            console.log('Marker clicked for:', center.name); // Log when the marker is clicked
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

function initSlider() {
    let currentSlideIndex = 0;
    const slides = document.querySelectorAll('.slide');

    if (slides.length === 0) {
        return;  // No slides to show, exit early
    }

    // Show the current slide
    function showSlide(index) {
        // Hide all slides
        slides.forEach((slide, i) => {
            slide.style.display = (i === index) ? 'block' : 'none';
        });
    }

    // Move the slider by a certain number of steps
    window.moveSlide = function(n) {
        currentSlideIndex = (currentSlideIndex + n + slides.length) % slides.length;
        showSlide(currentSlideIndex);
    };

    // Show the first slide
    showSlide(currentSlideIndex);
}


function displayCenterInfo(center) {
    console.log("Displaying center info for:", center.name);

    // Update HTML content for center-info
    var centerInfoDiv = document.getElementById('center-info');
    centerInfoDiv.innerHTML = `
        <div id="center-info-content">
            <!-- Image Slider Section -->
            <div id="image-slider" class="slider-container">
                <div class="slider-wrapper">
                    ${center.images.length > 0 
                        ? center.images.map(image => 
                            `<div class="slide">
                                <img src="${image}" alt="Facility image for ${center.name}">
                            </div>`).join('')
                        : '<p>No images available for this center.</p>'
                    }
                </div>
                <div class="slider-nav">
                    <button class="prev" onclick="moveSlide(-1)">&#10094;</button>
                    <button class="next" onclick="moveSlide(1)">&#10095;</button>
                </div>
            </div>

            <!-- Center Info Section -->
            <h2>${center.name}</h2>
            <p><strong>Address:</strong> ${center.address}</p>
            <p><strong>Contact:</strong> ${center.contact}</p>
            <p><strong>Website:</strong> <a href="${center.url}" target="_blank">${center.url}</a></p>
        </div>
        ${center.isAuthenticated ? 
            '<button class="write-review-btn" onclick="showReviewForm()">Write a Review</button>' :
            '<p><a href="/accounts/login/">Log in</a> to write a review.</p>'
        }
    `;

    // Initialize slider functionality after content is loaded
    initSlider();  // Initialize the slider for this center

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
    console.log("Selected Center ID:", selectedCenterId);
    loadCenters(centers, selectedCenterId);
});