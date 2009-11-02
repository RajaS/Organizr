
import os
import md5
import wx
import datetime
import Exifreader

# utility functions

def relative_time(timeobj, dawnoftime=None):
    """Given a datetime object, return time in seconds since
    an arbitrary epoch start. This dawn of time can be specified,
    defaults to 01-01-1970"""
    if dawnoftime == None:
        dawnoftime = datetime.datetime(1970, 1, 1)

    # difference as a timedelta obj
    td = timeobj - dawnoftime

    return (td.days * 24 * 60 * 60) + (td.seconds)


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
        try:
            newimage.SetData(img.convert( "RGB").tostring())
        except:
            pass # TODO: only fordebugging 
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
    print list_to_hist([1,2,1,1,3,4,2])


if __name__ == '__main__':
    main()
