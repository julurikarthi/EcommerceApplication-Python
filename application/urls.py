from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.data_view, name='data_view'),
    path('createStore/', views.createStore, name='createStore'),
]
