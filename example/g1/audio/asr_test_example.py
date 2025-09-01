#!/usr/bin/env python3
"""
ASR Test Example for Unitree G1 Robot
This example demonstrates ASR (Automatic Speech Recognition) functionality
extracted from the C++ audio client example.

Features:
1. ASR message subscription from rt/audio_msg topic
2. Multicast UDP audio recording
3. Audio data processing and WAV file saving
4. Threading for non-blocking audio recording

Usage: python3 asr_test_example.py <network_interface>
Example: python3 asr_test_example.py eth0
"""

import time
import sys
import socket
import struct
import threading
import platform
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.idl.std_msgs.msg.dds_ import String_

# ASR Configuration constants (matching C++ code)
AUDIO_SUBSCRIBE_TOPIC = "rt/audio_msg"
GROUP_IP = "239.168.123.161"  # 正确的组播地址
PORT = 5555
WAV_SECOND = 5  # record seconds
WAV_LEN = 16000 * 2 * WAV_SECOND  # 16kHz, 16-bit, mono
CHUNK_SIZE = 96000  # 3 seconds

class ASRTestClient:
    def __init__(self, network_interface):
        self.network_interface = network_interface
        self.sock = None
        self.recording_thread = None
        self.is_recording = False
        
        print(f"Initializing ASR Test Client with network interface: {network_interface}")
        print(f"Platform: {platform.system()} {platform.release()}")
        
        # Initialize channel factory
        ChannelFactoryInitialize(0, network_interface)
        
        # Initialize audio client
        self.audio_client = AudioClient()
        self.audio_client.SetTimeout(10.0)
        self.audio_client.Init()
        
        # Initialize ASR subscriber
        self.asr_subscriber = ChannelSubscriber(AUDIO_SUBSCRIBE_TOPIC, String_)
        self.asr_subscriber.Init(self.asr_handler, 10)
        
        print("ASR Test Client initialized successfully")
    
    def asr_handler(self, msg):
        """Handle ASR messages from the rt/audio_msg topic"""
        print(f"Topic:\"rt/audio_msg\" recv: {msg.data}")
    
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
        
        # Test Chinese TTS
        print("Testing Chinese TTS...")
        ret = self.audio_client.TtsMaker("你好。我是宇树科技的机器人。例程启动成功", 0)
        print(f"TtsMaker API ret: {ret}")
        time.sleep(5)
        
        # Test English TTS
        print("Testing English TTS...")
        ret = self.audio_client.TtsMaker(
            "Hello. I'm a robot from Unitree Robotics. The example has started successfully.", 1)
        print(f"TtsMaker API ret: {ret}")
        time.sleep(8)
        
        print("TTS test completed")
    
    def test_volume_control(self):
        """Test volume control functionality"""
        print("\n=== Testing Volume Control ===")
        
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
    
    def test_led_control(self):
        """Test LED control functionality"""
        print("\n=== Testing LED Control ===")
        
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
    
    def run_complete_test(self):
        """Run the complete ASR test suite"""
        print("\n" + "="*50)
        print("Starting Complete ASR Test Suite")
        print("="*50)
        
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
            print("Basic audio tests completed. Starting ASR test...")
            print("="*50)
            
            # Start recording in background
            self.start_recording()
            
            print("ASR test is running. Press Ctrl+C to stop...")
            print("Listening for ASR messages on topic: rt/audio_msg")
            print("Recording audio from multicast: {}:{}".format(GROUP_IP, PORT))
            print("\nIf no audio data is received, check:")
            print("1. Robot multicast audio streaming configuration")
            print("2. Network multicast support")
            print("3. Firewall settings")
            print("4. Run as administrator (Windows)")
            
            # Keep running to receive ASR messages
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nStopping ASR test...")
        except Exception as e:
            print(f"\nError during test: {e}")
        finally:
            self.stop_recording()
            self.asr_subscriber.Close()
            print("ASR test completed.")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <network_interface>")
        print("Example: python3 {sys.argv[0]} eth0")
        print("\nNote: On Windows, you may need to run as Administrator")
        sys.exit(1)

    network_interface = sys.argv[1]
    
    print("Unitree G1 ASR Test Example")
    print("=" * 40)
    
    # Create ASR test client
    asr_client = ASRTestClient(network_interface)
    
    try:
        # Run complete test suite
        asr_client.run_complete_test()
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
