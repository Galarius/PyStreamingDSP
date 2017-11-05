# PyStreamingDSP

Template program in Python showing how to setup streaming audio processing with `PyAudio`.

There are following streaming modes available:

1. (build-in input) -> [process] -> (build-in output)
2. (build-in input) -> [process] -> (virtual device output)
3. (virtual device input) -> [process] -> (build-in output)
4. (file) -> [process] -> (file)
5. (build-in input) -> [process] -> (file)
6. (file) -> [process] -> (build-in output)
7. (virtual device input) -> [process] -> (file)
8. (file) -> [process] -> (virtual device output)

## Requirements

* PyAudio
* NumPy

## Usage

**Setup**

Implement function `def __processing(self, signal)` in file `py_streaming_dsp.py`.

Change `settings.json` to setup audio devices.

If [SoundFlower](https://github.com/mattingalls/Soundflower) is used in the system, than field `virtual_audio_device_name` has value `Soundflower (2ch)`. 

**Run**

`python {0} [-h, -d, -v, -a, -b] [-i <in file>, -o <out file>]`

Press `Ctrl+C` to exit.

**Command-line options**

* `-h` print this help message
* `-d` print all available devices
* `-v` use virtual audio device instead of built-in 
       (can be used with -i/-o to activate mode 7/8)
* `-a` use built-in input with virtual audio device 
       or built-in output (mode 1 or 2)
* `-b` use built-in output with virtual audio device 
       or built-in input (mode 1 or 3)
* `-i`, `--ifile=` provide input wav file
* `-o`, `--ofile=` provide output wav file

**Use cases**

* `python {0} -a -b` - to activate mode 1
* `python {0} -a` - to activate mode 2
* `python {0} -b` - to activate mode 3
* `python {0} -i infile.wav -o outfile.wav` - to activate mode 4
* `python {0} -o outfile.wav` - to activate mode 5
* `python {0} -i infile.wav` - to activate mode 6
* `python {0} -v -o outfile.wav` - to activate mode 7
* `python {0} -v -i infile.wav` - to activate mode 8

## Applications

Streaming audio steganography algorithm in Python [gs-scrambler](https://github.com/Galarius/gs-scrambler) is using PyStreamingDSP.

# License

This project is licensed under the terms of the MIT license. (see [LICENSE.txt](LICENSE.txt) in the root)