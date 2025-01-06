from django.http import JsonResponse, HttpResponseForbidden

def data_view(request):
    return JsonResponse({
        "message": "Welcome to the world",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })