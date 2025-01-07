from django.http import JsonResponse, HttpResponseForbidden

def data_view(request):
    # Intentionally raise an error to simulate a crash
    raise ValueError("Simulated crash for log testing")
    return JsonResponse({
        "message": "start the project",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })
