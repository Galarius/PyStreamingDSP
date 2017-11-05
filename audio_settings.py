# -*- coding: utf-8 -*-

__author__ = 'Ilya Shoshin (Galarius)'

import os
import json
import pyaudio

SETTINGS_FILE_NAME = 'settings.json'
SETTINGS_KEY_FRAME_SIZE      = 'frame_size'
# unsupported for now
#SETTINGS_KEY_CHANNELS        = 'channels'
#SETTINGS_KEY_FORMAT          = 'pyaudio_format'
SETTINGS_KEY_RATE            = 'rate'
SETTINGS_KEY_BUILD_IN_INPUT  = 'build_in_input_audio_device_name'
SETTINGS_KEY_BUILD_IN_OUTPUT = 'build_in_output_audio_device_name'
SETTINGS_KEY_VIRTUAL_DEVICE  = 'virtual_audio_device_name'


class StreamMode:
    """
    Streaming Mode
    --------------
    * BuildInIn2Out:   (build-in input) -> [process] -> (build-in output)
    * BuildInIn2VD:    (build-in input) -> [process] -> (virtual device output)
    * VD2BuildInOut:   (virtual device input) -> [process] -> (build-in output)
    * File2File:       (file) -> [process] -> (file)
    * BuildInIn2File:  (build-in input) -> [process] -> (file)
    * File2BuildInOut: (file) -> [process] -> (build-in output)
    * VD2File:         (virtual device input) -> [process] -> (file)
    * File2VD:         (file) -> [process] -> (virtual device output)
    """
    BuildInIn2Out      = 0
    BuildInIn2VD       = 1
    VD2BuildInOut      = 2
    File2File          = 3
    BuildInIn2File     = 4
    File2BuildInOut    = 5
    VD2File            = 6
    File2VD            = 7


class AudioSettings:
    """
    Class to store, save and load settings
    """
    def __init__(self):
        self.frame_size = 1024
        self.channels = 2
        # paFloat32 (1)           #: 32 bit float
        # paInt32   (2)           #: 32 bit int
        # paInt24   (4)           #: 24 bit int
        # paInt16   (8)           #: 16 bit int
        # paInt8    (16)          #: 8 bit int
        # paUInt8   (32)          #: 8 bit unsigned int
        # paCustomFormat (65536)  # custom format
        self.format = pyaudio.paFloat32
        self.rate = 44100
        self.build_in_input_audio_device_name = "Built-in Input"
        self.build_in_output_audio_device_name = "Built-in Output"
        self.virtual_audio_device_name = "Soundflower (2ch)"

    def serialize(self):
        data = {SETTINGS_KEY_FRAME_SIZE: self.frame_size,
                # SETTINGS_KEY_CHANNELS: self.channels,
                # SETTINGS_KEY_FORMAT: self.format,
                SETTINGS_KEY_RATE: self.rate,
                SETTINGS_KEY_BUILD_IN_INPUT: self.build_in_input_audio_device_name,
                SETTINGS_KEY_BUILD_IN_OUTPUT: self.build_in_output_audio_device_name,
                SETTINGS_KEY_VIRTUAL_DEVICE: self.virtual_audio_device_name}
        with open(SETTINGS_FILE_NAME, 'w+') as out_file:
            json.dump(data, out_file)

    def deserialize(self, filename=SETTINGS_FILE_NAME):
        if os.path.isfile(filename):
                with open(filename, 'r') as in_file:
                    data = json.load(in_file)
                    self.frame_size = data[SETTINGS_KEY_FRAME_SIZE]
                    # self.channels = data[SETTINGS_KEY_CHANNELS]
                    # self.format = data[SETTINGS_KEY_FORMAT]
                    self.rate = data[SETTINGS_KEY_RATE]
                    self.build_in_input_audio_device_name = data[SETTINGS_KEY_BUILD_IN_INPUT]
                    self.build_in_output_audio_device_name = data[SETTINGS_KEY_BUILD_IN_OUTPUT]
                    self.virtual_audio_device_name = data[SETTINGS_KEY_VIRTUAL_DEVICE]
        else:
            print "{} couldn't be found. Applying default settings.".format(SETTINGS_FILE_NAME)
            self.serialize()
            self.deserialize()

    def validate_stream_mode(self, stream_mode):
        p_audio = pyaudio.PyAudio()
        result = False

        if stream_mode == StreamMode.BuildInIn2Out:
            result = self.detect_build_in_input_device_idx(p_audio) >= 0 and \
                     self.detect_build_in_output_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.BuildInIn2VD:
            result = self.detect_build_in_input_device_idx(p_audio) >= 0 and \
                     self.detect_virtual_audio_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.VD2BuildInOut:
            result = self.detect_virtual_audio_device_idx(p_audio) >= 0 and \
                     self.detect_build_in_output_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.File2File:
            result = self.detect_build_in_input_device_idx(p_audio) >= 0 and \
                     self.detect_build_in_output_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.BuildInIn2File:
            result = self.detect_build_in_input_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.File2BuildInOut:
            result = self.detect_build_in_output_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.VD2File:
            result = self.detect_virtual_audio_device_idx(p_audio) >= 0
        elif stream_mode == StreamMode.File2VD:
            result = self.detect_virtual_audio_device_idx(p_audio) >= 0
        else:
            print "Unsupported stream mode! [%i]" % stream_mode
        
        p_audio.terminate()
        return result

    @staticmethod
    def available_devices():
        """
        Get available audio devices
        """
        names = []
        p_audio = pyaudio.PyAudio()
        for i in range(p_audio.get_device_count()):
            info = p_audio.get_device_info_by_index(i)
            names.append(info['name'])
        p_audio.terminate()
        return names

    @staticmethod
    def validate_audio_setup(p_audio, input_format, input_channels, rate, input_device):
        """
        Validate pyaudio stream setup
        :param p: PyAudio instance
        ...
        """
        is_supported = p_audio.is_format_supported(
            input_format=input_format, 
            input_channels=input_channels, 
            rate=rate,
            input_device=input_device)
        return is_supported

    def detect_virtual_audio_device_idx(self, p):
        """
        Detect virtual audio device index
        :param p: PyAudio instance
        :return: device index
        """
        return self.__detect_device_index(p, self.virtual_audio_device_name)


    def detect_build_in_input_device_idx(self, p):
        """
        Detect Built-in input device index
        :param p: PyAudio instance
        :return: device index
        """
        return self.__detect_device_index(p, self.build_in_input_audio_device_name)


    def detect_build_in_output_device_idx(self, p):
        """
        Detect Built-in Output device index
        :param p: PyAudio instance
        :return: device index
        """
        return self.__detect_device_index(p, self.build_in_output_audio_device_name)

    def __detect_device_index(self, p, device_name):
        """
        Detect audio device index
        :param p: PyAudio instance
        :param device_name:
        :return: device index
        """
        idx = -1
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['name'] == device_name:
                idx = info['index']
                break
        return idx