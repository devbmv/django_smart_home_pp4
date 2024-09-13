# User Stories for Smart Home Project with M5Stack Core2

## 1. Project Setup
**Title:**  
As a developer, I want to set up the initial project structure to support both M5Stack Core2 and Django, so that I can manage the development process efficiently.

**Acceptance Criteria:**
- Create GitHub repositories for both Django and M5Stack Core2 code.
- Set up virtual environments and install necessary dependencies for Django.
- Prepare the M5Stack Core2 environment using Arduino IDE or PlatformIO.

---

## 2. DEMO Mode Configuration
**Title:**  
As a developer, I want to configure a DEMO mode in the project so that it can run without the M5Stack Core2 device for demonstration purposes.

**Acceptance Criteria:**
- Add a configuration option in Django and M5Stack Core2 code to toggle DEMO mode.
- In DEMO mode, simulate hardware interactions and use mock data instead of real sensor readings or device controls.
- Ensure that the system can switch between DEMO and normal modes seamlessly.

---

## 3. ElephantDB Integration
**Title:**  
As a developer, I want to integrate ElephantDB with the Django backend so that I can store and retrieve configuration settings for the Smart Home system.

**Acceptance Criteria:**
- Set up a connection to ElephantDB from the Django backend.
- Implement Django models to represent settings that will be stored in ElephantDB.
- Provide APIs to retrieve and update these settings.

---

## 4. Initialize Settings from ElephantDB
**Title:**  
As a developer, I want the system to load initial settings from ElephantDB on startup so that the devices and server use the most up-to-date configurations.

**Acceptance Criteria:**
- Implement code in Django to fetch settings from ElephantDB during server startup.
- Implement code in M5Stack Core2 to request settings from the Django server upon startup.
- Ensure that devices use these settings to configure their behavior (e.g., default light states, temperature thresholds).

---

## 5. Lights Control (with M5Stack Core2)
**Title:**  
As a user, I want to control the lights in my home via the web app so that I can manage energy consumption.

**Acceptance Criteria:**
- Develop a UI in Django for toggling lights on and off.
- Implement API endpoints in Django to handle light control requests.
- In normal mode, the Django server sends commands to M5Stack Core2 to control the physical lights. In DEMO mode, it simulates this action.
- M5Stack Core2 receives commands from Django and controls the actual hardware (e.g., turning on/off an LED).

---

## 6. Ventilation Control (with M5Stack Core2)
**Title:**  
As a user, I want to control the ventilation system in my home through the web app to maintain air quality.

**Acceptance Criteria:**
- Develop a UI component in Django for adjusting ventilation settings.
- Implement API endpoints in Django to manage ventilation.
- In normal mode, the Django server sends ventilation commands to M5Stack Core2. In DEMO mode, it simulates these actions.
- M5Stack Core2 processes these commands and controls the ventilation hardware.

---

## 7. Temperature Control (with M5Stack Core2) (Optional)
**Title:**  
As a user, I want to manage the heating system to ensure a comfortable temperature in each room.

**Acceptance Criteria:**
- Create a UI in Django for setting and adjusting temperatures.
- Implement logic in Django to handle temperature control and scheduling.
- In normal mode, Django sends temperature settings to M5Stack Core2, which adjusts the heating system accordingly. In DEMO mode, it simulates these actions.

---

## 8. Testing and Validation (Optional)
**Title:**  
As a developer, I want to thoroughly test both DEMO and normal modes to ensure the system functions correctly under all conditions.

**Acceptance Criteria:**
- Write unit tests for Django views and API endpoints.
- Perform integration testing to validate communication between Django and M5Stack Core2.
- Test settings initialization from ElephantDB in both modes.

---

## 9. Documentation and README
**Title:**  
As a developer, I want to create comprehensive documentation so that others can understand and contribute to the project.

**Acceptance Criteria:**
- Write a detailed README file explaining the project setup, features, and deployment process.
- Document the configuration process for both Django and M5Stack Core2.
- Include examples of how to run the project in both DEMO mode and connected mode, and how to integrate with ElephantDB.

---

## 10. Deployment
**Title:**  
As a developer, I want to deploy the Django project on Heroku and integrate it with M5Stack Core2, so that the system is live and accessible.

**Acceptance Criteria:**
- Set up deployment pipelines for Django on Heroku.
- Configure M5Stack Core2 to communicate with the Django backend over Wi-Fi.
- Ensure that the system works correctly with ElephantDB for storing and retrieving settings.
