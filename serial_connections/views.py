import requests
from django.http import HttpResponse, JsonResponse  # Corrected import
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from time import sleep
import threading

# =============================================================================

# Global variable to store received data
received_data = []
uart_running = False  # Variable to track UART status

# =============================================================================
# View to receive data from M5Core2
@csrf_exempt
def receive_serial_data(request):
    global uart_running
    if request.method == "POST" and uart_running:
        try:
            # Decode the POST body (expected to be in JSON format)
            data = json.loads(request.body)
            received_data.append(data)  # Store data in global variable
            print(f"Data received: {data}")
            return JsonResponse({"status": "success"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method or UART is stopped"},
        status=405,
    )


# View to send and process UART commands
@csrf_exempt
def uart_command(request):
    global uart_running, received_data
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            command = data.get("command")

            if command == "start":
                uart_running = True
                return JsonResponse({"status": "UART started"}, status=200)

            elif command == "stop":
                uart_running = False
                return JsonResponse({"status": "UART stopped"}, status=200)

            elif command == "clear":
                received_data = []  # Clear the data
                return JsonResponse({"status": "UART data cleared"}, status=200)

            return JsonResponse({"status": "Invalid command"}, status=400)

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=405
    )


# View to display serial data in HTML and return JSON for AJAX requests
def view_serial_data(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":  # Check if AJAX request
        # If it's an AJAX request, return data in JSON format
        return JsonResponse({"data": received_data})
    else:
        # If it's not an AJAX request, render the HTML page with data
        return render(
            request,
            "serial_connections/serial.html",
            {"data": received_data[-1] if received_data else "No data"},
        )
