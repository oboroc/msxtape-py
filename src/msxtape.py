# -*- coding: utf-8 -*-
"""
[hopefully a] python program for generating a wav file form a msx cas file
Encoding as per: https://github.com/oboroc/msx-books/blob/master/ru/msx2-fb-1993-ru.md#10
"""

import sys, os, wave

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
        with wave.open(f_name, 'w') as f:
            f.setnchannels(1)    # mono
            f.setsampwidth(self.sample_width)
            f.setframerate(self.sample_rate)
            f.writeframes(bytearray(self.pcm_data))


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
        for i in range(8):      # 8 bits of data
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


CAS_HEADER = [0x1f, 0xa6, 0xde, 0xba, 0xcc, 0x13, 0x7d, 0x74]
CAS_HEADER_LEN = len(CAS_HEADER)
BASIC = 0xd3
ASCII = 0xea
BINARY = 0xd0
CUSTOM = -1
BLOCK_HEADER_LEN = 10
FNAME_LEN = 6


class cas:
    def read(self, cas_name):
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
            for i in range(CAS_HEADER_LEN):
                if cas_data[idx + i] != CAS_HEADER[i]:
                    return False
                    break
            return True

        def dechex(n):
            """
            convert integer into string with it's value as a decimal,
            followed with hex in brakets
            """
            return str(n) + ' (' + hex(n) + ')'

        with open(cas_name, 'rb') as f:
            cas_data = f.read()
        if not cas_data:
            print("Error: can't read data from file", cas_name)
            return
        # iterate through blocks
        idx = 0
        self.blocks = []
        while idx < len(cas_data):
            if not is_cas_header(cas_data, idx):
                raise ValueError('no valid cas header at ' + dechex(idx))
            idx = idx + CAS_HEADER_LEN
            # is it a 10 byte block header?
            if reps(cas_data, idx, BLOCK_HEADER_LEN) >= BLOCK_HEADER_LEN:
                block_type = cas_data[idx]
                idx = idx + BLOCK_HEADER_LEN
            else:
                block_type = CUSTOM
            # 6 bytes file name and cas header
            block_fname = ''
            if block_type in [BASIC, ASCII, BINARY]:
                for i in range(FNAME_LEN):
                    block_fname = block_fname + chr(cas_data[idx + i])
                idx = idx + FNAME_LEN
                if not is_cas_header(cas_data, idx):
                    raise ValueError('no cas header after cas file name at ' + dechex(idx))
                idx = idx + CAS_HEADER_LEN
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
                        raise ValueError('expected ' + str(ASCII_SEQ_LEN) + ' bytes sequence in ASCII block ' +
                                         block_fname + '; there is only' + str(len(cas_data) - idx) +
                                         ' bytes of data left')
                    found_eof = False
                    for i in range(ASCII_SEQ_LEN):
                        block_data.append(cas_data[idx + i])
                        if cas_data[idx + i] == EOF:
                            found_eof = True
                    idx = idx + ASCII_SEQ_LEN
                    if found_eof:
                        break
                    if not is_cas_header(cas_data, idx):
                        raise ValueError('no cas header for next ASCII sequence at ' + dechex(idx))
                    idx = idx + CAS_HEADER_LEN
                if not found_eof:
                    raise ValueError('no eof found in ascii block at ' + dechex(idx))
            elif block_type == BINARY:
                start_address = cas_data[idx] + cas_data[idx + 1] * 256
                end_address = cas_data[idx + 2] + cas_data[idx + 3] * 256
                run_address = cas_data[idx + 4] + cas_data[idx + 5] * 256
                code_len = end_address - start_address + 1
                idx = idx + 6
                bin_start = idx
                if idx + code_len > len(cas_data):
                    raise ValueError('unexpected end in binary block data at ' + dechex(idx))
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
            else:
                raise ValueError('this is a bug, this code should never be reached')
            self.blocks.append([block_type, block_fname, block_data, start_address, end_address, run_address])
        del cas_data


    def write(self, fname, is_wav = False, s_rate = 44100.0, s_width = 1):
        """
        create a cas or wav (if is_wav == True) file from cas_data
        """
        if self.blocks == []:
            raise ValueError('no cas data, nothing to write to ' + fname)
        cas_data = []
        for block in self.blocks:
            block_type = block[0]
            block_fname = block[1]
            block_data = block[2]
            start_address = block[3]
            end_address = block[4]
            run_address = block[5]
            if is_wav:
                ww = wav_writer(s_rate, s_width)
                freq = 1200.0
                ww.add_long_header(freq)
            else:
                cas_data.extend(CAS_HEADER)
            if block_type in [BASIC, ASCII, BINARY]:
                for i in range(BLOCK_HEADER_LEN):
                    if is_wav:
                        ww.add_byte(freq, block_type)
                    else:
                        cas_data.append(block_type)
                for i in range(FNAME_LEN):
                    if is_wav:
                        ww.add_byte(freq, ord(block_fname[i]))
                    else:
                        cas_data.append(ord(block_fname[i]))
            if block_type == BASIC:
                if is_wav:
                    ww.add_short_header(freq)
                    for i in range(len(block_data)):
                        ww.add_byte(freq, block_data[i])
                else:
                    cas_data.extend(CAS_HEADER)
                    cas_data.extend(block_data)
            elif block_type == ASCII:
                for i in range(len(block_data)):
                    if i % 256 == 0:
                        if is_wav:
                            ww.add_short_header(freq)
                        else:
                            cas_data.extend(CAS_HEADER)
                    if is_wav:
                        ww.add_byte(freq, block_data[i])
                    else:
                        cas_data.append(block_data[i])
            elif block_type == BINARY:
                start_lo = start_address & 0xff
                start_hi = (start_address & 0xff00) >> 8
                end_lo = end_address & 0xff
                end_hi = (end_address & 0xff00) >> 8
                run_lo = run_address & 0xff
                run_hi = (run_address & 0xff00) >> 8
                if is_wav:
                    ww.add_short_header(freq)
                    ww.add_byte(freq, start_lo)
                    ww.add_byte(freq, start_hi)
                    ww.add_byte(freq, end_lo)
                    ww.add_byte(freq, end_hi)
                    ww.add_byte(freq, run_lo)
                    ww.add_byte(freq, run_hi)
                    for i in range(len(block_data)):
                        ww.add_byte(freq, block_data[i])
                else:
                    cas_data.extend(CAS_HEADER)
                    cas_data.append(start_lo)
                    cas_data.append(start_hi)
                    cas_data.append(end_lo)
                    cas_data.append(end_hi)
                    cas_data.append(run_lo)
                    cas_data.append(run_hi)
                    cas_data.extend(block_data)
            elif block_type == CUSTOM:
                if is_wav:
                    for i in range(len(block_data)):
                        ww.add_byte(freq, block_data[i])
                else:
                    cas_data.extend(block_data)
            else:
                raise ValueError('invalid block type ' + hex(block_type))
        if is_wav:
            ww.write(fname)
        else:
            with open(fname, 'wb') as f:
                f.write(bytearray(cas_data))
        del cas_data


def main():
    """
    for now just make some beeps
    """
    for i in range(1, len(sys.argv)):
        c = cas()
        c.read(sys.argv[i])
        bn = os.path.basename(sys.argv[i])
        fname = os.path.splitext(bn)[0] + '.wav'
        c.write(fname, True)

    
if __name__ == "__main__":
    main()
