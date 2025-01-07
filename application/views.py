from django.http import JsonResponse, HttpResponseForbidden

def data_view(request):
    # Intentionally raise an error to simulate a crash
    return JsonResponse({
        "message": "start the project three",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })
