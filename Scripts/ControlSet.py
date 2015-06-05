import logging
import wx

from wx.lib.pubsub import pub

logger = logging.getLogger('AORegistration.Video')

class ControlSet(wx.Panel):
    """wx.Panel to hold misc controls"""
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        sizer=wx.BoxSizer(wx.VERTICAL)
    
        mybutton = wx.Button(self,name='my button',size=(125,-1), label='Set Key Frame')
        self.Bind(wx.EVT_BUTTON,self._onClick,mybutton)
        sizer.Add(mybutton)
        self.SetSizer(sizer)
        
    def _onClick(self,evt):
        pass