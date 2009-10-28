#!/usr/bin/env python
"""
for organizing photos, especially those taken in RAW+ mode.
"""
from __future__ import division

import os
import wx
import Image
import ImageDraw
import time
import sys
import copy
import yaml
import commands

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from utils import *
import Exifreader
import overview
#########################
# TODO:
#  - Fix zoom and display of zoom frame in thumbnail
#  - Get exif information for all files in playlist
#  - Allow custom sort of files
##########################

ID_OPEN = wx.NewId()
ID_SAVE = wx.NewId()
ID_EXIT = wx.NewId()
ID_PREV = wx.NewId()
ID_NEXT = wx.NewId()
ID_ZOOMIN = wx.NewId()
ID_ZOOMOUT = wx.NewId()
ID_COMPOSITE = wx.NewId()


# utility functions
def reduce_fraction(fraction_string):
    """If the input string represents a fraction,
    reduce it and return to one decimal place.
    ex: input '71/10' gives 7.1
    input '5' gives 5"""
    try:
        num, den = fraction_string.split('/')
        reduced_string = '%0.1f' % (float(num) / float(den))
    except ValueError:
        reduced_string = '%s' % (fraction_string)
    return reduced_string


    
class Organizr(wx.App):
    """The core class"""
    def __init__(self):
        """initialize the app"""
        wx.App.__init__(self, 0)
        self.start_app()
        
    def start_app(self):
        """run the organizr"""
        organizrwindow = MainFrame()
        organizrwindow.Show()
        return True

    
class AutoWidthListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        """Use a mixin to construct a listctrl where the width of the
        last column is adjusted automatically to use up remaining space"""
        wx.ListCtrl.__init__(self, parent, -1,
                             style=wx.LC_REPORT|wx.LC_HRULES)
        ListCtrlAutoWidthMixin.__init__(self)

        
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "", style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()

        self.__set_properties()

        # first split - playlist on top
        self.bottompanel = wx.Panel(self, -1)
        #self.toppanel = wx.Panel(self, -1)
        #self.playlistcanvas = PlayListCanvas(self)
        self.actionlist = ActionList(self)

        # next split the bottom panel into canvas and sidepanel
        self.vertical_splitter = wx.SplitterWindow(self.bottompanel, -1,
                                            style=wx.SP_3D|wx.SP_BORDER)
        self.canvas = ImageCanvas(self.vertical_splitter)
        self.sidepanel = wx.Panel(self.vertical_splitter, -1)

        # split top panel for toggling between playlistcanvas
        # and composite control panel
        self.toggle_splitter = wx.SplitterWindow(self, -1,
                                            style=wx.SP_3D|wx.SP_BORDER)
        self.playlistcanvas = PlayListCanvas(self.toggle_splitter)
        self.composite_control = wx.Panel(self.toggle_splitter)
        self.toggle_splitter.SplitVertically(self.playlistcanvas,
                                             self.composite_control, 20)
        self.toggle_splitter.Unsplit()
        
        # split sidepanel into exifpanel and thumbnailpanel
        self.horizontal_splitter = wx.SplitterWindow(self.sidepanel, -1,
                                            style=wx.SP_3D|wx.SP_BORDER)
        self.exifpanel = AutoWidthListCtrl(self.horizontal_splitter)
        self.exifpanel.InsertColumn(0, 'Property', width=100)
        self.exifpanel.InsertColumn(1, 'Value')
        self.thumbnailpanel = ThumbnailCanvas(self.horizontal_splitter)
        
        self.statusbar = self.CreateStatusBar(2, 0)
        self.__do_layout()
        self.__build_menubar()
        self.__set_bindings()
        wx.FutureCall(500, self.__set_sash_positions())
        
    def __set_properties(self):
        self.SetTitle("Organizr")
        self.CURRENT_DIR = os.path.expanduser('~')
        self.WRAPON = True # wrap around in playlist
        self.AUTOROTATE = True # automatically rotate images
        self.COMPOSITE_SELECTED = False
        # need to have these ready before imagecanvas and
        # thumbnail canvas are initialized
        self.im = Im(self) 
        self.preview = SeriesPreview(self, [])
        self.tb_file = None # filename for thumbnail
        self.playlist = ['']
        self.nowshowing = 0
        self.trash_folder = '/data/tmp/organizr_trash/'
        
    def __do_layout(self):
        self.sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_1.Add(self.toggle_splitter, 1, wx.ALL|wx.EXPAND, 20)
        self.sizer_1.Add(self.bottompanel, 5, wx.ALL|wx.EXPAND, 4)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.horizontal_splitter.SplitHorizontally(self.exifpanel,
                                                   self.thumbnailpanel, 453)
        sizer_3.Add(self.horizontal_splitter, 1, wx.EXPAND, 0)
        self.sidepanel.SetSizer(sizer_3)
        self.vertical_splitter.SplitVertically(self.canvas, self.sidepanel, 700)
        sizer_2.Add(self.vertical_splitter, 1, wx.EXPAND, 0)
        self.bottompanel.SetSizer(sizer_2)

        self.SetSizer(self.sizer_1)
        self.Layout()

    def __set_sash_positions(self):
        """wait for frame size to be set and then set sash
        positions properly"""
        # not able to set sash size as per frame width and height
        #self.horizontal_splitter.SetSashPosition(w - int(w/5))
        #self.vertical_splitter.SetSashPosition(h - int(w/5))
        self.horizontal_splitter.SetSashPosition(650)
        
    def __build_menubar(self):
        """All the menu bar items go here"""
        menubar = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(ID_OPEN, "&Open","Open file")
        file_menu.Append(ID_SAVE, "&Save","Save Image")
        file_menu.Append(ID_EXIT, "&Exit","Exit")

        edit_menu = wx.Menu()
        edit_menu.Append(ID_PREV, "&Prev", "Previous Image")
        edit_menu.Append(ID_NEXT, "&Next", "Next Image")

        view_menu = wx.Menu()
        view_menu.Append(ID_ZOOMIN, "Zoomin", "Zoom in")
        view_menu.Append(ID_ZOOMOUT, "Zoomout", "Zoom out")
        view_menu.Append(ID_COMPOSITE, "Composite", "View Composite")

        menubar.Append(file_menu, "&File")
        menubar.Append(edit_menu, "&Edit")
        menubar.Append(view_menu, "&View")
        self.SetMenuBar(menubar)

    def __set_bindings(self):
        self.Bind(wx.EVT_MENU, self.onopen, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.onprev, id=ID_PREV)
        self.Bind(wx.EVT_MENU, self.onnext, id=ID_NEXT)
        self.Bind(wx.EVT_MENU, self.im.zoom_in, id=ID_ZOOMIN)
        self.Bind(wx.EVT_MENU, self.im.zoom_out, id=ID_ZOOMOUT)
        self.Bind(wx.EVT_MENU, self.view_composite, id=ID_COMPOSITE)
        
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
    def onopen(self, event):
        """Open a new file"""
        wildcard = ''.join(['Image files|',
                          '*.png;*.PNG;',
                          '*.jpg;*.jpeg;*.JPG;*.JPEG',
                          '*.tif;*.tiff;*.TIF;*.TIFF',
                          '*.bmp;*.BMP',
                          '|All files|*.*'])
        
        dlg = wx.FileDialog(self, defaultDir = self.CURRENT_DIR,
                            style=wx.OPEN, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            self.filepath = dlg.GetPath()
            self.CURRENT_DIR = os.path.dirname(self.filepath)
            self.create_playlist()
            
            self.nowshowing = self.playlist.index(self.filepath)
            self.load_new()
        else:
            return

    def view_composite(self, event):
        """view a composite images showing all pics in playlist"""
        self.ov = overview.Overview(self, self.playlist)
        self.ov.build_composite()
        self.COMPOSITE_SELECTED = True
        self.ov.load()

        self.toggle_splitter.SplitVertically(self.playlistcanvas,
                                             self.composite_control)
        self.toggle_splitter.Unsplit(self.playlistcanvas)
        
    def onnext(self, event):
        """display next image in the playlist.
        At end of playlist, behave according to whether we want to wrap"""
        self.nowshowing += 1
        if self.nowshowing == len(self.playlist):
            if self.WRAPON:
                self.nowshowing = 0
                self.SetStatusText('Wrapping to beginning', 1)

            else:
                self.nowshowing -= 1
                self.SetStatusText('Reached end of playlist', 1)
                
        self.load_new()
        
    def onprev(self, event):
        """display prev image in the playlist.
        At beginning of playlist, behave according to whether we want to wrap"""
        self.nowshowing -= 1
        if self.nowshowing < 0:
            if self.WRAPON:
                self.nowshowing = len(self.playlist)-1
                self.SetStatusText('Wrapping to end', 2)

            else:
                self.nowshowing = 0
                self.SetStatusText('Reached beginning of playlist', 2)

        self.load_new()
                
    def load_new(self):
        """common things to do when a new image is loaded"""
        # recreate playlist for every new file
        # TODO: not optimal to recreate each time
        self.filepath = self.playlist[self.nowshowing]
        self.create_playlist()
        self.nowshowing = self.playlist.index(self.filepath)

        self.exifinfo = ExifInfo(open
                                 (self.playlist[self.nowshowing], 'r'))
        self.exifpanel.DeleteAllItems()
        for info in self.exifinfo.exif_info_list:
            index = self.exifpanel.InsertStringItem(sys.maxint, info[0])
            self.exifpanel.SetStringItem(index, 1, info[1])

        # display thumbnails preview.
        # Handle negative indices for slicing
        preview_start = self.nowshowing - 3
        preview_end = self.nowshowing + 4
        if preview_start < 0:
            preview_files = self.playlist[
                preview_start:] + self.playlist[:preview_end]
        elif preview_end > len(self.playlist) - 1:
            preview_files = self.playlist[
                preview_start:] + self.playlist[:preview_end-len(self.playlist)]
        else:
            preview_files = self.playlist[
                preview_start:preview_end]
        
        self.preview  = SeriesPreview(self, preview_files)
        self.playlistcanvas.NEEDREDRAW = True

        # load and display image and thumbnail
        self.tb_file = get_thumbnailfile(self.playlist[self.nowshowing])
        self.im.load()
        
    def on_key_down(self, event):
        """process key presses"""
        keycode = event.GetKeyCode()
        if keycode == 79: #'o'
            self.onopen(event)
        elif keycode == 74: #'j'
            self.onprev(event)
        elif keycode == 75: #'k'
            self.onnext(event)
        elif keycode == 46: # '>'
            self.im.zoom_in(event)
        elif keycode == 44: # '<'
            self.im.zoom_out(event)
        elif keycode == 61: #'='
            self.im.no_zoom(event)
        elif keycode in [314, 315, 316, 317]: #arrow keys
            self.im.shift_zoom_frame(event)
        elif keycode == 65: # 'a'
            self.actionlist.ShowModal()
        else:
            print 'key pressed - ', keycode
        
    def create_playlist(self):
        """
        Make a playlist by listing all image files in the directory beginning
        from the selected file
        """
        self.playlist = []
        dirname = os.path.dirname(self.filepath)
        allfiles = os.listdir(dirname)
                
        for eachfile in allfiles:
            if os.path.splitext(eachfile)[1].lower() in ['.bmp', '.png',
                                        '.jpg', '.jpeg', '.tif', '.tiff']:
                self.playlist.append(os.path.join(dirname, eachfile))
        self.playlist.sort()

        
class DisplayCanvas(wx.Panel):
    """A panel that can be subclassed and used for displaying images"""
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, -1, **kwargs)

        self.NEEDREDRAW = False
        self.NEEDREDRAWFRAME = False
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_IDLE, self.on_idle)
        self.Bind(wx.EVT_PAINT, self.on_paint) 

    def on_idle(self, event):
        """Redraw if there is a change"""
        if self.NEEDREDRAW:
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer,
                               wx.BUFFER_CLIENT_AREA)
            dc.Clear()  #clear old image if still there        
            self.draw(dc)
            self.NEEDREDRAW = False

    def image_to_bitmap(self, img):
        newimage = apply(wx.EmptyImage, img.size)
        newimage.SetData(img.convert( "RGB").tostring())
        bmp = newimage.ConvertToBitmap()
        return bmp

    def on_resize(self, event):
        """when canvas  is resized, we create a new buffer, which will
        be redrawn on next idle event"""
        # update / initialize height and width
        self.width, self.height = self.GetSize()
        
        # update / create the buffer for the buffered dc
        image = wx.EmptyImage(self.width, self.height)
        wx.Image.Create(image, self.width, self.height, False)
        wx.Image.SetRGBRect(image, wx.Rect(0, 0, self.width, self.height),
                            255, 255, 255)        
        self.buffer = wx.BitmapFromImage(image)
        self.NEEDREDRAW = True

    def on_paint(self, event):
        dc = wx.BufferedPaintDC(self, self.buffer)

    def get_resize_params(self, imagewidth, imageheight):
        """calculate params for resizing image to canvas"""
        # What drives the scaling - height or width
        if imagewidth / imageheight > self.width / self.height:
            self.scalingvalue = self.width / imagewidth
        else:
            self.scalingvalue = self.height / imageheight
                
        # resize with antialiasing
        self.resized_width =  int(imagewidth * self.scalingvalue)
        self.resized_height = int(imageheight * self.scalingvalue)
        self.xoffset = (self.width-self.resized_width)/2
        self.yoffset = (self.height-self.resized_height)/2

    def draw(self, dc):
        """Drawing routine.Implement in subclass"""
        pass
        
