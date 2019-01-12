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
        #MSX_Z80_FREQ = 3580000  # 3.58 MHz
        #self.Z80_CYCLE = 1000000 / MSX_Z80_FREQ # 1 cpu cycle duration in microseconds
        #print('373 cycles in microseconds', 373 * self.Z80_CYCLE)


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
        add_value - add value to pcm data
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
        add_tone - adds a tone with specified frequency and duration to pcm_data
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
        add_bit_0 - encode a bit with value of 0
        write one pulse at given frequency
        """
        samples_per_pulse = self.sample_rate / freq
        last_sample = len(self.pcm_data)
        last_pulse = round(last_sample / samples_per_pulse)
        start_sample = round(last_pulse * samples_per_pulse)
        half_sample = round((last_pulse + 0.5) * samples_per_pulse)
        end_sample = round((last_pulse + 1) * samples_per_pulse)
        for i in range(half_sample - start_sample):
            self.add_value(self.minvol)
        for i in range(end_sample - half_sample):
            self.add_value(self.maxvol)


    def add_bit_1(self, freq):
        """
        add_bit_1 - encode a bit with value of 1
        write two pusles at twice the given frequency
        """
        self.add_bit_0(freq * 2)
        self.add_bit_0(freq * 2)


    def add_byte(self, freq, a_byte):
        """
        add_byte function - encode a byte
        write start bit 0, 8 byte bits and two stop bits 1
        """
        self.add_bit_0(freq)    # start bit
        for i in range(8):      # 8 bits in given byte
            a_bit = (a_byte >> i) & 1
            if a_bit == 0:
                self.add_bit_0(freq)
            else:
                self.add_bit_1(freq)
        self.add_bit_1(freq)    # 2 stop bits
        self.add_bit_1(freq)


    def add_short_header(self, freq):
        """
        add_short_header function - encode ~1.7 seconds of freq * 2 tone
        for tape speed of 1200 bod, we need 4000 pulses
        for tape speed of 2400 bod, we need 8000 pulses
        """
        total_pulses = round(freq * 4000 / 1200.0)
        for i in range(total_pulses):
            self.add_bit_0(freq * 2)


    def add_long_header(self, freq):
        """
        add_long_header - encode ~6.7 seconds of freq * 2 tone
        long header is 4x times the duration of short header
        """
        for i in range(4):
            self.add_short_header(freq)


    def add_cas(self, freq, cas_name):
        """
        read_cas - 
        """
        CAS_HEADER = [0x1f, 0xa6, 0xde, 0xba, 0xcc, 0x13, 0x7d, 0x74]
        BASIC_CODE = 0xd3
        ASCII_CODE = 0xea
        BINARY_CODE = 0xd0
        CODE_LEN = 10
        FNAME_LEN = 6

        f = open(cas_name, 'rb')
        if not f:
            print("Can't open file", cas_name)
            return

        cas_data = f.read(len(CAS_HEADER))
        if not cas_data:
            print("Can't read data from file", cas_name)
            return

        for i in range(len(CAS_HEADER)):
            if cas_data[i] != CAS_HEADER[i]:
                print("File", cas_name, "doesn't have a valid CAS header")
                return

        cas_data = f.read(CODE_LEN)
        basic = ascii = binary = 0
        for i in range(len(cas_data)):
            if cas_data[i] == BASIC_CODE:
                basic = basic + 1
            if cas_data[i] == ASCII_CODE:
                ascii = ascii + 1
            if cas_data[i] == BINARY_CODE:
                binary = binary + 1

        if basic == CODE_LEN:
            print('Basic block')
        elif ascii == CODE_LEN:
            print('Ascii block')
        elif binary == CODE_LEN:
            print('Binary block')
        else:
            s = 'Unexpected block header:'
            for i in range(len(cas_data)):
                s = s + ' ' + hex(cas_data[i])
            print(s)
            return

        self.add_long_header(freq)
        for i in range(len(cas_data)):
            self.add_byte(freq, cas_data[i])

        # 6 bytes file name
        cas_data = f.read(FNAME_LEN)
        fname = ''
        for i in range(len(cas_data)):
            if cas_data[i] >= 32:
                fname = fname + chr(cas_data[i])
        print('File name:', '"' + fname + '"')
        for i in range(len(cas_data)):
            self.add_byte(freq, cas_data[i])
        self.add_short_header(freq)


def main():
    """
    main function - for now just make some beeps
    """
#    print(__file__)
#    print(globals())
    t = msxtape('file.wav')
    t.add_cas(1200, '2.cas')
    
if __name__ == "__main__":
    main()
