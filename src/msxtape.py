# -*- coding: utf-8 -*-
"""
    [hopefully a] python program for generating wav file form msx cas file
"""

import wave, struct

class msxtape:
    def __init__(self, s_rate, s_width):
        self.sample_rate = s_rate
        self.sample_width = s_width

    def write_tone(self, freq, dur):
        wavf = wave.open('file.wav','w')
        wavf.setnchannels(1)    # mono
        wavf.setsampwidth(self.sample_width)
        wavf.setframerate(self.sample_rate)

        # this is 32767 for 16 bit
        # it should work for 16 bit or more samples
        # 8 bit samples are unsigned char (0..255)
        maxvol = pow(2, self.sample_width * 8 - 1) - 1
        minvol = -maxvol - 1
        period = self.sample_rate / freq
        for i in range(int(dur * self.sample_rate)):
            pos = i % period    # position within period
            if pos * 2 < period:    # is it first half-period?
                value = maxvol
            else:
                value = minvol
            data = struct.pack('<h', value)
            wavf.writeframes(data)
        wavf.close()


def main():
    """
    main function - for now just make a 5 second long 1200Hz beep
    """
#    print(__file__)
#    print(globals())

    sample_rate = 44100.0   # hertz
    sample_width = 2        # bytes per sample
    t = msxtape(sample_rate, sample_width)

    frequency = 1200.0      # hertz
    duration = 5.0          # seconds
    t.write_tone(frequency, duration)
    
if __name__ == "__main__":
    main()
