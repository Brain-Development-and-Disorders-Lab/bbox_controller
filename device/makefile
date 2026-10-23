# Define compilers
HOST_CXX := g++

# Project structure
SRC_DIR  := src
BUILD_DIR := dist
TARGET := behavior_box_device

# Vendored dependencies
IXWEBSOCKET_DIR := third_party/ixwebsocket
SPDLOG_DIR := third_party/spdlog
JSON_DIR := third_party/nlohmann_json

# Source files
SRCS := $(shell find $(SRC_DIR) -name '*.cpp') $(wildcard $(IXWEBSOCKET_DIR)/ixwebsocket/*.cpp)
INCLUDES := -I$(SRC_DIR) -I$(IXWEBSOCKET_DIR) -I$(SPDLOG_DIR) -I$(JSON_DIR)
CXXFLAGS := -std=c++17 -pthread -MMD -MP

# System dependencies (SDL3 and SDL3_ttf from Homebrew on macOS, or installed from source on the Pi)
SDL_CFLAGS := $(shell pkg-config --cflags sdl3 sdl3-ttf)
SDL_LIBS := $(shell pkg-config --libs sdl3 sdl3-ttf)

# Runtime assets (fonts) are copied next to the executable
ASSETS_DIR := assets
ASSETS := $(shell find $(ASSETS_DIR) -type f)

# Objects are kept per target so rebuilds only compile changed files
MAC_DIR := $(BUILD_DIR)/mac
MAC_OBJS := $(SRCS:%.cpp=$(MAC_DIR)/obj/%.o)
PI_DIR := $(BUILD_DIR)/pi
PI_OBJS := $(SRCS:%.cpp=$(PI_DIR)/obj/%.o)

# Default rule
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make mac   - Build app for testing on macOS"
	@echo "  make pi    - Build app for Raspberry Pi"
	@echo "  make clean - Delete all built objects and files safely"

# Build for MacOS
.PHONY: mac
mac: $(MAC_DIR)/$(TARGET) $(ASSETS:%=$(MAC_DIR)/%)
	@echo "MacOS Build Complete: $(MAC_DIR)/$(TARGET)"

$(MAC_DIR)/$(TARGET): $(MAC_OBJS)
	$(HOST_CXX) -pthread $^ $(SDL_LIBS) -o $@

$(MAC_DIR)/$(ASSETS_DIR)/%: $(ASSETS_DIR)/%
	@mkdir -p $(dir $@)
	cp $< $@

$(MAC_DIR)/obj/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(HOST_CXX) $(CXXFLAGS) $(INCLUDES) $(SDL_CFLAGS) -c $< -o $@

# Build for Raspberry Pi
.PHONY: pi
pi: $(PI_DIR)/$(TARGET) $(ASSETS:%=$(PI_DIR)/%)
	@echo "Raspberry Pi Build Complete: $(PI_DIR)/$(TARGET)"

$(PI_DIR)/$(TARGET): $(PI_OBJS)
	$(HOST_CXX) -pthread $^ $(SDL_LIBS) -o $@

$(PI_DIR)/$(ASSETS_DIR)/%: $(ASSETS_DIR)/%
	@mkdir -p $(dir $@)
	cp $< $@

$(PI_DIR)/obj/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(HOST_CXX) $(CXXFLAGS) -DTARGET_PI $(INCLUDES) $(SDL_CFLAGS) -c $< -o $@

# Clean up
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	@echo "Cleaned up build artifacts!"

-include $(MAC_OBJS:.o=.d) $(PI_OBJS:.o=.d)
