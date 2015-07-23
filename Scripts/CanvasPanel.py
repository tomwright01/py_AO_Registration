import wx
import wx.lib.newevent
import numpy as np
import logging
import matplotlib
from wx.lib.pubsub import pub

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
    
    def reset(self):
        self.axis_limits = None
        self.settingRoi = False
        self.roi=None
        
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        #Setup the drawing surface
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        
        self.settingRoi = False
        self.roi = None #can be a tuple holding coords for an ROI rectanlge
        
        #bind a click event to the canvas
        self.callbacks['canvas_click']=self.canvas.mpl_connect('button_press_event', self.on_canvas_click) 
        self.callbacks['canvas_clickrelease']=self.canvas.mpl_connect('button_release_event', self.on_canvas_click) 
        
        #Add a standard navigation toolbar
        toolbar = NavigationToolbar(self.canvas)
    
        pub.subscribe(self.__SetRoi,'set_roi')    
        
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
        if self.settingRoi:
            if event.name == 'button_press_event':
                self.roi_start = (event.xdata,event.ydata)
            if event.name == 'button_release_event':
                rct_width = abs(event.xdata - self.roi_start[0])
                rct_height = abs(event.ydata - self.roi_start[1])                
            
                rct_start = (min(event.xdata,self.roi_start[0]),
                             min(event.ydata,self.roi_start[1]))
            
                self.roi = (rct_start,rct_width,rct_height)
                self.drawRect(self.roi)
        
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
            
        if not self.roi is None:
            self.drawRect(self.roi)
        self.canvas.draw()

    def overlayImage(self,image):
        self.axes.imshow(image)
        self.canvas.draw()

    def drawRect(self,data):
        self.axes.add_patch(matplotlib.patches.Rectangle(data[0], data[1], data[2],fill=False))
        self.canvas.draw()
        
    def GetAxesLimits(self):
        """Get the current limits of the axes"""
        return self.axis_limits
    
    def SetAxesLimits(self,value):
        """Set the current limits of the axes
        value = (xmin,xmax,ymax,ymin)"""
        self.axis_limits = value
        
    def __SetRoi(self,data=None,event1=None,event2=None):
        if self.settingRoi:
            self.settingRoi = False
        else:
            self.settingRoi = True