# Copyright (C) 2010  Alex Yatskov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PIL import Image, ImageDraw

import math

class ImageFlags:
    Orient = 1 << 0
    Shrink = 1 << 1
    Frame = 1 << 2
    Quantize = 1 << 3
    # Add new flags here to not break compatability with older saves.
    Enlarge = 1 << 4
    Split = 1 << 5
    RightToLeft = 1 << 6

class KindleData:
    Palette4 = [
        0x00, 0x00, 0x00,
        0x55, 0x55, 0x55,
        0xaa, 0xaa, 0xaa,
        0xff, 0xff, 0xff
    ]

    Palette15 = [
        0x00, 0x00, 0x00,
        0x11, 0x11, 0x11,
        0x22, 0x22, 0x22,
        0x33, 0x33, 0x33,
        0x44, 0x44, 0x44,
        0x55, 0x55, 0x55,
        0x66, 0x66, 0x66,
        0x77, 0x77, 0x77,
        0x88, 0x88, 0x88,
        0x99, 0x99, 0x99,
        0xaa, 0xaa, 0xaa,
        0xbb, 0xbb, 0xbb,
        0xcc, 0xcc, 0xcc,
        0xdd, 0xdd, 0xdd,
        0xff, 0xff, 0xff,
    ]

    Profiles = {
        'Aura HD': ((1080, 1300), Palette15),
        'Kindle 1': ((600, 800), Palette4),
        'Kindle 2': ((600, 800), Palette15),
        'Kindle 3': ((600, 800), Palette15),
        'Kindle DX': ((824, 1200), Palette15),
        'Kindle DXG': ((824, 1200), Palette15),
        'nook': ((600, 730), Palette15),
        'nook color': ((600, 980), Palette15)
    }


def quantizeImage(image, palette):
    colors = len(palette) / 3
    if colors < 256:
        palette = palette + palette[:3] * (256 - colors)

    palImg = Image.new('P', (1, 1))
    palImg.putpalette(palette)

    return image.quantize(palette=palImg)


def resizeImage(image, size, shrink, enlarge):
    # The device dimensions aren't the *exact* size so much as a target.
    # We want to resize the image to fit these dimensions, while maintaining
    # its aspect ratio, so they're more like a maximum.
    widthDev, heightDev = size

    # Keep track of the original width/height so we know which filter to use later.
    widthImg, heightImg = image.size

    # It only makes sense to enlarge if both dimensions are smaller than the target.
    if (widthImg < widthDev and heightImg < heightDev) and not enlarge:
        return image

    # We shrink, however, if either dimension is too large.
    if (widthImg > widthDev or heightImg > heightDev) and not shrink:
        return image

    ratioImg = float(widthImg) / float(heightImg)
    ratioWidth = float(widthImg) / float(widthDev)
    ratioHeight = float(heightImg) / float(heightDev)

    if ratioWidth > ratioHeight:
        widthNew = widthDev
        heightNew = int(widthDev / ratioImg)
    elif ratioWidth < ratioHeight:
        heightNew = heightDev
        widthNew = int(heightDev * ratioImg)
    else:
        widthNew, heightNew = size

    # The antialias filter is best for shrinking, but bicubic is best for enlarging.
    if widthNew < widthImg or heightNew < heightImg:
        return image.resize((widthNew, heightNew), Image.ANTIALIAS)
    else:
        return image.resize((widthNew, heightNew), Image.BICUBIC)


def formatImage(image):
    if image.mode == 'RGB':
        return image
    return image.convert('RGB')


def orientImage(image, size):
    widthDev, heightDev = size
    widthImg, heightImg = image.size

    if (widthImg > heightImg) != (widthDev > heightDev):
        # Since a 90-degree rotation is easy, meaning we don't need to do any
        # filtering, just use the transpose version, to be explicit.
        return image.transpose(Image.ROTATE_90)

    return image


