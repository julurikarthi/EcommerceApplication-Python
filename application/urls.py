from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('data/', views.data_view, name='data_view'),
    path('createStore/', views.createStore, name='createStore'),
    path('uploadImage/', views.uploadImage, name='uploadImage'),
]

if settings.DEBUG:  # This check ensures it only happens in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)