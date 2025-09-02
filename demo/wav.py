#!/usr/bin/env python3
"""
Simple WAV file writer for audio recording
This module provides basic WAV file writing functionality for the robot audio system.
"""

import struct
import wave

def write_wave(filename, sample_rate, pcm_data, channels=1):
    """
    Write PCM data to a WAV file
    
    Args:
        filename (str): Output WAV file path
        sample_rate (int): Sample rate in Hz
        pcm_data (list): List of PCM samples
        channels (int): Number of channels (1 for mono, 2 for stereo)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit samples
            wav_file.setframerate(sample_rate)
            
            # Convert PCM data to bytes
            pcm_bytes = struct.pack('<' + 'h' * len(pcm_data), *pcm_data)
            wav_file.writeframes(pcm_bytes)
        
        print(f"WAV file written successfully: {filename}")
        return True
        
    except Exception as e:
        print(f"Error writing WAV file: {e}")
        return False

def read_wave(filename):
    """
    Read PCM data from a WAV file
    
    Args:
        filename (str): Input WAV file path
    
    Returns:
        tuple: (sample_rate, pcm_data) or (None, None) if failed
    """
    try:
        with wave.open(filename, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            # Read all frames
            frames = wav_file.readframes(wav_file.getnframes())
            
            # Convert bytes to PCM data
            if sample_width == 2:  # 16-bit
                pcm_data = struct.unpack('<' + 'h' * (len(frames) // 2), frames)
            else:
                print(f"Unsupported sample width: {sample_width}")
                return None, None
            
            return sample_rate, pcm_data
            
    except Exception as e:
        print(f"Error reading WAV file: {e}")
        return None, None
