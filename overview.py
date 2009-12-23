#!/usr/bin/env python

# Raja S

"""Provides an overview of all images in the playlist
with a composite showing all thumbnails and filtering
based on exif info"""

from __future__ import division
from organizr import get_thumbnailfile
import Image
import datetime
from utils import ExifInfo, reduce_fraction, relative_time, in_range

class Overview():
    def __init__(self, parent, playlist):
        """playlist is a list of full filenames"""
        self.playlist = playlist
        self.frame = parent
        self.tn_size = 128

        self.sub_playlist = self.playlist # selected images only
        self.get_exifinfo()
        
    def get_exifinfo(self):
        """For all files in playlist get the exif information"""
        # load all exif info
        self.exifdata = []
        for filename in self.playlist:
            exif_data = ExifInfo(open
                            (filename, 'r'))
            self.exifdata.append(exif_data.info)

        date_vals = [data.get('DateTime', '-1') for data in self.exifdata]
        self.aperture_vals = [reduce_fraction(data.get('FNumber', '-1'))
                              for data in self.exifdata]
        self.shutter_vals = [data.get('ExposureTime', '-1') for data in self.exifdata]
        self.focal_vals = [data.get('FocalLength', '-1') for data in self.exifdata]

        date_vals = [datetime.datetime.strptime(val, '%Y:%m:%d %H:%M:%S')
                     for val in date_vals if val != '-1']
        self.date_vals = [relative_time(date_val) for date_val in date_vals]


    def rebuild_subplaylist(self, date_range,
                            aperture_range, shutter_range, focal_range):
        """Narrow down the selected images in the playlist"""
        aperture_steps = self.frame.aperture_select.steps
        shutter_steps = self.frame.shutter_select.steps
        focal_steps = self.frame.focal_select.steps
        
        self.sub_playlist = [self.playlist[ind] for ind in range(len(self.playlist)) if
                in_range(self.date_vals[ind], date_range) and
                in_range(aperture_steps.index(self.aperture_vals[ind]),
                         aperture_range) and
                in_range(shutter_steps.index(self.shutter_vals[ind]), shutter_range) and
                in_range(focal_steps.index(self.focal_vals[ind]), focal_range)]

        
    def build_composite(self):
        """create a composite image using all the images"""
        w,h = self.frame.canvas.GetSize()
        num_pics = len(self.sub_playlist)

        if num_pics > 0:
            ratio = ((w*h) / num_pics) ** 0.5
            cols = int(w // ratio)
            rows = int(num_pics // cols)
        else:
            cols = 0
            rows = 0

        self.blankimage = Image.new('RGB', (self.tn_size, self.tn_size),
                                        (200, 200, 200))
        self.composite = Image.new('RGB', ((self.tn_size + 10) * cols,
                                           (self.tn_size + 10) * (rows + 1)),
                                           (255, 255, 255))
        # loop thro each pic and add it
        index = 0
        for r in range(rows+1):
            for c in range(cols):
                if index == len(self.sub_playlist):
                    break
                filename = self.sub_playlist[index]
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
                    
                self.composite.paste(tb, (int(x1+xoffset), int(y1+yoffset)))
                index += 1

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
        
    
