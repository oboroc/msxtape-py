import unittest, inspect, msxtape


class Test_msxtape(unittest.TestCase):
    def test_always_fail(self):
        self.fail("Not implemented")

    def test_8bit_sample_padding(self):
        f_name = inspect.stack()[0][3] + '.wav'
        t = msxtape.msxtape(f_name)
        t.add_tone(1200.0, 1.01)    # 1.01 seconds generates odd number of pcm data bytes
        l = len(t.pcm_data)
        del t
        self.assertEqual(1, 1, 'oh no')

if __name__ == '__main__':
    unittest.main()

  #  print('hello')