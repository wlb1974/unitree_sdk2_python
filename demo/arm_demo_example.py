#!/usr/bin/env python3
"""
Arm Demonstration Example
This script demonstrates how to use the RobotArmDemo module independently.
"""

import sys
import time
from RobotArmDemo import RobotArmDemo

def main():
    """Example usage of the arm demonstration module"""
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <network_interface>")
        print("Example: python3 {sys.argv[0]} eth0")
        sys.exit(1)

    network_interface = sys.argv[1]
    
    print("Unitree G1 Arm Demonstration Example")
    print("=" * 50)
    
    # Create arm demonstration instance
    arm_demo = RobotArmDemo(network_interface)
    
    try:
        # Initialize the module
        print("Initializing arm demonstration...")
        arm_demo.initialize()
        
        # Get initial status
        status = arm_demo.get_status()
        print(f"Initial status: {status}")
        
        # Start the demonstration
        print("\nStarting arm demonstration...")
        if arm_demo.start_demonstration():
            print("Arm demonstration started successfully!")
            
            # Monitor progress
            while not arm_demo.done:
                status = arm_demo.get_status()
                print(f"Status: {status['stage']} (Time: {status['time']:.1f}s)")
                time.sleep(1.0)
            
            print("Arm demonstration completed!")
        else:
            print("Failed to start arm demonstration")
            
    except KeyboardInterrupt:
        print("\nStopping demonstration...")
        arm_demo.stop_demonstration()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        arm_demo.shutdown()
        print("Example completed")

if __name__ == "__main__":
    main()
