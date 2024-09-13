import threading
from django.apps import AppConfig
from time import sleep
import requests

class LightAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "light_app"

    def ready(self):
        # Creăm un eveniment pentru a controla ping-ul
        self.ping_event = threading.Event()
        
        # Setăm evenimentul pentru a permite ping-ul
        self.ping_event.set()

    def start_ping_to_esp32(self, user_ip):
        count = 0
        while self.ping_event.is_set():  # Verificăm dacă evenimentul este activ pentru a continua ping-urile
            try:
                # Trimitem un request GET către ESP32
                response = requests.get(f"http://{user_ip}", timeout=50)
                print(f"ESP32 status code: {response.status_code}")
                print(f"ESP32 response din apps: {response.text}\n")

                # Verificăm dacă ESP32 a trimis un răspuns valid și dacă conține textul așteptat
                if "You can stop sending pings" in response.text:
                    print("ESP32 received the IP. Stopping pings.\n")
                    self.ping_event.clear()  # Oprim ping-urile prin dezactivarea evenimentului
                else:
                    sleep(3)  # Așteptăm 3 secunde înainte de a trimite următorul ping

            except requests.RequestException as e:
                count += 1
                print(f"\n{count} Error sending request to ESP32: {str(e)}\n")
                sleep(5)  # În caz de eroare, așteptăm 5 secunde și încercăm din nou
