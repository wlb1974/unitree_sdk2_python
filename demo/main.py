#!/usr/bin/env python3
"""
Main Entry Point for Unitree G1 Robot Control System
This module handles basic initialization and system self-check functionality.

Features:
1. System initialization and configuration
2. Network interface validation
3. Component health checks
4. Integration of audio and action modules

Usage: python3 main.py <network_interface>
Example: python3 main.py eth0
"""

import time
import sys
import platform
import socket
from RobotAudio import RobotAudio
from RobotAction import RobotAction
from RobotArmDemo import RobotArmDemo
import psutil


class RobotSystem:
    def __init__(self, network_interface):
        self.network_interface = network_interface
        self.audio_module = None
        self.action_module = None
        self.arm_demo_module = None
        self.system_ready = False
        
        print("=" * 60)
        print("Unitree G1 Robot Control System")
        print("=" * 60)
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python Version: {sys.version}")
        print(f"Network Interface: {network_interface}")
        print("=" * 60)
    
    def system_self_check(self):
        """Perform comprehensive system self-check"""
        print("\n=== System Self-Check ===")
        
        checks_passed = 0
        total_checks = 7
        
        # Check 1: Network interface validation
        if self._check_network_interface():
            checks_passed += 1
            print("✓ Network interface validation passed")
        else:
            print("✗ Network interface validation failed")
        
        # Check 2: Network connectivity
        if self._check_network_connectivity():
            checks_passed += 1
            print("✓ Network connectivity check passed")
        else:
            print("✗ Network connectivity check failed")
        
        # Check 3: Required modules availability
        if self._check_required_modules():
            checks_passed += 1
            print("✓ Required modules check passed")
        else:
            print("✗ Required modules check failed")
        
        # Check 4: System resources
        if self._check_system_resources():
            checks_passed += 1
            print("✓ System resources check passed")
        else:
            print("✗ System resources check failed")
        
        # Check 5: Audio module initialization
        if self._check_audio_module():
            checks_passed += 1
            print("✓ Audio module initialization passed")
        else:
            print("✗ Audio module initialization failed")
        
        # Check 6: Action module initialization
        if self._check_action_module():
            checks_passed += 1
            print("✓ Action module initialization passed")
        else:
            print("✗ Action module initialization failed")
        
        # Check 7: Arm demo module initialization
        if self._check_arm_demo_module():
            checks_passed += 1
            print("✓ Arm demo module initialization passed")
        else:
            print("✗ Arm demo module initialization failed")
        
        print(f"\nSystem Self-Check Results: {checks_passed}/{total_checks} checks passed")
        
        if checks_passed == total_checks:
            self.system_ready = True
            print("✓ System is ready for operation")
            return True
        else:
            print("✗ System is not ready - some checks failed")
            return False
    
    def _check_network_interface(self):
        """Check if the specified network interface exists and is valid"""
        try:
            # Try to get network interface information
            try:
                import psutil
                interfaces = psutil.net_if_addrs()
                if self.network_interface in interfaces:
                    return True
                else:
                    print(f"  Warning: Network interface '{self.network_interface}' not found")
                    print(f"  Available interfaces: {list(interfaces.keys())}")
                    return False
            except ImportError:
                print("  Warning: psutil not available, skipping detailed interface check")
                return True  # Assume it's valid if we can't check
        except Exception as e:
            print(f"  Error checking network interface: {e}")
            return False
    
    def _check_network_connectivity(self):
        """Check basic network connectivity"""
        try:
            # Test DNS resolution
            socket.gethostbyname("8.8.8.8")
            return True
        except Exception as e:
            print(f"  Error: Network connectivity test failed: {e}")
            return False
    
    def _check_required_modules(self):
        """Check if all required modules are available"""
        required_modules = [
            'unitree_sdk2py',
            'socket',
            'threading',
            'struct',
            'time'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"  Missing modules: {missing_modules}")
            return False
        return True
    
    def _check_system_resources(self):
        """Check system resources (memory, CPU, etc.)"""
        try:
            try:
                
                # Check available memory (should have at least 100MB free)
                memory = psutil.virtual_memory()
                if memory.available < 100 * 1024 * 1024:  # 100MB
                    print(f"  Warning: Low memory available: {memory.available // (1024*1024)}MB")
                    return False
                
                # Check CPU usage (should be less than 90%)
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > 90:
                    print(f"  Warning: High CPU usage: {cpu_percent}%")
                    return False
                
                return True
            except ImportError:
                print("  Warning: psutil not available, skipping resource check")
                return True  # Assume OK if we can't check
        except Exception as e:
            print(f"  Error checking system resources: {e}")
            return False
    
    def _check_audio_module(self):
        """Check audio module initialization"""
        try:
            self.audio_module = RobotAudio(self.network_interface)
            return True
        except Exception as e:
            print(f"  Error initializing audio module: {e}")
            return False
    
    def _check_action_module(self):
        """Check action module initialization"""
        try:
            self.action_module = RobotAction(self.network_interface)
            return True
        except Exception as e:
            print(f"  Error initializing action module: {e}")
            return False
    
    def _check_arm_demo_module(self):
        """Check arm demo module initialization"""
        try:
            self.arm_demo_module = RobotArmDemo(self.network_interface)
            return True
        except Exception as e:
            print(f"  Error initializing arm demo module: {e}")
            return False
    
    def initialize_system(self):
        """Initialize the complete robot system"""
        print("\n=== System Initialization ===")
        
        if not self.system_self_check():
            print("System initialization failed due to self-check failures")
            return False
        
        print("\nInitializing robot components...")
        
        try:
            # Initialize audio module
            if self.audio_module:
                print("Initializing audio module...")
                self.audio_module.initialize()
            
            # Initialize action module
            if self.action_module:
                print("Initializing action module...")
                self.action_module.initialize()
            
            # Initialize arm demo module
            if self.arm_demo_module:
                print("Initializing arm demo module...")
                self.arm_demo_module.initialize()
            
            print("✓ System initialization completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ System initialization failed: {e}")
            return False
    
    def run_system(self):
        """Run the main system loop"""
        if not self.system_ready:
            print("System is not ready. Please run system initialization first.")
            return
        
        print("\n=== Starting Robot System ===")
        print("System is now running. Press Ctrl+C to stop.")
        
        try:
            # Start audio processing
            if self.audio_module:
                self.audio_module.start()
            
            # Start action processing
            if self.action_module:
                self.action_module.start()
            
            # Start arm demo (optional - can be triggered manually)
            # if self.arm_demo_module:
            #     self.arm_demo_module.start_demonstration()
            
            # Main system loop
            while True:
                time.sleep(1)
                
                # Check system health periodically
                if not self._check_system_health():
                    print("System health check failed. Stopping system.")
                    break
                    
        except KeyboardInterrupt:
            print("\nShutting down system...")
        except Exception as e:
            print(f"System error: {e}")
        finally:
            self.shutdown_system()
    
    def _check_system_health(self):
        """Periodic system health check"""
        # This could be expanded to check various system components
        return True
    
    def shutdown_system(self):
        """Gracefully shutdown the system"""
        print("\n=== System Shutdown ===")
        
        try:
            if self.audio_module:
                print("Shutting down audio module...")
                self.audio_module.shutdown()
            
            if self.action_module:
                print("Shutting down action module...")
                self.action_module.shutdown()
            
            if self.arm_demo_module:
                print("Shutting down arm demo module...")
                self.arm_demo_module.shutdown()
            
            print("✓ System shutdown completed")
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
    
    def run_arm_demonstration(self):
        """Run the arm demonstration sequence"""
        if not self.arm_demo_module:
            print("Arm demo module not available")
            return False
        
        print("\n" + "="*60)
        print("Starting Arm Demonstration")
        print("="*60)
        
        try:
            # Start the demonstration
            if self.arm_demo_module.start_demonstration():
                # Wait for completion
                success = self.arm_demo_module.wait_for_completion()
                if success:
                    print("✓ Arm demonstration completed successfully")
                    return True
                else:
                    print("✗ Arm demonstration failed or timed out")
                    return False
            else:
                print("✗ Failed to start arm demonstration")
                return False
                
        except Exception as e:
            print(f"Error during arm demonstration: {e}")
            return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <network_interface> [demo]")
        print("Example: python3 {sys.argv[0]} eth0")
        print("Example: python3 {sys.argv[0]} eth0 demo")
        print("\nNote: On Windows, you may need to run as Administrator")
        print("Add 'demo' argument to run arm demonstration after initialization")
        sys.exit(1)

    network_interface = sys.argv[1]
    run_demo = len(sys.argv) > 2 and sys.argv[2].lower() == 'demo'
    
    # Create and initialize robot system
    robot_system = RobotSystem(network_interface)
    
    try:
        # Initialize system
        if robot_system.initialize_system():
            if run_demo:
                # Run arm demonstration
                print("\nRunning arm demonstration...")
                robot_system.run_arm_demonstration()
            else:
                # Run normal system
                robot_system.run_system()
        else:
            print("Failed to initialize system. Exiting.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