class ImageCanvas(DisplayCanvas):
    """panel where the images are displayed
    """
    def __init__(self, parent):
        """
	"""
        DisplayCanvas.__init__(self, parent)
        self.frame = wx.GetTopLevelParent(self)

        self.zoom_ratio = 1
        self.zoom_xoffset = None
        self.zoom_yoffset = None
        
        self.SetFocus() # to catch key events
    
    def resize_image(self):
        """Process the image by resizing to best fit current size"""
        if self.frame.COMPOSITE_SELECTED:
            self.resizedimage = self.frame.ov.image.copy()
        else:
            self.resizedimage = self.frame.im.image.copy()

        self.resizedimage.thumbnail((self.width, self.height), Image.NEAREST)
        self.resized_width, self.resized_height = self.resizedimage.size
        self.xoffset = (self.width-self.resized_width)/2
        self.yoffset = (self.height-self.resized_height)/2
        
        # blit the image centerd in x and y axes
        self.bmp = self.image_to_bitmap(self.resizedimage)

        self.imagedc = wx.MemoryDC()
        self.imagedc.SelectObject(self.bmp)

    def draw(self, dc):
        """Redraw the image"""
        self.resize_image()
        # blit the buffer on to the screen
        #w, h = self.frame.im.image.size
        dc.Blit(self.xoffset, self.yoffset,
                self.resized_width, self.resized_height, self.imagedc,
                0, 0)
        self.NEEDREDRAW = False

        
