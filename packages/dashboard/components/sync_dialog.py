#!/usr/bin/env python3
"""
Filename: dashboard/components/sync_dialog.py
Description: Dialog for showing file sync progress
"""

import os
import hashlib
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt


class SyncProgressDialog(QDialog):
    """Dialog showing file sync progress with checksum validation"""

    def __init__(self, parent=None, device_name: str = None):
        super().__init__(parent)
        self.device_name = device_name
        self.total_files = 0
        self.current_file = 0
        self.files_to_sync = []
        self.destination_dir = None
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Syncing Files")
        self.setMinimumSize(400, 150)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Status label
        self.status_label = QLabel("Preparing to sync files...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Details label
        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.details_label)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)

    def set_total_files(self, count):
        """Set the total number of files to sync"""
        self.total_files = count
        self.progress_bar.setMaximum(count)

    def update_progress(self, filename, current_file_num, total_files, status=""):
        """Update the progress display"""
        self.current_file = current_file_num
        self.status_label.setText(f"Syncing: {filename}")
        self.progress_bar.setValue(current_file_num)

        details = f"File {current_file_num} of {total_files}"
        if status:
            details += f" - {status}"
        self.details_label.setText(details)

    def set_finished(self, success_count, total_files):
        """Update UI when sync is finished"""
        if success_count == total_files:
            self.status_label.setText("Sync completed successfully!")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText(f"Sync completed with {success_count}/{total_files} files")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

        self.progress_bar.setValue(total_files)
        self.cancel_btn.setText("Close")

    def validate_checksum(self, content: str, expected_checksum: str) -> bool:
        """Validate file content against MD5 checksum"""
        calculated = hashlib.md5(content.encode()).hexdigest()
        return calculated == expected_checksum

    def save_file(self, filename: str, content: str, destination_dir: str) -> bool:
        """Save file to destination directory"""
        try:
            os.makedirs(destination_dir, exist_ok=True)
            filepath = os.path.join(destination_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file {filename}: {e}")
            return False

