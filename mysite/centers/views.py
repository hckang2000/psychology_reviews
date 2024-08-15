from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Center, Review
from .forms import ReviewForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import datetime

def index(request):
    centers = Center.objects.all()
    return render(request, 'index.html', {'centers': centers})

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

    for review in reviews:
        if isinstance(review.date, str):
            review.date = datetime.strptime(review.date, '%Y-%m-%d').date()

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

    return render(request, 'centers/center_detail.html', {
        'center': center,
        'reviews': reviews,
        'form': form,
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
    query = request.GET.get('q')
    results = Center.objects.filter(name__icontains=query) if query else []
    return render(request, 'centers/search_results.html', {'results': results, 'query': query})