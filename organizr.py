#!/usr/bin/env python
"""
for organizing photos, especially those taken in RAW+ mode.
"""
from __future__ import division

import os
import wx
import Image

import Exifreader


ID_OPEN = wx.NewId(); ID_SAVE = wx.NewId()
ID_EXIT = wx.NewId(); ID_PREV = wx.NewId()
ID_NEXT = wx.NewId()


class Organizr(wx.App):
    """The core class
    """
    def __init__(self):
        """
	"""
        wx.App.__init__(self, 0)

    def OnInit(self):
        """run the organizr"""
        organizrwindow = MainFrame()
        organizrwindow.Show()
        return True

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "", style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        self.splitter_1 = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.splitter_1_pane_2 = wx.Panel(self.splitter_1, -1)
        self.playlist_ribbon = wx.Panel(self.splitter_1, -1, style=wx.RAISED_BORDER|wx.TAB_TRAVERSAL)

        self.splitter_2 = wx.SplitterWindow(self.splitter_1_pane_2, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.canvas = ImageCanvas(self.splitter_2 )#, -1, style=wx.RAISED_BORDER|wx.TAB_TRAVERSAL)
        self.splitter_2_pane_2 = wx.Panel(self.splitter_2, -1)

        self.splitter_3 = wx.SplitterWindow(self.splitter_2_pane_2, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.exifpanel = wx.TextCtrl(self.splitter_3, -1, style=wx.RAISED_BORDER|wx.TE_MULTILINE)
        self.thumbnailpanel = wx.Panel(self.splitter_3, -1)
        
        self.statusbar = self.CreateStatusBar(2, 0)

        self.__set_properties()
        self.__do_layout()
        self.__build_menubar()
        self.__set_bindings()
        
    def __set_properties(self):
        self.SetTitle("Organizr")

        #variables and flags
        self.current_dir = os.path.expanduser('~')
        self.WRAPON = True # wrap around in playlist
        self.AUTOROTATE = True # automatically rotate images

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.splitter_3.SplitHorizontally(self.exifpanel, self.thumbnailpanel, 453)
        sizer_3.Add(self.splitter_3, 1, wx.EXPAND, 0)
        self.splitter_2_pane_2.SetSizer(sizer_3)
        self.splitter_2.SplitVertically(self.canvas, self.splitter_2_pane_2, 700)
        sizer_2.Add(self.splitter_2, 1, wx.EXPAND, 0)
        self.splitter_1_pane_2.SetSizer(sizer_2)
        self.splitter_1.SplitHorizontally(self.playlist_ribbon, self.splitter_1_pane_2, 110)
        sizer_1.Add(self.splitter_1, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        # have to set sash position again for splitter 3
        self.splitter_3.SetSashPosition(450)
        
    def __build_menubar(self):
        """All the menu bar items go here"""
        menubar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(ID_OPEN, "&Open\tCtrl-O","Open file")
        file_menu.Append(ID_SAVE, "&Save\tCtrl-S","Save Image")
        file_menu.Append(ID_EXIT, "&Exit\tCtrl-Q","Exit")

        edit_menu = wx.Menu()
        edit_menu.Append(ID_PREV, "&Prev", "Previous Image")
        edit_menu.Append(ID_NEXT, "&Next", "Next Image")
        
        menubar.Append(file_menu, "&File")
        menubar.Append(edit_menu, "&Edit")
        self.SetMenuBar(menubar)

    def __set_bindings(self):
        self.Bind(wx.EVT_MENU, self.onopen, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.onprev, id=ID_PREV)
        self.Bind(wx.EVT_MENU, self.onnext, id=ID_NEXT)

        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
    def onopen(self, event):
        """Open a new file"""
        filter = 'Image files|*.png;*.tif;*.tiff;*.jpg;*.jpeg;*.bmp|All files|*.*'
        dlg = wx.FileDialog(self,defaultDir = self.current_dir,
                            style=wx.OPEN, wildcard=filter)
        if dlg.ShowModal() == wx.ID_OK:
            self.filepath = dlg.GetPath()
            self.current_dir = os.path.dirname(self.filepath)
            self.create_playlist()
            self.load_new()
        else:
            return

    def onnext(self, event):
        """display next image in the playlist.
        At end of playlist, behave according to whether we want to wrap"""
        self.nowshowing += 1
        if self.nowshowing == len(self.playlist):
            if self.WRAPON:
                self.nowshowing = 0
            else:
                self.nowshowing -= 1
        self.load_new()
        
    def onprev(self, event):
        """display prev image in the playlist.
        At beginning of playlist, behave according to whether we want to wrap"""
        self.nowshowing -= 1
        if self.nowshowing < 0:
            if self.WRAPON:
                self.nowshowing = len(self.playlist) - 1
            else:
                self.nowshowing = 0
        self.load_new()
                
    def load_new(self):
        """common things to do when a new image is loaded"""
        self.exifinfo = ExifInfo(open(self.playlist[self.nowshowing], 'r'))
        self.canvas.im.load()
        self.exifpanel.Clear()
        self.exifpanel.WriteText(str(self.exifinfo))
        
    def on_key_down(self, event):
        """process key presses"""
        print event.GetKeyCode()
        keycode = event.GetKeyCode()
        if keycode == 74: #'j'
            self.onprev(event)
        elif keycode == 75: #'k'
            self.onnext(event)
        else:
            pass        
        
    def create_playlist(self):
        """
        Make a playlist by listing all image files in the directory beginning
        from the selected file
        """
        self.playlist = []
        dirname,currentimage = os.path.split(self.filepath)
        allfiles = os.listdir(dirname)
                
        for eachfile in allfiles:
            if os.path.splitext(eachfile)[1].lower() in ['.bmp','.png',
                                        '.jpg','.jpeg','.tif','.tiff']:
                self.playlist.append(os.path.join(dirname,eachfile))
        self.playlist.sort()
        self.nowshowing = self.playlist.index(self.filepath)
        self.canvas.im.load()
        
class ImageCanvas(wx.Panel):
    """panel where the images are displayed
    """
    def __init__(self, parent):
        """
	"""
        wx.Panel.__init__(self, parent, -1)
        self.frame = wx.GetTopLevelParent(self)

        self.NEEDREDRAW = False
        self.im = Im(self)
        
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_PAINT, self.OnPaint) 

    def OnIdle(self, event):
        """Redraw if there is a change"""
        if self.NEEDREDRAW:
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer,
                               wx.BUFFER_CLIENT_AREA)
            dc.Clear()  #clear old image if still there        
            self.resize_image()
            self.Draw(dc)
            self.NEEDREDRAW = False

    def OnResize(self, event):
        """when canvas  is resized, we create a new buffer, which will
        be redrawn on next idle event"""
        # update / initialize height and width
        self.width, self.height = self.GetSize()

        # update / create the buffer for the buffered dc
        image = wx.EmptyImage(self.width, self.height)
        wx.Image.Create(image,self.width, self.height, False)
        wx.Image.SetRGBRect(image, wx.Rect(0, 0, self.width, self.height),
                            255, 255, 255)        
        self.buffer = wx.BitmapFromImage(image)
        self.NEEDREDRAW = True

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)
    
    def resize_image(self):
        """Process the image by resizing to best fit current size"""
        image = self.im.image
        imagewidth, imageheight = image.size

        # What drives the scaling - height or width
        if imagewidth / imageheight > self.width / self.height:
            self.scalingvalue = self.width / imagewidth
        else:
            self.scalingvalue = self.height / imageheight
                
        # resize with antialiasing
        self.resized_width =  int(imagewidth * self.scalingvalue)
        self.resized_height = int(imageheight * self.scalingvalue)
        self.resizedimage = image.resize((self.resized_width,
                                          self.resized_height)
                                             , Image.ANTIALIAS)
        
        # blit the image centerd in x and y axes
        self.bmp = self.ImageToBitmap(self.resizedimage)
        self.imagedc = wx.MemoryDC()
        self.imagedc.SelectObject(self.bmp)
        self.xoffset = (self.width-self.resized_width)/2
        self.yoffset = (self.height-self.resized_height)/2

    def ImageToBitmap(self, img):
        newimage = apply(wx.EmptyImage, img.size)
        newimage.SetData(img.convert( "RGB").tostring())
        bmp = newimage.ConvertToBitmap()
        return bmp
 
    def Draw(self, dc):
        """Redraw the image"""
        # blit the buffer on to the screen 
        dc.Blit(self.xoffset, self.yoffset,
                self.resized_width, self.resized_height, self.imagedc, 0, 0)
        self.NEEDREDRAW = False 

 
