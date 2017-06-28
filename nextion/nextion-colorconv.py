#!/usr/bin/env python

# Nextion to RGB color convertor
# By Michal Ludvig <mludvig@logix.net.nz>

# Nextion uses 16-bit colour encoding:
# |R|R|R|R||R|G|G|G| |G|G|G|B||B|B|B|B|

def nextion2rgb(nxval):
    r = (nxval & 0xF800) >> 8
    g = (nxval & 0x07E0) >> 3
    b = (nxval & 0x001F) << 3
    #return (r, g, b)
    return "#%02X%02X%02X" % (r, g, b)

def rgb2tuple(rgb):
    """
    rgb2nextion(rgb) - convert 'rgb' string, e.g. '#F0F0F0' to (R,G,B) tuple
    """
    if rgb[0] == "#":
        rgb = rgb[1:]
    if len(rgb) != 6:
        return (0, 0, 0)
    r = int(rgb[0:2], 16)
    g = int(rgb[2:4], 16)
    b = int(rgb[4:6], 16)
    #print "%r" % ((r,g,b),)
    return (r, g, b)

def rgb2nextion(rgb):
    if type(rgb) in (str, unicode):
        rgb = rgb2tuple(rgb)
    (r, g, b) = rgb
    return ((r & 0xF8) << 8) | ((g & 0xF8) << 3) | ((b & 0xF8) >> 3)

print """
Enter a decimal number (e.g. 65535) to convert from Nextion to RGB
Enter a #XXXXXX number (e.g. #A0B1C2) to convert from RGB to Nextion
"""
while True:
    try:
        inp=raw_input("%> ")
    except EOFError:
        break
    if not inp:
        break
    if inp[0] == "#":
        print("Nextion: %d" % (rgb2nextion(inp)))
    else:
        print("RGB: %s" % (nextion2rgb(int(inp))))
