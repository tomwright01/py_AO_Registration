import wx
import wx.lib.newevent
import numpy as np
import logging
import matplotlib
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.figure import Figure

logger = logging.getLogger('AORegistration.CanvasPanel')

class CanvasPanel(wx.Panel):
    """This is a wx.panel that will hold a matplotlib canvas"""
    callbacks={}
    axis_limits=None

    evtAxesChange, EVT_AXES_CHANGE = wx.lib.newevent.NewEvent()
    
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        #Setup the drawing surface
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        
        #bind a click event to the canvas
        self.callbacks['canvas_click']=self.canvas.mpl_connect('button_press_event', self.on_canvas_click) 
        
        #Add a standard navigation toolbar
        toolbar = NavigationToolbar(self.canvas)
        
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1)
        sizer.Add(toolbar)
        self.SetSizer(sizer)

    def _axesChange(self,evt):
        #logger.debug('Axes change event detected')
        newEvt = self.evtAxesChange()
        wx.PostEvent(self,newEvt)
        
    def on_axes_changed(self,event):
        #logger.debug('axes change fired')
        self.axis_limits = self.axes.axis()
        self._axesChange(event)
        
    def on_canvas_click(self,event):
        logger.debug('Click caught')
        logger.debug('x:%s y:%s',event.xdata,event.ydata)
        
    def draw(self,image=None):
        """Draw an image onto the canvas"""
        if image is None:
            #Plot a simple numpy square is nothing is passed
            self.axes.imshow(np.ones((5,5)))
            return
        self.axes.clear()
        self.axes.imshow(image,cmap='gray')
            
        #Bind an event to the axes so I can update when the image is zoomed
        self.callbacks['xlim_change']=self.axes.callbacks.connect('xlim_changed',self.on_axes_changed)
        self.callbacks['ylim_change']=self.axes.callbacks.connect('ylim_changed',self.on_axes_changed)
        
        if not self.axis_limits is None:
            self.axes.axis(self.axis_limits)
        self.canvas.draw()

    def overlayImage(self,image):
        self.axes.imshow(image)
        self.canvas.draw()

    def GetAxesLimits(self):
        """Get the current limits of the axes"""
        return self.axis_limits
    
    def SetAxesLimits(self,value):
        """Set the current limits of the axes
        value = (xmin,xmax,ymax,ymin)"""
        self.axis_limits = value