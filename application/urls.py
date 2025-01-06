from django.urls import path
from . import views

urlpatterns = [
    path('data/', views.data_view, name='data_view'),
    path('view_logs/', views.view_logs, name='view_logs'),
]
