from django.urls import path, include
from django.contrib import admin
from application import views


urlpatterns = [
     path('data/', views.data_view, name='api-data'),
]



