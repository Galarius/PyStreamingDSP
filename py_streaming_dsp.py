# -*- coding: utf-8 -*-
#!/usr/bin/env python

__author__ = 'Ilya Shoshin (Galarius)'

import sys, getopt
import numpy as np
import pyaudio, wave, time
import audio_helper as ah
from audio_settings import StreamMode, AudioSettings
from extensions import elapsed_timer

# Keys
KEY_INPUT_FILE_NAME  = 'input_key'
KEY_OUTPUT_FILE_NAME = 'output_key'

def is_power2(num):
    "if a number is a power of two"
    return num and not num & (num - 1)

class AudioSession:
    """
    """
    def __init__(self, stream_mode, settings, **kwargs):
        """
        Init session
        :param stream_mode:
        :param kwargs:
        :return:
        """
        self.min_elapsed_time = 100.0
        self.max_elapsed_time = 0.0
        self.stream_mode = stream_mode
        self.settings = settings
        self.stream = None
        self.format = self.settings.format
        self.channels = self.settings.channels 
        self.rate = self.settings.rate
        self.__configure_for_stream_mode(**kwargs)

    def __configure_input_file(self, **kwargs):
        in_file = kwargs[KEY_INPUT_FILE_NAME]
        self.file_source = wave.open(in_file, 'rb')
        self.format = pyaudio.get_format_from_width(self.file_source.getsampwidth())
        self.channels = self.file_source.getnchannels()
        self.rate = self.file_source.getframerate()

    def __configure_output_file(self, **kwargs):
        self.output_wave_file = wave.open(kwargs[KEY_OUTPUT_FILE_NAME], 'wb')
        self.output_wave_file.setnchannels(self.file_source.getnchannels())
        self.output_wave_file.setsampwidth(self.file_source.getsampwidth())
        self.output_wave_file.setframerate(self.file_source.getframerate())

    def __configure_for_stream_mode(self, **kwargs):
        """
        Configure session for specified stream mode
        :param stream_mode:
        :param kwargs:
        :return:
        """
        print "Configurating..."
        stream_mode = self.stream_mode
        if stream_mode == StreamMode.BuildInIn2Out:
            # (build-in input) -> [process] -> (build-in output)
            pass
        elif stream_mode == StreamMode.BuildInIn2VD:
            # (build-in input) -> [process] -> (virtual device output)
            pass
        elif stream_mode == StreamMode.VD2BuildInOut:
            # (virtual device input) -> [process] ->  (build-in output)
            pass
        elif stream_mode == StreamMode.File2File:
            # (file) -> [process] -> (file)
            self.__configure_input_file(**kwargs)
            self.__configure_output_file(**kwargs)
        elif stream_mode == StreamMode.BuildInIn2File:
            # (build-in input) -> [process] -> (file)
            self.__configure_output_file(**kwargs)
        elif stream_mode == StreamMode.File2BuildInOut:
            # (file) -> [process] -> (build-in output)
            self.__configure_input_file(**kwargs)
        elif stream_mode == StreamMode.BuildInIn2File:
            # (virtual device input) -> [process] -> (file)
            self.__configure_output_file(**kwargs)
        elif stream_mode == StreamMode.File2BuildInOut:
            # (file) -> [process] -> (virtual device output)
            self.__configure_input_file(**kwargs)
        else:
            print "Unsupported stream mode! [{}]".format(stream_mode)

    def __recording_callback(self, in_data, frame_count, time_info, status):
        stream_mode = self.stream_mode
        with elapsed_timer() as elapsed:
            if stream_mode == StreamMode.BuildInIn2Out or \
               stream_mode == StreamMode.BuildInIn2VD or \
               stream_mode == StreamMode.VD2BuildInOut:
                # (build-in input) -> [process] -> (build-in output)
                # (build-in input) -> [process] -> (virtual device output)
                # (virtual device input) -> [process] -> (build-in output)
                signal = ah.audio_decode(in_data, self.settings.channels)
                signal = self.__processing(signal)
                processed_data = ah.audio_encode(signal)
            elif stream_mode == StreamMode.File2File or \
                 stream_mode == StreamMode.File2BuildInOut or \
                 stream_mode == StreamMode.File2VD:
                # (file) -> [process] -> (file)
                # (file) -> [process] -> (build-in output)
                in_data = self.file_source.readframes(frame_count)
                if not in_data:
                    return in_data, pyaudio.paComplete
                else:
                    signal = ah.audio_decode(in_data, self.file_source.getnchannels(), np.int16)
                    signal = self.__processing(signal)
                    processed_data = ah.audio_encode(signal, np.int16)
                    if stream_mode == StreamMode.File2File:
                        self.output_wave_file.writeframes(processed_data)
            elif stream_mode == StreamMode.BuildInIn2File or \
                 stream_mode == StreamMode.VD2File:
                # (build-in input) -> [process] -> (file)
                # (virtual device input) -> [process] -> (file)
                signal = ah.audio_decode(in_data, self.settings.channels)
                signal = self.__processing(signal)
                processed_data = ah.audio_encode(signal)
                self.output_wave_file.writeframes(processed_data)
            else:
                print "Unsupported stream mode! [{}]".format(stream_mode)
                processed_data = in_data
        elapsed = elapsed()        
        if elapsed < self.min_elapsed_time:
            self.min_elapsed_time = elapsed
        if elapsed > self.max_elapsed_time:
            self.max_elapsed_time = elapsed
        #-----------------------------------------------------------------------
        return processed_data, pyaudio.paContinue

    def __processing(self, signal):
        #-----------------------------------------------------------------------
        # Perform processing here
        #-----------------------------------------------------------------------
        left, right = signal
        # ...
        #-----------------------------------------------------------------------
        return right, left

    def __print_stat(self, input_dev_idx, output_dev_idx):
        src_latency = 1000.0 * self.stream.get_input_latency()
        buffer_latency = 1000.0 * self.settings.frame_size / self.rate
        dst_latency = 1000.0 * self.stream.get_output_latency()
        total_latency = buffer_latency + dst_latency + src_latency
        print "Input device: {}".format(input_dev_idx+1)
        print "Output device: {}".format(output_dev_idx+1)
        print "Format: {0}, Channels: {1}, Rate: {2}, Frame size: {3}".format(ah.py_audio_format_desc(self.format), \
            self.channels, self.rate, self.settings.frame_size)
        print "Round-trip latency: %0.1f ms (src: %0.1f ms, buf: %0.1f ms, dst: %0.1f ms)" % (
                total_latency, src_latency, buffer_latency, dst_latency)

    def open_stream(self):
        self.p_audio = pyaudio.PyAudio()
        stream_mode = self.stream_mode
        if stream_mode == StreamMode.BuildInIn2Out:
            # (build-in input) -> [process] -> (build-in output)
            print "Opening (build-in input) -> [process] -> (build-in output) stream..."
            input_dev_idx  = self.settings.detect_build_in_input_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_build_in_output_device_idx(self.p_audio)
            enable_input, enable_output = True, True
        elif stream_mode == StreamMode.BuildInIn2VD:
            # (build-in input) -> [process] -> (virtual device output)
            print "Opening (build-in input) -> [process] -> (virtual device output) stream..."
            input_dev_idx  = self.settings.detect_build_in_input_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_virtual_audio_device_idx(self.p_audio)
            enable_input, enable_output = True, True
        elif stream_mode == StreamMode.VD2BuildInOut:
            # (virtual device input) -> [process] -> (build-in output)
            print "Opening (virtual device input) -> [process] -> (build-in output) stream..."
            input_dev_idx = self.settings.detect_virtual_audio_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_build_in_output_device_idx(self.p_audio)
            enable_input, enable_output = True, True
        elif stream_mode == StreamMode.File2File:
            # (file) -> [process] -> (file)
            print "Opening (file) -> [process] -> (file) stream..."
            input_dev_idx  = self.settings.detect_build_in_input_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_build_in_output_device_idx(self.p_audio)
            enable_input, enable_output = True, False
        elif stream_mode == StreamMode.BuildInIn2File:
            # (build-in input) -> [process] -> (file)
            print "Opening (build-in input) -> [process] -> (file) stream..."
            input_dev_idx = self.settings.detect_build_in_input_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_build_in_output_device_idx(self.p_audio)
            enable_input, enable_output = True, False
        elif stream_mode == StreamMode.File2BuildInOut:
            # (file) -> [process] -> (build-in output)
            print "Opening (file) -> [process] -> (build-in output) stream..."
            input_dev_idx  = self.settings.detect_build_in_input_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_build_in_output_device_idx(self.p_audio)
            enable_input, enable_output = False, True
        elif stream_mode == StreamMode.BuildInIn2File:
            # (virtual device input) -> [process] -> (file)
            print "Opening (virtual device input) -> [process] -> (file) stream..."
            input_dev_idx = self.settings.detect_virtual_audio_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_build_in_output_device_idx(self.p_audio)
            enable_input, enable_output = True, False
        elif stream_mode == StreamMode.File2BuildInOut:
            # (file) -> [process] -> (virtual device output)
            print "Opening (file) -> [process] -> (virtual device output) stream..."
            input_dev_idx  = self.settings.detect_build_in_input_device_idx(self.p_audio)
            output_dev_idx = self.settings.detect_virtual_audio_device_idx(self.p_audio)
            enable_input, enable_output = False, True
        else:
            print "Unsupported stream mode! [{}]".format(stream_mode)
            raise ValueError("Unsupported stream mode! [{}]".format(stream_mode))
        
        # standard L-R stereo
        channel_map = (0, 1)
        try:
            stream_info = pyaudio.PaMacCoreStreamInfo(
                flags=pyaudio.PaMacCoreStreamInfo.paMacCorePlayNice,  # default
                channel_map=channel_map)
        except AttributeError:
            print "Sorry, couldn't find PaMacCoreStreamInfo. Make sure that you're running on OS X."
            sys.exit(-1)

        if self.settings.validate_audio_setup(self.p_audio, self.format, self.channels, self.rate, input_dev_idx):
            self.stream = self.p_audio.open(format=self.format,
                                            channels=self.channels,
                                            rate=self.rate,
                                            frames_per_buffer=self.settings.frame_size,
                                            input=enable_input,
                                            output=enable_output,
                                            output_host_api_specific_stream_info=stream_info,
                                            input_device_index=input_dev_idx,
                                            output_device_index=output_dev_idx,
                                            stream_callback=self.__recording_callback)
            self.stream.start_stream()

            self.__print_stat(input_dev_idx, output_dev_idx)
        else:
            print "Unsupported audio configuration!"
            raise ValueError("Unsupported audio configuration!")

    def close_stream(self):
        print "Closing stream..."
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print "Min processing time: %0.2f ms" % (self.min_elapsed_time * 1000)
        print "Max processing time: %0.2f ms" % (self.max_elapsed_time * 1000)

        stream_mode = self.stream_mode
        if stream_mode == StreamMode.BuildInIn2Out:
            # (build-in input) -> [process] -> (build-in output)
            pass
        elif stream_mode == StreamMode.BuildInIn2VD:
            # (build-in input) -> [process] -> (virtual device output)
            pass
        elif stream_mode == StreamMode.VD2BuildInOut:
            # (virtual device input) -> [process] -> (build-in output)
            pass
        elif stream_mode == StreamMode.File2File:
            # (file) -> [process] -> (file)
            self.file_source.close()
            self.output_wave_file.close()
        elif stream_mode == StreamMode.BuildInIn2File:
            # (build-in input) -> [process] -> (file)
            self.output_wave_file.close()
        elif stream_mode == StreamMode.File2BuildInOut:
            # (file) -> [process] -> (build-in output)
            self.file_source.close()
        elif stream_mode == StreamMode.BuildInIn2File:
            # (virtual device input) -> [process] -> (file)
            self.output_wave_file.close()
        elif stream_mode == StreamMode.File2BuildInOut:
            # (file) -> [process] -> (virtual device output)
            self.file_source.close()
        else:
            print "Unsupported stream mode! [{}]".format(stream_mode)

        self.p_audio.terminate()

