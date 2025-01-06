from django.http import JsonResponse, HttpResponseForbidden

def data_view(request):
    return JsonResponse({
        "message": "start the project",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })