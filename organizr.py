#!/usr/bin/env python
"""
for organizing photos, especially those taken in RAW+ mode.
"""

import wx
import Image

import Exifreader

class Organizr(wx.App):
    """The core class
    """
    def __init__(self):
        """
	"""
        wx.App.__init__(self, 0)

    def OnInit(self):
        """run the organizr"""
        organizrwindow = MainWindow()

        
        organizrwindow.Show()
        return True

class MainWindow(wx.Frame):
    """The frame for the gui
    """
    def __init__(self):
        """
	"""
        wx.Frame.__init__(self, None, -1, "")

        self.splitter1 = wx.SplitterWindow(self, style=wx.SP_3D)
        self.playlistpanel = wx.Panel(self.splitter1, -1)
        self.imagepanel = wx.Panel(self.splitter1, -1)
        self.splitter1.SplitHorizontally(self.playlistpanel, self.imagepanel)
        
        self.CreateStatusBar(2)


class ImageCanvas(wx.Panel):
    """panel where the images are displayed
    """
    def __init__(self, *args, **kwargs):
        """
	"""
        wx.Panel.__init__()
        pass
        

class Im():
    """the loaded image"""
    def __init__(self, imagefilenames):
        """imagefilenames is a list of the filenames.
        for single image this is a singleton list.
        Multiple items indicate this is a series to be loaded"""
        self.imagefilenames = imagefilenames

    def load(self):
        """load as a wx bitmap"""
        pass

    def load_multiple(self):
        """Load a list of images and construct a composite image"""
        pass


    def zoom(self, scale):
        """scale the bitmap by the given scale.
        use to zoom in or zoom out.
        return the viewing frame"""
        frame = []
        return frame

    
class Thumbnail():
    """thumbnail of the image"""
    def __init__(self, imagefilename):
        """imagefilename is filename of the single image
        or the name of the first in series for a series of images"""
        self.imagefilename = imagefilename
        pass
        
class ExifInfo():
    """exif information for an image"""
    def __init__(self, imagefilehandle):
        self.imagefilehandle = imagefilehandle

    def read_exif_info(self):
        """read the exif information"""
        try:
            self.exifdata = Exifreader.process(self.imagefilehandle)
        except Exifreader.ExifError, msg:
            self. exifdata = None


def main():
    """
    """
    organizr = Organizr()
    organizr.MainLoop()

if __name__ == '__main__':
    main()