def print_usage(name):
    print """
Streaming audio processing template program.

Offers the following streaming modes:
    * 1. (build-in input) -> [process] -> (build-in output)
    * 2. (build-in input) -> [process] -> (virtual device output)
    * 3. (virtual device input) -> [process] -> (build-in output)
    * 4. (file) -> [process] -> (file)
    * 5. (build-in input) -> [process] -> (file)
    * 6. (file) -> [process] -> (build-in output)
    * 7. (virtual device input) -> [process] -> (file)
    * 8. (file) -> [process] -> (virtual device output)

python {0} [-h, -d, -v, -a, -b] [-i <in file>, -o <out file>]

To exit:
    Press `Ctrl+C`

Setup:
    Change `settings.json` to setup audio devices

Options:
    -h print this help message
    -d print all available devices
    -v use virtual audio device instead of built-in 
       (can be used with -i/-o to activate mode 7/8)
    -a use built-in input with virtual audio device 
       or built-in output (mode 1 or 2)
    -b use built-in output with virtual audio device 
       or built-in input (mode 1 or 3)
    -i, --ifile= provide input wav file
    -o, --ofile= provide output wav file

Use cases:
    * `python {0} -a -b` - to activate 1
    * `python {0} -a` - to activate 2
    * `python {0} -b` - to activate 3
    * `python {0} -i infile.wav -o outfile.wav` - to activate 4
    * `python {0} -o outfile.wav` - to activate 5
    * `python {0} -i infile.wav` - to activate 6
    * `python {0} -v -o outfile.wav` - to activate 7
    * `python {0} -v -i infile.wav` - to activate 8
""".format(name)

