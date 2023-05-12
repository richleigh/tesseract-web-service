#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013
# Author: Mark Peng
#
# Extended from Zdenko Podobný's work at: http://code.google.com/p/tesseract-ocr/wiki/APIExample
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import optparse
import ctypes
from ctypes import pythonapi, util, py_object
import io
import urllib.request, urllib.parse, urllib.error, io
from PIL import Image
import pathlib

"""
Get result string directly from tesseract C API
"""
class TesseactWrapper:
    def __init__(self, lang, libpath, tessdata):
        libname = pathlib.Path(libpath) / "libtesseract.so"

        print("Trying to load '%s'..." % libname)
        self.tesseract = ctypes.cdll.LoadLibrary(str(libname))

        self.tesseract.TessBaseAPICreate.restype = ctypes.c_void_p
        self.tesseract.TessBaseAPICreate.argtypes = []

        self.tesseract.TessBaseAPIInit2.restype = ctypes.c_int
        self.tesseract.TessBaseAPIInit2.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

        self.tesseract.TessBaseAPISetImage.restype = None
        self.tesseract.TessBaseAPISetImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

        self.tesseract.TessBaseAPIGetUTF8Text.restype = ctypes.c_char_p
        self.tesseract.TessBaseAPIGetUTF8Text.argtypes = [ctypes.c_void_p]

        self.tesseract.TessBaseAPIDelete.restype = None
        self.tesseract.TessBaseAPIDelete.argtypes = [ctypes.c_void_p]

        self.tesseract.TessBaseAPIProcessPages.restype = ctypes.c_char_p
        self.tesseract.TessBaseAPIProcessPages.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int]

        self.api = self.tesseract.TessBaseAPICreate()

        OEM_TESSERACT_LSTM_COMBINED = 3

        rc = self.tesseract.TessBaseAPIInit2(self.api, tessdata.encode("utf-8"), lang.encode("utf-8"), OEM_TESSERACT_LSTM_COMBINED)
        if (rc):
            self.tesseract.TessBaseAPIDelete(self.api)
            print("Could not initialize tesseract.\n")
            exit(1)

    def imageFileToString(self, filePath):

        # Running tesseract-ocr
        text_out = self.tesseract.TessBaseAPIProcessPages(self.api, filePath.encode("utf-8"), None, 0)
        result_text = ctypes.string_at(text_out).decode("utf-8")

        return result_text.replace("\n", "")

    def imageUrlToString(self, url, minWidth):

        # download image from url
        file = io.BytesIO(urllib.request.urlopen(url).read())
        tmpImg = Image.open(file)
        tmpImg = tmpImg.convert("RGBA")

        # force resize to minimal width if the incoming image is too small for better precision
        width, height = tmpImg.size
        newHeight = height
        if width < minWidth:
            ratio = float(minWidth) / width
            newHeight = int(height * ratio)
            tmpImg = tmpImg.resize((minWidth, newHeight), Image.ANTIALIAS)
            width = minWidth

        # transform data bytes to single dimensional array
        data = tmpImg.getdata()
        copyData = [0] * len(data) * 4
        for i in range(len(data)):
            for j in range(len(data[i])):
                cursor = i * 4 + j
                copyData[cursor] = data[i][j]

        # compute stride
        bytesPerLine = width * 4

        # create a ctype ubyte array and copy data to it
        arrayLength = newHeight * width * 4
        ubyteArray = (ctypes.c_ubyte * arrayLength)()
        for i in range(arrayLength):
            ubyteArray[i] = copyData[i]

        # call SetImage
        self.tesseract.TessBaseAPISetImage(self.api, ubyteArray, width, newHeight, 4, bytesPerLine)

        # call GetUTF8Text
        text_out =  self.tesseract.TessBaseAPIGetUTF8Text(self.api).decode("utf-8")

        return text_out

def main():
    parser = optparse.OptionParser()
    parser.add_option('-l', '--lang', dest='lang', help='the targe language.')
    parser.add_option('-b', '--lib-path', dest='libPath', help='the absolute path of tesseract library.')
    parser.add_option('-d', '--tessdata-folder', dest='tessdata', help='the absolute path of tessdata folder containing language packs.')
    parser.add_option('-i', '--image-url', dest='imageUrl', help='the URL of image to do OCR.')
    parser.add_option('-m', '--min-width', dest='minWidth', help='the minmal width for image before running OCR. The program will try to resize the image to target width. (default: 150)')
    (options, args) = parser.parse_args()

    if not options.lang:   # if lang is not given
        parser.error('lang not given')
    if not options.libPath:   # if libPath is not given
        parser.error('lib-path not given')
    if not options.tessdata:   # if tessdata is not given
        parser.error('tessdata not given')
    if not options.imageUrl:   # if imageUrl is not given
        parser.error('image-url not given')
    if not options.minWidth:   # if minWidth is not given
        targetWidth = 150
    else:
        targetWidth = options.minWidth

    # call tesseract C API
    wrapper = TesseactWrapper(options.lang, options.libPath, options.tessdata)
    wrapper.imageUrlToString(options.imageUrl, targetWidth)

    # Test
    # lang = "eng"
    # libpath = "/home/markpeng/local/lib"
    # tessdata = "/home/markpeng/temp/tesseract-ocr/"
    # wrapper = TesseactWrapper(lang, libpath, tessdata)
    # url = "http://price2.suning.cn/webapp/wcs/stores/prdprice/398956_9017_10000_9-1.png"
    # url = "http://price1.suning.cn/webapp/wcs/stores/prdprice/12973756_9017_10052_11-9.png"
    # wrapper.imageUrlToString(url, 150)

if __name__ == '__main__':
    main()
