import requests
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from .models import Room, Light, UserSettings
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings  # Importăm setările
from django.contrib.auth.decorators import login_required
from .forms import RoomForm, LightForm, UserSettingsForm, UserUpdateForm, UserSettings
from django.utils.translation import gettext as _
from home_control_project.settings import TEST_MODE
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import base64
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from time import sleep
import threading
from django.apps import AppConfig

# Variabile globale pentru controlul ping-ului
ping_active = False


import requests
from django.conf import settings
from time import sleep

# Global variable for controlling the ping status
ping_active = False


def ping_esp32(user):
    """
    Pings the ESP32 to check if it's online.

    Arguments:
    user -- The user whose ESP32 settings are used for pinging.

    This function stops pinging when it gets a successful response
    or after an error occurs.
    """
    global ping_active
    try:
        while ping_active:
            response = requests.get(
                f"http://{user.usersettings.m5core2_ip}", timeout=50
            )
            if settings.TEST_MODE:
                print(f"ESP32 response: {response.text}")

            if "You can stop sending pings" in response.text:
                ping_active = False
                if settings.TEST_MODE:
                    print("ESP32 received IP. Stopping pings.")
            else:
                sleep(5)
    except requests.RequestException as e:
        if settings.TEST_MODE:
            print(f"Error sending request to ESP32: {str(e)}")
    finally:
        ping_active = False


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt  # Dezactivează protecția CSRF pentru acest endpoint
def status_response_for_esp32(request):
    if request.method == "GET":
        # Verificăm dacă există un header de autorizare (Basic Authentication)

        auth_header = request.headers.get("Authorization")

        if auth_header:
            # Trimitem un răspuns simplu cu un mesaj de succes
            response_data = {
                "status": "success",
                "message": "ESP32 successfully connected to Django server",
            }
            return JsonResponse(response_data, status=200)

        else:
            # Dacă nu există un header de autorizare, răspundem cu 401 Unauthorized
            return JsonResponse({"error": "Unauthorized"}, status=401)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate
import base64
import requests
from django.conf import settings

@csrf_exempt
def check_server_status(request):
    """
    Verifies the status of the server by checking the IP
    and handling authentication.

    Returns JSON response with the server status or an error message.
    """
    django_server_ip = request.get_host()
    
    if settings.TEST_MODE:
        print(f"Django server IP: {django_server_ip}")

    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        if settings.TEST_MODE:
            print("No Authorization header received")
        return HttpResponse("Unauthorized", status=401)

    if settings.TEST_MODE:
        print(f"Authorization header: {auth_header}")

    try:
        auth_type, auth_string = auth_header.split(" ")
        if auth_type.lower() != "basic":
            if settings.TEST_MODE:
                print("Invalid authorization type")
            return HttpResponse("Unauthorized", status=401)

        decoded = base64.b64decode(auth_string).decode("utf-8")
        username, password = decoded.split(":")
        
        if settings.TEST_MODE:
            print(f"Decoded username: {username}")

        user = authenticate(username=username, password=password)
        if user is not None:
            request.user = user
        else:
            if settings.TEST_MODE:
                print(f"Authentication failed for user: {username}")
            return HttpResponse("Unauthorized", status=401)
    except Exception as e:
        if settings.TEST_MODE:
            print(f"Error during authentication: {str(e)}")
        return HttpResponse("Unauthorized", status=401)

    try:
        silence_mode = request.user.usersettings.silence_mode
        server_online = False
        
        if request.user_ip:
            try:
                response = requests.get(f"http://{request.user_ip}", timeout=3)
                server_online = response.ok
                if settings.TEST_MODE:
                    print("ESP32 is Online" if server_online else "Response not OK")
            except requests.RequestException as e:
                if settings.TEST_MODE:
                    print(f"Error contacting ESP32: {e}")
        else:
            if settings.TEST_MODE:
                print("No ESP32 IP found in user settings.")
        
        context = {
            "server_online": server_online,
            "silence_mode": silence_mode,
        }

        return JsonResponse(context)

    except Exception as e:
        if settings.TEST_MODE:
            print(f"Error retrieving user settings: {e}")
        return HttpResponse("User settings not found", status=404)


