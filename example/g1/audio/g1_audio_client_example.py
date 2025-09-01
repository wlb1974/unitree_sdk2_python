import time
import sys
import socket
import struct
import threading
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.idl.std_msgs.msg.dds_ import String_

# ASR Configuration constants
AUDIO_SUBSCRIBE_TOPIC = "rt/audio_msg"
GROUP_IP = "239.168.123.161"
PORT = 5555
WAV_SECOND = 5  # record seconds
WAV_LEN = 16000 * 2 * WAV_SECOND  # 16kHz, 16-bit, mono
CHUNK_SIZE = 96000  # 3 seconds

class ASRAudioClient:
    def __init__(self, network_interface):
        self.network_interface = network_interface
        self.sock = None
        self.recording_thread = None
        self.is_recording = False
        
        # Initialize channel factory
        ChannelFactoryInitialize(0, network_interface)
        
        # Initialize audio client
        self.audio_client = AudioClient()
        self.audio_client.SetTimeout(10.0)
        self.audio_client.Init()
        
        # Initialize ASR subscriber
        self.asr_subscriber = ChannelSubscriber(AUDIO_SUBSCRIBE_TOPIC, String_)
        self.asr_subscriber.Init(self.asr_handler, 10)
        
        # Initialize loco client
        self.sport_client = LocoClient()
        self.sport_client.SetTimeout(10.0)
        self.sport_client.Init()
    
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
    
    def record_audio_thread(self):
        """Thread function for recording audio from multicast"""
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1.0)  # 1 second timeout
            local_addr = ('', PORT)
            self.sock.bind(local_addr)
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(GROUP_IP), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            local_ip = self.get_local_ip_for_multicast()
            print(f"local ip: {local_ip}")
            
            # Record audio data
            total_bytes = 0
            pcm_data = []
            print("start record!")
            
            while total_bytes < WAV_LEN and self.is_recording:
                try:
                    buffer, addr = self.sock.recvfrom(2048)
                    if buffer:
                        len_data = len(buffer)
                        sample_count = len_data // 2
                        samples = struct.unpack(f'<{sample_count}h', buffer)
                        pcm_data.extend(samples)
                        total_bytes += len_data
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error receiving audio data: {e}")
                    break
            
            # Save recorded audio to WAV file
            if pcm_data:
                from wav import write_wave
                success = write_wave("record.wav", 16000, pcm_data, 1)
                if success:
                    print("record finish! save to record.wav")
                else:
                    print("Failed to save WAV file")
            
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
            print("Audio recording started...")
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        print("Audio recording stopped.")
    
    def test_basic_audio_functions(self):
        """Test basic audio client functionality"""
        # Test volume control
        ret = self.audio_client.GetVolume()
        print("debug GetVolume: ", ret)
        
        self.audio_client.SetVolume(85)
        
        ret = self.audio_client.GetVolume()
        print("debug GetVolume: ", ret)
        
        # Test TTS
        self.audio_client.TtsMaker("大家好!我是宇树科技人形机器人。语音开发测试例程运行成功！ 很高兴认识你！", 0)
        time.sleep(8)
        
        self.audio_client.TtsMaker("接下来测试灯带开发例程！", 0)
        time.sleep(1)
        
        # Test LED control
        self.audio_client.LedControl(255, 0, 0)  # Red
        time.sleep(1)
        self.audio_client.LedControl(0, 255, 0)  # Green
        time.sleep(1)
        self.audio_client.LedControl(0, 0, 255)  # Blue
        
        time.sleep(3)
        self.audio_client.TtsMaker("测试完毕，谢谢大家！", 0)
    
    def run_asr_test(self):
        """Run the complete ASR test including recording"""
        print("AudioClient API test finish, ASR start...")
        
        # Start recording in background
        self.start_recording()
        
        try:
            # Keep running to receive ASR messages
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping ASR test...")
        finally:
            self.stop_recording()
            self.asr_subscriber.Close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} networkInterface")
        sys.exit(-1)

    network_interface = sys.argv[1]
    
    # Create ASR audio client
    asr_client = ASRAudioClient(network_interface)
    
    try:
        # Test basic audio functions first
        asr_client.test_basic_audio_functions()
        
        # Run ASR test
        asr_client.run_asr_test()
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if hasattr(asr_client, 'asr_subscriber'):
            asr_client.asr_subscriber.Close()
    
