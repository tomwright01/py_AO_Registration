import wx
import logging
import os
import argparse
import commands
import numpy as np
import scipy.misc

import CanvasPanel
import AOVideo
import VideoControl
import ControlSet
import ProcessedVideo
import FrameAvgControlSet
from wx.lib.pubsub import pub

class MyMainFrame(wx.Frame):
    """Top level frame
    Subscribes frame_change"""
    #_video = AOVideo.AOVideo()
    
    def __init__(self,*args,**kwargs):
        
        if kwargs.has_key('procFilename'):
            #going to process the file path to extract subjectid and testid
            self.procFilename=True
            kwargs.pop('procFilename')
        else:
            self.procFilename=False

        wx.Frame.__init__(self,*args,**kwargs)
        
        self.dirname = ''
        self.setroi = False
        
        self.CreateStatusBar() # A Statusbar in the bottom of the window
        #initialise the video object
        self._video = AOVideo.AOVideo()
        
        # Setting up the menu
        self.filemenu = wx.Menu()
        menuItem_fileopen = self.filemenu.Append(wx.ID_OPEN,"&0pen File..."," Open source file")
        menuItem_pfileopen = self.filemenu.Append(-1,"0pen &Processed File..."," Open processed file")
        self.filemenu.AppendSeparator()
        menuItem_save = self.filemenu.Append(wx.ID_SAVE,"&Save Progress...","Save progress file")        
        self.filemenu.AppendSeparator()                                         
        menuItem_about = self.filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        self.filemenu.AppendSeparator()
        menuItem_exit = self.filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        
        self.Bind(wx.EVT_MENU,self.onOpen,menuItem_fileopen)
        self.Bind(wx.EVT_MENU,self.onOpenProcessed,menuItem_pfileopen)
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
        cntrl_avgFrame = FrameAvgControlSet.FrameAvgControlSet(self,wx.ID_ANY,size=(110,-1))
        
        sizer_tb = wx.BoxSizer(wx.VERTICAL)
        sizer_tb.Add(self.image, proportion=1, border=1)
        sizer_tb.Add(self.videoControls, proportion=0, border=5)
    
        sizer_lr = wx.BoxSizer(wx.HORIZONTAL)
        sizer_lr.Add(sizer_tb, proportion=1,flag=wx.EXPAND)
        sizer_lr.Add(controlset, proportion=0)
        sizer_lr.Add(cntrl_avgFrame,proportion=0)
    
        #Layout sizers
        self.SetSizer(sizer_lr)
    
        #subscribe to frame_change events
        pub.subscribe(self.__frameChange,'frame_change')
        pub.subscribe(self.__blinkReject,'blink_reject')
        pub.subscribe(self.__setKeyFrame,'key_frame')
        pub.subscribe(self.__launchJob,'launch_job')
        #pub.subscribe(self.__SetRoi,'set_roi')
        #pub.subscribe(self.__canvasClick,'canvas_click')
        pub.subscribe(self.__getAvgFrame,'generate_average')
        pub.subscribe(self.__saveAvgFrame,'save_avg_frame')
        
        self.Show(True)
        logger.debug('Initialised')
        
    def __frameChange(self,data,extra1=None,extra2=None):
        try:
            self._video.currentframeidx = data
        except ValueError:
            self._video.currentframeidx = 0
        self.UpdateDisplay()
        
    def onOpenProcessed(self,evt):
        """Function for meuitem open processed
        Read the *.npz files in a directory and converts to a video"""
        dlg = wx.DirDialog(self,"Choose a Directory")
        
        if dlg.ShowModal() == wx.ID_OK:
            dirpath = dlg.GetPath()
            procVid = ProcessedVideo.ProcessedVideo(path=dirpath)
            self.dirname = dirpath
            if self.procFilename:
                pathbits = dirpath.split(os.sep)
                self.vidid = pathbits[-1]
                self.testid = pathbits[-2]
                self.subjectid = pathbits[-3]
                #fname,ext = os.path.splitext(filename)
                #self.filename = fname
            
            newVid = AOVideo.AOVideo(frameheight = procVid.frameheight,
                             framewidth = procVid.framewidth)
            for frame in procVid:
                newVid.addFrame(frame)
            self._video = newVid

            self._video.currentframeidx = 0
            self.videoControls.maxval = self._video.framecount
            self.videoControls.curval = self._video.currentframeidx   
            pub.sendMessage('max_frame_count',data=self._video.framecount)
            self.image.reset()
            self.UpdateDisplay()
            
    def onOpen(self,evt):
        """Function for menuitem Open
        Opens the video to be processed"""
        filename = None
        dirname = self.dirname
        dlg = wx.FileDialog(self, "Choose a file", dirname, "", "*.avi", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            self.dirname = dirname
        dlg.Destroy()
        if self.procFilename:
            pathbits = dirname.split(os.sep)
            self.testid = pathbits[-1]
            self.subjectid = pathbits[-2]
            fname,ext = os.path.splitext(filename)
            self.filename = fname
            
        self._video.filename = os.path.join(dirname,filename)
        self._video.LoadVideo()
        self._video.currentframeidx = 0
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
        
    def __SetRoi(self,data=None,extra1=None,extra2=None):
        if self.setroi:
            self.setroi=False
        else:
            self.setroi=True
    
    def __saveAvgFrame(self):
        filename = '{0}.tiff'.format(self.vidid)
        dirname = self.dirname
        dlg = wx.FileDialog(self, "Choose a file", dirname, filename, "", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            self.dirname = dirname
            scipy.misc.imsave(os.path.join(dirname,filename),self.avg_frame)
            logger.info('Saved average frame. Subject:{0} Test:{1} File:{2}'.format(self.subjectid,self.testid,filename))
        dlg.Destroy()        
    
    def __drawAvgFrame(self):
        self.image.draw(np.uint8(self.avg_frame))
        
    def __getAvgFrame(self,nframes):
        framediffs = self._video.compframes(self._video.currentframeidx,self.image.roi)
        sorted_diffs = np.argsort(framediffs)
        #avg_frame = np.zeros((self._video.frameheight,self._video.framewidth,3),np.uint64)
        avg_frame = np.zeros((self._video.frameheight,self._video.framewidth),np.uint64)
        for idx in sorted_diffs[range(nframes)]:
            logger.debug('max = {0}'.format(self._video.GetFrame(idx).max()))
            avg_frame = avg_frame + self._video.GetFrame(idx)
            #avg_frame[:,:,0] = avg_frame[:,:,0] + self._video.GetFrame(idx)
            #avg_frame[:,:,1] = avg_frame[:,:,1] + self._video.GetFrame(idx)
            #avg_frame[:,:,2] = avg_frame[:,:,2] + self._video.GetFrame(idx)
        #avg_frame[:,:,0] = avg_frame[:,:,0] / nframes
        #avg_frame[:,:,1] = avg_frame[:,:,1] / nframes
        #avg_frame[:,:,2] = avg_frame[:,:,2] / nframes
        self.avg_frame = avg_frame / nframes
        self.__drawAvgFrame()
        #self.image.draw(np.uint8(avg_frame))
        pass
    def __canvasClick(self,data,extra1=None,extra2=None):
        if self.setroi:
            self.image.drawRect(data)
        pass
    
    def __blinkReject(self,data,extra1=None,extra2=None):
        self._video = self._video.FilterBlinks(new=True)
        pub.sendMessage('range_change',data=self._video.framecount)
        self.UpdateDisplay()
    def __setKeyFrame(self,data,extra1=None,extra2=None):
        self._video.SetKeyFrame()
        
    def __launchJob(self,data,extra1=None,extra2=None):
        if not self.procFilename:
            raise NotImplementedError, "Must use structured source directory"
        
        basepath = '/home/tom/hpf2/'
        newName = '{0}_{1}_{2}'.format(self.subjectid,self.testid,self.filename)
        np.savez(os.path.join(basepath,'input_data',newName + '.npz'),
                 data=self._video._cache,
                 key_frame = self._video.keyframe)
        
        try:
            scriptFile = os.path.join('scripts',newName + '.scr')
            f = open(os.path.join(basepath,scriptFile),'w')
        except IOError, e:
            logger.error('Failed writing script file' + str(e))
            raise
        
        f.write('#!/bin/bash\n')
        f.write('#PBS -N AORegistration_{0}\n'.format(self.filename))
        f.write('#PBS -l nodes=1:ppn=40\n')
        f.write('#PBS -l gres=localhd:10\n')
        f.write('#PBS -l mem=10g,vmem=10g\n')
        f.write('#PBS -j oe /home/tomwright/output/\n')
        f.write('#PBS -M thomas.wright@sickkids.ca\n')
        f.write('#PBS -m abe\n')
        
        f.write('module load anaconda\n')
        f.write('export TMPDIR=/localhd/$PBS_JOBID\n')
        f.write('cp /home/tomwright/input_data/{0}.npz $TMPDIR/data.npz\n'.format(newName))
        f.write('mkdir $TMPDIR/output_data\n')
        f.write('export OUTDIR=/localhd/$PBS_JOBID/output_data\n')
        
        f.write('python /home/tomwright/scripts/ThreadedRegistration.py $TMPDIR/data.npz $OUTDIR\n')
        
        f.write('mkdir -p /home/tomwright/output_data/{0}/{1}/{2}\n'.format(self.subjectid,
                                                                            self.testid,
                                                                            newName))
        f.write('cp $OUTDIR/* /home/tomwright/output_data/{0}/{1}/{2}/\n'.format(self.subjectid,
                                                                            self.testid,
                                                                            newName))
        f.write('rm /home/tomwright/input_data/{0}.npz\n'.format(newName))
        f.close()
        
        status,jobid = commands.getstatusoutput("ssh tomwright@hpf.ccm.sickkids.ca 'qsub {0}'".format(scriptFile))
        logger.info('Processing Subject:{0},Test:{1},File:{2} with jobID:{3}'.format(self.subjectid,
                                                                                   self.testid,
                                                                                   self.filename,
                                                                                   jobid))
        #logger.info('Creating launch file Subject:{0},Test:{1},File:{2} with jobID:X'.format(self.subjectid,
                                                                                   #self.testid,
                                                                                   #self.filename))        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess AO videos for frame registration') 
    parser.add_argument('-v','--verbose',help="Increase the amount of output",
                        action="count")
    parser.add_argument('-l','--logfile',default=None,help="Path to log file")
    parser.add_argument('-f','--parseFilename',help="If the data is in structure subid/testid/file.avi parse to extract info",
                        action='store_true')    
    
    args=parser.parse_args()
    
    logger = logging.getLogger('AORegistration')
    formatter = logging.Formatter('%(module)s : %(levelname)s - %(message)s')
    
    if args.logfile:
        handler = logging.FileHandler(args.logfile)
        handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

    logger.addHandler(handler)

    if args.verbose == 1:
        logger.setLevel(logging.WARN)
    elif args.verbose == 2:
        logger.setLevel(logging.INFO)
    elif args.verbose > 2:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    if args.parseFilename:
        parseFilename=True
    else:
        parseFilename=False

    logger.debug('XXXXXX')
    app = wx.App(False)
    frame = MyMainFrame(parent=None,title='AORegistration',size=(800,600),procFilename=parseFilename)
    app.MainLoop()