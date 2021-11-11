import sys
from os import listdir
from os.path import isfile, join
from struct import *
from PIL import Image

for f in listdir(sys.argv[1]):
    path = join(sys.argv[1], f)
    if isfile(path):
        with open(path, "rb") as stream:
            stream.seek(0, 2)
            length = stream.tell() - 8
            stream.seek(0)
            w = unpack("<I", stream.read(4))[0]
            h = unpack("<I", stream.read(4))[0]
            buf = stream.read(length)
            img = Image.frombytes(mode="RGBA", data=buf, size=(w,h))
            img.save(join(sys.argv[2], f) + ".png")
