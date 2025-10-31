#!/usr/bin/env python3
"""
Pytest configuration and fixtures for dashboard UI tests.

This module provides common fixtures and setup for testing PyQt6 UI components.
"""

import sys
import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """
    Create a QApplication instance for the test session.

    This fixture ensures only one QApplication exists during the test session,
    which is required for PyQt6 to work properly.
    """
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def qtbot(qapp):
    """
    Create a QtBot instance for interacting with widgets.

    Note: For advanced Qt testing features, install pytest-qt:
        pip install pytest-qt

    This fixture provides a basic QtBot implementation. If pytest-qt is installed,
    it will automatically use the more feature-rich qtbot from pytest-qt.
    """
    try:
        from pytestqt import qtbot as pytestqt_qtbot  # type: ignore
        return pytestqt_qtbot.QtBot(qapp)
    except ImportError:
        # Fallback to basic implementation if pytest-qt is not installed
        class BasicQtBot:
            def __init__(self, app):
                self.app = app

            def wait(self, timeout=1000):
                """Wait for events to process"""
                self.app.processEvents()

            def waitSignal(self, signal, timeout=1000):
                """Basic signal waiting - for full support, use pytest-qt"""
                self.app.processEvents()

            def waitUntil(self, condition, timeout=1000):
                """Basic condition waiting - for full support, use pytest-qt"""
                self.app.processEvents()
                return condition()

        return BasicQtBot(qapp)

