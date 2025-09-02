#!/usr/bin/env python3
"""
Robot Arm Demonstration Module for Unitree G1 Robot
This module provides a complete arm movement demonstration sequence.

Features:
1. Low-level arm control using SDK DDS
2. Multi-stage arm movement sequence
3. Safety checks and validation
4. Real-time joint control
5. Smooth trajectory planning

The demonstration includes:
- Stage 1: Set robot to zero posture
- Stage 2: Lift arms up to target positions
- Stage 3: Return to zero posture
- Stage 4: Release arm SDK control
"""

import time
import sys
import numpy as np
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread

# Mathematical constants
kPi = 3.141592654
kPi_2 = 1.57079632

class G1JointIndex:
    """G1 Robot Joint Index Definitions"""
    # Left leg
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleB = 4
    LeftAnkleRoll = 5
    LeftAnkleA = 5

    # Right leg
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleB = 10
    RightAnkleRoll = 11
    RightAnkleA = 11

    WaistYaw = 12
    WaistRoll = 13        # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistA = 13           # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistPitch = 14       # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistB = 14           # NOTE: INVALID for g1 23dof/29dof with waist locked

    # Left arm
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20   # NOTE: INVALID for g1 23dof
    LeftWristYaw = 21     # NOTE: INVALID for g1 23dof

    # Right arm
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27  # NOTE: INVALID for g1 23dof
    RightWristYaw = 28    # NOTE: INVALID for g1 23dof

    kNotUsedJoint = 29 # NOTE: Weight