def main(opts):
    in_file  = ''
    out_file = ''
    use_virtual_device    = False
    use_build_in_input = False
    use_build_in_output = False
    audio_session = None

    for opt, arg in opts:
        if opt == '-h':
            print_usage(sys.argv[0])
            sys.exit(0)
        elif opt == '-d':
            devices = AudioSettings.available_devices()
            print "Available audio devices:"
            for i, d in enumerate(devices):
                print "\t{}. {}".format(i+1, d)
            sys.exit(0)
        elif opt == '-v':
            use_virtual_device = True
        elif opt == '-a':
            use_build_in_input = True
        elif opt == '-b':
            use_build_in_output = True
        elif opt in ("-i", "--ifile"):
            in_file = arg
        elif opt in ("-o", "--ofile"):
            out_file = arg
    
    settings = AudioSettings()
    settings.deserialize()

    if not in_file and not out_file:
        if use_build_in_input and use_build_in_output:
            if settings.validate_stream_mode(StreamMode.BuildInIn2Out):
                audio_session = AudioSession(StreamMode.BuildInIn2Out, settings)
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
        elif use_build_in_input and not use_build_in_output:
            if settings.validate_stream_mode(StreamMode.BuildInIn2VD):
                audio_session = AudioSession(StreamMode.BuildInIn2VD, settings)
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
        elif use_build_in_output and not use_build_in_input:
            if settings.validate_stream_mode(StreamMode.VD2BuildInOut):
                audio_session = AudioSession(StreamMode.VD2BuildInOut, settings)
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
        else:
            print_usage(sys.argv[0])
            sys.exit(0)
    elif in_file and not out_file:
        if use_virtual_device:
            if settings.validate_stream_mode(StreamMode.File2VD):
                audio_session = AudioSession(StreamMode.File2VD, settings, **{ KEY_INPUT_FILE_NAME:in_file})
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
        else:
            if settings.validate_stream_mode(StreamMode.File2BuildInOut):
                audio_session = AudioSession(StreamMode.File2BuildInOut, settings, **{ KEY_INPUT_FILE_NAME:in_file})
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
    elif out_file and not in_file:
        if use_virtual_device:
            if settings.validate_stream_mode(StreamMode.VD2File):
                audio_session = AudioSession(StreamMode.VD2File, settings, **{ KEY_OUTPUT_FILE_NAME:out_file})
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
        else:
            if settings.validate_stream_mode(StreamMode.BuildInIn2File):
                audio_session = AudioSession(StreamMode.BuildInIn2File, settings, **{ KEY_OUTPUT_FILE_NAME:out_file})
                audio_session.open_stream()
            else:
                print "There are no supported audio devices for current stream mode."
    elif in_file and out_file:
        if settings.validate_stream_mode(StreamMode.File2File):
            audio_session = AudioSession(StreamMode.File2File, settings, **{ KEY_INPUT_FILE_NAME:in_file,KEY_OUTPUT_FILE_NAME:out_file})
            audio_session.open_stream()
        else:
            print "There are no supported audio devices for current stream mode."

    if audio_session:
        try:
            while audio_session.stream.is_active():
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            audio_session.close_stream()
            print 'Done!'
        sys.exit(0)
    else:
        print 'Failed to init audio session!'
        sys.exit(1)

if __name__ == "__main__":
    try:
       opts, args = getopt.getopt(sys.argv[1:], "hdvabi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print_usage(sys.argv[0])
        sys.exit(2)

    main(opts)