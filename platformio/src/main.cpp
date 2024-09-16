#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <WiFiClientSecure.h>
#include <base64.h>    // Base64 library for encoding
#include <M5Unified.h> // M5Core2 support
#include <mbedtls/md.h>
#include <mbedtls/sha1.h>
#include <map>
#include <SPIFFS.h>
#include <Update.h>
#include <WebSocketsServer.h>
#include <mbedtls/entropy.h>
#include <mbedtls/ctr_drbg.h>
#include <esp_task_wdt.h>

//============================================================================

struct Light;

struct Room;

std::map<String, Room> roomLightMap;

//============================================================================
mbedtls_entropy_context entropy;
mbedtls_ctr_drbg_context ctr_drbg;

#define M5CORE2
#ifdef M5CORE2
#include <M5Unified.h>
M5GFX &lcd = M5.Lcd;
#endif

// Wi-Fi credentials and server URLs
AsyncWebServer server(80);
// WebSocketsServer webSocket = WebSocketsServer(81);

String base64Encode(String str);
void addBasicAuth(HTTPClient &http);
void reconnectWiFi();
void debug(String msg, uint16_t col, uint16_t row);
void checkServerStatus();
void fetchInitialLightStates();
void printLightStates();
void serverSetup();
void displayIP();
void processSerialCommands();
// void sendWebSocketMessage(String message);
void sendMessage(String data);
void initializeSystem();
void runMainLoop();
void debug(String msg, uint16_t col, uint16_t row);
void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length);
void detectIPHandler(AsyncWebServerRequest *request);
WiFiClient client;
uint16_t serverCheckInterval = 3000; // Interval to check the server status
bool localServer = true;             // Variable that determines if using local or Heroku server

String ssid = WIFI_SSID;                 // Modifiable variable for WiFi SSID
String password = WIFI_PASSWORD;         // Modifiable variable for WiFi password
String djangoUserName = DJANGO_USERNAME; // Modifiable variable for Django username
String djangoPassword = DJANGO_PASSWORD; // Modifiable variable for Django password
unsigned long lastSendTime = 0;          // Variabilă pentru a reține timpul ultimei trimiteri
uint16_t setup_debug_time = 1000;
uint16_t loop_debug_time = 10000;
String clientIPAddress = "";
bool checkServer = true;
bool djangoOnline = false;
// String serverCheckUrl = "http://192.168.1.16:8000/check-server-status/";
// String lightStatusUrl = "http://192.168.1.16:8000/lights_status/";
// String serialPostUrl = "http://192.168.1.16:8000/esp/serial_data/"; /tring serverCheckUrl = "http://192.168.1.16:8000/check-server-status/";

String serverCheckUrl = "";
String lightStatusUrl = "";
String serialPostUrl = ""; // Endpoint for posting serial data
//============================================================================

void init_rng()
{
    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);

    const char *personalization = "ssl_rng";
    int ret = mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy,
                                    (const unsigned char *)personalization, strlen(personalization));

    if (ret != 0)
    {
        Serial.println("Failed to initialize RNG.");
    }
    else
    {
        Serial.println("RNG initialized.");
    }
}

void monitorHeap(String tag)
{
    debug(String("Free heap memory:" + String(ESP.getFreeHeap()) + " bytes\n"), 0, 150);
}

File certFile;
void spiffsInit()
{
    if (!SPIFFS.begin(true))
    {
        Serial.println("An error has occurred while mounting SPIFFS");
        return;
    }
    else
    {
        Serial.println("SPIFFS mounted successfully");
    }

    // Example: List all files in SPIFFS
    File root = SPIFFS.open("/");
    File file = root.openNextFile();
    while (file)
    {
        Serial.print("FILE: ");
        Serial.println(file.name());
        file = root.openNextFile();
    }

    // Open certificate file
    certFile = SPIFFS.open("/cert.pem", "r");
    if (!certFile)
    {
        Serial.println("Failed to open cert.pem");
        return;
    }
    else
    {
        Serial.printf("Cert file opened successfully, size: %d bytes\n", certFile.size());
    }
}

void setup()
{
    init_rng();
    initializeSystem(); // Inițializare sistem
}

//============================================================================

void loop()
{
    runMainLoop();
}

//============================================================================

