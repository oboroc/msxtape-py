# -*- coding: utf-8 -*-
"""
[hopefully a] python program for generating a wav file form a msx cas file
Encoding as per: https://github.com/oboroc/msx-books/blob/master/ru/msx2-fb-1993-ru.md#10
"""

import sys, wave

class wav_writer:
    def __init__(self, s_rate = 44100.0, s_width = 1):
        """
        initialize constants and variables
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


    def write(self, f_name):
        """
        create a wav file from pcm data
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
        add value to pcm data
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
        add tone with specified frequency and duration to pcm data
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
        encode a bit with value of 0
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
        encode a bit with value of 1
        write two pusles at twice the given frequency
        """
        self.add_bit_0(freq * 2)
        self.add_bit_0(freq * 2)


    def add_byte(self, freq, a_byte):
        """
        encode a byte
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
        encode ~1.7 seconds of freq * 2 tone
        for tape speed of 1200 bod, we need 4000 pulses
        for tape speed of 2400 bod, we need 8000 pulses
        """
        total_pulses = round(freq * 4000 / 1200.0)
        for i in range(total_pulses):
            self.add_bit_0(freq * 2)


    def add_long_header(self, freq):
        """
        encode ~6.7 seconds of freq * 2 tone
        long header is 4x times the duration of short header
        """
        for i in range(4):
            self.add_short_header(freq)


    def add_cas(self, freq, cas):
        """
        take object cas and add pcm data based on it
        """


class cas_reader:
    CAS_HEADER = [0x1f, 0xa6, 0xde, 0xba, 0xcc, 0x13, 0x7d, 0x74]
    def __init__(self, cas_name):
        """
        read and parse a cas file
        """

        def reps(lst, idx, maxrep):
            """
            count the number of same values in lst, repeated after the value at index idx
            stop counting after maxrep
            """
            rep = 1
            for i in range(1, min(maxrep, len(lst) - idx)):
                if lst[idx] != lst[idx + i]:
                    break
                rep = rep + 1
            return rep

        def is_cas_header(lst, idx):
            """
            check if we have cas header starting at idx position
            """
            for i in range(len(self.CAS_HEADER)):
                if cas_data[idx + i] != self.CAS_HEADER[i]:
                    return False
                    break
            return True

        with open(cas_name, 'rb') as f:
            cas_data = f.read()
        if not cas_data:
            print("Can't read data from file", cas_name)
            return
        idx = 0
        # iterate through blocks
        self.blocks = []
        block_type = -1 # invalid value
        BASIC = 0xd3
        ASCII = 0xea
        BINARY = 0xd0
        BLOCK_HEADER_LEN = 10
        while idx < len(cas_data):
            if not is_cas_header(cas_data, idx):
                print('no valid cas header at', idx, hex(idx))
                return
            idx = idx + len(self.CAS_HEADER)
            # is it a 10 byte block header?
            if reps(cas_data, idx, BLOCK_HEADER_LEN) >= BLOCK_HEADER_LEN:
                block_type = cas_data[idx]
                idx = idx + BLOCK_HEADER_LEN
            else:
                s = 'Unexpected block header:'
                for i in range(min(BLOCK_HEADER_LEN, len(cas_data) - idx)):
                    s = s + ' ' + hex(cas_data[idx + i])
                s = s + ' at ' + hex(idx) + ' (' + str(idx) + ')'
                print(s)
                return
            # 6 bytes file name
            FNAME_LEN = 6
            block_fname = ''
            for i in range(FNAME_LEN):
                block_fname = block_fname + chr(cas_data[idx + i])
            idx = idx + FNAME_LEN
            if not is_cas_header(cas_data, idx):
                print('no cas header after cas file name at', idx)
                return
            idx = idx + len(self.CAS_HEADER)
            block_data = []
            start_address = end_address = run_address = -1
            if block_type == BASIC:
                BASIC_END_TOK = 7
                BASIC_END_LEN = 7
                while idx < len(cas_data):
                    if cas_data[idx] == BASIC_END_TOK and reps(cas_data, idx, BASIC_END_LEN) >= BASIC_END_LEN:
                        idx = idx + BASIC_END_LEN
                        break
                    block_data.append(cas_data[idx])
                    idx = idx + 1
            elif block_type == ASCII:
                ASCII_SEQ_LEN = 256
                EOF = 0x1a
                while idx < len(cas_data):
                    if len(cas_data) - idx < ASCII_SEQ_LEN:
                        print('expected', ASCII_SEQ_LEN, 'bytes sequence in ASCII block', block_fname,
                              '; there is only', len(cas_data) - idx, 'bytes of data left')
                        return
                    found_eof = False
                    for i in range(ASCII_SEQ_LEN):
                        block_data.append(cas_data[idx + i])
                        if cas_data[idx + i] == EOF:
                            found_eof = True
                    idx = idx + ASCII_SEQ_LEN
                    if found_eof:
                        break
                    if not is_cas_header(cas_data, idx):
                        print('no cas header for next ASCII sequence at', idx)
                        return
                    idx = idx + len(self.CAS_HEADER)

                print('>>> end of ascii block at', idx, hex(idx))
                if not found_eof:
                    print('>>> no eof found in ascii block at', idx)
                    return
            elif block_type == BINARY:
                if not is_cas_header(cas_data, idx):
                    print("block", cas_name, "doesn't have a valid CAS header")
                    return
                idx = idx + len(self.CAS_HEADER)
                start_address = cas_data[idx] + cas_data[idx + 1] * 256
                end_address = cas_data[idx + 2] + cas_data[idx + 3] * 256
                run_address = cas_data[idx + 4] + cas_data[idx + 5] * 256
                code_len = end_address - start_address + 1
                idx = idx + 6
                if idx + code_len > len(cas_data):
                    print('unexpected end in binary block data')
                    return
                while idx < len(cas_data):
                    if is_cas_header(cas_data, idx):
                        break
                    block_data.append(cas_data[idx])
                    idx = idx + 1
            elif block_type == CUSTOM:
                while idx < len(cas_data):
                    if is_cas_header(cas_data, idx):
                        break
                    block_data.append(cas_data[idx])
                    idx = idx + 1
            self.blocks.append([block_type, block_fname, block_data, start_address, end_address, run_address])


def main():
    """
    for now just make some beeps
    """
#    print(__file__)
#    print(globals())
     #MSX_Z80_FREQ = 3580000  # 3.58 MHz
     #Z80_CYCLE = 1000000 / MSX_Z80_FREQ # 1 cpu cycle duration in microseconds
     #print('373 cycles in microseconds', 373 * Z80_CYCLE)

    for i in range(1, len(sys.argv)):
        print('cas file:', sys.argv[i])
        c = cas_reader(sys.argv[i])
        print('---')
#    t = wav_writer()
#    t.add_cas(1200, c)
#    t.write('test.wav')

    
if __name__ == "__main__":
    main()
