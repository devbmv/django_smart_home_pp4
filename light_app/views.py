import requests
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from .models import Room, Light, UserSettings
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings  # Importăm setările
from django.contrib.auth.decorators import login_required
from .forms import RoomForm, LightForm, UserSettingsForm, UserUpdateForm, UserSettings
from django.utils.translation import gettext as _
from home_control_project.settings import debug,home_online_status,API_PASSWORD
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import base64
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from time import sleep
import threading
from django.apps import AppConfig
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Variabile globale pentru controlul ping-ului
ping_active = True
home_online=False

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


@csrf_exempt
def check_server_status(request):
    if not hasattr(request.user, 'usersettings'):
        UserSettings.objects.create(user=request.user, api_password=API_PASSWORD, server_check_interval=request.user.usersettings.server_check_interval)

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        debug("No Authorization header received")
        return HttpResponse("Unauthorized", status=401)

    debug(f"Authorization header: {auth_header}")

    try:
        # Verificăm dacă tipul de autentificare este Basic
        auth_type, auth_string = auth_header.split(" ")
        if auth_type.lower() != "basic":
            debug("Invalid authorization type")
            return HttpResponse("Unauthorized", status=401)

        # Decodăm credentialele de autentificare
        decoded = base64.b64decode(auth_string).decode("utf-8")
        username, password = decoded.split(":")
        debug(f"Decoded username: {username}")

        # Autentificăm utilizatorul
        user = authenticate(username=username, password=password)
        if user is not None:
            debug(f"Authentication successful for user: {username}")
            request.user = user
        else:
            debug(f"Authentication failed for user: {username}")
            return HttpResponse("Unauthorized", status=401)
    except Exception as e:
        debug(f"Error during authentication: {str(e)}")
        return HttpResponse("Unauthorized", status=401)

    # Verificăm setările utilizatorului
    try:
        silence_mode = request.user.usersettings.silence_mode

        if request.user_ip:
            try:
                # Verificăm dacă ESP32 este online
                response = requests.get(f"http://{request.user_ip}", timeout=3)
                if response.ok:
                    debug(f"Esp is Online")
                else:
                    pass
                    debug(f"Response from ESP32 is not OK")
            except requests.RequestException as e:
                debug(f"Error contacting ESP32 server: {e}")
        else:
            pass
            debug("No ESP32 IP found in user settings.")
            debug(request.user_ip)

        # Pregătim răspunsul
        context = {

            "home_online":home_online_status[request.user.id],
            "silence_mode": silence_mode,
        }
        print(context["home_online"])
        # Răspuns final
        return JsonResponse(context)

    except Exception as e:
        #debug(f"Error retrieving user settings: {e}")
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
    print(home_online_status)
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
        #debug("No ESP32 IP configured for user.")
        return JsonResponse({"error": "ESP32 IP not configured for user"}, status=400)

    response_text = ""
    action = "off" if light.state == 1 else "on"

    if user_ip:

        try:
            try:
                #debug(f"Checking if ESP32 is online at IP: {user_ip}")
                response = requests.get(f"http://{request.user_ip}", timeout=50)
                if response.status_code == 200:
                    home_online = True
                    #debug(f"\nESP32 is online at IP: {user_ip}\n")
            except requests.exceptions.RequestException as e:
                home_online = False
                #debug("Esp Server Offline")
                response_text = f"Server offline: {e}"

            if home_online:
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