void initializeSystem()
{
#ifdef M5CORE2
    auto cfg = M5.config();
    M5.begin(cfg);
    M5.Display.setTextSize(2);
    M5.Display.setCursor(0, 0);
    M5.Display.fillScreen(BLACK); // Clear the screen
#endif
    monitorHeap("Begin Setup");
    Serial.begin(115200);
    if (djangoUserName.isEmpty() || djangoPassword.isEmpty())
    {
        debug("Django credentials are missing.", 0, 0);
        delay(setup_debug_time);
    }
    else
    {
        Serial.println("Django credentials are present.");
        debug("Django credentials are present.", 0, 0);
        debug("Django Username: " + djangoUserName, 0, 0);
        debug("Django Password: " + djangoPassword, 0, 20);
        delay(setup_debug_time);
    }

    reconnectWiFi();
    serverSetup();
    delay(setup_debug_time);
    displayIP();
    delay(setup_debug_time);
    fetchInitialLightStates();
    delay(setup_debug_time);
    // webSocket.begin();
    // webSocket.onEvent(webSocketEvent); // Funcția de gestiune a evenimentelor WebSocket
    delay(setup_debug_time);
    if (clientIPAddress.isEmpty())
    {
        delay(5000);
    }
#ifdef M5CORE2
    M5.Display.setTextSize(2);
    M5.Display.setCursor(0, 0);
    M5.Display.fillScreen(BLACK); // Clear the screen
#endif
}

//============================================================================

void runMainLoop()
{

    // webSocket.loop(); // Handle WebSocket events
    static uint32_t serverTimer;
    if (millis() - serverTimer > loop_debug_time)
    {
        if (checkServer)
        {
            checkServerStatus();
        }
        // processSerialCommands(); // Continuously process serial commands
        // sendWebSocketMessage("Hello from ESP32!");
        serverTimer = millis();
    }
}

//============================================================================

// Structures to hold light information dynamically
struct Light
{
    String name;
    bool state;
};

//============================================================================

struct Room
{
    String state;
    std::vector<Light> lights;
};

//============================================================================

// void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length)
// {
//     switch (type)
//     {
//     case WStype_DISCONNECTED:
//         Serial.printf("[%u] Disconnected!\n", num);
//         break;
//     case WStype_CONNECTED:
//         Serial.printf("[%u] Connected from %s\n", num, webSocket.remoteIP(num).toString().c_str());
//         break;
//     case WStype_TEXT:
//         Serial.printf("[%u] Text: %s\n", num, payload);
//         webSocket.sendTXT(num, "Message received!");
//         break;
//     }
// }

//============================================================================

void sendMessage(String data)
{
    debug("Starting HTTP POST request to server...", 0, 220);

    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        if (!serverCheckUrl.startsWith("http"))
        {
            debug("Invalid server URL", 0, 220);
            return;
        }

        // WiFiClientSecure client; // Sau WiFiClientSecure, dacă folosești SSL
        http.begin(serialPostUrl);

        http.setTimeout(30000); // Setează timeout-ul pentru HTTP

        http.addHeader("Content-Type", "application/json");

        String payload = "{\"data\": \"" + data + "\"}";
        int httpResponseCode = http.POST(payload);
        if (httpResponseCode == -1)
        {
            debug("Error: Failed to connect to the server.", 0, 220);
        }

        if (httpResponseCode > 0)
        {
            String response = http.getString();
            Serial.println("Răspunsul serverului: " + response);
        }
        else
        {
            Serial.println("Eroare la trimiterea POST: " + String(httpResponseCode));
            if (httpResponseCode >= 400 && httpResponseCode < 500)
            {
                Serial.println("Client error. Please check your request.");
            }
            else if (httpResponseCode >= 500)
            {
                debug("Server error. Please try again later.", 0, 220);
            }
        }

        http.end(); // Încheie conexiunea
    }
    else
    {
        debug("I am  try to reconnect to Wi-Fi in fun sendMessage", 0, 220);
        reconnectWiFi();
    }
}

