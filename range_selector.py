
"""A widget allowing user to select a sub-range from
a given range easily using the mouse"""

# Raja S
# Oct 2009

from __future__ import division
import wx
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

        # customize if needed when subclassing
        self.CONTINUOUS = True # is the range continuous or discrete
        self.steps = [] # for discrete data, define the steps

        # convert list vals into a dict
        self.vals = list_to_hist(vals)

        self.range_brush = wx.Brush((200, 200, 200), wx.SOLID)
        self.subrange_brush = wx.Brush((100, 100, 100), wx.SOLID)
        self.border = 20
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self.NEEDREDRAW = True

        self.reset_steps() # can call again from subclass
        
    def reset_steps(self):
        """Initial set up and resetting of range and subrange
        values"""
        if self.CONTINUOUS:
            self.range_min, self.range_max = self.range
            self.ticks = [self.range_min + inc*((self.range_max - self.range_min)/5)
                          for inc in range(1,5)]
            self.ticklabels = [self.format_val(x) for x in self.ticks]
            
        else:
            self.range_min = 0
            self.range_max = len(self.steps) - 1
            self.ticks = range(len(self.steps))
            self.ticklabels = self.steps

        self.vals = list_to_hist(self.vals)
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

        try: #TODO:for debugging only
            dc.DrawText(self.format_val(self.range_min), self.border - 10,
                    self.height - self.border)
            dc.DrawText(self.format_val(self.range_max), self.width - self.border,
                    self.height - self.border)
        except:
            pass

        # and the subrange rectangle
        dc.SetBrush(self.subrange_brush)
        x1 = self.range_to_canvas(self.subrange_min)
        x2 = self.range_to_canvas(self.subrange_max)
        dc.DrawRectangle(x1,self.height - self.rect_ht - self.border,
                         x2 - x1, self.rect_ht)

        if not self.CONTINUOUS:
            self.subrange_min = int(self.subrange_min) + 1
            self.subrange_max = int(self.subrange_max)
            if self.subrange_min > self.subrange_max:
                self.subrange_min = -1
                self.subrange_max = -1

        try:
            dc.DrawText(self.format_val(self.subrange_min), x1 - 10,
                    self.height - self.rect_ht - 2*self.border)
            dc.DrawText(self.format_val(self.subrange_max), x2,
                    self.height - self.rect_ht - 2* self.border)
        except:
            pass
        
        # draw the ticks
        dc.SetPen(wx.Pen(wx.BLACK, 1, wx.SOLID))
        y1 = self.height - self.border * 0.2
        y2 = self.height - self.border 
        for ind in range(len(self.ticks)):
            tickx = self.range_to_canvas(self.ticks[ind])
            try:
                dc.DrawLine(tickx, y1, tickx, y2)
                dc.DrawText(self.ticklabels[ind],
                        tickx, self.height - self.border)
            except:
                pass

        # Draw the vals
        self.draw_vals(dc)

    def draw_vals(self, dc):
        """Draw the individual values"""
        dc.SetPen(wx.Pen(wx.RED, 2, wx.SOLID))
        dc.SetBrush(wx.Brush(wx.RED, wx.SOLID))
        
        y1 = self.height - self.border - self.rect_ht/10

        if self.CONTINUOUS:
            for val in self.vals:
                x = self.range_to_canvas(val)
                dc.DrawLine(x, y1, x, y1 - self.vals[val])
        else:
            # draw as ' squares' for discrete variables
            for val in self.vals:
                ind = self.convert_to_index(val)
                x = self.range_to_canvas(ind)
                val_count = self.vals[val]
                max_width = self.range_to_canvas(1) - 4

                sq_width = int(val_count ** 0.5) + 1
                half_width = sq_width // 2

                if val_count == 1:
                    dc.DrawPoint(x, y1)
                elif sq_width > max_width:
                    ht = int(val_count / max_width)
                    dc.DrawRectangle(x - max_width//2, y1 - ht,
                                     max_width, ht)
                else:
                    dc.DrawRectangle(x-half_width, y1-sq_width,
                                     sq_width, sq_width)

            
    def convert_to_index(self, x):
        """for discrete variables, convert a value to
        the index used for range"""
        try:
            return self.steps.index(str(x))
        except IndexError:
            print 'not found value', x
            pass
        except ValueError:
            print x
            print 'notfound'
            
    def format_val(self, val):
        """Format the values in the range into readable
        form. Note that this may be customized in the subclasses"""
        if self.CONTINUOUS:
            return '%0.1f' % (val)
        else:
            if val == -1:
                return ''
            else:
                return self.steps[int(val)]
        
    def get_subrange(self, x, y):
        """From the x,y coords of the mouse position,
        calculate the chosen subrange.
        """
        self.subrange_center = self.x_to_center(x)
        subrange_width = self.y_to_width(y)
        start = max(self.range_min, self.subrange_center - subrange_width)
        end = min(self.range_max, self.subrange_center + subrange_width)

        return start, end

    def range_to_canvas(self, x):
        """convert a value on the specified range to the x value
        on the canvas"""
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
        # divide by range / 1.8 so that there is a buffer
        # making it easier to cover the whole range
        return  ((self.bbox[3] - y) / (
                    self.bbox[3] - self.bbox[1]))*((
                    self.range_max - self.range_min) / 1.8)
        
    
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
    win = RangeSelector(nb, (0,10), [2,3,4, 2, 3, 1, 7, 8, 3, 3, 2, 3, 3, 3, 3])
    win.CONTINUOUS = False
    win.steps = ['0.1', '0.5', '2', '5', '7']
    win.vals = [0.5, 0.5, 0.5,  2]
    win.reset_steps()
    return win


if __name__ == "__main__":
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

