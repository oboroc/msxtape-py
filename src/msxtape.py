# -*- coding: utf-8 -*-
"""
    [hopefully a] python program for generating wav file form msx cas file
"""

def write_tone(freq, dur):
    print('write_tone(' + str(freq) + ', ' + str(dur) + ')')

def msxtape():
    """
    main function - for now just make a 5 second long 1200Hz beep
    """

    import wave, struct

#    print(__file__)
#    print(globals())

    duration = 5.0          # seconds
    frequency = 1200.0      # hertz
    sample_rate = 44100.0   # hertz
    sample_width = 2        # bytes per sample

    write_tone(duration, frequency)

    wavf = wave.open('file.wav','w')
    wavf.setnchannels(1)    # mono
    wavf.setsampwidth(sample_width)
    wavf.setframerate(sample_rate)

    # this is 32767 for 16 bit
    # it should work for 16 bit or more samples
    # 8 bit samples are unsigned char (0..255)
    maxvol = pow(2, sample_width * 8 - 1) - 1
    minvol = -maxvol - 1
    period = sample_rate / frequency
    for i in range(int(duration * sample_rate)):
        pos = i % period    # position within period
        if pos * 2 < period:    # is it first half-period?
            value = maxvol
        else:
            value = minvol
        data = struct.pack('<h', value)
        wavf.writeframes(data)
    wavf.close()


if __name__ == "__main__":
    msxtape()
