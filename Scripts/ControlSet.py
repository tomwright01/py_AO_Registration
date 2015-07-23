import logging
import wx

from wx.lib.pubsub import pub

logger = logging.getLogger('AORegistration.Video')

class ControlSet(wx.Panel):
    """wx.Panel to hold misc controls"""
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        sizer=wx.BoxSizer(wx.VERTICAL)
    
        btn_blinkReject = wx.Button(self,name='Blink_Reject',size=(125,-1), label='Blink Reject')
        btn_setKeyFrame = wx.Button(self,name='Key_Frame',size=(125,-1), label='Key Frame')
        btn_launchJob = wx.Button(self,name='Launch_Job',size=(125,-1), label='Launch Job')
        
        self.Bind(wx.EVT_BUTTON,self._onClick,btn_blinkReject)
        self.Bind(wx.EVT_BUTTON,self._onClick,btn_setKeyFrame)
        self.Bind(wx.EVT_BUTTON,self._onClick,btn_launchJob)
        
        sizer.Add(btn_blinkReject)
        sizer.Add(btn_setKeyFrame)
        sizer.Add(btn_launchJob)
        
        self.SetSizer(sizer)
        
    def _onClick(self,evt):
        if evt.GetEventObject().Name == 'Blink_Reject':
            pub.sendMessage('blink_reject',data=None)
        if evt.GetEventObject().Name == 'Key_Frame':
            pub.sendMessage('key_frame',data=None)            
        if evt.GetEventObject().Name == 'Launch_Job':
            pub.sendMessage('launch_job',data=None)                    
        pass