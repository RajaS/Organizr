
"""A widget allowing user to select a sub-range from
a given range easily using the mouse"""

# Raja S
# Oct 2009

import wx

class RangeSelector(wx.Panel):
    """The selector
    """
    def __init__(self, parent, range):
        """
	"""
        wx.Panel.__init__(self, parent, -1)
        self.min, self.max = range

        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)


    def on_mouse(self, event):
        """Handle mouse movements"""
        if event.Dragging:
            print event.GetPosition()

def runTest(frame, nb, log):
    win = RangeSelector(nb, (1,4))
    return win


if __name__ == "__main__":
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

