# Define compilers
HOST_CXX := g++
PI_CXX := /opt/homebrew/bin/armv7-unknown-linux-gnueabihf-g++

# Project structure
SRC_DIR  := src
BUILD_DIR := dist
TARGET := behavior_box_device

# Vendored dependencies
IXWEBSOCKET_DIR := third_party/ixwebsocket

# Source files
SRCS := $(wildcard $(SRC_DIR)/*.cpp) $(wildcard $(IXWEBSOCKET_DIR)/ixwebsocket/*.cpp)
INCLUDES := -I$(IXWEBSOCKET_DIR)

# Default rule
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make mac   - Build native app for testing on macOS"
	@echo "  make pi    - Cross-compile app for Raspberry Pi"
	@echo "  make clean - Delete all built objects and files safely"

# Build for MacOS
.PHONY: mac
mac:
	@mkdir -p $(BUILD_DIR)/mac
	$(HOST_CXX) -std=c++17 -pthread $(INCLUDES) $(SRCS) -o $(BUILD_DIR)/mac/$(TARGET)
	@echo "MacOS Build Complete: $(BUILD_DIR)/mac/$(TARGET)"

# Build for Raspberry Pi
.PHONY: pi
pi:
	@mkdir -p $(BUILD_DIR)/pi
	$(PI_CXX) -std=c++17 -pthread -DTARGET_PI $(INCLUDES) $(SRCS) -o $(BUILD_DIR)/pi/$(TARGET) -latomic
	@echo "Raspberry Pi Build Complete -> $(BUILD_DIR)/pi/$(TARGET)"

# Clean up
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	@echo "Cleaned up build artifacts!"