class RobotArmDemo:
    def __init__(self, network_interface):
        self.network_interface = network_interface
        self.is_initialized = False
        self.is_running = False
        self.done = False
        
        # Control parameters
        self.time_ = 0.0
        self.control_dt_ = 0.02  # 50Hz control loop
        self.duration_ = 3.0     # Duration for each stage
        self.counter_ = 0
        self.weight = 0.0
        self.weight_rate = 0.2
        self.kp = 60.0           # Position gain
        self.kd = 1.5            # Velocity gain
        self.dq = 0.0
        self.tau_ff = 0.0
        self.mode_machine_ = 0
        
        # SDK components
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.low_state = None
        self.first_update_low_state = False
        self.crc = CRC()
        
        # Publishers and subscribers
        self.arm_sdk_publisher = None
        self.lowstate_subscriber = None
        self.lowCmdWriteThreadPtr = None
        
        # Target positions for arm joints
        self.target_pos = [
            0.0,      kPi_2,  0.0,    kPi_2,  0.0,    # Left leg
            0.0,     -kPi_2,  0.0,    kPi_2,  0.0,    # Right leg
            0.0,      0.0,    0.0                      # Waist
        ]

        # Arm joint indices
        self.arm_joints = [
            G1JointIndex.LeftShoulderPitch,  G1JointIndex.LeftShoulderRoll,
            G1JointIndex.LeftShoulderYaw,    G1JointIndex.LeftElbow,
            G1JointIndex.LeftWristRoll,
            G1JointIndex.RightShoulderPitch, G1JointIndex.RightShoulderRoll,
            G1JointIndex.RightShoulderYaw,   G1JointIndex.RightElbow,
            G1JointIndex.RightWristRoll,
            G1JointIndex.WaistYaw,
            G1JointIndex.WaistRoll,
            G1JointIndex.WaistPitch
        ]
        
        print(f"Initializing Robot Arm Demo with network interface: {network_interface}")
    
    def initialize(self):
        """Initialize the arm demonstration module"""
        try:
            print("Initializing arm demonstration components...")
            
            # Initialize channel factory
            ChannelFactoryInitialize(0, self.network_interface)
            
            # Create publisher for arm SDK commands
            self.arm_sdk_publisher = ChannelPublisher("rt/arm_sdk", LowCmd_)
            self.arm_sdk_publisher.Init()

            # Create subscriber for low state feedback
            self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
            self.lowstate_subscriber.Init(self.low_state_handler, 10)
            
            self.is_initialized = True
            print("✓ Arm demonstration module initialized successfully")
            
        except Exception as e:
            print(f"✗ Arm demonstration module initialization failed: {e}")
            raise
    
    def low_state_handler(self, msg: LowState_):
        """Handle low state messages from the robot"""
        self.low_state = msg
        
        if not self.first_update_low_state:
            self.first_update_low_state = True
            print("First low state update received")
    
    def low_cmd_write(self):
        """Main control loop for arm movement"""
        self.time_ += self.control_dt_

        if self.time_ < self.duration_:
            # [Stage 1]: Set robot to zero posture
            self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = 1  # Enable arm_sdk
            for i, joint in enumerate(self.arm_joints):
                ratio = np.clip(self.time_ / self.duration_, 0.0, 1.0)
                self.low_cmd.motor_cmd[joint].tau = 0.0
                self.low_cmd.motor_cmd[joint].q = (1.0 - ratio) * self.low_state.motor_state[joint].q
                self.low_cmd.motor_cmd[joint].dq = 0.0
                self.low_cmd.motor_cmd[joint].kp = self.kp
                self.low_cmd.motor_cmd[joint].kd = self.kd

        elif self.time_ < self.duration_ * 3:
            # [Stage 2]: Lift arms up to target positions
            for i, joint in enumerate(self.arm_joints):
                ratio = np.clip((self.time_ - self.duration_) / (self.duration_ * 2), 0.0, 1.0)
                self.low_cmd.motor_cmd[joint].tau = 0.0
                self.low_cmd.motor_cmd[joint].q = ratio * self.target_pos[i] + (1.0 - ratio) * self.low_state.motor_state[joint].q
                self.low_cmd.motor_cmd[joint].dq = 0.0
                self.low_cmd.motor_cmd[joint].kp = self.kp
                self.low_cmd.motor_cmd[joint].kd = self.kd

        elif self.time_ < self.duration_ * 6:
            # [Stage 3]: Set robot back to zero posture
            for i, joint in enumerate(self.arm_joints):
                ratio = np.clip((self.time_ - self.duration_ * 3) / (self.duration_ * 3), 0.0, 1.0)
                self.low_cmd.motor_cmd[joint].tau = 0.0
                self.low_cmd.motor_cmd[joint].q = (1.0 - ratio) * self.low_state.motor_state[joint].q
                self.low_cmd.motor_cmd[joint].dq = 0.0
                self.low_cmd.motor_cmd[joint].kp = self.kp
                self.low_cmd.motor_cmd[joint].kd = self.kd

        elif self.time_ < self.duration_ * 7:
            # [Stage 4]: Release arm_sdk control
            for i, joint in enumerate(self.arm_joints):
                ratio = np.clip((self.time_ - self.duration_ * 6) / self.duration_, 0.0, 1.0)
                self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = (1 - ratio)  # Disable arm_sdk
        else:
            self.done = True
            print("Arm demonstration completed!")

        # Calculate CRC and publish command
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.arm_sdk_publisher.Write(self.low_cmd)
    
    def start_demonstration(self):
        """Start the arm demonstration sequence"""
        if not self.is_initialized:
            print("Arm demonstration module not initialized")
            return False
        
        if self.is_running:
            print("Arm demonstration already running")
            return False
        
        print("\n" + "="*60)
        print("Starting Robot Arm Demonstration")
        print("="*60)
        print("WARNING: Please ensure there are no obstacles around the robot!")
        print("The demonstration will:")
        print("1. Set robot to zero posture (3 seconds)")
        print("2. Lift arms up to target positions (6 seconds)")
        print("3. Return to zero posture (9 seconds)")
        print("4. Release arm SDK control (3 seconds)")
        print("="*60)
        
        try:
            # Wait for first low state update
            print("Waiting for robot state feedback...")
            while not self.first_update_low_state:
                time.sleep(0.1)
            
            # Start control thread
            self.lowCmdWriteThreadPtr = RecurrentThread(
                interval=self.control_dt_, target=self.low_cmd_write, name="arm_control"
            )
            self.lowCmdWriteThreadPtr.Start()
            
            self.is_running = True
            print("✓ Arm demonstration started")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start arm demonstration: {e}")
            return False
    
    def wait_for_completion(self, timeout=30.0):
        """Wait for the demonstration to complete"""
        if not self.is_running:
            print("Arm demonstration not running")
            return False
        
        print("Waiting for arm demonstration to complete...")
        start_time = time.time()
        
        while not self.done and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if self.done:
            print("✓ Arm demonstration completed successfully")
            return True
        else:
            print("✗ Arm demonstration timed out")
            return False
    
    def stop_demonstration(self):
        """Stop the arm demonstration"""
        if not self.is_running:
            print("Arm demonstration not running")
            return
        
        print("Stopping arm demonstration...")
        
        try:
            # Stop control thread
            if self.lowCmdWriteThreadPtr:
                self.lowCmdWriteThreadPtr.Stop()
                self.lowCmdWriteThreadPtr = None
            
            self.is_running = False
            self.done = True
            print("✓ Arm demonstration stopped")
            
        except Exception as e:
            print(f"Error stopping arm demonstration: {e}")
    
    def shutdown(self):
        """Shutdown the arm demonstration module"""
        print("Shutting down arm demonstration module...")
        
        try:
            # Stop demonstration if running
            if self.is_running:
                self.stop_demonstration()
            
            # Close subscribers
            if self.lowstate_subscriber:
                self.lowstate_subscriber.Close()
            
            print("✓ Arm demonstration module shutdown completed")
            
        except Exception as e:
            print(f"Error during arm demonstration module shutdown: {e}")
    
    def get_status(self):
        """Get current demonstration status"""
        return {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'done': self.done,
            'time': self.time_,
            'stage': self._get_current_stage()
        }
    
    def _get_current_stage(self):
        """Get current demonstration stage"""
        if self.time_ < self.duration_:
            return "Stage 1: Zero Posture"
        elif self.time_ < self.duration_ * 3:
            return "Stage 2: Lift Arms"
        elif self.time_ < self.duration_ * 6:
            return "Stage 3: Return to Zero"
        elif self.time_ < self.duration_ * 7:
            return "Stage 4: Release Control"
        else:
            return "Completed"

def main():
    """Main function for standalone execution"""
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <network_interface>")
        print("Example: python3 {sys.argv[0]} eth0")
        sys.exit(1)

    network_interface = sys.argv[1]
    
    print("Unitree G1 Arm Demonstration")
    print("=" * 40)
    
    # Create arm demonstration
    arm_demo = RobotArmDemo(network_interface)
    
    try:
        # Initialize
        arm_demo.initialize()
        
        # Start demonstration
        if arm_demo.start_demonstration():
            # Wait for completion
            arm_demo.wait_for_completion()
        
    except KeyboardInterrupt:
        print("\nStopping demonstration...")
        arm_demo.stop_demonstration()
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        arm_demo.shutdown()

if __name__ == "__main__":
    main()