def frameImage(image, foreground, background, size):
    widthDev, heightDev = size
    widthImg, heightImg = image.size
    
    # This is going to be the size of our new image. It will match the device's
    # aspect ratio, and it will be at a minimum the same size as the device.
    widthNew = widthDev
    heightNew = heightDev
    
    # If the image is larger than the device in either dimension, we'll add
    # a frame so the new image matches the device's aspect ratio, rather than
    # chopping it down to the device's size. If the user wanted that, they
    # would have chosen to shrink the image in the first place.
    if widthImg > widthDev or heightImg > heightDev:
        aspectDev = float(widthDev) / float(heightDev)
        aspectImg = float(widthImg) / float(heightImg)
        
        # If the image's aspect ratio is greater than the device's, that means
        # it is relatively wider, and we need to add to the top/bottom.
        if aspectImg > aspectDev:
            widthNew = widthImg
            heightNew = int(widthImg / aspectDev)
        elif aspectImg < aspectDev:
            heightNew = heightImg
            widthNew = int(heightImg * aspectDev)
        else:
            widthNew = widthImg
            heightNew = heightImg

    pastePt = (
        max(0, int((widthNew - widthImg) / 2)),
        max(0, int((heightNew - heightImg) / 2))
    )

    corner1 = (
        pastePt[0] - 1,
        pastePt[1] - 1
    )

    corner2 = (
        pastePt[0] + widthImg,
        pastePt[1] + heightImg
    )

    imageBg = Image.new(image.mode, (widthNew, heightNew), background)
    imageBg.paste(image, pastePt)

    draw = ImageDraw.Draw(imageBg)
    draw.rectangle([corner1, corner2], outline=foreground)

    return imageBg


def splitImage(image, size, rtl = True):
    widthDev, heightDev = size
    widthImg, heightImg = image.size
    
    # Assumption: It only makes sense to split images vertically, like two
    # pages of a book side-by-side in the same image. There are probably some
    # images which are wider than two pages, so we could have to split it
    # multiple times. But we want to split them evenly, assuming if something
    # is ~3x as wide as the device, it's 3 pages.
    
    # To make this safe to run on *any* image, whether it's been shrunk to
    # fit on a specific device or not, we'll do our comparisons on the aspect
    # ratios. If the image's aspect ratio is larger than the device's, it means
    # the image is relatively wider than the device.
    aspectDev = float(widthDev) / float(heightDev)
    aspectImg = float(widthImg) / float(heightImg)
    
    # If the image has a larger aspect ratio, this will be greater than 1.
    # If the image has a smaller aspect ratio, this will be 1.
    # We use the ceiling because, if we used the floor, the new images would
    # end up still wider than the device.
    numPages = int(math.ceil(float(aspectImg) / float(aspectDev)))
    
    # The list of images we'll be returning. Even if we don't split anything,
    # everything else has to assume they'll be getting multiple images.
    images = []
    
    if numPages > 1:
        # We use the ceiling so the last page is, possibly, a few pixels
        # short, due to rounding issues, but none of the pages are wider
        # than we want. If we used the floor, the last page would be several
        # pixels WIDER than the other pages, possibly exceeding our target.
        targetWidth = int(math.ceil(float(widthImg) / float(numPages)))
        
        # Start generating our new pages.
        # rtl specifies right-to-left ordering. If enabled, the first page
        # created is from the section farthest right in the image.
        for i in (range(numPages) if not rtl else reversed(range(numPages))):
            newWidth = targetWidth
            
            # Account for the rounding discrepancy described above.
            # Rather than assuming the same width for the last page, get
            # the exact width by removing the width of all the other pages
            # from the total width of the original image.
            if i == numPages - 1:
                newWidth = widthImg - ((numPages - 1) * targetWidth)
            
            # This one's easy.
            newHeight = heightImg
            
            newImage = image.crop(
              (targetWidth * i, 0, (targetWidth * i) + newWidth, newHeight)
            ).copy()
            
            images.append(newImage)
        
    else:
        images = [image]
    
    return images
    
def convertImage(source, device, flags):
    try:
        size, palette = KindleData.Profiles[device]
    except KeyError:
        raise RuntimeError('Unexpected output device %s' % device)

    try:
        image = Image.open(source)
    except IOError:
        raise RuntimeError('Cannot read image file %s' % source)

    shrink = flags & ImageFlags.Shrink
    enlarge = flags & ImageFlags.Enlarge

    image = formatImage(image)
    if flags & ImageFlags.Orient:
        image = orientImage(image, size)
    
    # Since splitting is now an option, it is possible, at any time, that
    # one image might become two or three or a thousand images, so we move
    # forward assuming all converted images are lists of images.
    images = []
    
    if flags & ImageFlags.Split:
        images = splitImage(image, size, flags & ImageFlags.RightToLeft)
    else:
        images = [image]
    
    # Loop over every image in the list, and perform these steps on them.
    for x in range(len(images)):
      
      if enlarge or shrink:
          images[x] = resizeImage(images[x], size, shrink, enlarge)
          
      if flags & ImageFlags.Frame:
          # tuple(palette[:3] and tuple(palette[-3:]) refer to black and white,
          # which happen to be the first/last colors in the palettes defined.
          images[x] = frameImage(images[x], tuple(palette[:3]), tuple(palette[-3:]), size)
          
      if flags & ImageFlags.Quantize:
          images[x] = quantizeImage(images[x], palette)

    return images
