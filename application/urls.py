from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.data_view, name='data_view'),
    path('createStore/', views.createStore, name='createStore'),
    path('uploadImage/', views.uploadImage, name='uploadImage'),
    path('downloadImage/', views.downloadImage, name='downloadImage'),
    path('createUser/', views.create_user, name='create_user'),
]