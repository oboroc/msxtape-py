# -*- coding: utf-8 -*-
"""
    [hopefully a] python program for generating wav file form msx cas file
"""


def msxtape():
    """
    main function - for now just make a 3 second 2.4KHz beep
    """

    import wave, struct, math

#    print(__file__)
#    print(globals())

    duration = 3.0          # sec
    sample_rate = 44100.0   # hz
    sample_width = 2        # bytes per sample
    frequency = 1200.0      # hz

    wavf = wave.open('file.wav','w')
    wavf.setnchannels(1)    # mono
    wavf.setsampwidth(sample_width)
    wavf.setframerate(sample_rate)

    maxvol = pow(2, sample_width * 8 - 1) - 1   # this is 127 for 8 bit samples and 32767 for 16 bit
    
    for i in range(int(duration * sample_rate)):
        value = int(maxvol * math.sin(frequency * math.pi * float(i) / float(sample_rate)))
        if value > 0:
            value = maxvol
        if value <= 0:
            value = -maxvol
        data = struct.pack('<h', value)
        wavf.writeframes(data)

    wavf.close()


if __name__ == "__main__":
    msxtape()
