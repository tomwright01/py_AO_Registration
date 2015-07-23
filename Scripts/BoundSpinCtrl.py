class BoundSpinCtrl(wx.Panel):
    """A static text box with a spincontrol"""
    def __init__(self,parent,ID,name,label,minVal,maxVal,initVal):
        wx.Panel.__init__(self,parent,ID)
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