
import os
import md5
import wx

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


def get_thumbnailfile(filename):
    """for any image filename, find the stored thumbnail.
    As per free desktop specifications, this is stored in
    the .thumbnails dir in the home directory"""
    file_hash = md5.new('file://'+filename).hexdigest()
    tb_filename = os.path.join(os.path.expanduser('~/.thumbnails/normal'),
                               file_hash) + '.png'
    if os.path.exists(tb_filename):
        return tb_filename
    else:
        return None

def in_rectangle((x,y), (x1, y1, x2, y2)):
    """is the point (x,y) within the rectangle whose
    corners are (x1, y1) and (x2, y2)"""
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    return x1 < x < x2 and y1 < y < y2

def list_to_hist(vals):
    """Given a list of values, rearrange into a dict
    giving frequency of each value
     - like a histogam.
    So, given [1,2,1,1,3,4,2], we get
    {1:3; 2:2; 3:1; 4:1}"""
    hist = {}
    for val in vals:
        if val in hist.keys():
            hist[val] += 1
        else:
            hist[val] = 1
    return hist


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


def main():
    print list_to_hist([1,2,1,1,3,4,2])


if __name__ == '__main__':
    main()
