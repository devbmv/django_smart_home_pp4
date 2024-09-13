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
#include <Update.h>
#include <WebSocketsServer.h>
#include <mbedtls/entropy.h>
#include <mbedtls/ctr_drbg.h>
#include <esp_task_wdt.h>

//============================================================================

// Structures to hold light information dynamically
struct Light;

struct Room;

// Map to store rooms and their associated lights
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
void displayText(String text, int x, int y);
void reconnectWiFi();
bool checkServerStatus();
void fetchInitialLightStates();
void printLightStates();
void serverSetup();
void displayIP();
void computeHMAC_SHA256(const char *key, const char *payload, byte *hmacResult);
void processSerialCommands();
// void sendWebSocketMessage(String message);
void sendMessage(String data);
void initializeSystem();
void runMainLoop();
void debug(String msg, uint16_t col, uint16_t row);
void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length);

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
bool checkServer = false;

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

void setup()
{
    // Adaugă taskul curent în watchdog
    Serial.printf("Heap Free: %d bytes\n", ESP.getFreeHeap());

    init_rng();
    initializeSystem();
    if (ESP.getMaxAllocHeap() < 500)
    {
        Serial.print("Low memory: Unable to allocate space for JSON parsing.");
        Serial.println(ESP.getMaxAllocHeap());
    }
}

//============================================================================

void loop()
{
    runMainLoop();
}

//============================================================================

void initializeSystem()
{
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

#ifdef M5CORE2
    auto cfg = M5.config();
    M5.begin(cfg);
    M5.Display.setTextSize(2);
    M5.Display.setCursor(0, 0);
    M5.Display.fillScreen(BLACK); // Clear the screen
#endif

    reconnectWiFi();
    delay(setup_debug_time);
    displayIP();
    delay(setup_debug_time);
    // fetchInitialLightStates();
    serverSetup();
    delay(setup_debug_time);
    // webSocket.begin();
    // webSocket.onEvent(webSocketEvent); // Funcția de gestiune a evenimentelor WebSocket
    delay(setup_debug_time);
    checkServerStatus();
    delay(setup_debug_time);
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
        processSerialCommands(); // Continuously process serial commands
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

void monitorHeap()
{
    if (millis() % loop_debug_time == 0)
    {
        Serial.printf("Free heap memory: %d bytes\n", ESP.getFreeHeap());
    }
}

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
    debug("Starting HTTP POST request to server...", 0, 0);

    if (WiFi.status() != WL_CONNECTED)
    {
        debug("I am  try to reconnect to Wi-Fi", 0, 20);
        reconnectWiFi();
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        // Creăm un obiect local HTTPClient
        HTTPClient http;

        // Verificăm dacă URL-ul este valid înainte de a iniția cererea
        if (!serverCheckUrl.startsWith("http"))
        {
            debug("Invalid server URL", 0, 40);
            return;
        }

        WiFiClient client; // Sau WiFiClientSecure, dacă folosești SSL
        http.begin(client, serverCheckUrl);

        http.setTimeout(30000); // Setează timeout-ul pentru HTTP

        http.addHeader("Content-Type", "application/json");

        String payload = "{\"data\": \"" + data + "\"}";
        int httpResponseCode = http.POST(payload);
        if (httpResponseCode == -1)
        {
            debug("Error: Failed to connect to the server.", 0, 40);
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
                debug("Server error. Please try again later.", 0, 40);
            }
        }

        http.end(); // Încheie conexiunea
    }
    else
    {
        debug("Nu s-a reușit conectarea la WiFi.", 0, 20);
    }
}

//============================================================================

// Function to compute HMAC-SHA256
void computeHMAC_SHA256(const char *key, const char *payload, byte *hmacResult)
{
    mbedtls_md_context_t ctx;
    mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;

    size_t keyLength = strlen(key);
    size_t payloadLength = strlen(payload);

    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 1);
    mbedtls_md_hmac_starts(&ctx, (const unsigned char *)key, keyLength);
    mbedtls_md_hmac_update(&ctx, (const unsigned char *)payload, payloadLength);
    mbedtls_md_hmac_finish(&ctx, hmacResult);
    mbedtls_md_free(&ctx);
}

