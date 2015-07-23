import logging
import wx

from wx.lib.pubsub import pub

logger = logging.getLogger('AORegistration.Video')

class VideoPosition(wx.Panel):
    '''class for displaying position in a video
    Emits a position_change message to pubsub
    Subscribe to range_change event
    Subscribe to frame_change event'''
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)    
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        pub.subscribe(self.__rangeChange,'range_change')
        pub.subscribe(self.__frameChange,'frame_change')

        self.sld_position = wx.Slider(self,wx.ID_ANY,style=wx.HORIZONTAL, size=(400,-1))
        self.txt_position = wx.TextCtrl(self,wx.ID_ANY,style=wx.HORIZONTAL,size=(100,-1))

        if kwargs.has_key('maxval'):
            self.sld_position.Max=kwargs['maxval']
            
        if kwargs.has_key('curval'):
            self.sld_position.Value=kwargs['curval']
            self.txt_position.Value=kwargs['curval']

        self.Bind(wx.EVT_TEXT,self._stateChange,self.txt_position)
        self.Bind(wx.EVT_SCROLL_CHANGED, self._stateChange,self.sld_position)
        
        sizer.Add(self.sld_position, proportion = 0)
        sizer.Add(self.txt_position, proportion = 0)

        self.SetSizer(sizer)

    def _stateChange(self,evt):
        """Handler for change events"""
        newVal = int(evt.GetEventObject().GetValue())
        if newVal > self.sld_position.Max:
            logger.error('Invalid position specified')
            self.txt_position.Value = str(self.sld_position.Value)
            raise ValueError

        if self.sld_position.Value != newVal:
            self.sld_position.SetValue(newVal)
            pub.sendMessage('position_change',data=newVal)
        if int(self.txt_position.Value) != newVal:
            self.txt_position.SetValue(str(newVal))
            pub.sendMessage('position_change',data=newVal)

    def __rangeChange(self,data,extra1=1,extra2=None):
        logger.debug('rangeChange event detected')
        self.sld_position.Max = data

    def __frameChange(self,data,extra1=None,extra2=None):
        logger.debug('frameChange event detected')
        if data > self.sld_position.Max or data < 0:
            logger.error('Invalid position specified')
            raise ValueError

        self.sld_position.Value = data
        self.txt_position.SetValue(str(data))
            


class VideoButtons(wx.Panel):
    """wx.Panel to hold forward, backward buttons
    publishes event video_change with data1 [forward|backward]"""
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        sizer=wx.BoxSizer(wx.VERTICAL)

        btn_backward = wx.Button(self,wx.ID_BACKWARD)
        btn_forward = wx.Button(self,wx.ID_FORWARD)

        self.Bind(wx.EVT_BUTTON, self.onForward, btn_forward)
        self.Bind(wx.EVT_BUTTON, self.onBackward, btn_backward)

        sizer.Add(btn_forward)
        sizer.Add(btn_backward)

        self.SetSizer(sizer)

    def onForward(self,event):
        logger.debug('Frame forward click event')
        pub.sendMessage('position_change', data='forward')

    def onBackward(self,event):
        logger.debug('Frame backward click event')
        pub.sendMessage('position_change', data='backward')

class VideoControl(wx.Panel):
    """Panel to control a video
    Subscribes position_change
    Emits range_change
    Emits frame_change"""
    def __init__(self,*args,**kwargs):
        wx.Panel.__init__(self,*args,**kwargs)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        pnl_position = VideoPosition(self)
        pnl_controls = VideoButtons(self)

        sizer.Add(pnl_position, proportion=3)
        sizer.Add(pnl_controls,proportion = 1)

        self.SetSizer(sizer)

        pub.subscribe(self.__positionChange,'position_change')

        if kwargs.has_key('maxval'):
            self.maxval = kwargs['maxval']
        if kwargs.has_key('curval'):
            self.curval = kwargs['curval']

    def __positionChange(self,data,extra1=None,extra2=None):
        logger.debug('positionChange notification received')
        if isinstance(data,int):
            self.curval = data
        elif data=='forward':
            self.curval += 1
        elif data=='backward':
            self.curval -= 1
        else:
            logger.error('Unhandled notification')

    def SetMaxval(self,maxval):
        self._maxval=int(maxval)
        pub.sendMessage('range_change',data=maxval)

    def GetMaxval(self):
        return self._maxval
        
    def SetCurval(self,curval):
        if int(curval) > self.maxval:
            logger.debug('Invalid value')
            raise ValueError('Invalid value')
        else:
            self._curval = int(curval)
            pub.sendMessage('frame_change',data=curval)

    def GetCurval(self):
        return self._curval
        

    maxval = property(fget = GetMaxval, fset=SetMaxval, doc='Maximum value')
    curval = property(fget=GetCurval, fset=SetCurval, doc='Current Value')
    