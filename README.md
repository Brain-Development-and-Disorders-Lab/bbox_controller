# Behavior Box Controller

This repository contains the code to control a behavior box utilizing IO and displays.

## Control Panel

The control panel facilitates wireless monitoring and control via Websockets. To launch the control panel, run `python3 src/control_panel/main.py`.

Use the *Connection* frame to connect to the device using an IP address and port number. The *Console* frame shows the live console output from the device. The *Input Status* frame shows the current state of the device IO with low latency. The *Test Status* frame allows the IO to be tested, specifically the water deliver, actuators, and the IR beam.

To run an experiment, enter the animal ID in the *Experiment Management* frame and click the *Start* button.

## Device

Both `input` and `output` controllers are implemented. Inputs include levers and other sensors, outputs include LEDs and display modules.

### Simulation

You can run the device in simulation mode for development and testing without physical hardware. Simulation mode is activated automatically if hardware libraries (e.g., gpiozero) are unavailable.

### Controls in Simulation Mode

- **1**: Left Lever (hold to press)
- **2**: Right Lever (hold to press)
- **3**: Nose Poke (hold to activate)
- **Space**: Nose Poke (alternative)
- **ESC**: Exit

### Hardware Usage

To run the device controller code, use the Python script:

`python3 src/device/main.py`

Or, use the included shell script once `chmod +x` permissions have been applied:

`./src/device/run.sh`

## License

<!-- CC BY-NC-SA 4.0 License -->
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">
  <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" />
</a>
<br />
This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.

## Issues and Feedback

Please contact **Henry Burgess** <[henry.burgess@wustl.edu](mailto:henry.burgess@wustl.edu)> for all code-related issues and feedback.
