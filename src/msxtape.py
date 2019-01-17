# -*- coding: utf-8 -*-
"""
[hopefully a] python program for generating a wav file form a msx cas file
Encoding as per: https://github.com/oboroc/msx-books/blob/master/ru/msx2-fb-1993-ru.md#10
"""

import wave

class wav_writer:
    def __init__(self, s_rate = 44100.0, s_width = 1):
        """
        constructor - initializes constants and variables
        """
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


    def __del__(self):
        """
        destructor - dumps pcm data to a file
        """


    def write(self, f_name):
        """
        write - creates a wav file from pcm_data
        """
        # pad pcm data with one extra byte if we ended up with odd number of bytes
        if (len(self.pcm_data) & 1) == 1:
            self.pcm_data.append(0)
        ba = bytearray(self.pcm_data)
        with wave.open(f_name, 'w') as f:
            f.setnchannels(1)    # mono
            f.setsampwidth(self.sample_width)
            f.setframerate(self.sample_rate)
            f.writeframes(ba)
        del ba


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


    def add_cas(self, freq, cas):
        """
        add_cas - take object cas and add pcm data based on it
        """


class cas_reader:
    def __init__(self, cas_name):
        """
        read_cas - read cas, parse it into a stream of tokens
        """
        CAS_HEADER = [0x1f, 0xa6, 0xde, 0xba, 0xcc, 0x13, 0x7d, 0x74]
        BASIC_CODE = 0xd3
        ASCII_CODE = 0xea
        BINARY_CODE = 0xd0
        CODE_LEN = 10
        FNAME_LEN = 6
        with open(cas_name, 'rb') as f:
            cas_data = f.read()
        if not cas_data:
            print("Can't read data from file", cas_name)
            return
        idx = 0
        for i in range(len(CAS_HEADER)):
            if cas_data[idx + i] != CAS_HEADER[i]:
                print("File", cas_name, "doesn't have a valid CAS header")
                return
        idx = idx + len(CAS_HEADER)

        basic = ascii = binary = 0
        for i in range(CODE_LEN):
            if cas_data[idx + i] == BASIC_CODE:
                basic = basic + 1
            if cas_data[idx + i] == ASCII_CODE:
                ascii = ascii + 1
            if cas_data[idx + i] == BINARY_CODE:
                binary = binary + 1

        if basic == CODE_LEN:
            print('BASIC block')
        elif ascii == CODE_LEN:
            print('ASCII block')
        elif binary == CODE_LEN:
            print('Binary block')
        else:
            s = 'Unexpected block header:'
            for i in range(CODE_LEN):
                s = s + ' ' + hex(cas_data[idx + i])
            print(s)
            return
        idx = idx + CODE_LEN

        self.add_long_header(freq)
        for i in range(CODE_LEN):
            self.add_byte(freq, cas_data[idx + i])

        # 6 bytes file name
        fname = ''
        for i in range(FNAME_LEN):
            if cas_data[idx + i] >= 32:
                fname = fname + chr(cas_data[idx + i])
        print('File name:', '"' + fname + '"')
        for i in range(FNAME_LEN):
            self.add_byte(freq, cas_data[idx + i])
        self.add_short_header(freq)
        idx = idx + FNAME_LEN

        # we need to somehow count the number of bytes same as current, up to 10 bytes
        same = 1
        for i in range(1, min(10, len(cas_data) - idx)):
            if cas_data[idx] != cas_data[idx + i]:
                break
            same = same + 1
        print('same =', same)


def main():
    """
    main function - for now just make some beeps
    """
#    print(__file__)
#    print(globals())
     #MSX_Z80_FREQ = 3580000  # 3.58 MHz
     #Z80_CYCLE = 1000000 / MSX_Z80_FREQ # 1 cpu cycle duration in microseconds
     #print('373 cycles in microseconds', 373 * Z80_CYCLE)
    c = cas_reader('2.cas')
    t = wav_writer()
    t.add_cas(1200, c)
    t.write('test.wav')

    
if __name__ == "__main__":
    main()
