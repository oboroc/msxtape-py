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

    sampleRate = 22050.0    # hertz
    duration = 3.0          # seconds
    frequency = 2400.0      # hertz

    wavf = wave.open('file.wav','w')
    wavf.setnchannels(1)    # mono
    wavf.setsampwidth(2)    # 16 bit
    wavf.setframerate(sampleRate)

    for i in range(int(duration * sampleRate)):
        value = int(32767.0 * math.cos(frequency * math.pi * float(i) / float(sampleRate)))
        data = struct.pack('<h', value)
        wavf.writeframes(data)

    wavf.close()



if __name__ == "__main__":
    msxtape()