class Im():
    """the loaded image"""
    def __init__(self, parent):
        """imagefilenames is a list of the filenames.
        for single image this is a singleton list.
        Multiple items indicate this is a series to be loaded"""
        self.image = Image.new('RGB', (100,200), (255,255,255))
        self.canvas = parent
        
    def load(self):
        """load as a wx bitmap"""
        filepath = self.canvas.frame.playlist[self.canvas.frame.nowshowing]
        try:
            self.image = Image.open(filepath, 'r')
        except:
            self.canvas.frame.SetStatusText('Could not load image')
            return
        
        if self.canvas.frame.AUTOROTATE:
            self.autorotate(self.canvas.frame.exifinfo.info["Orientation"])
        self.canvas.NEEDREDRAW = True
        self.canvas.frame.SetStatusText(os.path.basename(filepath))

    def load_multiple(self):
        """Load a list of images and construct a composite image"""
        print 'not implemented yet'
        pass

    def zoom(self, scale):
        """scale the bitmap by the given scale.
        use to zoom in or zoom out.
        return the viewing frame"""
        frame = []
        return frame

    def autorotate(self, exif_orientation):
        """Given the exif orientation tag, rotate the image"""
        exif_orientation = int(exif_orientation)
        if exif_orientation == 1:
            return 
        elif exif_orientation == 6:
            self.image = self.image.rotate(-90)
        elif exif_orientation == 8:
            self.image = self.image.rotate(90)
        elif exif_orientation == 3:
            self.image = self.image.rotate(180)
    
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
        self.read_exif_info()
        self.info = self.process_exif_info()

    def read_exif_info(self):
        """read the exif information"""
        try:
            self.exifdata = Exifreader.process_file(self.imagefilehandle)
        except Exifreader.ExifError, msg:
            self. exifdata = None

    def __str__(self):
        return repr(self)
            
    def __repr__(self):
        """formatted string of exif info"""
        return '\n'.join(['Model : %s' %(self.info['Model']),
                          'Time : %s' %(self.info['DateTime']),
                          'Mode : %s' %(self.info['ExposureMode']),
                          'ISO : %s' %(self.info['ISOSpeed']),
                          'Aperture : %s' %(self.info['FNumber']),
                          'Shutter time : %s' %(self.info['ExposureTime']),
                          'Focal length : %s' %(self.info['FocalLength']),
                          'Flash : %s' %(self.info['FlashMode']),
                          'Lens : %s - %s' %(self.info['ShortFocalLengthOfLens'],
                                             self.info['LongFocalLengthOfLens'])]) 
            
    def process_exif_info(self):
        """Extract the useful info only"""
        info = {}
        data = self.exifdata
        for key in data.keys():
            for wanted_key in ['ExposureMode', 'DateTime',
                               'ExposureTime', 'FocalLength',
                               'FlashMode', 'ISOSpeed',
                               'Model', 'Orientation',
                               'FNumber', 'LongFocalLengthOfLens',
                               'ShortFocalLengthOfLens']:
                if wanted_key in key:
                    info[wanted_key] = str(data[key])

        return info

def main():
    """
    """
    organizr = Organizr()
    organizr.MainLoop()

if __name__ == '__main__':
    main()
