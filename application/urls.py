from django.urls import path
from . import views
from .views import ProductViewSet 
from rest_framework.routers import DefaultRouter
from django.urls import path, include 
from .views import HomeView
from .views import AddProductView
router = DefaultRouter()
router.register(r'', ProductViewSet, basename='product')


urlpatterns = [
    path('login', HomeView.as_view(), name='home'),
    path('addProduct', AddProductView.as_view(), name='add_product'),
    path('api/', include(router.urls)), 
]