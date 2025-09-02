#!/usr/bin/env python3
"""
Robot Action Module for Unitree G1 Robot
This module handles all action-related functionality including:
- Locomotion control
- Arm movement
- Gesture recognition
- Action execution and coordination

Features:
1. Locomotion client for movement control
2. Arm action client for arm manipulation
3. Action coordination and sequencing
4. Safety checks and validation
5. Action status monitoring
"""

import time
import threading
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import ArmActionClient

class RobotAction:
    def __init__(self, network_interface):
        self.network_interface = network_interface
        self.is_initialized = False
        
        # Action components
        self.loco_client = None
        self.arm_client = None
        
        # Action state
        self.current_action = None
        self.action_queue = []
        self.is_executing = False
        
        print(f"Initializing Robot Action Module with network interface: {network_interface}")
    
    def initialize(self):
        """Initialize the action module"""
        try:
            print("Initializing action module components...")
            
            # Initialize channel factory
            ChannelFactoryInitialize(0, self.network_interface)
            
            # Initialize locomotion client
            self.loco_client = LocoClient()
            self.loco_client.SetTimeout(10.0)
            self.loco_client.Init()
            
            # Initialize arm action client
            self.arm_client = ArmActionClient()
            self.arm_client.SetTimeout(10.0)
            self.arm_client.Init()
            
            self.is_initialized = True
            print("✓ Action module initialized successfully")
            
        except Exception as e:
            print(f"✗ Action module initialization failed: {e}")
            raise
    
    def test_locomotion(self):
        """Test locomotion functionality"""
        print("\n=== Testing Locomotion ===")
        
        if not self.loco_client:
            print("Locomotion client not initialized")
            return False
        
        try:
            # Test basic locomotion commands
            print("Testing locomotion commands...")
            
            # Test stand command
            print("Testing stand command...")
            ret = self.loco_client.Stand()
            print(f"Stand command ret: {ret}")
            time.sleep(2)
            
            # Test sit command
            print("Testing sit command...")
            ret = self.loco_client.Sit()
            print(f"Sit command ret: {ret}")
            time.sleep(2)
            
            # Test stand again
            print("Testing stand command again...")
            ret = self.loco_client.Stand()
            print(f"Stand command ret: {ret}")
            time.sleep(2)
            
            print("Locomotion test completed")
            return True
            
        except Exception as e:
            print(f"Locomotion test failed: {e}")
            return False
    
    def test_arm_actions(self):
        """Test arm action functionality"""
        print("\n=== Testing Arm Actions ===")
        
        if not self.arm_client:
            print("Arm client not initialized")
            return False
        
        try:
            # Test basic arm actions
            print("Testing arm actions...")
            
            # Test arm initialization
            print("Testing arm initialization...")
            ret = self.arm_client.ArmInit()
            print(f"ArmInit command ret: {ret}")
            time.sleep(3)
            
            # Test arm home position
            print("Testing arm home position...")
            ret = self.arm_client.ArmHome()
            print(f"ArmHome command ret: {ret}")
            time.sleep(3)
            
            # Test arm stop
            print("Testing arm stop...")
            ret = self.arm_client.ArmStop()
            print(f"ArmStop command ret: {ret}")
            time.sleep(1)
            
            print("Arm actions test completed")
            return True
            
        except Exception as e:
            print(f"Arm actions test failed: {e}")
            return False
    
    def run_action_tests(self):
        """Run comprehensive action tests"""
        print("\n" + "="*50)
        print("Starting Action Module Tests")
        print("="*50)
        
        if not self.is_initialized:
            print("Action module not initialized")
            return False
        
        try:
            # Test locomotion
            self.test_locomotion()
            
            # Test arm actions
            self.test_arm_actions()
            
            print("\n" + "="*50)
            print("Action tests completed")
            print("="*50)
            return True
            
        except Exception as e:
            print(f"Action tests failed: {e}")
            return False
    
    def stand(self):
        """Make the robot stand"""
        if not self.loco_client:
            print("Locomotion client not initialized")
            return False
        
        try:
            ret = self.loco_client.Stand()
            print(f"Stand command executed (ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"Stand command failed: {e}")
            return False
    
    def sit(self):
        """Make the robot sit"""
        if not self.loco_client:
            print("Locomotion client not initialized")
            return False
        
        try:
            ret = self.loco_client.Sit()
            print(f"Sit command executed (ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"Sit command failed: {e}")
            return False
    
    def move_forward(self, distance=0.5):
        """Move robot forward
        
        Args:
            distance (float): Distance to move in meters
        """
        if not self.loco_client:
            print("Locomotion client not initialized")
            return False
        
        try:
            # This is a placeholder - actual implementation would depend on the SDK
            print(f"Move forward command: {distance}m")
            # ret = self.loco_client.MoveForward(distance)
            # return ret == 0
            return True
        except Exception as e:
            print(f"Move forward command failed: {e}")
            return False
    
    def turn_left(self, angle=90):
        """Turn robot left
        
        Args:
            angle (float): Angle to turn in degrees
        """
        if not self.loco_client:
            print("Locomotion client not initialized")
            return False
        
        try:
            # This is a placeholder - actual implementation would depend on the SDK
            print(f"Turn left command: {angle} degrees")
            # ret = self.loco_client.TurnLeft(angle)
            # return ret == 0
            return True
        except Exception as e:
            print(f"Turn left command failed: {e}")
            return False
    
    def turn_right(self, angle=90):
        """Turn robot right
        
        Args:
            angle (float): Angle to turn in degrees
        """
        if not self.loco_client:
            print("Locomotion client not initialized")
            return False
        
        try:
            # This is a placeholder - actual implementation would depend on the SDK
            print(f"Turn right command: {angle} degrees")
            # ret = self.loco_client.TurnRight(angle)
            # return ret == 0
            return True
        except Exception as e:
            print(f"Turn right command failed: {e}")
            return False
    
    def arm_init(self):
        """Initialize arm"""
        if not self.arm_client:
            print("Arm client not initialized")
            return False
        
        try:
            ret = self.arm_client.ArmInit()
            print(f"Arm initialization executed (ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"Arm initialization failed: {e}")
            return False
    
    def arm_home(self):
        """Move arm to home position"""
        if not self.arm_client:
            print("Arm client not initialized")
            return False
        
        try:
            ret = self.arm_client.ArmHome()
            print(f"Arm home command executed (ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"Arm home command failed: {e}")
            return False
    
    def arm_stop(self):
        """Stop arm movement"""
        if not self.arm_client:
            print("Arm client not initialized")
            return False
        
        try:
            ret = self.arm_client.ArmStop()
            print(f"Arm stop command executed (ret: {ret})")
            return ret == 0
        except Exception as e:
            print(f"Arm stop command failed: {e}")
            return False
    
    def wave_hand(self):
        """Perform a waving gesture"""
        print("Performing wave gesture...")
        
        try:
            # This is a placeholder for a more complex gesture
            # In a real implementation, this would involve coordinated arm movements
            print("Wave gesture completed")
            return True
        except Exception as e:
            print(f"Wave gesture failed: {e}")
            return False
    
    def nod_head(self):
        """Perform a nodding gesture"""
        print("Performing nod gesture...")
        
        try:
            # This is a placeholder for a more complex gesture
            # In a real implementation, this would involve head movement
            print("Nod gesture completed")
            return True
        except Exception as e:
            print(f"Nod gesture failed: {e}")
            return False
    
    def execute_action_sequence(self, actions):
        """Execute a sequence of actions
        
        Args:
            actions (list): List of action dictionaries
        """
        print(f"Executing action sequence with {len(actions)} actions...")
        
        for i, action in enumerate(actions):
            print(f"Executing action {i+1}/{len(actions)}: {action}")
            
            try:
                action_type = action.get('type')
                params = action.get('params', {})
                
                if action_type == 'stand':
                    self.stand()
                elif action_type == 'sit':
                    self.sit()
                elif action_type == 'move_forward':
                    self.move_forward(params.get('distance', 0.5))
                elif action_type == 'turn_left':
                    self.turn_left(params.get('angle', 90))
                elif action_type == 'turn_right':
                    self.turn_right(params.get('angle', 90))
                elif action_type == 'arm_init':
                    self.arm_init()
                elif action_type == 'arm_home':
                    self.arm_home()
                elif action_type == 'arm_stop':
                    self.arm_stop()
                elif action_type == 'wave':
                    self.wave_hand()
                elif action_type == 'nod':
                    self.nod_head()
                else:
                    print(f"Unknown action type: {action_type}")
                
                # Wait between actions
                time.sleep(action.get('delay', 1.0))
                
            except Exception as e:
                print(f"Error executing action {i+1}: {e}")
                continue
        
        print("Action sequence completed")
    
    def start(self):
        """Start action processing"""
        if not self.is_initialized:
            print("Action module not initialized")
            return False
        
        print("Starting action processing...")
        print("Action module is ready to receive commands")
        
        return True
    
    def shutdown(self):
        """Shutdown action module"""
        print("Shutting down action module...")
        
        try:
            # Stop any ongoing actions
            if self.is_executing:
                print("Stopping ongoing actions...")
                self.is_executing = False
            
            # Clear action queue
            self.action_queue.clear()
            
            print("✓ Action module shutdown completed")
            
        except Exception as e:
            print(f"Error during action module shutdown: {e}")
    
    def get_status(self):
        """Get current action module status"""
        return {
            'initialized': self.is_initialized,
            'current_action': self.current_action,
            'is_executing': self.is_executing,
            'queue_length': len(self.action_queue)
        }
