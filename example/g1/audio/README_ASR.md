# ASR (Automatic Speech Recognition) Examples for Unitree G1 Robot

This directory contains Python examples demonstrating ASR functionality extracted from the C++ audio client example.

## Overview

The ASR examples provide the following functionality:

1. **ASR Message Subscription**: Subscribe to the `rt/audio_msg` topic to receive speech recognition results
2. **Multicast Audio Recording**: Record audio data from a multicast UDP stream
3. **Audio Processing**: Convert raw PCM data to WAV format
4. **Threading**: Non-blocking audio recording with background threads

## Files

- `g1_audio_client_example.py` - Enhanced version with ASR functionality
- `asr_test_example.py` - Dedicated ASR test example
- `wav.py` - WAV file handling utilities
- `README_ASR.md` - This documentation file

## Prerequisites

- Python 3.6+
- Unitree SDK2 Python package
- Network interface configured for robot communication
- Access to multicast network (239.168.123.161:5555)

## Configuration

The examples use the following configuration constants (matching the C++ code):

```python
AUDIO_SUBSCRIBE_TOPIC = "rt/audio_msg"    # ASR message topic
GROUP_IP = "239.168.123.161"              # Multicast group IP
PORT = 5555                               # Multicast port
WAV_SECOND = 5                            # Recording duration in seconds
WAV_LEN = 16000 * 2 * WAV_SECOND         # Total bytes to record
CHUNK_SIZE = 96000                        # Chunk size for processing
```

## Usage

### Basic ASR Test

```bash
python3 asr_test_example.py <network_interface>
```

Example:
```bash
python3 asr_test_example.py eth0
```

### Enhanced Audio Client with ASR

```bash
python3 g1_audio_client_example.py <network_interface>
```

## Features

### 1. ASR Message Handling

The examples subscribe to the `rt/audio_msg` topic and handle incoming speech recognition results:

```python
def asr_handler(self, msg):
    """Handle ASR messages from the rt/audio_msg topic"""
    print(f"Topic:\"rt/audio_msg\" recv: {msg.data}")
```

### 2. Multicast Audio Recording

Audio data is received from a multicast UDP stream:

```python
# Create UDP socket and join multicast group
self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
self.sock.settimeout(1.0)
local_addr = ('', PORT)
self.sock.bind(local_addr)

# Join multicast group
mreq = struct.pack("4sl", socket.inet_aton(GROUP_IP), socket.INADDR_ANY)
self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
```

### 3. Audio Data Processing

Raw PCM data is processed and converted to WAV format:

```python
# Convert bytes to 16-bit samples
samples = struct.unpack(f'<{sample_count}h', buffer)
pcm_data.extend(samples)

# Save to WAV file
success = write_wave("record.wav", 16000, pcm_data, 1)
```

### 4. Threading

Audio recording runs in a background thread to avoid blocking:

```python
def start_recording(self):
    if not self.is_recording:
        self.is_recording = True
        self.recording_thread = threading.Thread(
            target=self.record_audio_thread, daemon=True)
        self.recording_thread.start()
```

## Test Sequence

The examples follow this test sequence:

1. **Initialization**: Set up channel factory, audio client, and ASR subscriber
2. **Volume Control**: Test volume get/set functionality
3. **TTS Testing**: Test text-to-speech in Chinese and English
4. **LED Control**: Test RGB LED functionality
5. **ASR Testing**: Start audio recording and listen for ASR messages
6. **Cleanup**: Stop recording and close connections

## Network Requirements

- **Multicast Support**: The network must support multicast traffic on 239.168.123.161:5555
- **Network Interface**: Must be configured for robot communication
- **Subnet**: Preferably on 192.168.123.x subnet for optimal performance

## Troubleshooting

### Common Issues

1. **Network Interface Error**: Ensure the specified network interface exists and is configured
2. **Multicast Join Failure**: Check if multicast is enabled on your network
3. **No Audio Data**: Verify the robot is streaming audio to the multicast address
4. **ASR Messages Not Received**: Check if the robot's ASR service is running

### Debug Information

The examples provide detailed logging:

- Network interface and IP address information
- Multicast group joining status
- Audio recording progress
- ASR message reception
- Error details for troubleshooting

## Differences from C++ Version

The Python version includes several improvements:

- **Better Error Handling**: More robust error handling and recovery
- **Progress Indicators**: Real-time recording progress updates
- **Graceful Shutdown**: Proper cleanup of resources and threads
- **Modular Design**: Separated concerns into distinct methods
- **Documentation**: Comprehensive inline documentation

## Extending the Examples

The examples can be extended for:

- **Custom Audio Processing**: Modify the audio data handling
- **Different Audio Formats**: Support for other audio formats
- **Real-time Processing**: Implement real-time audio analysis
- **Integration**: Combine with other robot control features

## Support

For issues or questions:

1. Check the network configuration
2. Verify the robot's ASR service is running
3. Review the error messages and debug output
4. Ensure all prerequisites are met

## License

This code follows the same license as the Unitree SDK2 Python package.
