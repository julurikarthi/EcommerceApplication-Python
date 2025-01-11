from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.data_view, name='data_view'),
    path('createDatabase/', views.createDatabase, name='create_database'),
]
