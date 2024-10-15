from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Center, Review
from .forms import ReviewForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Q

def index(request):
    centers = Center.objects.all().prefetch_related('images')  # Prefetch images

    center_list = []
    for center in centers:
        center_data = {
            'id': center.id,
            'name': center.name,
            'lat': center.latitude,
            'lng': center.longitude,
            'address': center.address,
            'contact': center.contact,
            'url': center.url,
            'operating_hours': center.operating_hours,
            'description': center.description,
            'images': [image.image.url for image in center.images.all()],  # Image URLs
            'is_authenticated': request.user.is_authenticated
        }
        print(center.name, center.images.all())  # Debug: log the images for each center
        center_list.append(center_data)

    selected_center_id = request.GET.get('center_id')
    return render(request, 'index.html', {'centers': center_list, 'selected_center_id': selected_center_id})



def get_reviews(request, center_id):
    center = get_object_or_404(Center, pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-date')
    reviews_data = [
        {'title': review.title, 'summary': review.summary, 'date': review.date, 'url': review.url}
        for review in reviews
    ]
    return JsonResponse({'reviews': reviews_data})

def center_detail(request, center_id):
    center = Center.objects.get(pk=center_id)
    reviews = Review.objects.filter(center=center).order_by('-date')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')  # Redirect to login if user is not authenticated
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.center = center
            review.date = timezone.now()
            review.save()
            return redirect('center_detail', center_id=center_id)
    else:
        form = ReviewForm()

    # Pass the center images to the template
    center_images = center.images.all()

    return render(request, 'centers/center_detail.html', {
        'center': center,
        'reviews': reviews,
        'form': form,
        'center_images': center_images,  # Pass the images to the template
    })

    
@login_required
def add_review(request, center_id):
    center = Center.objects.get(pk=center_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.center = center
            review.date = timezone.now()
            review.url = ''  # Set default value for URL
            review.save()
            return redirect(f'/?center_id={center_id}')  # Redirect to index with center ID
    else:
        form = ReviewForm()
    return render(request, 'centers/center_detail.html', {'form': form, 'center': center})

def search(request):
    query = request.GET.get('q', '')
    if query:
        centers = Center.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(contact__icontains=query)
        )
    else:
        centers = Center.objects.none()

    return render(request, 'centers/search_results.html', {'centers': centers})