import os
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings

def data_view(request):
    return JsonResponse({
        "message": "Welcome to the world",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })