#!/usr/bin/env python
#
# Inspired by Sparkfun's image raw2bmp.py
# https://github.com/sparkfun/SparkFun_HM01B0_Camera_ArduinoLibrary/blob/master/utils/raw2bmp.py

import argparse
import array
import base64
import numpy as np
from PIL import Image

# From image sensor size of HM01B0
HEIGHT = 244
WIDTH = 324


def read_file(infile):
    """Extract raw bytes of image data from last image in infile"""
    reading_data = False
    result = None
    y = 0
    for line in infile:
        if line == '+++ base64 +++\n':
            print('Found image')
            reading_data = True
            result = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
            y = 0
        elif line == '--- base64 ---\n':
            reading_data = False
        elif reading_data and line != '\n':
            for x, val in enumerate(base64.standard_b64decode(line)):
                result[y, x] = val
            y += 1
    infile.close()
    return result


def main():
    parser = argparse.ArgumentParser(description='read raw HM01B0 images frome file')
    parser.add_argument('input', type=argparse.FileType('r'),
            help='Console output to read.')
    parser.add_argument('output', type=argparse.FileType('wb'),
            help='Bitmap file to write')

    args = parser.parse_args()

    image_data = read_file(args.input)
    image = Image.fromarray(image_data, 'L')
    image.save(args.output)

    print ("done!")


if __name__ == "__main__":
   main()
