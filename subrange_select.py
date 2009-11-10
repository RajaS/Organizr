"""A widget allowing user to interactively select
a subrange from among a range of values"""

from __future__ import division
import wx
import time

from utils import DisplayCanvas


class SubRangeSelect(DisplayCanvas):
    """Displaycanvas takes care of basics of drawing
    """
    def __init__(self, parent, vals=[], steps=[], CONTINUOUS=True):
        """
        vals is the dataset to be displayed.
        steps need to be given for discrete ranges only
	"""
        DisplayCanvas.__init__(self, parent)
        self.vals = vals
        self.steps = steps
        self.CONTINUOUS = CONTINUOUS
        self.border = 20

        # brushes and pens
        self.range_brush = wx.Brush((200, 200, 200), wx.SOLID)
        self.subrange_brush = wx.Brush((100, 100, 100), wx.SOLID)
        self.tick_pen = wx.Pen(wx.BLACK, 1, wx.SOLID)
        
        self._init_range() #call if vals and steps changes

        self.on_resize(None)
        self.run_tests()
        
    def on_resize(self, event):
            """when canvas  is resized, we create a new buffer, which will
            be redrawn on next idle event. This is also the ideal time to
            update the size of the range rectangle and the bounding box"""
            # update / initialize height and width
            self.width, self.height = self.GetSize()

            # update size of rectangle
            self.rect_ht = self.height // 5
            self.rect_wd = self.width - 2 * self.border

            #update size of bounding box
            self.bbox = (self.border,
                         self.height - self.border - 3*self.rect_ht,
                         self.width - self.border,
                         self.height - self.border)

            # update / create the buffer for the buffered dc
            image = wx.EmptyImage(self.width, self.height)
            wx.Image.Create(image, self.width, self.height, False)
            wx.Image.SetRGBRect(image, wx.Rect(0, 0, self.width, self.height),
                                255, 255, 255)        
            self.buffer = wx.BitmapFromImage(image)
            self.RESIZED = True
            self.NEEDREDRAW = True
            
    def _init_range(self):
        """Initialise range limits from vals / steps.
        For discrete vals, also convert vals to indices"""
        if self.CONTINUOUS:
            self.val_min = min(self.vals)
            self.val_max = max(self.vals)
            buffer_width = (self.val_max - self.val_min) / 10

            self.range_min = self.val_min - buffer_width
            self.range_max = self.val_max + buffer_width
            self.subrange_min = self.val_min
            self.subrange_max = self.val_max

        else:
            # range goes from -1 to length
            self.range_min = -1
            self.range_max = len(self.steps)

            self.steps += [''] # blank at end will serve as the range limit
            self.vals = [self.steps.index(val)
                         for val in self.vals]
            
            self.subrange_min = -0.5
            self.subrange_max = self.range_max - 0.5

    def val_to_canvasx(self, val):
        """convert a value to the x position of the canvas"""
        canvas_x1 = self.border # left edge of rectangle
        canvas_x2 = self.width - self.border # right edge
        scale = (canvas_x2 - canvas_x1) / (self.range_max - self.range_min)
        return (val - self.range_min) * scale + canvas_x1

    def canvasx_to_val(self, x):
        """convert an x coordinate on the canvas to a value"""
        canvas_x1 = self.border # left edge of rectangle
        canvas_x2 = self.width - self.border # right edge
        scale =  (self.range_max - self.range_min) / (canvas_x2 - canvas_x1)
        return (x - canvas_x1) * scale + self.range_min

    def canvasy_to_width(self, y):
        """convert y coordinate on canvas to width of subrange"""
        # divide by range / 1.8 so that there is a buffer
        # making it easier to cover the whole range
        scale = (self.range_max - self.range_min) / 1.8
        y_ht = self.bbox[3] - y
        bbox_ht = self.bbox[3] - self.bbox[1]
        return (y_ht / bbox_ht) * scale

    def get_subrange(self, x, y):
        """From the x,y coords of the mouse position,
        calculate the chosen subrange.
        """
        subrange_center = self.canvasx_to_val(x)
        subrange_width = self.canvasy_to_width(y)
        start = max(self.range_min, subrange_center - subrange_width)
        end = min(self.range_max, subrange_center + subrange_width)
        return start, end

    def draw(self, dc):
        """Draw all the elements"""
        # range rectangle is only drawn on resizes
        dc_font = dc.GetFont()
        if self.RESIZED:
            dc.SetBrush(self.range_brush)
            dc.DrawRectangle(self.border,
                             self.height - self.rect_ht - self.border,
                             self.rect_wd, self.rect_ht)
            self.RESIZED = False
        # extreme values for range
        dc_font.SetPointSize(9)
        dc.SetFont(dc_font)
        dc.DrawText(self.format_val(self.range_min), self.border,
                    self.height - self.border)
        dc.DrawText(self.format_val(self.range_max), self.width - self.border - 20,
                    self.height - self.border)
        # ticks for range
        if self.CONTINUOUS:
            interval = (self.range_max - self.range_min) / 5
            ticks = [self.range_min + interval * (multiple + 1)
                     for multiple in range(4)]
        else:
            # range_min and max are always integers, interval is always 1
            ticks = range(self.range_min +1, self.range_max)

        ticklabels = [self.format_val(tick) for tick in ticks]
        tickpos = [self.val_to_canvasx(tick) for tick in ticks]
        y1 = self.height - self.border * 0.5
        y2 = self.height - self.border
        dc.SetPen(self.tick_pen)
        dc_font.SetPointSize(8)
        dc.SetFont(dc_font)
        for tickx, label in zip(tickpos, ticklabels):
            dc.DrawLine(tickx, y1, tickx, y2)
            dc.DrawText(label, tickx + 2, self.height - self.border + 2)
        
        # draw subrange
        dc.SetBrush(self.subrange_brush)
        x1 = self.val_to_canvasx(self.subrange_min)
        x2 = self.val_to_canvasx(self.subrange_max)
        dc.DrawRectangle(x1,self.height - self.rect_ht - self.border,
                         x2 - x1, self.rect_ht)
        # subrange extrema values
        dc_font.SetPointSize(9)
        dc.SetFont(dc_font)
        dc.DrawText(self.format_val(self.subrange_min), x1 - 10,
                    self.height - self.rect_ht - 2*self.border)
        dc.DrawText(self.format_val(self.subrange_max), x2,
                    self.height - self.rect_ht - 2* self.border)        

            
        # draw subrange values

    def format_val(self, val, min=False, max=False):
        """Return a formatted form of a value suitable for printing"""
        if self.CONTINUOUS:
            return '%0.1f' % (val)
        else:
            # can format differently based on min/max/neither
            if min:
                return self.steps[int(val) + 1]
            elif max:
                return self.steps[int(val)]
            else:
                return self.steps[int(val)]
    
    def run_tests(self):
        # tests for val_to_canvasx and canvasx_to_val
        print 'val to canvas, min', self.val_to_canvasx(self.range_min), self.border
        print 'val to canvas, max', self.val_to_canvasx(self.range_max
                                                        ), self.width - self.border
        print 'canvas to val, left border', self.canvasx_to_val(self.border), self.range_min
        print 'canvas to val, right border', self.canvasx_to_val(
            self.width - self.border), self.range_max

    
def runTest(frame, nb, log):
    Cont_Test = 0
    if Cont_Test:
        win = SubRangeSelect(nb, [2,3,4, 2, 3, 1, 7, 8, 3, 3, 2, 3, 3, 3, 3])
    else:
        win = SubRangeSelect(nb, ['1/5', '1/5', '1/3', '1', '1', '1'],
                            ['1/5', '1/3', '1/2', '1', '2', '3'], False)

    return win

if __name__ == "__main__":
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

