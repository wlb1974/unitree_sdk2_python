# Unitree G1 Robot Control System

This directory contains the refactored robot control system with modular architecture.

## Files

### main.py
Main entry point for the robot control system. Handles:
- System initialization and configuration
- Network interface validation
- Component health checks
- Integration of audio and action modules

### RobotAudio.py
Audio module handling all audio-related functionality:
- ASR (Automatic Speech Recognition)
- TTS (Text-to-Speech)
- Audio recording and playback
- Volume control
- LED control
- Multicast audio streaming

### RobotAction.py
Action module handling all action-related functionality:
- Locomotion control (stand, sit, move, turn)
- Arm movement and manipulation
- Gesture recognition
- Action execution and coordination
- Safety checks and validation

### RobotArmDemo.py
Advanced arm demonstration module with complete movement sequences:
- Low-level SDK DDS arm control
- Multi-stage arm movement demonstration
- Real-time joint control and trajectory planning
- Safety checks and validation
- Complete arm movement sequence (zero posture → lift arms → return → release)

### wav.py
Simple WAV file writer for audio recording functionality.

## Usage

```bash
# Run the main system
python3 main.py <network_interface>

# Run with arm demonstration
python3 main.py <network_interface> demo

# Examples
python3 main.py eth0
python3 main.py eth0 demo

# Run arm demonstration standalone
python3 RobotArmDemo.py eth0

# Run arm demonstration example
python3 arm_demo_example.py eth0
```

## Features

### System Initialization
- Comprehensive system self-check
- Network interface validation
- Component health monitoring
- Resource availability checks

### Audio System
- Real-time ASR message processing
- Multicast audio recording
- TTS functionality in Chinese and English
- Volume and LED control
- Audio file saving

### Action System
- Locomotion commands (stand, sit, move, turn)
- Arm control (init, home, stop)
- Gesture execution (wave, nod)
- Action sequence coordination

### Arm Demonstration System
- Complete arm movement sequence demonstration
- Multi-stage trajectory planning (4 stages, ~21 seconds total)
- Real-time joint control with position and velocity feedback
- Safety checks and obstacle warnings
- Low-level SDK DDS integration for precise control

## Dependencies

- unitree_sdk2py
- socket
- threading
- struct
- time
- platform
- numpy (for mathematical operations)
- psutil (optional, for enhanced system monitoring)
- wave (for WAV file operations)

## Network Requirements

- Network interface supporting multicast
- Access to robot's multicast audio stream (239.255.0.1:7401)
- Proper firewall configuration for multicast traffic

## Notes

- On Windows, you may need to run as Administrator for multicast functionality
- The system performs comprehensive self-checks before operation
- All modules are designed for graceful error handling and recovery
- The modular architecture allows for easy extension and maintenance
- **IMPORTANT**: Ensure there are no obstacles around the robot when running arm demonstrations
- The arm demonstration includes safety warnings and requires user confirmation
- Arm demonstrations use low-level control and should be run in a safe environment
