# Dashboard UI Tests

This directory contains unit tests for the dashboard UI components built with PyQt6.

## Setup

The test suite uses pytest and includes fixtures for PyQt6 testing. The tests can run with or without the optional `pytest-qt` package.

### Basic Setup (No additional dependencies)

The tests will work with just PyQt6 and pytest. A basic QtBot implementation is provided in `conftest.py`.

### Optional: Enhanced Qt Testing

For better Qt testing features (signal waiting, event processing, etc.), install `pytest-qt`:

```bash
pip install pytest-qt
```

## Running Tests

Run all dashboard tests:
```bash
pytest test/dashboard/
```

Run a specific test file:
```bash
pytest test/dashboard/test_device_dialog.py
```

Run with verbose output:
```bash
pytest test/dashboard/ -v
```

## Test Files

- `conftest.py` - Pytest configuration and fixtures (QApplication, QtBot)
- `test_device_dialog.py` - Tests for DeviceDialog component
- `test_device_tab.py` - Tests for DeviceTab widget
- `test_main_window.py` - Tests for MainWindow

## Writing New Tests

When writing new UI tests:

1. Use the `qapp` fixture for QApplication instance (automatically provided)
2. Use the `qtbot` fixture for widget interaction
3. Import components from the dashboard package
4. Clean up widgets by calling `.close()` after each test
5. Use `QTest` from `PyQt6.QtTest` for simulating user interactions

Example:
```python
def test_my_widget(qapp, qtbot):
    widget = MyWidget()
    widget.show()

    # Simulate button click
    from PyQt6.QtTest import QTest
    from PyQt6.QtCore import Qt
    QTest.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    # Wait for events
    qtbot.wait(100)

    # Assert results
    assert widget.some_property == expected_value

    widget.close()
```

## Notes

- Some tests may skip if UI files are not available in the test environment
- Mock external dependencies (network, file I/O) when possible
- Use temporary files/directories for tests that require file system access