//============================================================================
void processSerialCommands()
{
    if (Serial.available() > 0)
    {
        String input = Serial.readStringUntil('\n');
        input.trim();
        sendMessage(input);
        // sendWebSocketMessage(input);

        if (input.startsWith("set "))
        {
            if (input.startsWith("set ssid "))
            {
                ssid = input.substring(9);
            }
            else if (input.startsWith("set password "))
            {
                password = input.substring(13);
            }
            else if (input.startsWith("set username "))
            {
                djangoUserName = input.substring(13);
            }
            else if (input.startsWith("set djangoPassword "))
            {
                djangoPassword = input.substring(17);
            }
            else if (input.startsWith("set interval "))
            {
                loop_debug_time = input.substring(13).toInt();
            }
            // Setăm URL pentru verificarea serverului
            else if (input.startsWith("set url_check "))
            {
                serverCheckUrl = input.substring(14); // Scoate partea "set url_check "
                Serial.println("Server check URL updated to: " + serverCheckUrl);
            }
            // Setăm URL pentru starea luminilor
            else if (input.startsWith("set url_light "))
            {
                lightStatusUrl = input.substring(14); // Scoate partea "set url_light "
                Serial.println("Light status URL updated to: " + lightStatusUrl);
            }
            // Setăm URL pentru trimiterea de date seriale
            else if (input.startsWith("set url_serial "))
            {
                serialPostUrl = input.substring(15); // Scoate partea "set url_serial "
                Serial.println("Serial data post URL updated to: " + serialPostUrl);
            }
            else
            {
                Serial.println("Unknown command: " + input);
            }
            Serial.println("Settings updated.");
        }
        else if (input == "!local")
        {
            localServer = !localServer;
            Serial.println("Local server: " + String(localServer));
        }
        else if (input == "!check")
        {
            checkServer = !checkServer;
            Serial.println("Check server is: " + String(checkServer ? "ON" : "OFF"));
        }
        else
        {
            Serial.println("Unknown command: " + input);
        }
    }
}

//============================================================================

// Function to add Basic Authentication header to each HTTP request
void addBasicAuth(HTTPClient &http)
{
    if (djangoUserName.isEmpty() || djangoPassword.isEmpty())
    {
        debug("Username or password for django is missing.", 0, 180);
        return;
    }
    String auth = base64Encode(djangoUserName + ":" + djangoPassword);
    debug(String("Auth urlcode = " + auth), 0, 180);
    http.addHeader("Authorization", "Basic " + auth);
}

//============================================================================
bool isLocalServer(const String &ipAddress)
{
    // Verificăm dacă adresa IP este locală (192.168.x.x, 10.x.x.x sau 127.0.0.1)
    return ipAddress.startsWith("192.168") || ipAddress.startsWith("10.") || ipAddress == "127.0.0.1";
}

void checkServerStatus()
{
    static String message = "";

    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;

        // Creăm un obiect local HTTPClient

        // Verificăm dacă URL-ul este valid
        if (!serverCheckUrl.startsWith("http"))
        {
            if (!clientIPAddress.isEmpty())
            {
                // Verificăm dacă este un server local sau Heroku pe baza adresei IP
                if (isLocalServer(clientIPAddress))
                {
                    // Dacă serverul este local, adăugăm portul 8000
                    serverCheckUrl = "http://" + clientIPAddress + ":8000/status_response_for_esp32/";
                    message = "ServerCheckUrl auto-setat pentru serverul local la: " + serverCheckUrl;
                }
                else
                {
                    // Dacă este pe Heroku, folosim URL-ul fără port (Heroku folosește port implicit pentru HTTPS)
                    serverCheckUrl = "https://" + clientIPAddress + "/status_response_for_esp32/";
                    message = "ServerCheckUrl auto-setat pentru Heroku la: " + serverCheckUrl;
                }
            }
            else
            {
                message = "Django IP is not detected!";
                debug(message, 0, 0);
                return;
            }
            debug(message, 0, 0);
        }
        Serial.println("send request to URL: " + serverCheckUrl);
        http.begin(serverCheckUrl);
        addBasicAuth(http);    // Adaugăm Basic Authentication
        http.setTimeout(5000); // Setăm timeout-ul pentru HTTP

        int httpResponseCode = http.GET();

        if (httpResponseCode >= 200 && httpResponseCode < 300)
        {
            Serial.println("Success! Server response:");
            Serial.println(http.getString());
            djangoOnline = true;
        }
        else if (httpResponseCode == -1)
        {
            // Afișează eroarea de conexiune
            Serial.println("Connection failed. Check WiFi, server address, or firewall.");
            djangoOnline = false;
        }
        else if (httpResponseCode >= 300 && httpResponseCode < 400)
        {
            Serial.printf("Redirection error: %d\n", httpResponseCode);
            Serial.println("Server is trying to redirect.");
            debug("Django is Offline", 0, 180);
            djangoOnline = false;
        }
        else if (httpResponseCode >= 400 && httpResponseCode < 500)
        {
            Serial.printf("Client error: %d\n", httpResponseCode);
            Serial.println("Possible authentication or request issue.");
            Serial.println(http.getString());
            debug("Django is Offline", 0, 180);
            djangoOnline = false;
        }
        else if (httpResponseCode >= 500)
        {
            Serial.printf("Server error: %d\n", httpResponseCode);
            Serial.println("Server might be down or there is an internal error.");
            Serial.println(http.getString());
            djangoOnline = false;
        }
        else
        {
            Serial.printf("Unexpected error: %d\n", httpResponseCode);
            djangoOnline = false;
        }
        http.end(); // Încheie conexiunea
    }
    else
    {
        debug("WiFi not connected.", 0, 180);
        djangoOnline = false;
        reconnectWiFi();
        delay(500);
    }
    debug(String(djangoOnline ? "Django Online" : "Django Offline"), 100, 120);
}

