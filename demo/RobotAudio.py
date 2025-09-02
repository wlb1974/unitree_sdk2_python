#!/usr/bin/env python3
"""
Robot Audio Module for Unitree G1 Robot
This module handles all audio-related functionality including:
- ASR (Automatic Speech Recognition)
- TTS (Text-to-Speech)
- Audio recording and playback
- Volume control
- LED control

Features:
1. ASR message subscription from rt/audio_msg topic
2. Multicast UDP audio recording
3. Audio data processing and WAV file saving
4. Threading for non-blocking audio recording
5. TTS functionality for speech synthesis
6. Volume and LED control
"""

import time
import socket
import struct
import threading
import platform
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.idl.std_msgs.msg.dds_ import String_
import json

# Audio Configuration constants
AUDIO_SUBSCRIBE_TOPIC = "rt/audio_msg"
GROUP_IP = "239.255.0.1"  # Multicast address
PORT = 7401
WAV_SECOND = 5  # record seconds
WAV_LEN = 16000 * 2 * WAV_SECOND  # 16kHz, 16-bit, mono
CHUNK_SIZE = 96000  # 3 seconds

class RobotAudio:
    def __init__(self, network_interface):
        self.network_interface = network_interface
        self.sock = None
        self.recording_thread = None
        self.is_recording = False
        self.is_initialized = False
        
        # Audio components
        self.audio_client = None
        self.asr_subscriber = None
        self.asr_callback = None
        
        print(f"Initializing Robot Audio Module with network interface: {network_interface}")
        print(f"Platform: {platform.system()} {platform.release()}")
    
    def initialize(self):
        """Initialize the audio module"""
        try:
            print("Initializing audio module components...")
            
            # Initialize channel factory
            ChannelFactoryInitialize(0, self.network_interface)
            
            # Initialize audio client
            self.audio_client = AudioClient()
            self.audio_client.SetTimeout(10.0)
            self.audio_client.Init()
            
            # Initialize ASR subscriber
            self.asr_subscriber = ChannelSubscriber(AUDIO_SUBSCRIBE_TOPIC, String_)
            self.asr_subscriber.Init(self.asr_handler, 10)
            
            self.is_initialized = True
            print("✓ Audio module initialized successfully")
            
        except Exception as e:
            print(f"✗ Audio module initialization failed: {e}")
            raise
    
    def set_asr_callback(self, callback):
        """Set the callback function for ASR messages"""
        self.asr_callback = callback
    
    def asr_handler(self, msg):
        """Handle ASR messages from the rt/audio_msg topic"""
        print(f"ASR Message received: {msg.data}")
        try:
            data = json.loads(msg.data)
            if hasattr(data, 'text') and data['text'] != '':
                print(f"ASR: {data['text']}")
                if self.asr_callback:
                    self.asr_callback(data['text'])
        except Exception as e:
            print(f"Error in ASR handler: {e}")
        # Here you could add logic to process the recognized speech
        # and trigger appropriate actions
    
    def get_local_ip_for_multicast(self):
        """Get local IP address for multicast interface"""
        try:
            # Try to get local IP by connecting to external address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Check if it's in the expected subnet
            if local_ip.startswith("192.168.123."):
                return local_ip
            else:
                print(f"Warning: Local IP {local_ip} is not in expected subnet 192.168.123.x")
                return local_ip
        except Exception as e:
            print(f"Error getting local IP: {e}")
            return "127.0.0.1"
    
    def test_multicast_connectivity(self):
        """Test basic multicast connectivity"""
        print("\n=== Testing Multicast Connectivity ===")
        
        try:
            # Create test socket
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.settimeout(2.0)
            
            # Bind to any address
            test_sock.bind(('', 0))
            print(f"Test socket bound to port: {test_sock.getsockname()[1]}")
            
            # Try to join multicast group
            try:
                mreq = struct.pack("4sl", socket.inet_aton(GROUP_IP), socket.INADDR_ANY)
                test_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                print(f"Successfully joined multicast group: {GROUP_IP}")
            except Exception as e:
                print(f"Failed to join multicast group: {e}")
                return False
            
            # Test receiving data
            print("Testing multicast data reception (timeout: 2s)...")
            try:
                data, addr = test_sock.recvfrom(1024)
                print(f"Received data from {addr}: {len(data)} bytes")
                return True
            except socket.timeout:
                print("No data received within timeout (this is normal if no one is sending)")
                return True
            except Exception as e:
                print(f"Error receiving data: {e}")
                return False
            finally:
                test_sock.close()
                
        except Exception as e:
            print(f"Multicast connectivity test failed: {e}")
            return False
    
    def record_audio_thread(self):
        """Thread function for recording audio from multicast"""
        try:
            print("Setting up multicast audio recording...")
            
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1.0)  # 1 second timeout
            
            # Set socket options for better multicast support
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to specific port
            local_addr = ('', PORT)
            self.sock.bind(local_addr)
            print(f"Socket bound to port {PORT}")
            
            # Join multicast group
            try:
                mreq = struct.pack("4sl", socket.inet_aton(GROUP_IP), socket.INADDR_ANY)
                self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                print(f"Successfully joined multicast group: {GROUP_IP}")
            except Exception as e:
                print(f"Failed to join multicast group: {e}")
                return
            
            local_ip = self.get_local_ip_for_multicast()
            print(f"Local IP: {local_ip}")
            print(f"Multicast group: {GROUP_IP}:{PORT}")
            
            # Record audio data
            total_bytes = 0
            pcm_data = []
            print("Starting audio recording...")
            print("Waiting for audio data from multicast stream...")
            
            # Add packet counter for debugging
            packet_count = 0
            last_packet_time = time.time()
            
            while total_bytes < WAV_LEN and self.is_recording:
                try:
                    buffer, addr = self.sock.recvfrom(2048)
                    if buffer:
                        packet_count += 1
                        current_time = time.time()
                        len_data = len(buffer)
                        sample_count = len_data // 2
                        samples = struct.unpack(f'<{sample_count}h', buffer)
                        pcm_data.extend(samples)
                        total_bytes += len_data
                        
                        # Print packet info for first few packets
                        if packet_count <= 5:
                            print(f"Packet {packet_count}: {len_data} bytes from {addr}")
                            print(f"  First 4 samples: {samples[:4] if len(samples) >= 4 else samples}")
                        
                        # Progress indicator
                        if total_bytes % (WAV_LEN // 10) == 0:
                            progress = (total_bytes / WAV_LEN) * 100
                            print(f"Recording progress: {progress:.1f}% ({total_bytes}/{WAV_LEN} bytes)")
                        
                        last_packet_time = current_time
                            
                except socket.timeout:
                    # Print timeout message every 10 seconds
                    current_time = time.time()
                    if current_time - last_packet_time > 10:
                        print(f"No audio data received for {int(current_time - last_packet_time)}s...")
                        print("Possible issues:")
                        print("  1. Robot is not streaming audio to multicast")
                        print("  2. Network doesn't support multicast")
                        print("  3. Firewall blocking multicast traffic")
                        print("  4. Wrong multicast address or port")
                        last_packet_time = current_time
                    continue
                except Exception as e:
                    print(f"Error receiving audio data: {e}")
                    break
            
            # Print final statistics
            print(f"\nRecording completed:")
            print(f"  Total packets received: {packet_count}")
            print(f"  Total bytes received: {total_bytes}")
            print(f"  Total samples: {len(pcm_data)}")
            
            # Save recorded audio to WAV file
            if pcm_data:
                print(f"Recording complete! Saving {len(pcm_data)} samples to WAV file...")
                try:
                    try:
                        from wav import write_wave
                        success = write_wave("record.wav", 16000, pcm_data, 1)
                        if success:
                            print("Audio saved successfully to record.wav")
                        else:
                            print("Failed to save WAV file")
                    except ImportError:
                        print("Warning: wav module not available, cannot save audio file")
                        print(f"PCM data: {len(pcm_data)} samples, {total_bytes} bytes")
                except Exception as e:
                    print(f"Error saving WAV file: {e}")
            else:
                print("No audio data recorded")
                print("\nTroubleshooting tips:")
                print("1. Check if the robot is configured to stream audio to multicast")
                print("2. Verify the multicast address and port are correct")
                print("3. Ensure your network supports multicast routing")
                print("4. Check firewall settings")
                print("5. Try running as administrator (Windows)")
            
        except Exception as e:
            print(f"Error in recording thread: {e}")
        finally:
            if self.sock:
                self.sock.close()
                self.sock = None
    
    def start_recording(self):
        """Start audio recording in a separate thread"""
        if not self.is_recording:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self.record_audio_thread, daemon=True)
            self.recording_thread.start()
            print("Audio recording started in background thread...")
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            print("Waiting for recording thread to finish...")
            self.recording_thread.join(timeout=3.0)
        print("Audio recording stopped.")
    
    def test_tts(self):
        """Test Text-to-Speech functionality"""
        print("\n=== Testing TTS (Text-to-Speech) ===")
        
        if not self.audio_client:
            print("Audio client not initialized")
            return False
        
        try:
            # Test Chinese TTS
            print("Testing Chinese TTS...")
            ret = self.audio_client.TtsMaker("你好。我是小江老师。检测程序启动成功", 0)
            print(f"TtsMaker API ret: {ret}")
            time.sleep(5)
            
            # Test English TTS
            print("Testing English TTS...")
            ret = self.audio_client.TtsMaker(
                "Hello. I'm a teacher named Jiang. The example has started successfully.", 1)
            print(f"TtsMaker API ret: {ret}")
            time.sleep(8)
            
            print("TTS test completed")
            return True
            
        except Exception as e:
            print(f"TTS test failed: {e}")
            return False
    
    def test_volume_control(self):
        """Test volume control functionality"""
        print("\n=== Testing Volume Control ===")
        
        if not self.audio_client:
            print("Audio client not initialized")
            return False
        
        try:
            # Get current volume
            ret, volume_data = self.audio_client.GetVolume()
            if ret == 0 and volume_data:
                current_volume = volume_data.get('volume', 'Unknown')
                print(f"Current volume: {current_volume}")
            else:
                print(f"GetVolume API ret: {ret}")
            
            # Set volume to 100%
            ret = self.audio_client.SetVolume(100)
            print(f"SetVolume to 100%, API ret: {ret}")
            
            # Verify volume change
            ret, volume_data = self.audio_client.GetVolume()
            if ret == 0 and volume_data:
                new_volume = volume_data.get('volume', 'Unknown')
                print(f"New volume: {new_volume}")
            
            print("Volume control test completed")
            return True
            
        except Exception as e:
            print(f"Volume control test failed: {e}")
            return False
    
    def test_led_control(self):
        """Test LED control functionality"""
        print("\n=== Testing LED Control ===")
        
        if not self.audio_client:
            print("Audio client not initialized")
            return False
        
        try:
            # Test different LED colors
            print("Testing LED colors...")
            self.audio_client.LedControl(0, 255, 0)  # Green
            time.sleep(1)
            self.audio_client.LedControl(0, 0, 0)    # Off
            time.sleep(1)
            self.audio_client.LedControl(0, 0, 255)  # Blue
            time.sleep(1)
            self.audio_client.LedControl(0, 0, 0)    # Off
            
            print("LED control test completed")
            return True
            
        except Exception as e:
            print(f"LED control test failed: {e}")
            return False
    
    def run_audio_tests(self):
        """Run comprehensive audio tests"""
        print("\n" + "="*50)
        print("Starting Audio Module Tests")
        print("="*50)
        
        if not self.is_initialized:
            print("Audio module not initialized")
            return False
        
        try:
            # Test basic audio functions
            self.test_volume_control()
            self.test_tts()
            self.test_led_control()
            
            # Test multicast connectivity
            if not self.test_multicast_connectivity():
                print("Warning: Multicast connectivity test failed!")
                print("This may indicate network configuration issues.")
            
            print("\n" + "="*50)
            print("Audio tests completed")
            print("="*50)
            return True
            
        except Exception as e:
            print(f"Audio tests failed: {e}")
            return False
    
    def start(self):
        """Start audio processing"""
        if not self.is_initialized:
            print("Audio module not initialized")
            return False
        
        print("Starting audio processing...")
        
        # Start recording in background
        self.start_recording()
        
        print("Audio processing started")
        print("Listening for ASR messages on topic: rt/audio_msg")
        print("Recording audio from multicast: {}:{}".format(GROUP_IP, PORT))
        
        return True
    
    def shutdown(self):
        """Shutdown audio module"""
        print("Shutting down audio module...")
        
        try:
            # Stop recording
            self.stop_recording()
            
            # Close ASR subscriber
            if self.asr_subscriber:
                self.asr_subscriber.Close()
            
            print("✓ Audio module shutdown completed")
            
        except Exception as e:
            print(f"Error during audio module shutdown: {e}")
    
    def speak(self, text, language=0):
        """Speak text using TTS
        
        Args:
            text (str): Text to speak
            language (int): 0 for Chinese, 1 for English
        """
        if not self.audio_client:
            print("Audio client not initialized")
            return False
        
        try:
            ret = self.audio_client.TtsMaker(text, language)
            print(f"TTS: {text} (language: {language}, ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"TTS error: {e}")
            return False
    
    def set_volume(self, volume):
        """Set audio volume
        
        Args:
            volume (int): Volume level (0-100)
        """
        if not self.audio_client:
            print("Audio client not initialized")
            return False
        
        try:
            ret = self.audio_client.SetVolume(volume)
            print(f"Volume set to {volume}% (ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"Volume control error: {e}")
            return False
    
    def set_led(self, r, g, b):
        """Set LED color
        
        Args:
            r (int): Red component (0-255)
            g (int): Green component (0-255)
            b (int): Blue component (0-255)
        """
        if not self.audio_client:
            print("Audio client not initialized")
            return False
        
        try:
            self.audio_client.LedControl(r, g, b)
            print(f"LED set to RGB({r}, {g}, {b})")
            return True
        except Exception as e:
            print(f"LED control error: {e}")
            return False
