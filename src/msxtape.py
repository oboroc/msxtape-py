# -*- coding: utf-8 -*-
"""
    [hopefully a] python program for generating wav file form msx cas file
"""

import wave, struct

class msxtape:
    def __init__(self, f_name, s_rate = 44100.0, s_width = 1):
        self.sample_rate = s_rate
        self.sample_width = s_width

        self.wavf = wave.open(f_name, 'w')
        self.wavf.setnchannels(1)    # mono
        self.wavf.setsampwidth(self.sample_width)
        self.wavf.setframerate(self.sample_rate)

        self.pcm_data = []

        if self.sample_width == 1:
            # 8 bit samples are unsigned char (0..255)
            self.minvol = 0
            self.maxvol = 255
        elif self.sample_width == 2:
            # -32768 and 32767 for 16 bit, should work with samples 2 bytes wide or more
            self.minvol = -pow(2, self.sample_width * 8 - 1)
            self.maxvol = -self.minvol - 1
        else:
            raise ValueError('Unexpected sample width')

        MSX_Z80_FREQ = 3580000  # 3.58 MHz
        self.Z80_CYCLE = 1000000 / MSX_Z80_FREQ # 1 cpu cycle duration in microseconds
        print('373 cycles in microseconds', 373 * self.Z80_CYCLE)


    def __del__(self):
        # pad pcm data with one extra byte if we ended up with odd number of bytes
        if (self.sample_width == 1) and ((pcm_bytes & 1) == 1):
            self.pcm_data.append(0)

        ba = bytearray(self.pcm_data)
        self.wavf.writeframes(ba)
        self.wavf.close()


    def add_tone(self, freq, dur):
        pcm_bytes = 0
        period = self.sample_rate / freq
        for i in range(int(dur * self.sample_rate)):
            pos = i % period    # position within period
            if pos * 2 < period:    # is it first half-period?
                value = self.minvol
            else:
                value = self.maxvol

            if self.sample_width == 1:
                self.pcm_data.append(value & 0xff)
                pcm_bytes = pcm_bytes + 1
            else:
                self.pcm_data.append(value & 0xff)
                self.pcm_data.append((value >> 8) & 0xff)


def main():
    """
    main function - for now just make some beeps
    """
#    print(__file__)
#    print(globals())


    t = msxtape('file.wav')

    t.add_tone(1200.0, 1.0)   # frequency in hertz and duration in seconds
    t.add_tone(2400.0, 1.0)
    t.add_tone(1200.0, 1.0)
    
if __name__ == "__main__":
    main()
