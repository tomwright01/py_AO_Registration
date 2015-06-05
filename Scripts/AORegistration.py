import wx
import logging
import os

import CanvasPanel
import AOVideo
import VideoControl
import ControlSet

from wx.lib.pubsub import pub

class MyMainFrame(wx.Frame):
    """Top level frame
    Subscribes frame_change"""
    #_video = AOVideo.AOVideo()
    
    def __init__(self,*args,**kwargs):
        wx.Frame.__init__(self,*args,**kwargs)
        
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        #initialise the video object
        self._video = AOVideo.AOVideo()
        
        # Setting up the menu
        self.filemenu = wx.Menu()
        menuItem_fileopen = self.filemenu.Append(wx.ID_OPEN,"&0pen File..."," Open source file")
        self.filemenu.AppendSeparator()
        menuItem_save = self.filemenu.Append(wx.ID_SAVE,"&Save Progress...","Save progress file")        
        self.filemenu.AppendSeparator()                                         
        menuItem_about = self.filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        self.filemenu.AppendSeparator()
        menuItem_exit = self.filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        
        self.Bind(wx.EVT_MENU,self.onOpen,menuItem_fileopen)
        self.Bind(wx.EVT_MENU,self.onSave,menuItem_save)
        self.Bind(wx.EVT_MENU,self.onAbout,menuItem_about)
        self.Bind(wx.EVT_MENU,self.onExit,menuItem_exit)        
        
        #Creating the menubar
        menuBar = wx.MenuBar()
        menuBar.Append(self.filemenu,"&File") #adding the filemenu to the menubar
        self.SetMenuBar(menuBar)        
        
        
        #Layout 2 panels
        self.image = CanvasPanel.CanvasPanel(self,wx.ID_ANY, style = wx.BORDER_RAISED) # the canvas for image display
        self.videoControls = VideoControl.VideoControl(self, wx.ID_ANY)

        controlset = ControlSet.ControlSet(self,wx.ID_ANY,size=(110,-1))
        
        
        sizer_tb = wx.BoxSizer(wx.VERTICAL)
        sizer_tb.Add(self.image, proportion=1, border=1)
        sizer_tb.Add(self.videoControls, proportion=0, border=5)
    
        sizer_lr = wx.BoxSizer(wx.HORIZONTAL)
        sizer_lr.Add(sizer_tb, proportion=1,flag=wx.EXPAND)
        sizer_lr.Add(controlset, proportion=0)
    
        #Layout sizers
        self.SetSizer(sizer_lr)
    
        #subscribe to frame_change events
        pub.subscribe(self.__frameChange,'frame_change')
        self.Show(True)
        logger.debug('Initialised')
        
    def __frameChange(self,data,extra1=None,extra2=None):
        self._video.currentframeidx = data
        self.UpdateDisplay()
        
    def onOpen(self,evt):
        """Function for menuitem Open
        Opens the video to be processed"""
        filename = None
        dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", dirname, "", "*.avi", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
        dlg.Destroy()
        self._video.filename = os.path.join(dirname,filename)
        self._video.LoadVideo()
        self.videoControls.maxval = self._video.framecount
        self.videoControls.curval = self._video.currentframeidx
        self.UpdateDisplay()
        
    def onSave(self,evt):
        """Function for menuitem Save
        Saves the video to be processed"""        
        pass
      
    def onAbout(self, event):
        """callback for menuitem_about"""
        dlg = wx.MessageDialog( self, "Frame registration \n tom@maladmin.com", "AO Registration", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
        
    def onExit(self, event):
        """callback for menuitem_exit"""
        self.Close(True)
        
    def UpdateDisplay(self):
        frame = self._video.currentframe
        if frame is None:
            frame = np.ones((5,5))
        self.image.draw(self._video.currentframe)
        
if __name__ == '__main__':
    logger = logging.getLogger('AORegistration')
    formatter = logging.Formatter('%(module)s : %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)    
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug('XXXXXX')
    app = wx.App(False)
    frame = MyMainFrame(parent=None,title='AORegistration',size=(800,600))
    app.MainLoop()