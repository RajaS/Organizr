
"""A widget allowing user to select a sub-range from
a given range easily using the mouse"""

# Raja S
# Oct 2009

from __future__ import division
import wx
from organizr import DisplayCanvas
from utils import in_rectangle


class RangeSelector(DisplayCanvas):
    """The selector
    """
    def __init__(self, parent, range, vals=[]):
        """range is a tuple specifying limits of the range.
        vals are the populated values, that is the
        preexisting values to display
	"""
        DisplayCanvas.__init__(self, parent)
        self.min, self.max = range
        self.vals = vals

        self.subrange_min = self.min
        self.subrange_max = self.max

        self.range_brush = wx.Brush((200, 200, 200), wx.SOLID)
        self.subrange_brush = wx.Brush((100, 100, 100), wx.SOLID)
        self.border = 20
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self.NEEDREDRAW = True
        
    def draw(self, dc):
        """Draw the range and the selected subrange"""
        self.panel_width, self.panel_height = self.GetSize()
        ht = self.panel_height // 10
        wd = self.panel_width - 2*self.border

        # bounding box where mouse drag will work
        self.bbox = (self.border, self.panel_height - self.border - 5*ht,
                     self.panel_width - self.border,
                     self.panel_height - self.border - ht)

        # draw the range rectangle
        dc.SetBrush(self.range_brush)
        dc.DrawRectangle(self.border, self.panel_height - ht - self.border,
                         wd, ht)

        dc.DrawText(str(self.min), self.border - 10,
                    self.panel_height - ht - 2*self.border)
        dc.DrawText(str(self.max), self.panel_width - self.border,
                    self.panel_height - ht - 2*self.border)

        # and the subrange rectangle
        dc.SetBrush(self.subrange_brush)
        x1 = self.range_to_canvas(self.subrange_min)
        x2 = self.range_to_canvas(self.subrange_max)
        dc.DrawRectangle(x1,self.panel_height - ht - self.border,
                         x2 - x1, ht)
        dc.DrawText('%0.2f' % (self.subrange_min), x1 - 10,
                    self.panel_height - ht - 2*self.border)
        dc.DrawText('%0.2f' %(self.subrange_max), x2,
                    self.panel_height - self.border)

        # draw the vals
        # TODO: donot overlap vals, instead stack them
        dc.SetPen(wx.Pen(wx.RED, 2, wx.SOLID))
        y1 = self.panel_height - self.border - ht/5
        y2 = self.panel_height - self.border - ht + ht/5
        for val in self.vals:
            x = self.range_to_canvas(val)
            dc.DrawLine(x, y1, x, y2)

    def get_subrange(self, x, y):
        """From the x,y coords of the mouse position,
        calculate the chosen subrange.
        """
        subrange_center = self.canvas_to_range(x)
        print 'center', subrange_center
        subrange_width = ((self.bbox[3] - y) / (
                self.bbox[3] - self.bbox[1]))*((
                self.max - self.min) / 2)

        start = max(self.min, subrange_center - subrange_width)
        end = min(self.max, subrange_center + subrange_width)
        return start, end

    def canvas_to_range(self, x):
        """convert a value from x coord on canvas to
        actual value in the range"""
        return (x - self.border) * (
            (self.max - self.min) / (self.panel_width - 2*self.border)) + self.min
        
    def range_to_canvas(self, x):
        """convert a value on the specified range to the x value
        on the canvas"""
        # we assume that x is in the supplied range
        return self.border + (x - self.min) * (
            (self.panel_width - 2*self.border) / (self.max - self.min))
        
    def on_mouse(self, event):
        """Handle mouse movements"""
        if event.LeftIsDown() and event.Dragging():
            x, y = event.GetPosition()

            if in_rectangle((x,y), self.bbox):
                self.subrange_min, self.subrange_max = self.get_subrange(
                    x, y)
                self.NEEDREDRAW = True
        else:
            event.Skip()

def runTest(frame, nb, log):
    win = RangeSelector(nb, (1,10), [2,3,4])
    return win


if __name__ == "__main__":
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

