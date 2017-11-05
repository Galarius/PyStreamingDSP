# -*- coding: utf-8 -*-

__author__ = 'Ilya Shoshin (Galarius)'

import numpy as np
import pyaudio

def py_audio_format_to_numpy(fmt):
    if fmt == pyaudio.paFloat32:
        return np.float32
    elif fmt == pyaudio.paInt32:
        return np.int32
    elif fmt == pyaudio.paInt24:
        raise TypeError("Unsupported audio Int24 format.")
    elif fmt == pyaudio.paInt16:
        return np.int16
    elif fmt == pyaudio.paInt8:
        return np.int8
    elif fmt == pyaudio.paUInt8:
        return np.uint8
    if fmt == pyaudio.paCustomFormat:
        raise TypeError("Unsupported custom audio format.")
    else:
        raise TypeError("Unsupported audio format.")

def py_audio_format_desc(fmt):
    if fmt == pyaudio.paFloat32:
        return "32 bit float"
    elif fmt == pyaudio.paInt32:
        return "32 bit int"
    elif fmt == pyaudio.paInt24:
        return "24 bit int"
    elif fmt == pyaudio.paInt16:
        return "16 bit int"
    elif fmt == pyaudio.paInt8:
        return "8 bit int"
    elif fmt == pyaudio.paUInt8:
        return "8 bit unsigned int"
    if fmt == pyaudio.paCustomFormat:
        return "custom format"
    else:
        return "Unsupported format!"

# pcm2float and float2pcm
# are taken from here: 
# https://github.com/mgeier/python-audio/blob/master/audio-files/utility.py

def pcm2float(sig, dtype='float32'):
    """Convert PCM signal to floating point with a range from -1 to 1.
    Use dtype='float32' for single precision.
    Parameters
    ----------
    sig : array_like
        Input array, must have integral type.
    dtype : data type, optional
        Desired (floating point) data type.
    Returns
    -------
    numpy.ndarray
        Normalized floating point data.
    See Also
    --------
    float2pcm, dtype
    """
    sig = np.asarray(sig)
    if sig.dtype.kind not in 'iu':
        raise TypeError("'sig' must be an array of integers")
    dtype = np.dtype(dtype)
    if dtype.kind != 'f':
        raise TypeError("'dtype' must be a floating point type")

    i = np.iinfo(sig.dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig.astype(dtype) - offset) / abs_max

def float2pcm(sig, dtype='int16'):
    """Convert floating point signal with a range from -1 to 1 to PCM.
    Any signal values outside the interval [-1.0, 1.0) are clipped.
    No dithering is used.
    Note that there are different possibilities for scaling floating
    point numbers to PCM numbers, this function implements just one of
    them.  For an overview of alternatives see
    http://blog.bjornroche.com/2009/12/int-float-int-its-jungle-out-there.html
    Parameters
    ----------
    sig : array_like
        Input array, must have floating point type.
    dtype : data type, optional
        Desired (integer) data type.
    Returns
    -------
    numpy.ndarray
        Integer data, scaled and clipped to the range of the given
        *dtype*.
    See Also
    --------
    pcm2float, dtype
    """
    sig = np.asarray(sig)
    if sig.dtype.kind != 'f':
        raise TypeError("'sig' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind not in 'iu':
        raise TypeError("'dtype' must be an integer type")

    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)

def audio_decode(in_data, channels, dtype=np.float32):
    signal = np.fromstring(in_data, dtype=dtype)
    if dtype == np.float32:
        signal = float2pcm(signal, np.int16)
    chunk_length = len(signal) / channels
    output = np.reshape(signal, (chunk_length, channels))
    return output[:, 0], output[:, 1]

def audio_encode(signal, dtype=np.float32):
    interleaved = np.array(signal).flatten('F')
    if dtype == np.float32:
        signal = pcm2float(signal, np.float32)
    out_data = interleaved.astype(dtype).tostring()
    return out_data