//============================================================================
void fetchInitialLightStates()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        // Creăm un obiect local HTTPClient
        HTTPClient http;

        // Verificăm dacă URL-ul este valid
        if (!lightStatusUrl.startsWith("http"))
        {
            debug("Invalid lightStatusUrl format!", 0, 20);
            return;
        }

        http.begin(lightStatusUrl);
        addBasicAuth(http);

        int httpResponseCode = http.GET();
        if (httpResponseCode == 200)
        {
            String payload = http.getString();
            if (ESP.getMaxAllocHeap() < 500)
            {
                Serial.println("Low memory: Unable to allocate space for JSON parsing.");
                debug("Invalid light format!", 0, 20);
                return;
            }

            size_t jsonCapacity = 1048; // Capacitate ajustată
            DynamicJsonDocument doc(jsonCapacity);
            DeserializationError error = deserializeJson(doc, payload);

            if (error)
            {
                Serial.print(F("Error parsing JSON: "));
                debug("Error parsing JSON:", 0, 20);
                Serial.println(error.f_str());
                return;
            }

            roomLightMap.clear(); // Șterge datele anterioare

            for (JsonObject roomEntry : doc.as<JsonArray>())
            {
                String roomName = roomEntry["room"];
                String lightName = roomEntry["light"];
                bool lightState = String(roomEntry["state"].as<const char *>()) == "on";

                if (roomLightMap.find(roomName) == roomLightMap.end())
                {
                    roomLightMap[roomName] = Room{roomName};
                }

                roomLightMap[roomName].lights.push_back(Light{lightName, lightState});
            }

            Serial.println("Room and light states fetched from server.");
            printLightStates();
        }
        else
        {
            Serial.printf("Error fetching light states: %d\n", httpResponseCode);
            String responsePayload = http.getString();
            Serial.println("Response payload: " + responsePayload);
        }

        http.end(); // Încheie conexiunea
    }
}

//============================================================================

// Function to print the current light states
void printLightStates()
{
    int line = 0;
    for (const auto &roomEntry : roomLightMap)
    {
        Serial.printf("Room: %s\n", roomEntry.first.c_str());
        debug("Room: " + roomEntry.first, 0, line);
        line += 20;
        for (const Light &light : roomEntry.second.lights)
        {
            String lightStateText = "Light: " + light.name + ", State: " + (light.state ? "on" : "off");
            Serial.println(lightStateText);
            sendMessage(lightStateText);
            debug(lightStateText, 0, line);
            line += 20;
        }
    }
}

//============================================================================

// Function to reconnect to Wi-Fi
void reconnectWiFi()
{

    WiFi.begin(ssid, password);
    unsigned long startAttemptTime = millis();

    while (WiFi.status() != WL_CONNECTED && (millis() - startAttemptTime) < 10000)
    {
        delay(1000);
        Serial.println("Connecting to WiFi...");
        debug("Connecting to WiFi...", 0, 40);
    }
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("Failed to connect. Rebooting...");
    }
    Serial.println("Conectat la WiFi.");
    debug("Connected to WiFi.", 0, 40);
}

//============================================================================

// Function to display the IP address
void displayIP()
{
    IPAddress ip = WiFi.localIP();
    String ipText = "MY IP: " + ip.toString();
    debug(ipText, 0, 10);
}

//============================================================================
void handleUpdateStart(AsyncWebServerRequest *request, String filename, size_t index, uint8_t *data, size_t len, bool final)
{

    if (!index)
    {
        Serial.printf("Update Start: %s\n", filename.c_str());
        debug("Update start:", 0, 60);
        if (filename == "firmware.bin")
        {
            Update.begin(UPDATE_SIZE_UNKNOWN);
        }
        else if (filename == "spiffs.bin")
        {
            Update.begin(UPDATE_SIZE_UNKNOWN, U_SPIFFS);
        }
        else if (filename == "bootloader.bin")
        {
            Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH, 0x1000);
        }
        else if (filename == "partitions.bin")
        {
            Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH, 0x8000);
        }
        else
        {
            Serial.println("File is not supported for updates.");
            debug("File is not supported ", 0, 60);
            return;
        }
    }
    if (!Update.hasError())
    {
        Update.write(data, len);
    }
    if (final)
    {
        if (Update.end(true))
        {
            Serial.printf("Update Success: %u\n", index + len);
            debug("Update Success:", 0, 60);
        }
        else
        {
            Serial.printf("Update Error: %s\n", Update.errorString());
            debug("Update Error:", 0, 60);
        }
        delay(5000);
        lcd.clear();
    }
}

