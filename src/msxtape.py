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

    duration = 5.0          # sec
    sampleRate = 44100.0    # hz
    frequency = 1200.0      # hz

    wavf = wave.open('file.wav','w')
    wavf.setnchannels(1)    # mono
    wavf.setsampwidth(2)    # 16 bit
    wavf.setframerate(sampleRate)

    squarevol = 20000

    for i in range(int(duration * sampleRate)):
        value = int(32767.0 * math.sin(frequency * math.pi * float(i) / float(sampleRate)))
        if value > 0:
            value = squarevol
        if value <= 0:
            value = -squarevol
        data = struct.pack('<h', value)
        wavf.writeframes(data)

    wavf.close()


if __name__ == "__main__":
    msxtape()