class PlayListCanvas(DisplayCanvas):
    """Display list of images """
    def __init__(self, parent):
        DisplayCanvas.__init__(self, parent, style=wx.RAISED_BORDER)
        self.frame = wx.GetTopLevelParent(self)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)
        
    def resize_image(self):
        """Process the image by resizing to best fit current size"""
        image = self.frame.preview.composite
        imagewidth, imageheight = image.size

        self.get_resize_params(imagewidth, imageheight)
        self.resizedimage = image.resize((self.resized_width,
                                          self.resized_height)
                                             , Image.ANTIALIAS)
        # blit the image centerd in x and y axes
        self.bmp = self.image_to_bitmap(self.resizedimage)

        self.imagedc = wx.MemoryDC()
        self.imagedc.SelectObject(self.bmp)

    def draw(self, dc):
        """Redraw the image"""
        self.resize_image()
        # blit the buffer on to the screen
        dc.Blit(self.xoffset, self.yoffset,
                self.resized_width, self.resized_height, self.imagedc,
                0, 0)

    def on_mouse_events(self, event):
        """catch mouse clicks and jump to corresponding image"""
        if event.LeftDown():
            x,y = event.GetPosition()
            pos = int((x - self.xoffset) / (self.resized_width / 7))
            relative_pos = pos - 3
            if relative_pos != 0:
                self.frame.nowshowing += relative_pos
                self.frame.load_new()
        else:
            pass
        
