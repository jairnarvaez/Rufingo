from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from flashcards import views as flash_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('flashcards.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('logout/', flash_views.logout_view, name='logout'),

    path('service-worker.js', TemplateView.as_view(
        template_name='service-worker.js',
        content_type='application/javascript'
    ), name='service-worker'),
]
