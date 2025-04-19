from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Custom login view
    path('logout/', LogoutView.as_view(next_page='centers:index'), name='logout'),
]