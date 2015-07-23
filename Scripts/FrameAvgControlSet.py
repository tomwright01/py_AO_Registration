import logging
import wx

from wx.lib.pubsub import pub

logger = logging.getLogger('AORegistration.FrameAvg')

class BoundSpinCtrl(wx.Panel):
    """A static text box with a spincontrol"""
    def __init__(self,parent,name,initVal,minVal,maxVal,label,*args,**kwargs):
        wx.Panel.__init__(self,parent,*args,**kwargs)
        self.value = initVal
        self.Name = name
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,label=label)
        self.sc = wx.SpinCtrl(self,value=str(initVal))

        self.sc.SetRange(minVal,maxVal)
        self.Bind(wx.EVT_SPINCTRL,self.on_update_spin)
        
        sizer.Add(label)
        sizer.Add(self.sc)
        
        self.SetSizer(sizer)
        #sizer.Fit(self)
        
    def on_update_spin(self,event):
        self.value = self.sc.GetValue()
        event.SetEventObject(self) #Change the originating object to be the boundCtrl
        #logger.debug('Caught spin event at bound control')
        event.Skip()
        
    def GetValue(self):
        return self.value
    
    def GetName(self):
        return self.name

    def SetValue(self,value):
        self.sc.SetValue(value)
        
    def SetRange(self,value):
        if self.value > value[1]:
            self.SetValue(value[1])
        self.sc.SetRange(value[0],value[1])

class FrameAvgControlSet(wx.Panel):
    """wx.Panel to hold misc controls"""
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        btn_setroi = wx.ToggleButton(self,name='Set_ROI',size=(125,-1),label='Set ROI')
        btn_avgframe = wx.Button(self,name='avgframe',size=(125,-1),label='Average')

        self.spn_avgFrameCount = BoundSpinCtrl(self, 'spn_avgFrameCount', 1, 1, 10, 
                                      'Count')
        btn_saveFrame = wx.Button(self,name='saveAvgFrame',size=(125,-1),label='Save')
        
        
        self.Bind(wx.EVT_TOGGLEBUTTON,self._onClick)
        self.Bind(wx.EVT_BUTTON,self._onClick)
        self.Bind(wx.EVT_SPINCTRL,self._onClick)
        
        sizer.Add(btn_setroi)
        sizer.Add(btn_avgframe)
        sizer.Add(self.spn_avgFrameCount)
        sizer.Add(btn_saveFrame)
        self.SetSizer(sizer)
        
        pub.subscribe(self.setMaxCount,'max_frame_count')
    def setMaxCount(self,data):
        self.spn_avgFrameCount.SetRange((0,data))
    def _onClick(self,evt):
        if evt.GetEventObject().Name == 'Set_ROI':
            pub.sendMessage('set_roi')
        if evt.GetEventObject().Name == 'avgframe':
            pub.sendMessage('generate_average',nframes=self.spn_avgFrameCount.value)
        if evt.GetEventObject().Name == 'spn_avgFrameCount':
            pub.sendMessage('generate_average',nframes=self.spn_avgFrameCount.value)
        if evt.GetEventObject().Name == 'saveAvgFrame':
            pub.sendMessage('save_avg_frame')