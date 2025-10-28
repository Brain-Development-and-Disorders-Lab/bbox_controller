#!/usr/bin/env python3

import json
import threading
import time
import websocket
from typing import Optional, Callable, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal


class DeviceConnectionManager(QObject):
    """Manages WebSocket connection and messaging for a single device"""

    connected = pyqtSignal()  # Emitted when connection is established
    disconnected = pyqtSignal()  # Emitted when connection is lost
    message_received = pyqtSignal(dict)  # Emitted when a message is received from the device

    def __init__(self, device_name: str, ip_address: str, port: int = 8765):
        super().__init__()
        self.device_name = device_name
        self.ip_address = ip_address
        self.port = port
        self.ws_url = f"ws://{ip_address}:{port}"

        self.ws: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.is_connected = False
        self.device_version = "unknown"

    def connect(self):
        """Establish WebSocket connection to the device"""
        if self.is_connected:
            return

        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )

            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()

            # Wait for connection (max 10 seconds)
            for _ in range(20):
                if self.ws.sock and self.ws.sock.connected:
                    self.is_connected = True
                    self.connected.emit()
                    return
                time.sleep(0.5)

            raise ConnectionError(f"Failed to connect to {self.device_name} within 10 seconds")

        except Exception as e:
            raise ConnectionError(f"Error connecting to {self.device_name}: {str(e)}")

    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
        self.is_connected = False
        self.disconnected.emit()

    def send_message(self, message: Dict[str, Any]):
        """Send a message to the device"""
        if not self.is_connected or not self.ws:
            raise ConnectionError(f"Not connected to {self.device_name}")

        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            raise ConnectionError(f"Failed to send message to {self.device_name}: {str(e)}")

    def send_command(self, command: str):
        """Send a command string to the device"""
        if not self.is_connected or not self.ws:
            raise ConnectionError(f"Not connected to {self.device_name}")

        try:
            self.ws.send(command)
        except Exception as e:
            raise ConnectionError(f"Failed to send command to {self.device_name}: {str(e)}")

    def _run_websocket(self):
        """Run the WebSocket in a separate thread"""
        self.ws.run_forever()

    def _on_open(self, ws):
        """Handle WebSocket opening"""
        self.is_connected = True
        self.connected.emit()

    def _on_message(self, ws, message: str):
        """Handle incoming WebSocket messages"""
        try:
            parsed_message = json.loads(message)

            # Extract version info if present
            if isinstance(parsed_message, dict) and "version" in parsed_message:
                new_version = parsed_message["version"]
                if new_version != self.device_version:
                    self.device_version = new_version

            # Emit signal with the parsed message
            self.message_received.emit(parsed_message)

        except json.JSONDecodeError:
            pass  # Ignore invalid JSON

    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error for {self.device_name}: {error}")
        self.is_connected = False
        self.disconnected.emit()

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket closing"""
        self.is_connected = False
        self.disconnected.emit()

