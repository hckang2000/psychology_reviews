from django.contrib import admin
from .models import Center, Review, Therapist, CenterImage

# Inline for managing images within the Center admin
class CenterImageInline(admin.TabularInline):
    model = CenterImage
    extra = 1  # Number of extra blank image forms to show
    fields = ['image']  # Only show the image field

class TherapistInline(admin.TabularInline):
    model = Therapist
    extra = 1  # Number of extra blank therapist forms to show

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'contact', 'url', 'operating_hours')
    search_fields = ('name', 'address')
    inlines = [TherapistInline, CenterImageInline]  # Display therapists and images inline

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('center', 'title', 'date')
    search_fields = ('center__name', 'title')
    list_filter = ('center', 'date')

@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ('name', 'center', 'experience', 'specialty')
    search_fields = ('name', 'specialty')
    list_filter = ('center', 'specialty')

@admin.register(CenterImage)
class CenterImageAdmin(admin.ModelAdmin):
    list_display = ('center', 'image')  # Display center and image in list view