class ThumbnailCanvas(DisplayCanvas):
    """panel where the thumbnail image is displayed
    """
    def __init__(self, parent):
        """
	"""
        DisplayCanvas.__init__(self, parent)
        self.frame = wx.GetTopLevelParent(self)
        self.pen = wx.Pen(wx.WHITE, 2, wx.SOLID)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)

        self.oldx1 = 0; self.oldx2 = 0
        self.oldy1 = 0; self.oldy2 = 0
        self.xoffset = 0; self.yoffset = 0
        self.resized_height = 0; self.resized_width = 0
        self.NEEDREDRAWFRAME = False
        self.startdrag = False
        self.firstdraw = True

        
    def resize_image(self):
        """Process the image by resizing to best fit current size"""
        self.resizedimage = self.frame.im.original_image.copy()
        self.resizedimage.thumbnail((self.width, self.height), Image.NEAREST)
        self.resized_width, self.resized_height = self.resizedimage.size
        self.xoffset = int((self.width-self.resized_width)/2)
        self.yoffset = int((self.height-self.resized_height)/2)
        
        # blit the image centerd in x and y axes
        self.bmp = self.image_to_bitmap(self.resizedimage)

        self.imagedc = wx.MemoryDC()
        self.imagedc.SelectObject(self.bmp)

    def on_mouse_events(self, event):
        """Handle mouse events.
        Left click and drag moves the zoomframe"""
        x, y = event.GetPosition()

        # unless we start dragging, only click matters
        if not self.startdrag and not event.LeftDown():
            return
        
        elif event.LeftDown() and not self.startdrag:
            self.startdrag = True
            self.startx, self.starty = x, y
            self.relative_x1 = self.x1 - self.startx
            self.relative_x2 = self.x2 - self.startx
            self.relative_y1 = self.y1 - self.starty
            self.relative_y2 = self.y2 - self.starty

        elif event.Dragging() and event.LeftIsDown():
            if not in_rectangle((x,y), (self.x1, self.y1, self.x2, self.y2)):
                return
                
            if self.startdrag:
                self.currx, self.curry = event.GetPosition()

                x1 = self.relative_x1 + self.currx
                x2 = self.relative_x2 + self.currx
                y1 = self.relative_y1 + self.curry
                y2 = self.relative_y2 + self.curry

                # if frame is extending beyond limits,
                # dont update frame params
                if x1 < self.xoffset or\
                   y1 < self.yoffset or\
                   x2 > self.xoffset + self.resized_width or\
                   y2 > self.yoffset + self.resized_height:
                    return

                else:
                    (self.x1, self.y1, self.x2, self.y2) = copy.deepcopy(
                        (x1, y1, x2, y2))
                
                self.frame.im.zoomframe = self.reverse_translate_frame()
                self.frame.canvas.NEEDREDRAW = True
                self.NEEDREDRAW = True
                self.NEEDREDRAWFRAME = True

        elif event.LeftUp():
            if self.startdrag:
                self.startdrag = False
        
    def draw(self, dc):
        """Redraw the image"""
        # update thumbnail frame coords
        # if we are dragging on thumbnail frame,
        # update the canvas zoom offset
        if self.startdrag:
            self.frame.im.zoomframe = self.reverse_translate_frame()
            self.frame.im.image = self.frame.im.original_image.crop(
                self.frame.im.zoomframe)
        
        self.resize_image()
        # blit the buffer on to the screen
        dc.Blit(self.xoffset, self.yoffset,
                self.resized_width, self.resized_height, self.imagedc,
                0, 0)

        if not self.startdrag:
            self.translate_frame() 
            
        self.draw_frame(dc)
        self.NEEDREDRAW = False

    def translate_frame(self):
        """get the zoomframe of the image and translate into
        frame to be drawn over the thumbnail"""
        x1, y1, x2, y2 = self.frame.im.zoomframe
        self.x1 = int(self.xoffset + x1 *
                      (self.resized_width / self.frame.im.width))
        self.x2 = int(self.xoffset + x2 *
                      (self.resized_width / self.frame.im.width))
        self.y1 = int(self.yoffset + y1 *
                      (self.resized_height / self.frame.im.height))
        self.y2 = int(self.yoffset + y2 *
                      (self.resized_height / self.frame.im.height))
        
    def reverse_translate_frame(self):
        """given thumbnails frame, calculate zoomframe for the image"""
        x1 = (self.x1 - self.xoffset) * (
              self.frame.im.width / self.resized_width)
        x2 = (self.x2 - self.xoffset) * (
              self.frame.im.width / self.resized_width)
        y1 = (self.y1 - self.yoffset) * (
              self.frame.im.height / self.resized_height)
        y2 = (self.y2 - self.yoffset) * (
              self.frame.im.height / self.resized_height)

        return (x1, y1, x2, y2)
        
    def draw_rect(self, dc, coords):
        """draw rectangle as series of lines
        coords are (x1, y1, x2, y2)"""
        x1, y1, x2, y2 = coords
        dc.DrawLine(x1, y1, x2, y1)
        dc.DrawLine(x2, y1, x2, y2)
        dc.DrawLine(x2, y2, x1, y2)
        dc.DrawLine(x1, y2, x1, y1)

        
    def draw_frame(self, dc):
        """draw the zoomframe"""
        dc.SetPen(self.pen)
        self.draw_rect(dc, (self.x1, self.y1, self.x2, self.y2))

        self.oldx1, self.oldx2, self.oldy1, self.oldy2 = copy.copy((
            self.x1, self.x2, self.y1, self.y2))

        
