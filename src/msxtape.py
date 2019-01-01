# -*- coding: utf-8 -*-
"""
    [hopefully a] python program for generating wav file form msx cas file
"""

import wave, struct

class msxtape:
    def __init__(self, f_name, s_rate = 44100.0, s_width = 2):
        self.sample_rate = s_rate
        self.sample_width = s_width

        self.wavf = wave.open(f_name,'w')
        self.wavf.setnchannels(1)    # mono
        self.wavf.setsampwidth(self.sample_width)
        self.wavf.setframerate(self.sample_rate)

    def __del__(self):
        self.wavf.close()

    def write_tone(self, freq, dur):

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
            self.wavf.writeframes(data)


def main():
    """
    main function - for now just make some beeps
    """
#    print(__file__)
#    print(globals())

    t = msxtape('file.wav')

    t.write_tone(1200.0, 1.0)   # frequency in hertz and duration in seconds
    t.write_tone(2400.0, 1.0)
    t.write_tone(1200.0, 1.0)
    
if __name__ == "__main__":
    main()
