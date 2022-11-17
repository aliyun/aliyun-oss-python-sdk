from .common import *

class TestBucketCname(OssTestCase):
    def test_1_bucket_cname(self):
        test_domain = 'www.example.com'
        cert_id = '49311111-cn-hangzhou'
        previous_cert_id = '493333'
        certificate = '''-----BEGIN CERTIFICATE-----
MIIDWzCCAkOgAwIBAgIUV4spou0CenmvKqa7Hml/MC+JKiAwDQYJKoZIhvcNAQEL
BQAwPTELMAkGA1UEBhMCVVMxEzARBgNVBAgMCkNhbGlmb3JuaWExGTAXBgNVBAoM
EFRvcm5hZG8gV2ViIFRlc3QwHhcNMTgwOTI5MTM1NjQ1WhcNMjgwOTI2MTM1NjQ1
WjA9MQswCQYDVQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTEZMBcGA1UECgwQ
VG9ybmFkbyBXZWIgVGVzdDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
AKT0LdyI8tW5uwP3ahE8BFSz+j3SsKBDv/0cKvqxVVE6sLEST2s3HjArZvIIG5sb
iBkWDrqnZ6UKDvB4jlobLGAkepxDbrxHWxK53n0C28XXGLqJQ01TlTZ5rpjttMeg
5SKNjHbxpOvpUwwQS4br4WjZKKyTGiXpFkFUty+tYVU35/U2yyvreWHmzpHx/25t
H7O2RBARVwJYKOGPtlH62lQjpIWfVfklY4Ip8Hjl3B6rBxPyBULmVQw0qgoZn648
oa4oLjs0wnYBz01gVjNMDHej52SsB/ieH7W1TxFMzqOlcvHh41uFbQJPgcXsruSS
9Z4twzSWkUp2vk/C//4Sz38CAwEAAaNTMFEwHQYDVR0OBBYEFLf8fQ5+u8sDWAd3
r5ZjZ5MmDWJeMB8GA1UdIwQYMBaAFLf8fQ5+u8sDWAd3r5ZjZ5MmDWJeMA8GA1Ud
EwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBADkkm3pIb9IeqVNmQ2uhQOgw
UwyToTYUHNTb/Nm5lzBTBqC8gbXAS24RQ30AB/7G115Uxeo+YMKfITxm/CgR+vhF
F59/YrzwXj+G8bdbuVl/UbB6f9RSp+Zo93rUZAtPWr77gxLUrcwSRzzDwxFjC2nC
6eigbkvt1OQY775RwnFAt7HKPclE0Out+cGJIboJuO1f3r57ZdyFH0GzbZEff/7K
atGXohijWJjYvU4mk0KFHORZrcBpsv9cfkFbmgVmiRwxRJ1tLauHM3Ne+VfqYE5M
4rTStSyz3ASqVKJ2iFMQueNR/tUOuDlfRt+0nhJMuYSSkW+KTgnwyOGU9cv+mxA=
-----END CERTIFICATE-----'''
        private_key = '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCk9C3ciPLVubsD
