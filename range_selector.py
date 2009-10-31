
"""A widget allowing user to select a sub-range from
a given range easily using the mouse"""

# Raja S
# Oct 2009

from __future__ import division
import wx
import math
from utils import in_rectangle, list_to_hist, DisplayCanvas


class RangeSelector(DisplayCanvas):
    """The selector
    """
    def __init__(self, parent, range, vals=[]):
        """range is a tuple specifying limits of the range.
        vals are the populated values, that is the
        preexisting values to display
	"""
        DisplayCanvas.__init__(self, parent)
        self.range = range
        #self.range = range
        #self.min, self.max = range

        # customize if needed when subclassing
        self.CONTINUOUS = True # is the range continuous or discrete
        self.steps = [] # for discrete data, define the steps

        # convert list vals into a dict
        self.vals = list_to_hist(vals)

        #self.subrange_min = self.min
        #self.subrange_max = self.max

        self.range_brush = wx.Brush((200, 200, 200), wx.SOLID)
        self.subrange_brush = wx.Brush((100, 100, 100), wx.SOLID)
        self.border = 20
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self.NEEDREDRAW = True

        self.reset_steps() # can call again from sublass
        
    def reset_steps(self):
        """Initial set up and resetting of range and subrange
        values"""
        if self.CONTINUOUS:
            self.range_min, self.range_max = self.range
        else:
            self.range_min = 0
            self.range_max = len(self.steps)

        self.subrange_min = self.range_min
        self.subrange_max = self.range_max

    def on_resize(self, event):
        """when canvas  is resized, we create a new buffer, which will
        be redrawn on next idle event"""
        # update / initialize height and width
        self.width, self.height = self.GetSize()

        # update size of rectangle
        self.rect_ht = self.height // 5
        self.rect_wd = self.width - 2 * self.border

        #update size of bounding box
        self.bbox = (self.border,
                     self.height - self.border - 3*self.rect_ht,
                     self.width - self.border,
                     self.height - self.border - self.rect_ht)
        
        # update / create the buffer for the buffered dc
        image = wx.EmptyImage(self.width, self.height)
        wx.Image.Create(image, self.width, self.height, False)
        wx.Image.SetRGBRect(image, wx.Rect(0, 0, self.width, self.height),
                            255, 255, 255)        
        self.buffer = wx.BitmapFromImage(image)
        self.NEEDREDRAW = True

        
    def draw(self, dc):
        """Draw the range and the selected subrange"""

        # draw the range rectangle
        dc.SetBrush(self.range_brush)
        dc.DrawRectangle(self.border,
                         self.height - self.rect_ht - self.border,
                         self.rect_wd,
                         self.rect_ht)

        dc.DrawText(self.format_val(self.range_min), self.border - 10,
                    self.height - self.rect_ht - 2*self.border)
        dc.DrawText(self.format_val(self.range_max), self.width - self.border,
                    self.height - self.rect_ht - 2*self.border)

        # and the subrange rectangle
        dc.SetBrush(self.subrange_brush)
        x1 = self.range_to_canvas(self.subrange_min)
        x2 = self.range_to_canvas(self.subrange_max)
        dc.DrawRectangle(x1,self.height - self.rect_ht - self.border,
                         x2 - x1, self.rect_ht)

        dc.DrawText(self.format_val(self.subrange_min), x1 - 10,
                    self.height - self.rect_ht - 2*self.border)
        dc.DrawText(self.format_val(self.subrange_max), x2,
                    self.height - self.border)

        # draw the vals
        dc.SetPen(wx.Pen(wx.RED, 2, wx.SOLID))
        y1 = self.height - self.border - self.rect_ht/10
        for val in self.vals:
            x = self.range_to_canvas(val)
            dc.DrawLine(x, y1, x, y1 - self.vals[val])

    def format_val(self, val):
        """Format the values in the range into readable
        form. Note that this may be customized in the subclasses"""
        return '%0.2f' % (val)
            
    def get_subrange(self, x, y):
        """From the x,y coords of the mouse position,
        calculate the chosen subrange.
        """
        self.subrange_center = self.canvas_to_range(x)
        subrange_width = ((self.bbox[3] - y) / (
                self.bbox[3] - self.bbox[1]))*((
                self.range_max - self.range_min) / 2)
        start = max(self.range_min, self.subrange_center - subrange_width)
        end = min(self.range_max, self.subrange_center + subrange_width)

        return start, end

    def canvas_to_range(self, x):
        """convert a value from x coord on canvas to
        actual value in the range"""
        return (x - self.border) * (
                (self.range_max - self.range_min) / (self.width - 2*self.border)) + self.range_min

        
    def range_to_canvas(self, x):
        """convert a value on the specified range to the x value
        on the canvas"""
        # we assume that x is in the supplied range
        return self.border + (x - self.range_min) * (
            (self.width - 2*self.border) / (self.range_max - self.range_min))

    def x_to_center(self, x):
        """from x position of the mouse event,
        determine the center of the subrange"""
        scale = (self.range_max - self.range_min) / (
                     self.width - 2*self.border)

        return ((x - self.border) * scale) + self.range_min


    def y_to_width(self, y):
        """From y of mouse position,
        determine the width of the subrange"""
        # TODo:
        subrange_width = ((self.bbox[3] - y) / (
                    self.bbox[3] - self.bbox[1]))*((
                    self.range_max - self.range_min) / 2)
        
    
    def on_mouse(self, event):
        """Handle mouse movements"""
        x, y = event.GetPosition()

        if event.LeftIsDown() and event.Dragging():
            if in_rectangle((x,y), self.bbox):
                self.subrange_min, self.subrange_max = self.get_subrange(
                    x, y)
                self.NEEDREDRAW = True

        else:
            event.Skip()

            
def runTest(frame, nb, log):
    win = RangeSelector(nb, (1,10), [2,3,4, 2, 3, 1, 7, 8, 3, 3, 2, 3, 3, 3, 3])
    return win


if __name__ == "__main__":
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

