#include <iostream>

int main() {
    std::iostream::sync_with_stdio(false);
    std::cout << "Hello from the C++ Application!" << std::endl;

    #ifdef TARGET_PI
        std::cout << "[Target: Raspberry Pi] Running on ARM Linux." << std::endl;
    #else
        std::cout << "[Target: macOS] Simulating functionality on Mac." << std::endl;
    #endif

    return 0;
}