void detectIPHandler(AsyncWebServerRequest *request = nullptr)
{

    if (clientIPAddress.isEmpty() || clientIPAddress != request->client()->remoteIP().toString())
    {
        IPAddress clientIP = request->client()->remoteIP();
        clientIPAddress = clientIP.toString();

        if (isLocalServer(clientIPAddress))
        {

            serverCheckUrl = "http://" + clientIPAddress + ":8000/status_response_for_esp32/";
            lightStatusUrl = "http://" + clientIPAddress + ":8000/lights_status/";
            serialPostUrl = "http://" + clientIPAddress + ":8000/esp/serial_data/";
        }
        else
        {
            serverCheckUrl = "http://" + clientIPAddress + "/status_response_for_esp32/";
            lightStatusUrl = "http://" + clientIPAddress + "/lights_status/";
            serialPostUrl = "http://" + clientIPAddress + "/esp/serial_data/";
        }
        
        Serial.println("Client IP assigned: " + clientIPAddress);
        Serial.println("ServerCheckURL is set to : " + serverCheckUrl);
        Serial.println("lightStatusUrl is set to:" + lightStatusUrl);
        Serial.println("serialPostUrl is set to: " + serialPostUrl);
        request->send(200, "text/plain", "I succesful received your IP" + clientIPAddress + " You can stop sending pings");
    }
    else
    {
        request->send(200, "text/plain", "I succesful received your IP" + clientIPAddress + " You can stop sending pings");
    }
}

// Function to set up the server
void serverSetup()
{

    //============================================================================
    server.on("/control_led", HTTP_GET, [](AsyncWebServerRequest *request)
              {
                  String room, light, action;
                  if (request->hasParam("room"))
                  {
                      room = request->getParam("room")->value();
                      Serial.println("Room: " + room);
                  }
                  if (request->hasParam("light"))
                  {
                      light = request->getParam("light")->value();
                      Serial.println("Light: " + light);
                  }
                  if (request->hasParam("action"))
                  {
                      action = request->getParam("action")->value();
                      Serial.println("Action: " + action);
                  }
                  String combinedText = room + " " + light + " is: " + action;

                  debug(combinedText,0,80);


                  request->send(200, "application/json", " {\"status\":\"success\"} "); });

    //============================================================================

    // Handler pentru cererile OPTIONS (preflight request pentru CORS)
    server.on("/django_update_firmware", HTTP_OPTIONS, [](AsyncWebServerRequest *request)
              {
    AsyncWebServerResponse *response = request->beginResponse(200);
    response->addHeader("Access-Control-Allow-Origin", "*");  // Permite accesul de pe orice sursă
    response->addHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
    response->addHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
    request->send(response); });

    //============================================================================
    // Handler pentru cererile POST
    server.on("/django_update_firmware", HTTP_POST, [](AsyncWebServerRequest *request)
              {

    if (!Update.hasError()) {
        AsyncWebServerResponse *response = request->beginResponse(200, "text/plain", "Update Success! Rebooting...");
        
        response->addHeader("Access-Control-Allow-Origin", "*");  // Permite accesul de pe orice sursă
        response->addHeader("Connection", "close");
        request->send(response);
        ESP.restart();
    } else {
        AsyncWebServerResponse *response = request->beginResponse(500, "text/plain", "Update Failed");
        response->addHeader("Access-Control-Allow-Origin", "*");  // Permite accesul de pe orice sursă
        request->send(response);
    } }, handleUpdateStart);

    //============================================================================

    server.on("/", HTTP_GET, detectIPHandler);
    //============================================================================

    server.begin();
}

//============================================================================

// void sendWebSocketMessage(String message)
// {
//     for (int i = 0; i < webSocket.connectedClients(); i++)
//     {
//         webSocket.sendTXT(i, message); // Trimite mesajul fiecărui client conectat
//         debug("WSMSG sended: " + message, 0, 100);
//     }
// }

//============================================================================

String base64Encode(String str)
{
    return base64::encode(str); // Encode using densaugeo/base64 library
}

//============================================================================

void debug(String msg, uint16_t col, uint16_t row)
{
    Serial.println(msg);
#ifdef M5CORE2
    lcd.setCursor(col, row);
    lcd.fillRect(col, row, 320, 20, BLACK); // Clear the area where the text will be displayed
    lcd.println(msg);
#endif
}

//============================================================================