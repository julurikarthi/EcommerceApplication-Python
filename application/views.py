from django.http import JsonResponse, HttpResponseForbidden

def data_view(request):
    raise ValueError("Simulated crash for log testing")
    
