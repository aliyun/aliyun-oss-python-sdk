# -*- coding: utf-8 -*-

from .common import *
import oss2
import crcmod

class TestCrc64Combine(OssTestCase):
    def test_crc64_combine(self):
        _POLY = 0x142F0E1EBA9EA3693
        _XOROUT = 0XFFFFFFFFFFFFFFFF

        string_a = oss2.to_bytes('12345')
        string_b = oss2.to_bytes('67890')

        combine_fun = oss2.crc64_combine.mkCombineFun(_POLY, 0, True, _XOROUT)

        crc64_a = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_a.update(string_a)
        crc1 = crc64_a.crcValue

        crc64_b = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_b.update(string_b)
        crc2 = crc64_b.crcValue

        crc_combine = combine_fun(crc1, crc2, len(string_b))

        crc64_c = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_c.update(string_a + string_b)
        crc_raw = crc64_c.crcValue

        self.assertEqual(crc_combine, crc_raw)

    def test_crc64_combine_rev_false(self):
        _POLY = 0x142F0E1EBA9EA3693
        _XOROUT = 0XFFFFFFFFFFFFFFFF

        string_a = oss2.to_bytes('12345')
        string_b = oss2.to_bytes('67890')

        combine_fun = oss2.crc64_combine.mkCombineFun(_POLY, 0, False, _XOROUT)

        crc64_a = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_a.update(string_a)
        crc1 = crc64_a.crcValue

        crc64_b = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_b.update(string_b)
        crc2 = crc64_b.crcValue

        crc_combine = combine_fun(crc1, crc2, len(string_b))

        crc64_c = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_c.update(string_a + string_b)
        crc_raw = crc64_c.crcValue

        self.assertTrue(crc_combine !=  crc_raw)

    def test_crc64_combine_str2_empty(self):
        _POLY = 0x142F0E1EBA9EA3693
        _XOROUT = 0XFFFFFFFFFFFFFFFF

        string_a = oss2.to_bytes('12345')
        string_b = oss2.to_bytes('')

        combine_fun = oss2.crc64_combine.mkCombineFun(_POLY, 0, True, _XOROUT)

        crc64_a = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_a.update(string_a)
        crc1 = crc64_a.crcValue

        crc64_b = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_b.update(string_b)
        crc2 = crc64_b.crcValue

        crc_combine = combine_fun(crc1, crc2, len(string_b))

        crc64_c = crcmod.Crc(_POLY, initCrc=0, xorOut=_XOROUT)
        crc64_c.update(string_a + string_b)
        crc_raw = crc64_c.crcValue

        self.assertEqual(crc_combine, crc_raw)


if __name__ == '__main__':
    unittest.main()
