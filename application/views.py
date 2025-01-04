from django.http import JsonResponse

def data_view(request):
    return JsonResponse({
        "message": "Hello, World!",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })
