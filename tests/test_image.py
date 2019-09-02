# -*- coding: utf-8 -*-

import unittest
import sys
import oss2
import json

from .common import *


class TestImage(OssTestCase):
    def __prepare(self):
        original_image = 'tests/example.jpg'
        new_image = self.random_key('.jpg')
        
        self.bucket.put_object_from_file(original_image, original_image)
        
        return original_image, new_image
    
    def __clear(self, original_image, new_image):
        self.bucket.delete_object(original_image)
        self.bucket.delete_object(new_image)

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
        style = "image/resize,m_fixed,w_100,h_100"  # 缩放
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 100, 100, 3267, 'jpg')
        self.__clear(original_image, new_image)
            
    def test_crop(self):
        style = "image/crop,w_100,h_100,x_100,y_100,r_1"  # 裁剪
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 100, 100, 1969, 'jpg')
        self.__clear(original_image, new_image)
        
    def test_rotate(self):
        style = "image/rotate,90"  # 旋转
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 400, 267, 20998, 'jpg')
        self.__clear(original_image, new_image)
        
    def test_sharpen(self):
        style = "image/sharpen,100"  # 锐化
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 267, 400, 23015, 'jpg')
        self.__clear(original_image, new_image)
        
    def test_watermark(self):
        style = "image/watermark,text_SGVsbG8g5Zu-54mH5pyN5YqhIQ"  # 文字水印
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 267, 400, 26378, 'jpg')
        self.__clear(original_image, new_image)
        
    def test_format(self):
        style = "image/format,png"  # 图像格式转换
        
        original_image, new_image = self.__prepare()
        self.__test(original_image, new_image, style)
        self.__check(new_image, 267, 400, 160733, 'png')
        self.__clear(original_image, new_image)
        
    def test_resize_to_file(self):
        style = "image/resize,m_fixed,w_100,h_100"  # 缩放
        
        original_image, new_image = self.__prepare()
        self.__test_to_file(original_image, new_image, style)
        self.__check(new_image, 100, 100, 3267, 'jpg')
        self.__clear(original_image, new_image)
         

if __name__ == '__main__':
    unittest.main()
