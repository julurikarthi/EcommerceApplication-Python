import os
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings

def data_view(request):
    return JsonResponse({
        "message": "Welcome to the world",
        "status": "success",
        "data": {"id": 1, "name": "Sample Item"}
    })

def view_logs(request):

    # Define log file paths
    log_files = {
        "nginx_error": "/var/log/nginx/error.log",
        "gunicorn_error": "/var/log/gunicorn-error.log",  # Adjust the path if necessary
        "django_debug": "/var/log/django/debug.log",  # Match your Django log config
    }

    logs_content = {}
    for name, path in log_files.items():
        if os.path.exists(path):
            with open(path, "r") as log_file:
                logs_content[name] = log_file.readlines()[-50:]  # Fetch the last 50 lines
        else:
            logs_content[name] = f"{path} does not exist."

    return JsonResponse(logs_content)
