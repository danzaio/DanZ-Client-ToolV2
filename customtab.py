"""
DanZ Client Tool - Custom Tab
Raw HTTP request builder and LCDS invoke interface.
"""

import json
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit,
    QPlainTextEdit, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt

from lcu import lcu


class CustomTab(QWidget):
    """Custom HTTP request builder tab."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Splitter for request/response
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- Request Section ---
        request_widget = QWidget()
        request_layout = QVBoxLayout(request_widget)
        request_layout.setContentsMargins(0, 0, 0, 0)
        
        # HTTP Request Group
        http_group = QGroupBox("HTTP/HTTPS Request Builder")
        http_layout = QGridLayout(http_group)
        
        # Quick fill buttons
        fill_layout = QHBoxLayout()
        fill_layout.addWidget(QLabel("Quick Fill:"))
        
        self.lcu_fill_btn = QPushButton("LCU")
        self.lcu_fill_btn.clicked.connect(lambda: self.quick_fill("lcu"))
        fill_layout.addWidget(self.lcu_fill_btn)
        
        self.riot_fill_btn = QPushButton("Riot Client")
        self.riot_fill_btn.clicked.connect(lambda: self.quick_fill("riot"))
        fill_layout.addWidget(self.riot_fill_btn)
        
        self.store_fill_btn = QPushButton("Store")
        self.store_fill_btn.clicked.connect(lambda: self.quick_fill("store"))
        fill_layout.addWidget(self.store_fill_btn)
        
        self.edge_fill_btn = QPushButton("League Edge")
        self.edge_fill_btn.clicked.connect(lambda: self.quick_fill("edge"))
        fill_layout.addWidget(self.edge_fill_btn)
        
        fill_layout.addStretch()
        http_layout.addLayout(fill_layout, 0, 0, 1, 4)
        
        # Method
        http_layout.addWidget(QLabel("Method:"), 1, 0)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "PATCH", "DELETE"])
        http_layout.addWidget(self.method_combo, 1, 1)
        
        # URL
        http_layout.addWidget(QLabel("URL:"), 2, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://127.0.0.1:PORT/endpoint")
        http_layout.addWidget(self.url_input, 2, 1, 1, 3)
        
        # Body
        http_layout.addWidget(QLabel("Body (JSON):"), 3, 0)
        self.body_input = QPlainTextEdit()
        self.body_input.setPlaceholderText('{"key": "value"}')
        self.body_input.setMaximumHeight(150)
        http_layout.addWidget(self.body_input, 3, 1, 1, 3)
        
        # Custom headers
        http_layout.addWidget(QLabel("Custom Headers:"), 4, 0)
        self.headers_input = QPlainTextEdit()
        self.headers_input.setPlaceholderText('{"Header-Name": "value"}')
        self.headers_input.setMaximumHeight(80)
        http_layout.addWidget(self.headers_input, 4, 1, 1, 3)
        
        # Send button
        self.send_http_btn = QPushButton("Send Request")
        self.send_http_btn.clicked.connect(self.send_http_request)
        http_layout.addWidget(self.send_http_btn, 5, 0, 1, 4)
        
        request_layout.addWidget(http_group)
        
        # LCDS Invoke Group
        lcds_group = QGroupBox("LCDS Invoke")
        lcds_layout = QGridLayout(lcds_group)
        
        # Destination
        lcds_layout.addWidget(QLabel("Destination:"), 0, 0)
        self.lcds_dest = QLineEdit()
        self.lcds_dest.setPlaceholderText("e.g., lcdsServiceProxy")
        lcds_layout.addWidget(self.lcds_dest, 0, 1)
        
        # Method
        lcds_layout.addWidget(QLabel("Method:"), 0, 2)
        self.lcds_method = QLineEdit()
        self.lcds_method.setPlaceholderText("e.g., call")
        lcds_layout.addWidget(self.lcds_method, 0, 3)
        
        # Args
        lcds_layout.addWidget(QLabel("Args (JSON):"), 1, 0)
        self.lcds_args = QLineEdit()
        self.lcds_args.setPlaceholderText('[]')
        lcds_layout.addWidget(self.lcds_args, 1, 1, 1, 3)
        
        # Send button
        self.send_lcds_btn = QPushButton("Send LCDS")
        self.send_lcds_btn.clicked.connect(self.send_lcds_request)
        lcds_layout.addWidget(self.send_lcds_btn, 2, 0, 1, 4)
        
        request_layout.addWidget(lcds_group)
        
        splitter.addWidget(request_widget)
        
        # --- Response Section ---
        response_group = QGroupBox("Response")
        response_layout = QVBoxLayout(response_group)
        
        # Status
        self.status_label = QLabel("Status: -")
        response_layout.addWidget(self.status_label)
        
        # Response body
        self.response_output = QPlainTextEdit()
        self.response_output.setReadOnly(True)
        self.response_output.setPlaceholderText("Response will appear here...")
        response_layout.addWidget(self.response_output)
        
        # Copy button
        self.copy_response_btn = QPushButton("Copy Response")
        self.copy_response_btn.clicked.connect(self.copy_response)
        response_layout.addWidget(self.copy_response_btn)
        
        splitter.addWidget(response_group)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
    
    def quick_fill(self, target: str):
        """Fill in URL with appropriate base."""
        if not lcu.is_connected and target in ["lcu", "riot"]:
            return
        
        if target == "lcu":
            if lcu.lcu_credentials:
                base = lcu.lcu_credentials.base_url
                self.url_input.setText(f"{base}/")
        elif target == "riot":
            if lcu.riot_credentials:
                base = lcu.riot_credentials.base_url
                self.url_input.setText(f"{base}/")
        elif target == "store":
            store_url, _ = lcu.get_store_url()
            if store_url:
                self.url_input.setText(f"{store_url}/storefront/v3/")
        elif target == "edge":
            self.url_input.setText("https://api.ledge.leagueoflegends.com/")
    
    def send_http_request(self):
        """Send the custom HTTP request."""
        method = self.method_combo.currentText()
        url = self.url_input.text().strip()
        
        if not url:
            self.status_label.setText("Status: Error - No URL specified")
            return
        
        # Parse body
        body = None
        body_text = self.body_input.toPlainText().strip()
        if body_text:
            try:
                body = json.loads(body_text)
            except json.JSONDecodeError as e:
                self.status_label.setText(f"Status: Error - Invalid JSON body: {e}")
                return
        
        # Parse custom headers
        custom_headers = {}
        headers_text = self.headers_input.toPlainText().strip()
        if headers_text:
            try:
                custom_headers = json.loads(headers_text)
            except json.JSONDecodeError as e:
                self.status_label.setText(f"Status: Error - Invalid JSON headers: {e}")
                return
        
        # Determine which connection to use based on URL
        try:
            import requests
            
            # Build headers
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            
            # Add auth if local
            if "127.0.0.1" in url:
                if lcu.lcu_credentials:
                    headers["Authorization"] = lcu.lcu_credentials.auth_header
            
            # Apply custom headers
            headers.update(custom_headers)
            
            # Send request
            if body is not None:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                    verify=False,
                    timeout=10
                )
            else:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    verify=False,
                    timeout=10
                )
            
            # Display response
            self.status_label.setText(f"Status: {response.status_code}")
            
            # Try to format JSON
            try:
                data = response.json()
                self.response_output.setPlainText(json.dumps(data, indent=2))
            except ValueError:
                self.response_output.setPlainText(response.text)
        
        except Exception as e:
            self.status_label.setText(f"Status: Error - {e}")
            self.response_output.setPlainText("")
    
    def send_lcds_request(self):
        """Send an LCDS invoke request."""
        if not lcu.is_connected:
            self.status_label.setText("Status: Not connected")
            return
        
        destination = self.lcds_dest.text().strip()
        method = self.lcds_method.text().strip()
        
        if not destination or not method:
            self.status_label.setText("Status: Error - Destination and method required")
            return
        
        # Parse args
        args = []
        args_text = self.lcds_args.text().strip()
        if args_text:
            try:
                args = json.loads(args_text)
            except json.JSONDecodeError as e:
                self.status_label.setText(f"Status: Error - Invalid JSON args: {e}")
                return
        
        # Send LCDS invoke
        result = lcu.lcds_invoke(destination, method, args)
        
        self.status_label.setText(f"Status: {result.status_code}")
        
        if result.data:
            try:
                self.response_output.setPlainText(json.dumps(result.data, indent=2))
            except (TypeError, ValueError):
                self.response_output.setPlainText(str(result.data))
        elif result.error:
            self.response_output.setPlainText(f"Error: {result.error}")
        else:
            self.response_output.setPlainText("")
    
    def copy_response(self):
        """Copy the response to clipboard."""
        from PySide6.QtWidgets import QApplication
        
        text = self.response_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
