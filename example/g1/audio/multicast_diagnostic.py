#!/usr/bin/env python3
"""
Multicast Diagnostic Tool for Unitree G1 Robot
This script helps diagnose multicast connectivity issues.

Usage: python3 multicast_diagnostic.py
"""

import socket
import struct
import time
import platform
import subprocess
import sys

# Configuration
GROUP_IP = "239.255.0.1"
PORT = 7400
TEST_DURATION = 10  # seconds

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_platform():
    """Check platform information"""
    print_header("Platform Information")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python Version: {sys.version}")
    
    if platform.system() == "Windows":
        print("Note: Windows may require administrator privileges for multicast")

def check_network_interfaces():
    """Check available network interfaces"""
    print_header("Network Interfaces")
    
    try:
        # Get local IP addresses
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"Hostname: {hostname}")
        print(f"Local IP: {local_ip}")
        
        # Try to get external IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            external_ip = s.getsockname()[0]
            s.close()
            print(f"External IP: {external_ip}")
            
            # Check subnet
            if external_ip.startswith("192.168.123."):
                print("✓ IP is in expected subnet 192.168.123.x")
            else:
                print(f"⚠ IP {external_ip} is not in expected subnet 192.168.123.x")
                
        except Exception as e:
            print(f"Could not determine external IP: {e}")
            
    except Exception as e:
        print(f"Error checking network interfaces: {e}")

def check_multicast_support():
    """Check if multicast is supported"""
    print_header("Multicast Support Check")
    
    try:
        # Test basic multicast socket creation
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("✓ UDP socket creation: OK")
        
        # Test multicast group join
        try:
            mreq = struct.pack("4sl", socket.inet_aton(GROUP_IP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            print(f"✓ Multicast group join ({GROUP_IP}): OK")
            
            # Test binding to port
            sock.bind(('', PORT))
            print(f"✓ Port binding ({PORT}): OK")
            
        except Exception as e:
            print(f"✗ Multicast group join failed: {e}")
            return False
        finally:
            sock.close()
            
        return True
        
    except Exception as e:
        print(f"✗ Socket creation failed: {e}")
        return False

def test_multicast_reception():
    """Test actual multicast data reception"""
    print_header("Multicast Reception Test")
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        
        # Set socket options
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind and join multicast group
        sock.bind(('', PORT))
        mreq = struct.pack("4sl", socket.inet_aton(GROUP_IP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        print(f"Listening on multicast {GROUP_IP}:{PORT}")
        print(f"Test duration: {TEST_DURATION} seconds")
        print("Waiting for data...")
        
        start_time = time.time()
        packet_count = 0
        total_bytes = 0
        
        while time.time() - start_time < TEST_DURATION:
            try:
                data, addr = sock.recvfrom(2048)
                packet_count += 1
                total_bytes += len(data)
                
                print(f"✓ Received packet {packet_count}: {len(data)} bytes from {addr}")
                
                # Show first few bytes as hex
                if len(data) > 0:
                    hex_data = ' '.join([f'{b:02x}' for b in data[:8]])
                    print(f"  First 8 bytes: {hex_data}")
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"✗ Error receiving data: {e}")
                break
        
        # Print results
        elapsed = time.time() - start_time
        print(f"\nTest Results:")
        print(f"  Duration: {elapsed:.1f} seconds")
        print(f"  Packets received: {packet_count}")
        print(f"  Total bytes: {total_bytes}")
        
        if packet_count > 0:
            print(f"  Average packet size: {total_bytes // packet_count if packet_count > 0 else 0} bytes")
            print("✓ Multicast reception: SUCCESS")
        else:
            print("✗ Multicast reception: NO DATA RECEIVED")
            print("\nPossible causes:")
            print("1. Robot is not streaming audio to multicast")
            print("2. Network doesn't support multicast routing")
            print("3. Firewall blocking multicast traffic")
            print("4. Wrong multicast address or port")
        
        sock.close()
        return packet_count > 0
        
    except Exception as e:
        print(f"✗ Multicast reception test failed: {e}")
        return False

def check_firewall():
    """Check firewall status (Windows)"""
    print_header("Firewall Check")
    
    if platform.system() == "Windows":
        try:
            # Check Windows Firewall status
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles"], 
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                if "ON" in output:
                    print("⚠ Windows Firewall is ON - may block multicast")
                    print("  Consider temporarily disabling for testing")
                else:
                    print("✓ Windows Firewall is OFF")
            else:
                print("Could not check firewall status")
                
        except Exception as e:
            print(f"Error checking firewall: {e}")
    else:
        print("Firewall check not implemented for this platform")

def run_connectivity_tests():
    """Run basic connectivity tests"""
    print_header("Connectivity Tests")
    
    # Test basic internet connectivity
    try:
        socket.gethostbyname("8.8.8.8")
        print("✓ Basic internet connectivity: OK")
    except:
        print("✗ Basic internet connectivity: FAILED")
    
    # Test DNS resolution
    try:
        socket.gethostbyname("www.google.com")
        print("✓ DNS resolution: OK")
    except:
        print("✗ DNS resolution: FAILED")

def main():
    print("Unitree G1 Multicast Diagnostic Tool")
    print("=" * 50)
    
    # Run all diagnostic checks
    check_platform()
    check_network_interfaces()
    check_multicast_support()
    check_firewall()
    run_connectivity_tests()
    
    print_header("Multicast Test")
    print("Starting multicast reception test...")
    success = test_multicast_reception()
    
    print_header("Summary")
    if success:
        print("✓ Multicast is working correctly!")
        print("  If you're still not receiving audio data, the issue may be:")
        print("  - Robot configuration (not streaming to multicast)")
        print("  - Wrong multicast address/port in robot settings")
    else:
        print("✗ Multicast connectivity issues detected")
        print("\nRecommended actions:")
        print("1. Run as Administrator (Windows)")
        print("2. Check robot multicast audio streaming configuration")
        print("3. Verify network supports multicast routing")
        print("4. Temporarily disable firewall for testing")
        print("5. Check with network administrator")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
    except Exception as e:
        print(f"\nDiagnostic failed: {e}")
        sys.exit(1)
