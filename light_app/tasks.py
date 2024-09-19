import threading
from time import sleep
import requests
from home_control_project.settings import debug,home_online_status

from datetime import datetime  # Importăm modulul pentru a obține timpul curent
from .models import UserSettings

# Funcția pentru a obține timpul curent ca string
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Funcția care trimite ping-uri către ESP32
def send_ping_to_esp32(user_ip, check_interval, user_id):
    while True:
        try:
            # Trimitem un request GET către ESP32
            response = requests.get(f"http://{user_ip}", timeout=3)
            current_time = get_current_time()
            debug(f"[{current_time}] ESP32 status code: {response.status_code}")
            debug(f"[{current_time}] ESP32 response: {response.text}\n")

            # Setăm starea home_online la True dacă primim un răspuns de succes
            home_online_status[user_id] = True

        except requests.RequestException as e:
            current_time = get_current_time()
            # Verificăm dacă excepția conține un obiect response cu cod de status
            if e.response:
                error_code = e.response.status_code
                debug(f"[{current_time}] Error sending request to ESP32: HTTP Status Code {error_code}\n")
            else:
                # În caz de alte erori (ex. timeout), raportăm tipul erorii
                debug(f"[{current_time}] Error sending request to ESP32: {type(e).__name__}\n")
            
            # Dacă apare o eroare, setăm home_online la False
            home_online_status[user_id] = False

        # Așteptăm înainte de a trimite următoarea cerere
        sleep(check_interval)

# Funcția care pornește un thread pentru fiecare utilizator
def start_ping_for_user(user):
    try:
        settings = UserSettings.objects.get(user=user)
        user_ip = settings.m5core2_ip
        check_interval = settings.server_check_interval

        if user_ip:
            # Inițializăm starea home_online ca False pentru acest utilizator
            home_online_status[user.id] = False

            # Pornim un thread separat pentru a trimite ping-ul în mod continuu
            ping_thread = threading.Thread(
                target=send_ping_to_esp32, args=(user_ip, check_interval, user.id)
            )
            ping_thread.daemon = True  # Setăm daemon pentru a nu bloca la shutdown
            ping_thread.start()

            current_time = get_current_time()
            debug(f"[{current_time}] Started pinging ESP32 for user: {user.username} every {check_interval} seconds")
        else:
            current_time = get_current_time()
            debug(f"[{current_time}] No IP found for user: {user.username}. Cannot start pinging.")
    except UserSettings.DoesNotExist:
        current_time = get_current_time()
        debug(f"[{current_time}] UserSettings not found for user: {user.username}")

# Funcția care inițiază procesul de ping pentru toți utilizatorii
def start_ping_for_all_users():
    from django.contrib.auth.models import User
    users = User.objects.all()

    for user in users:
        start_ping_for_user(user)