//============================================================================
void processSerialCommands()
{
    if (Serial.available() > 0)
    {
        String input = Serial.readStringUntil('\n');
        input.trim();
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
        else if (input = "!check")
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

String base64Encode(String str)
{
    return base64::encode(str); // Encode using densaugeo/base64 library
}

//============================================================================

// Function to add Basic Authentication header to each HTTP request
void addBasicAuth(HTTPClient &http)
{
    if (djangoUserName.isEmpty() || djangoPassword.isEmpty())
    {
        Serial.println("Username or password for django is missing.");
        return;
    }
    String auth = base64Encode(djangoUserName + ":" + djangoPassword);
    Serial.println("Auth urlcode = " + auth);
    http.addHeader("Authorization", "Basic " + auth);
}

//============================================================================

// Function to display text on the M5Core2 screen
void displayText(String text, int x, int y)
{
#ifdef M5CORE2
    lcd.setCursor(x, y);
    lcd.fillRect(x, y, 320, 20, BLACK); // Clear the area where the text will be displayed
    lcd.println(text);
#endif
}

//============================================================================
bool checkServerStatus() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;

        if (!serverCheckUrl.startsWith("http")) {
            if (!clientIPAddress.isEmpty()) {
                serverCheckUrl = "http://" + clientIPAddress + ":8000/status_response_for_esp32/";
                Serial.println("ServerCheckUrl auto-setat la: " + serverCheckUrl);
            } 
        }

        // Verifică URL-ul serverului
        Serial.println("Verific URL-ul: " + serverCheckUrl);
        http.begin(serverCheckUrl);
        addBasicAuth(http);
        http.setTimeout(30000);

        Serial.println("\nSending request to check server status...");

        int httpResponseCode = http.GET();

        if (httpResponseCode >= 200 && httpResponseCode < 300) {
            Serial.println("Success! Server response:");
            Serial.println(http.getString());
        } else if (httpResponseCode == -1) {
            // Afișează eroarea de conexiune
            Serial.println("Connection failed. Check WiFi, server address, or firewall.");
        } else if (httpResponseCode >= 300 && httpResponseCode < 400) {
            Serial.printf("Redirection error: %d\n", httpResponseCode);
            Serial.println("Server is trying to redirect.");
        } else if (httpResponseCode >= 400 && httpResponseCode < 500) {
            Serial.printf("Client error: %d\n", httpResponseCode);
            Serial.println("Possible authentication or request issue.");
            Serial.println(http.getString());
        } else if (httpResponseCode >= 500) {
            Serial.printf("Server error: %d\n", httpResponseCode);
            Serial.println("Server might be down or there is an internal error.");
            Serial.println(http.getString());
        } else {
            Serial.printf("Unexpected error: %d\n", httpResponseCode);
        }

        http.end();
    } else {
        Serial.println("WiFi not connected.");
        displayText("WiFi not connected", 0, 0);
    }
    return false;
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
            Serial.println("Invalid lightStatusUrl format!");
            displayText("Invalid lightStatusUrl format!", 0, 20);
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
                displayText("Invalid light format!", 0, 20);
                return;
            }

            size_t jsonCapacity = 1048; // Capacitate ajustată
            DynamicJsonDocument doc(jsonCapacity);
            DeserializationError error = deserializeJson(doc, payload);

            if (error)
            {
                Serial.print(F("Error parsing JSON: "));
                displayText("Error parsing JSON:", 0, 20);
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
        displayText("Room: " + roomEntry.first, 0, line);
        line += 20;
        for (const Light &light : roomEntry.second.lights)
        {
            String lightStateText = "Light: " + light.name + ", State: " + (light.state ? "on" : "off");
            Serial.println(lightStateText);
            sendMessage(lightStateText);
            displayText(lightStateText, 0, line);
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
        displayText("Connecting to WiFi...", 0, 40);
    }
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("Failed to connect. Rebooting...");
    }
    Serial.println("Conectat la WiFi.");
    displayText("Connected to WiFi.", 0, 40);
}

//============================================================================

// Function to display the IP address
void displayIP()
{
    IPAddress ip = WiFi.localIP();
    String ipText = "IP: " + ip.toString();
    Serial.println(ipText);
    displayText(ipText, 0, 10);
}

//============================================================================
void handleUpdateStart(AsyncWebServerRequest *request, String filename, size_t index, uint8_t *data, size_t len, bool final)
{

    if (!index)
    {
        Serial.printf("Update Start: %s\n", filename.c_str());
        displayText("Update start:", 0, 60);
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
            displayText("File is not supported ", 0, 60);
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
            displayText("Update Success:", 0, 60);
        }
        else
        {
            Serial.printf("Update Error: %s\n", Update.errorString());
            displayText("Update Error:", 0, 60);
        }
        delay(5000);
        lcd.clear();
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

    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request)
              {
    // Obține IP-ul clientului
    IPAddress clientIP = request->client()->remoteIP();
    clientIPAddress = clientIP.toString();

    if (clientIPAddress.isEmpty()) {

    clientIPAddress = request->client()->remoteIP().toString();
    // Setează URL-urile pe baza IP-ului clientului
    // Setează URL-urile pentru comunicarea cu Django
    serverCheckUrl = "http://" + clientIPAddress + ":8000/check-server-status/";
    lightStatusUrl = "http://" + clientIPAddress + ":8000/lights_status/";
    serialPostUrl = "http://" + clientIPAddress + ":8000/esp/serial_data/";

    // Afișează IP-ul clientului pe consolă
    Serial.println("Client IP assigned: " + clientIPAddress);

    // Trimite răspunsul către client
    request->send(200, "text/plain", "IP Address received: " + clientIPAddress + " You can stop sending pings");
    }else{
    request->send(200,"text/plain","I am esp32 and you succesful checked, my status ONLINE");
} });
   //============================================================================

    server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request)
              {
                  Serial.println(request->client()->remoteIP());
                  request->send(200,"text/plain","SUcces received request"); }

    );
}