class ActionList(wx.Dialog):
    def __init__(self, parent):
        """presents a list of available actions that are
        shell commands to be run on the file or the current
        selection of files"""
        wx.Dialog.__init__(self, parent)
        self.frame = parent
        self.listpanel = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
        self.controlpanel = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|
                                    wx.TAB_TRAVERSAL)
        self.playlistctrl = wx.ListCtrl(self.listpanel, -1,
                            style=wx.LC_REPORT|wx.LC_SINGLE_SEL | wx.SUNKEN_BORDER)
        self.playlistctrl.InsertColumn(0, "Key", width=100)
        self.playlistctrl.InsertColumn(1, "Action", width=180)
        
        self.addbutton = wx.Button(self.controlpanel, -1, 'Add')
        self.removebutton = wx.Button(self.controlpanel, -1, 'Remove')
        self.editbutton = wx.Button(self.controlpanel, -1, 'Edit')

        self.__do_layout()

        self.actionlist = []
        self.commands = {}

        
        self.configfile = os.path.expanduser('~/.organizr_actions')
        self.readconfigfile()
        self.load_actions()

        self.playlistctrl.Bind(wx.EVT_KEY_DOWN, self.process_key)
        self.playlistctrl.SetFocus()

    def readconfigfile(self):
        """read the actions from the file"""
        fi = open(self.configfile, 'r')
        action_dict = yaml.load(fi)
        self.actionlist = []
        for actionname in sorted(action_dict.keys()):
            self.actionlist.append((actionname,
                                    action_dict[actionname]['key'],
                                    action_dict[actionname]['action']))

    def process_key(self, event):
        """read in a key,
        if key is in commands, perform the necessary command
        with substitutions"""
        self.replacements = [('%f',
           os.path.splitext(self.frame.playlist[self.frame.nowshowing])[0]),
                             ('%F',
             self.frame.playlist[self.frame.nowshowing]),
                             ('%t',
             self.frame.trash_folder)]

        # escape closes dialog
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(0)
            return
            
        key = chr(event.GetKeyCode()).lower()
        try:
            cmd = self.commands[key]
        except KeyError:
            self.frame.SetStatusText('%s key not defined' %(key), 1)
            return
            
        for rep in self.replacements:
            cmd = cmd.replace(rep[0], rep[1])
        st, output = commands.getstatusoutput(cmd)
        if st != 0:
            self.frame.SetStatusText('Failed - %s' %(output),1)
        self.EndModal(0)
            
    def __do_layout(self):
        """"""
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        controlsizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.playlistctrl, 1, wx.EXPAND, 0)
        self.listpanel.SetSizer(sizer_1)
        mainsizer.Add(self.listpanel, 5, wx.ALL|wx.EXPAND, 2)
        
        controlsizer.Add(self.addbutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.removebutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        controlsizer.Add(self.editbutton, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        self.controlpanel.SetSizer(controlsizer)
        mainsizer.Add(self.controlpanel, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|
                      wx.EXPAND, 2)
        self.SetSizer(mainsizer)
        mainsizer.Fit(self)
        self.Layout()
        self.SetSize((300, 400))

    def load_actions(self):
        """load the actions that have been read in"""
        # make command list with substitutions
        for action in self.actionlist:
            self.commands[action[1]] = action[2]
        
        # populate the list control
        for action in self.actionlist:
            index = self.playlistctrl.InsertStringItem(sys.maxint, action[1])
            self.playlistctrl.SetStringItem(index, 1, action[0])
        
        
class SeriesPreview():
    """A composite image made of thumbnails from all playlist images.
    Should be triggered by opening a new file"""
    def __init__(self, parent, imagelist):
        # imagelist is list of filenames to load
        self.filenames = imagelist
        self.frame = parent
        
        if len(self.filenames) == 0:
            self.composite = Image.new('RGB', (800, 100), (255, 255, 255))
        else:
            self.tn_size = 100 # thumbnail size
            self.blankimage = Image.new('RGB', (self.tn_size, self.tn_size),
                                        (200, 200, 200))
            self.composite = Image.new('RGB', ((self.tn_size + 10) *
                                               len(self.filenames),
                                      self.tn_size + 10), (255, 255, 255))
            self.build_composite()

    def build_composite(self):
        """Build a composite image with thumbnails of the images."""
        self.im_list = []
        for filename in self.filenames:
            # get thumbnail from nautilus store if possible
            tb_file = get_thumbnailfile(filename)
            if tb_file:
                self.im_list.append(Image.open(tb_file))
            else:
                try:
                    self.im_list.append(Image.open(filename))
                except:
                    self.im_list.append(self.blankimage)

        # resize
        self.thumbnails = self.im_list
        for im in self.im_list:
            im.thumbnail((self.tn_size, self.tn_size)) #, Image.ANTIALIAS)

        # paste the thumbnails
        for index in range(len(self.im_list)):
            w, h = self.thumbnails[index].size
            x1 = 5 + index * (self.tn_size + 10)
            xoffset = (self.tn_size - w) / 2
            yoffset = (self.tn_size - h) / 2
            self.composite.paste(self.thumbnails[index],
                                 (x1 + xoffset, 5 + yoffset)) 

        # draw box highlighting current image
        center = int(len(self.im_list) / 2)
        draw = ImageDraw.Draw(self.composite)
        x1 = center * (self.tn_size + 10)
        x2 = x1 + 105
        draw.line((x1, 0, x2, 0, x2, 100, x1, 100, x1, 0),
                  width=5, fill=(255,0,0))
        
class Im():
    """the loaded image"""
    def __init__(self, parent):
        """imagefilenames is a list of the filenames.
        for single image this is a singleton list.
        Multiple items indicate this is a series to be loaded"""
        # start with blank images
        self.image = Image.new('RGB', (100, 200), (255, 255, 255))
        self.original_image = Image.new('RGB', (100, 200), (255, 255, 255))

        self.frame = parent
 
        self.width = 1; self.height = 1
        self.zoomframe = (0, 0, 0, 0)
        self.ZOOMSTEP = 1.1
        self.SHIFTZOOMSTEP = 5
        
    def load(self):
        """load as a wx bitmap"""
        self.frame.SetStatusText('Loading')
        stime = time.time()
        filepath = self.frame.playlist[self.frame.nowshowing]
        try:
            self.original_image = Image.open(filepath, 'r')
        except:
            self.frame.SetStatusText('Could not load image')
            return

        self.frame.SetStatusText('Loaded in %s seconds' %
                                 (time.time() - stime), 1)
        # depending on orientation info in exif, rotate the image
        if self.frame.AUTOROTATE:
            try:
                self.autorotate(self.frame.exifinfo.info["Orientation"])
            except KeyError:
                pass # no exif orientation info    

        self.width, self.height = self.original_image.size
        self.zoom_xoffset = None
        self.zoom_yoffset = None
        self.zoom_ratio = 1
        self.zoomframe = (0, 0, 0, 0)
        # on loading, there is no zoom
        self.image = self.original_image
        
        self.frame.canvas.NEEDREDRAW = True
        self.frame.thumbnailpanel.NEEDREDRAW = True
        status_string = os.path.basename(filepath)
        if os.path.exists(os.path.splitext(filepath)[0] + '.CR2'):
            status_string += ' : RAW+'
        self.frame.SetStatusText(status_string)

    def load_multiple(self):
        """Load a list of images and construct a composite image"""
        print 'not implemented yet'
        pass

    def zoom(self):
        """scale the bitmap by the given scale.
        use to zoom in or zoom out.
        Scale goes from 1 (fit to window) upwards
        as multiple of that size
        If offsets are not given center the zoom
        """
        scale = self.zoom_ratio
        #xoffset = self.zoom_xoffset; yoffset = self.zoom_yoffset
        frame = []
        newwidth = self.width / scale
        newheight = self.height / scale

        if self.zoom_xoffset == None:
            # the zoom frame is centered
            self.zoom_xoffset = (self.width - newwidth) / 2
        else:
            self.zoom_xoffset = min(self.zoom_xoffset,
                                    self.width - newwidth)

        if self.zoom_yoffset == None:
            self.zoom_yoffset = (self.height - newheight) / 2
        else:
            self.zoom_yoffset = min(self.zoom_yoffset,
                                    self.height - newheight)

        self.zoomframe = [int(value) for value in
                          [self.zoom_xoffset, self.zoom_yoffset,
                           self.zoom_xoffset + newwidth,
                           self.zoom_yoffset + newheight]]
        #
        if self.zoom_xoffset < 0:
            self.zoom_xoffset = 0
        if self.zoom_yoffset < 0:
            self.zoom_yoffset = 0

        self.image = self.original_image.crop(self.zoomframe)

        self.frame.canvas.NEEDREDRAW = True
        self.frame.thumbnailpanel.NEEDREDRAW = True

    def zoom_in(self, event):
        """zoom into the image"""
        self.zoom_ratio *= self.ZOOMSTEP
        self.zoom()

    def zoom_out(self, event):
        """zoom out"""
        self.zoom_ratio /= self.ZOOMSTEP
        self.zoom_ratio = max(self.zoom_ratio, 1) # cant go below 1
        self.zoom()

    def no_zoom(self, event):
        """Reset zoom"""
        self.zoom_ratio = 1
        self.zoom()

    def shift_zoom_frame(self, event):
        key = event.GetKeyCode()

        if key == 314:
            self.zoom_xoffset += self.SHIFTZOOMSTEP
        elif key == 315:
            self.zoom_yoffset += self.SHIFTZOOMSTEP
        elif key == 316:
            self.zoom_xoffset -= self.SHIFTZOOMSTEP
        elif key == 317:
            self.zoom_yoffset -= self.SHIFTZOOMSTEP

        self.zoom()
        
    def autorotate(self, exif_orientation):
        """Given the exif orientation tag, rotate the image"""
        exif_orientation = int(exif_orientation)
        if exif_orientation == 1:
            return 
        elif exif_orientation == 6:
            self.original_image = self.original_image.rotate(-90)
        elif exif_orientation == 8:
            self.original_image = self.original_image.rotate(90)
        elif exif_orientation == 3:
            self.original_image = self.original_image.rotate(180)
     
        
class ExifInfo():
    """exif information for an image"""
    def __init__(self, imagefilehandle):
        self.imagefilehandle = imagefilehandle
        self.read_exif_info()
        self.info = self.process_exif_info()
        self.exif_info_list = self.info_list()
        
    def read_exif_info(self):
        """read the exif information"""
        try:
            self.exifdata = Exifreader.process_file(self.imagefilehandle)
        except Exifreader.ExifError, msg:
            self. exifdata = None

    def info_list(self):
        """exif information as a list of tuples"""
        return [('Model', '%s' %(self.info.get('Model', 'NA'))),
                ('Time', '%s' %(self.info.get('DateTime', 'NA'))),
                ('Mode', '%s' %(self.info.get('ExposureMode', 'NA'))),
                ('ISO', '%s' %(self.info.get('ISOSpeed', 'NA'))),
                ('Aperture', '%s' %(reduce_fraction(self.info.get('FNumber', 'NA')))),
                ('Shutter time', '%s' %(self.info.get('ExposureTime', 'NA'))),
                ('Focal length', '%s' %(self.info.get('FocalLength', 'NA'))),
                ('Flash', '%s' %(self.info.get('FlashMode', 'NA'))),
                ('Lens', '%s - %s' %(self.info.get('ShortFocalLengthOfLens', 'NA'),
                                     (self.info.get('LongFocalLengthOfLens', 'NA'))))]
        
    def __str__(self):
        return repr(self)
            
    def __repr__(self):
        """formatted string of exif info"""
        return '\n'.join(['Model : %s' %(self.info.get('Model', 'NA')),
                          'Time : %s' %(self.info.get('DateTime', 'NA')),
                          'Mode : %s' %(self.info.get('ExposureMode', 'NA')),
                          'ISO : %s' %(self.info.get('ISOSpeed', 'NA')),
                          'Aperture : %s' %(reduce_fraction(self.info.get('FNumber', 'NA'))),
                          'Shutter time : %s' %(self.info.get('ExposureTime', 'NA')),
                          'Focal length : %s' %(self.info.get('FocalLength', 'NA')),
                          'Flash : %s' %(self.info.get('FlashMode', 'NA')),
                          'Lens : %s - %s' %(self.info.get('ShortFocalLengthOfLens', 'NA'),
                                             self.info.get('LongFocalLengthOfLens', 'NA'))]) 
            
    def process_exif_info(self):
        """Extract the useful info only"""
        info = {}
        data = self.exifdata

        if not data:
            return info
        
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
    #cachetest()
    #resizetest()
