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


class ImageFlags:
    Orient = 1 << 0
    Shrink = 1 << 1
    Frame = 1 << 2
    Quantize = 1 << 3
    # Add new flags here to not break compatability with older saves.
    Enlarge = 1 << 4
    Split = 1 << 5

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
        'Kindle 1': ((600, 800), Palette4),
        'Kindle 2': ((600, 800), Palette15),
        'Kindle 3': ((600, 800), Palette15),
        'Kindle DX': ((824, 1200), Palette15),
        'Kindle DXG': ((824, 1200), Palette15),
        'nook': ((600, 730), Palette15),
        'nook color': ((600, 1024), Palette15)
    }


def quantizeImage(image, palette):
    colors = len(palette) / 3
    if colors < 256:
        palette = palette + palette[:3] * (256 - colors)

    palImg = Image.new('P', (1, 1))
    palImg.putpalette(palette)

    return image.quantize(palette=palImg)


def resizeImage(image, size, shrink, enlarge):
    # The size we're taking in isn't the *exact* size so much as it is a target.
    # We want to resize the image to fit these dimensions, while maintaining
    # its aspect ratio, so we call them the max width/height.
    widthMax, heightMax = size

    # Keep track of the original width/height so we know which filter to use later.
    widthOrig, heightOrig = image.size

    # It only makes sense to enlarge if both dimensions are smaller than the target.
    if (widthOrig < widthMax and heightOrig < heightMax) and not enlarge:
        return image

    # We shrink, however, if either dimension is too large.
    if (widthOrig > widthMax or heightOrig > heightMax) and not shrink:
        return image

    ratioImg = float(widthOrig) / float(heightOrig)
    ratioWidth = float(widthOrig) / float(widthMax)
    ratioHeight = float(heightOrig) / float(heightMax)

    if ratioWidth > ratioHeight:
        widthNew = widthMax
        heightNew = int(widthMax / ratioImg)
    elif ratioWidth < ratioHeight:
        heightNew = heightMax
        widthNew = int(heightMax * ratioImg)
    else:
        widthNew, heightNew = size

    # The antialias filter is best for shrinking, but bicubic is best for enlarging.
    if widthNew < widthOrig or heightNew < heightOrig:
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
        return image.rotate(90, Image.BICUBIC, True)

    return image


def frameImage(image, foreground, background, size):
    widthDev, heightDev = size
    widthImg, heightImg = image.size

    pastePt = (
        max(0, (widthDev - widthImg) / 2),
        max(0, (heightDev - heightImg) / 2)
    )

    corner1 = (
        pastePt[0] - 1,
        pastePt[1] - 1
    )

    corner2 = (
        pastePt[0] + widthImg + 1,
        pastePt[1] + heightImg + 1
    )

    imageBg = Image.new(image.mode, size, background)
    imageBg.paste(image, pastePt)

    draw = ImageDraw.Draw(imageBg)
    draw.rectangle([corner1, corner2], outline=foreground)

    return imageBg


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
    if enlarge or shrink:
        image = resizeImage(image, size, shrink, enlarge)
    if flags & ImageFlags.Frame:
        image = frameImage(image, tuple(palette[:3]), tuple(palette[-3:]), size)
    if flags & ImageFlags.Quantize:
        image = quantizeImage(image, palette)

    return image
