#!/usr/bin/env python

# Raja S

"""Provides an overview of all images in the playlist
with a composite showing all thumbnails and filtering
based on exif info"""

from __future__ import division
from organizr import get_thumbnailfile
import Image

class Overview():
    def __init__(self, parent, playlist):
        """playlist is a list of full filenames"""
        self.playlist = playlist
        self.frame = parent
        self.tn_size = 128

    def build_composite(self):
        """create a composite image using all the images"""
        w,h = self.frame.canvas.GetSize()
        num_pics = len(self.playlist)

        ratio = ((w*h) / num_pics) ** 0.5
        rows = w // ratio
        cols = num_pics // rows
        
        self.blankimage = Image.new('RGB', (self.tn_size, self.tn_size),
                                        (200, 200, 200))
                    
        self.composite = Image.new('RGB', ((self.tn_size + 10) * cols,
                                           (self.tn_size + 10) * rows),
                                   (255, 255, 255))


        index = 0
        for r in range(rows):
            for c in range(cols):
                filename = self.playlist[index]
                tb_file = get_thumbnailfile(filename)
                if not tb_file:
                    try:
                        print 'no stored tb'
                        tb = Image.open(filename)
                    except:
                        tb = self.blankimage
                else:
                    tb = Image.open(tb_file)
                        
                x1 = 5 + c * (self.tn_size + 10)
                y1 = 5 + r * (self.tn_size + 10) 

                tb_width, tb_height = tb.size
                xoffset = (self.tn_size - tb_width) / 2
                yoffset = (self.tn_size - tb_height) / 2
                    
                self.composite.paste(tb, (x1+xoffset, y1+yoffset))
                index += 1

        self.composite.save('/data/tmp/composite.jpg')

    def load(self):
        """load the composite image on the canvas"""
        self.frame.SetStatusText('Loading')

        self.width, self.height = self.composite.size
        self.zoom_xoffset = None
        self.zoom_yoffset = None
        self.zoom_ratio = 1
        self.zoomframe = (0, 0, 0, 0)
        # on loading, there is no zoom
        self.image = self.composite
        
        self.frame.canvas.NEEDREDRAW = True
        status_string = "composite"
        self.frame.SetStatusText(status_string)
        
def test():
    overview = Overview(None, range(63))
    overview.build_composite()

        
if __name__ == "__main__":
    test()
        
    