# =============================================================================


@login_required
def user_settings_view(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    form = UserSettingsForm(instance=user_settings)

    if request.method == "POST":
        form = UserSettingsForm(request.POST, instance=user_settings)

        # Actualizează setările utilizatorului și profilul fără obligativitatea de a schimba parola
        if form.is_valid():
            form.save()

            # Redirecționează către pagina principală după salvarea cu succes
            return redirect("home")

    return render(
        request,
        "light_app/user_settings.html",
        {
            "form": form,
        },
    )


def home(request):
    return render(request, "light_app/index.html")


# =============================================================================


@login_required
def room_list_view(request):
    rooms = Room.objects.filter(user=request.user).prefetch_related("lights").all()
    paginator = Paginator(rooms, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "room_list": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "page_obj": page_obj,
    }
    return render(request, "light_app/rooms_list.html", context)


# =============================================================================


def lights_status(request):
    lights_data = []
    rooms = Room.objects.all()
    for room in rooms:
        lights = room.lights.all()
        for light in lights:
            lights_data.append(
                {
                    "room": room.name,
                    "light": light.name,
                    "state": "on" if light.state == 1 else "off",
                }
            )
    return JsonResponse(lights_data, safe=False)


# =============================================================================


@login_required
def toggle_light(request, room_name, light_name):
    room = get_object_or_404(Room, name=room_name, user=request.user)
    light = get_object_or_404(Light, room=room, name=light_name)

    user_ip = request.user_ip
    if not user_ip or user_ip == "none":
        print("No ESP32 IP configured for user.")
        return JsonResponse({"error": "ESP32 IP not configured for user"}, status=400)

    response_text = ""
    action = "off" if light.state == 1 else "on"

    if user_ip:

        try:
            try:
                print(f"Checking if ESP32 is online at IP: {user_ip}")
                response = requests.get(f"http://{request.user_ip}", timeout=50)
                if response.status_code == 200:
                    server_online = True
                    print(f"\nESP32 is online at IP: {user_ip}\n")
            except requests.exceptions.RequestException as e:
                server_online = False
                print("Esp Server Offline")
                response_text = f"Server offline: {e}"

            if server_online:
                response = requests.get(
                    f"http://{request.user_ip}/control_led",
                    params={"room": room_name, "light": light_name, "action": action},
                    timeout=30,
                )
                if response.ok:
                    light.state = 1 if action == "on" else 2
                    light.save()
                    response_text = response.json()
                else:
                    response_text = "Failed to change light state on M5Core2 server."
        except Exception as e:
            response_text = f"Error: {e}"

    # Răspuns AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {"state": light.get_state_display(), "esp_response": response_text}
        )

    return redirect("room_list")


# =============================================================================


@login_required
def add_room(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.user = request.user
            room.save()
            return redirect("room_list")
    else:
        form = RoomForm()

    return render(request, "light_app/add_room.html", {"form": form})


# =============================================================================


@login_required
def add_light(request):
    if request.method == "POST":
        form = LightForm(request.POST, user=request.user)
        if form.is_valid():
            light = form.save(commit=False)
            light.save()
            return redirect("room_list")
    else:
        form = LightForm(user=request.user)

    return render(request, "light_app/add_light.html", {"form": form})


# =============================================================================


@login_required
def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id, user=request.user)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect("room_list")
    else:
        form = RoomForm(instance=room)

    return render(request, "light_app/edit_room.html", {"form": form, "room": room})


@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == "POST":
        room.delete()
        return redirect("room_list")

    return render(request, "light_app/delete_room.html", {"room": room})


# =============================================================================


@login_required
def edit_light(request, light_id):
    light = get_object_or_404(Light, id=light_id, room__user=request.user)
    if request.method == "POST":
        form = LightForm(request.POST, instance=light, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("room_list")
    else:
        form = LightForm(instance=light, user=request.user)

    return render(request, "light_app/edit_light.html", {"form": form, "light": light})


@login_required
def delete_light(request, light_id):
    light = get_object_or_404(Light, id=light_id)
    if request.method == "POST":
        light.delete()
        return redirect("room_list")

    return render(request, "light_app/delete_light.html", {"light": light})
