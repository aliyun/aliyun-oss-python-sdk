# -*- coding: utf-8 -*-

import unittest
import sys
import oss2
import json

from common import *


class TestImage(OssTestCase):
    def __prepare(self):
        original_image = 'tests/example.jpg'
        new_image = self.random_key('.jpg')
        
        self.bucket.put_object_from_file(original_image, original_image)
        
        return original_image, new_image
    
    def __test(self, original_image, new_image, image_style):
        original_image_content = self.bucket.get_object(original_image, process=image_style)
        self.bucket.put_object(new_image, original_image_content)
        
    def __test_to_file(self, original_image, new_image, image_style):
        self.bucket.get_object_to_file(original_image, new_image, process=image_style)
        self.bucket.put_object_from_file(new_image, new_image)
        oss2.utils.silently_remove(new_image)
        
    def __check(self, image_key, image_height, image_width, image_size, image_format):
        result = self.bucket.get_object(image_key, process='image/info')
        json_content = result.read()
        decoded_json = json.loads(oss2.to_unicode(json_content))
        
        self.assertEqual(int(decoded_json['ImageHeight']['value']), image_height)
        self.assertEqual(int(decoded_json['ImageWidth']['value']), image_width)
        self.assertEqual(int(decoded_json['FileSize']['value']), image_size)
        self.assertEqual(decoded_json['Format']['value'], image_format)
    
    def test_resize(self):
        style = "image/resize,m_fixed,w_100,h_100"  # resize
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 100, 100, 3267, 'jpg')
            
    def test_crop(self):
        style = "image/crop,w_100,h_100,x_100,y_100,r_1"  # crop
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 100, 100, 1969, 'jpg')
        
    def test_rotate(self):
        style = "image/rotate,90"  # rotate
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 400, 267, 20998, 'jpg')
        
    def test_sharpen(self):
        style = "image/sharpen,100"  # sharpen
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 267, 400, 23015, 'jpg')
        
    def test_watermark(self):
        style = "image/watermark,text_SGVsbG8g5Zu-54mH5pyN5YqhIQ"  # watermark
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 267, 400, 26369, 'jpg')
        
    def test_format(self):
        style = "image/format,png"  # format transcode
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 267, 400, 160733, 'png')
        
    def test_resize_to_file(self):
        style = "image/resize,m_fixed,w_100,h_100"  # resize
        
        original_image, new_image = self.__prepare()
        self.__test_to_file(original_image, new_image, style)
        self.__check(new_image, 100, 100, 3267, 'jpg')
         

if __name__ == '__main__':
    unittest.main()
