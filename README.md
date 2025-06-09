# Behavior Box Controller (BBox Controller)

This repository contains the code for the Behavior Box Controller (BBox Controller).

## Controllers

Both `input` and `output` controllers are implemented. Inputs include levers and other sensors, outputs include LEDs and display modules.

## Simulation Mode (No Hardware Required)

You can run the device in simulation mode for development and testing without physical hardware. Simulation mode is activated automatically if hardware libraries (e.g., gpiozero) are unavailable.

### Controls in Simulation Mode
- **1**: Left Lever (hold to press)
- **2**: Right Lever (hold to press)
- **3**: Nose Poke (hold to activate)
- **Space**: Nose Poke (alternative)
- **ESC**: Exit

The waiting screen will show these controls and the current simulated input states.

### How to Use
1. Run the device: `python src/device/main.py`
2. Use the keys above to simulate lever/nose poke actions
3. All trial logic and experiments work as if real hardware is present

### Key Points
- Simulation state is shown live on the waiting screen
- Only essential trial events are logged in simulation mode
- All input/output logic is identical to real hardware
- Automated tests are available in `tests/device/`

### Testing Simulation
Run all simulation tests with:
```bash
pytest tests/device/
```

## License

<!-- CC BY-NC-SA 4.0 License -->
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">
  <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" />
</a>
<br />
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

## Issues and Feedback

Please contact **Henry Burgess** <[henry.burgess@wustl.edu](mailto:henry.burgess@wustl.edu)> for all code-related issues and feedback.
