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
        with wave.open(f_name, 'w') as f:
            f.setnchannels(1)    # mono
            f.setsampwidth(self.sample_width)
            f.setframerate(self.sample_rate)
            f.writeframes(bytearray(self.pcm_data))
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


    def add_cas(self, freq, cas):
        """
        take object cas and add pcm data based on it
        """


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
                print('Error: no valid cas header at', dechex(idx))
                return
            idx = idx + CAS_HEADER_LEN
            # is it a 10 byte block header?
            if reps(cas_data, idx, BLOCK_HEADER_LEN) >= BLOCK_HEADER_LEN:
                block_type = cas_data[idx]
                idx = idx + BLOCK_HEADER_LEN
            else:
                block_type = CUSTOM
            if block_type == BASIC:
                s = 'BASIC'
            elif block_type == ASCII:
                s = 'ASCII'
            elif block_type == BINARY:
                s = 'BINARY'
            else:
                s = 'CUSTOM'
            #print(s, 'block start at', dechex(idx))
            # 6 bytes file name and cas header
            block_fname = ''
            if block_type in [BASIC, ASCII, BINARY]:
                for i in range(FNAME_LEN):
                    block_fname = block_fname + chr(cas_data[idx + i])
                idx = idx + FNAME_LEN
                if not is_cas_header(cas_data, idx):
                    print('Error: no cas header after cas file name at', dechex(idx))
                    return
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
                #print('BASIC block end at', dechex(idx))
            elif block_type == ASCII:
                ASCII_SEQ_LEN = 256
                EOF = 0x1a
                while idx < len(cas_data):
                    if len(cas_data) - idx < ASCII_SEQ_LEN:
                        print('Error: expected', ASCII_SEQ_LEN, 'bytes sequence in ASCII block', block_fname,
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
                        #print('Error: no cas header for next ASCII sequence at', dechex(idx))
                        return
                    idx = idx + CAS_HEADER_LEN
                #print('ASCII block end at', dechex(idx))
                if not found_eof:
                    print('Error: no eof found in ascii block at', dechex(idx))
                    return
            elif block_type == BINARY:
                start_address = cas_data[idx] + cas_data[idx + 1] * 256
                #print('start address:', dechex(start_address))
                end_address = cas_data[idx + 2] + cas_data[idx + 3] * 256
                #print('end address:  ', dechex(end_address))
                run_address = cas_data[idx + 4] + cas_data[idx + 5] * 256
                #print('run address:  ', dechex(run_address))
                code_len = end_address - start_address + 1
                #print('code length: ', dechex(code_len))
                idx = idx + 6
                bin_start = idx
                if idx + code_len > len(cas_data):
                    print('Error: unexpected end in binary block data')
                    return
                while idx < len(cas_data):
                    if is_cas_header(cas_data, idx):
                        break
                    block_data.append(cas_data[idx])
                    idx = idx + 1
                #print('block length:', dechex(idx - bin_start))
                #print('BINARY block end at', dechex(idx))
            elif block_type == CUSTOM:
                while idx < len(cas_data):
                    if is_cas_header(cas_data, idx):
                        break
                    block_data.append(cas_data[idx])
                    idx = idx + 1
                #print('CUSTOM block end at', dechex(idx))
            else:
                print('Error: this is a bug, this code should never be reached')
                return
            self.blocks.append([block_type, block_fname, block_data, start_address, end_address, run_address])


    def write(self, cas_name):
        """
        create a cas file from cas_data
        """
        if self.blocks == []:
            print('Error: no cas data, nothing to write to', cas_name)
            return
        f = open(cas_name, 'wb')
        if not f:
            print("Error: can't create file", cas_name)
            return
        print('create cas file:', cas_name)
        for block in self.blocks:
            block_type = block[0]
            block_fname = block[1]
            block_data = block[2]
            start_address = block[3]
            end_address = block[4]
            run_address = block[5]

            print('block_type:', hex(block_type))
            print('block_fname:', block_fname)
            print('len(block_data):', len(block_data))
            print('start_address:', hex(start_address))
            print('end_address:', hex(end_address))
            print('run_address:', hex(run_address))

            f.write(bytearray(CAS_HEADER))
            if block_type in [BASIC, ASCII, BINARY]:
                for i in range(BLOCK_HEADER_LEN):
                    f.write(bytes(block_type))
                fname_bytes = []
                for i in range(len(block_fname)):
                    fname_bytes.append(int(block_fname[i]))
                for i in range(len(block_fname), FNAME_LEN):
                    fname_bytes.append(0x20)    # pad with spaces
            if block_type == BASIC:
                print('BASIC')
            elif block_type == ASCII:
                print('ASCII')
                for i in range(len(block_data)):
                    if i % 256 == 0:
                        f.write(bytearray(CAS_HEADER))
                    f.write(bytes(block_data[i]))

            elif block_type == BINARY:
                print('BINARY')
            elif block_type == CUSTOM:
                print('CUSTOM')
            else:
                print('Error: invalid block type', block_type)
                return






def main():
    """
    for now just make some beeps
    """
    for i in range(1, len(sys.argv)):
        c = cas()
        c.read(sys.argv[i])
        c.write('---' + sys.argv[i])
        print('---')
#        t = wav_writer()
#        t.add_cas(1200, c)
#        t.write('test.wav')
#        del t
        del c

    
if __name__ == "__main__":
    main()
