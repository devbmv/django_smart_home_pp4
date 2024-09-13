from django.shortcuts import render
import requests  # Corectarea importului
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings


@csrf_exempt
def update_esp_firmware(request):
    context = {
        'user_ip': request.user_ip,  # Aici transmiți user_ip către template
    }
    return render(request, "firmware_manager/update.html",context)



@csrf_exempt
def upload_firmware(request):
    if request.method == "POST":
        firmware_file = request.FILES["firmware"]
        file_path = os.path.join(settings.MEDIA_ROOT, firmware_file.name)

        with open(file_path, "wb+") as destination:
            for chunk in firmware_file.chunks():
                destination.write(chunk)

        # Trimite fișierul la M5Core2
        with open(file_path, "rb") as f:
            url = f"http://{request.user_ip}/django_update_firmware"  # Adresa IP a ESP32
            response = requests.post(url, files={"firmware": f})

        if response.status_code == 200:
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Firmware uploaded to ESP32 successfully",
                }
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "Failed to upload firmware to ESP32"},
                status=500,
            )
    return HttpResponse(status=405)
