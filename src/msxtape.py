# -*- coding: utf-8 -*-
"""
    [hopefully a] python program for generating wav file form msx cas file
    Encoding as per: https://github.com/oboroc/msx-books/blob/master/ru/msx2-fb-1993-ru.md#10
"""

import wave

class msxtape:
    def __init__(self, f_name, s_rate = 44100.0, s_width = 1):
        """
        constructor - initializes constants and variables
        """

        self.file_name = f_name
        self.sample_rate = s_rate
        self.sample_width = s_width

        self.pcm_data = []

        if self.sample_width == 1:
            # 8 bit samples are unsigned char (0..255)
            self.minvol = 0
            self.maxvol = 255
        elif self.sample_width > 1:
            # -32768 and 32767 for 16 bit, should work with samples 2 bytes wide or more
            self.minvol = -pow(2, self.sample_width * 8 - 1)
            self.maxvol = -self.minvol - 1
        else:
            raise ValueError('Unexpected sample width')

        MSX_Z80_FREQ = 3580000  # 3.58 MHz
        self.Z80_CYCLE = 1000000 / MSX_Z80_FREQ # 1 cpu cycle duration in microseconds
        print('373 cycles in microseconds', 373 * self.Z80_CYCLE)


    def __del__(self):
        """
        destructor - dumps pcm data to a file
        """

        # pad pcm data with one extra byte if we ended up with odd number of bytes
        if (len(self.pcm_data) & 1) == 1:
            self.pcm_data.append(0)
        ba = bytearray(self.pcm_data)
        wavf = wave.open(self.file_name, 'w')
        wavf.setnchannels(1)    # mono
        wavf.setsampwidth(self.sample_width)
        wavf.setframerate(self.sample_rate)
        wavf.writeframes(ba)
        wavf.close()

    def add_value(self, value):
        """
        add_value function - add value to pcm data
        """
        if self.sample_width == 1:
            self.pcm_data.append(value & 0xff)
        elif self.sample_width == 2:
            self.pcm_data.append(value & 0xff)
            self.pcm_data.append((value >> 8) & 0xff)
        else:
            raise ValueError('Unsupported sample width')


    def add_tone(self, freq, dur):
        """
        add_tone function - adds a tone with specified frequency and duration to pcm_data
        """
        period = self.sample_rate / freq
        for i in range(int(dur * self.sample_rate)):
            pos = i % period    # position within period
            if pos * 2 < period:    # is it first half-period?
                value = self.minvol
            else:
                value = self.maxvol
            self.add_value(value)


    def add_bit_0(self, freq):
        """
        add_bit_0 function - encode a bit with value of 0
        I'm not yet sure how to do it, so here is a free form thinking on the matter:
        1 sample dutation in seconds is 1 second / sample_rate, i.e. 1/44100
        1 pulse (iteration of wave) in seconds is 1 second / freq, i.e. 1/1200
        1 pulse in samples = sample_rate / freq = 44100 / 1200 = 36.75
        To output bit 0 we need to output half a pulse at minvol and half a pulse at maxvol.
        We also want to somehow use the reminder for next iteration, so if we need to write
        bit 0 three times, we'll have the first one represented at 37 samples (round up 36.75).
        How many samples should the second bit 0 be? It starts at sample 38, right after first bit,
        and it lasts until 2*36.75=73.5 ~ 74. 74-37=37. Second bit 0 is encoded with 36 samples.
        Third bit 0 starts at sample 75 and goes on until 3*36.75=110.25 ~ 110. 110-74=36.
        So all three bits are encoded by 37+37+36=110 samples.
        """
        samples_per_pulse = self.sample_rate / freq

        last_sample = len(self.pcm_data)
        print('last_sample =', last_sample)

        last_pulse = round(last_sample / samples_per_pulse)
        print('last_pulse =', last_pulse)

        start_sample = round(last_pulse * samples_per_pulse)
        print('start_sample =', start_sample)

        half_sample = round((last_pulse + 0.5) * samples_per_pulse)
        print('half_sample =', half_sample)

        end_sample = round((last_pulse + 1) * samples_per_pulse)
        print('end_sample =', end_sample)

        msg = '1st pulse half:'
        for i in range(half_sample - start_sample):
            self.add_value(self.minvol)
            msg = msg + ' ' + hex(self.minvol) + ' '
        print(msg)

        msg = '2nd pulse half:'
        for i in range(end_sample - half_sample):
            self.add_value(self.maxvol)
            msg = msg + ' ' + hex(self.maxvol)
        print(msg)

        print('pulse length in samples:', end_sample - start_sample)

        print('---')




def main():
    """
    main function - for now just make some beeps
    """
#    print(__file__)
#    print(globals())
    t = msxtape('file.wav')
#    t.add_tone(1200.0, 1.0)   # frequency in hertz and duration in seconds
    for i in range(100):
        t.add_bit_0(1200.0)
    
if __name__ == "__main__":
    main()