92oRPARUs/o90rCgQ7/9HCr6sVVROrCxEk9rNx4wK2byCBubG4gZFg66p2elCg7w
eI5aGyxgJHqcQ268R1sSud59AtvF1xi6iUNNU5U2ea6Y7bTHoOUijYx28aTr6VMM
EEuG6+Fo2Siskxol6RZBVLcvrWFVN+f1Nssr63lh5s6R8f9ubR+ztkQQEVcCWCjh
j7ZR+tpUI6SFn1X5JWOCKfB45dweqwcT8gVC5lUMNKoKGZ+uPKGuKC47NMJ2Ac9N
YFYzTAx3o+dkrAf4nh+1tU8RTM6jpXLx4eNbhW0CT4HF7K7kkvWeLcM0lpFKdr5P
wv/+Es9/AgMBAAECggEABi6AaXtYXloPgB6NgwfUwbfc8OQsalUfpMShd7OdluW0
KW6eO05de0ClIvzay/1EJGyHMMeFQtIVrT1XWFkcWJ4FWkXMqJGkABenFtg8lDVz
X8o1E3jGZrw4ptKBq9mDvL/BO9PiclTUH+ecbPn6AIvi0lTQ7grGIryiAM9mjmLy
jpCwoutF2LD4RPNg8vqWe/Z1rQw5lp8FOHhRwPooHHeoq1bSrp8dqvVAwAam7Mmf
uFgI8jrNycPgr2cwEEtbq2TQ625MhVnCpwT+kErmAStfbXXuqv1X1ZZgiNxf+61C
OL0bhPRVIHmmjiK/5qHRuN4Q5u9/Yp2SJ4W5xadSQQKBgQDR7dnOlYYQiaoPJeD/
7jcLVJbWwbr7bE19O/QpYAtkA/FtGlKr+hQxPhK6OYp+in8eHf+ga/NSAjCWRBoh
MNAVCJtiirHo2tFsLFOmlJpGL9n3sX8UnkJN90oHfWrzJ8BZnXaSw2eOuyw8LLj+
Q+ISl6Go8/xfsuy3EDv4AP1wCwKBgQDJJ4vEV3Kr+bc6N/xeu+G0oHvRAWwuQpcx
9D+XpnqbJbFDnWKNE7oGsDCs8Qjr0CdFUN1pm1ppITDZ5N1cWuDg/47ZAXqEK6D1
z13S7O0oQPlnsPL7mHs2Vl73muAaBPAojFvceHHfccr7Z94BXqKsiyfaWz6kclT/
Nl4JTdsC3QKBgQCeYgozL2J/da2lUhnIXcyPstk+29kbueFYu/QBh2HwqnzqqLJ4
5+t2H3P3plQUFp/DdDSZrvhcBiTsKiNgqThEtkKtfSCvIvBf4a2W/4TJsW6MzxCm
2KQDuK/UqM4Y+APKWN/N6Lln2VWNbNyBkWuuRVKFatccyJyJnSjxeqW7cwKBgGyN
idCYPIrwROAHLItXKvOWE5t0ABRq3TsZC2RkdA/b5HCPs4pclexcEriRjvXrK/Yt
MH94Ve8b+UftSUQ4ytjBMS6MrLg87y0YDhLwxv8NKUq65DXAUOW+8JsAmmWQOqY3
MK+m1BT4TMklgVoN3w3sPsKIsSJ/jLz5cv/kYweFAoGAG4iWU1378tI2Ts/Fngsv
7eoWhoda77Y9D0Yoy20aN9VdMHzIYCBOubtRPEuwgaReNwbUBWap01J63yY/fF3K
8PTz6covjoOJqxQJOvM7nM0CsJawG9ccw3YXyd9KgRIdSt6ooEhb7N8W2EXYoKl3
g1i2t41Q/SC3HUGC5mJjpO8=
-----END PRIVATE KEY-----
'''
        try:
            result = self.bucket.create_bucket_cname_token(test_domain)
        except:
            self.assertFalse(True, "should not get a exception")
            self.assertEqual(200, result.status)
            self.assertEqual(test_domain, result.cname)

        try:
            result = self.bucket.get_bucket_cname_token(test_domain)
        except:
            self.assertEqual(200, result.status)
            self.assertEqual(test_domain, result.cname)


        cert = oss2.models.CertInfo(cert_id, certificate, private_key, previous_cert_id, True, False)
        input = oss2.models.PutBucketCnameRequest(test_domain, cert)
        try:
            result = self.bucket.put_bucket_cname(input)
            self.assertFalse(True, "should not get a exception")
        except oss2.exceptions.ServerError as e:
            self.assertEqual(e.details['Code'], 'NeedVerifyDomainOwnership')
        except:
            self.assertFalse(True, "should not get other exception")


        result = self.bucket.list_bucket_cname()
        self.assertEqual(200, result.status)

        self.bucket.delete_bucket_cname(test_domain)
        self.assertEqual(200, result.status)


if __name__ == '__main__':
    unittest.main()
