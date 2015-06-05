import numpy as np
import logging
import cv2
import os

logger = logging.getLogger('AORegistration.AOVideo')

class AOVideo():
    """An AO video."""
    def __init__(self,*args,**kwargs):
        """Initialise the AO video object.
        
        Can either be initialised as an empty object or from an avi file.
        filename should not be provided if initialising as empty
        If initialised as empty, filename should be set then loadvideo()
        
        Position arguments
        filename
        
        Keyword arguments:
        filename=string
        size=(height,width)
        framecount=int
        
        """
        self._filename = None
        self._framecount = 0
        self._frameheight = None
        self._framewidth = None
        self._currentframeidx = None
        self.vid=None
        self._cache=None
        
        if len(args) == 1:
            self.filename=args[0]
        elif len(args) == 3:
            self.framecount=args[0]
            self.frameheight=args[1]
            self.framewidth=args[2]
            
        
        if kwargs.has_key('filename'):
            if len(kwargs) > 1:
                logger.debug('Attempt to provide additional args when initialising from a file')
            self.filename=kwargs['filename']
        else:
            if kwargs.has_key('framecount'):
                self.framecount=kwargs['framecount']
            if kwargs.has_key('frameheight'):
                self.frameheight=kwargs['frameheight']
            if kwargs.has_key('framewidth'):
                self.framewidth=kwargs['framewidth']            
            
        if self.filename:
            self.LoadVideo()
            
    def __iter__(self):
        self.currentframeidx = 0
        return self
    
    def next(self):
        self.currentframeidx += 1
        if self.currentframeidx >= self.framecount:
            raise StopIteration
        return self.currentframe
    
    def LoadVideo(self):
        "loads the video into a cv2 object"
        assert self.filename,"Filename not set"
        if not os.path.isfile(self.filename):
            logger.error('invalid filename')
            raise Exception('invalid filename')
        
        self.vid = cv2.VideoCapture(self.filename)
        self._framecount = self.vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
        self._frameheight = self.vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)        
        self._framewidth =  self.vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)        
        self.currentframeidx = 0
        self._cacheVideo()
        
    def GetFilename(self):
        return self._filename
    
    def SetFilename(self,filename):
        self._filename = fname
               
    def GetFrameCount(self):
        assert self.vid,"Video not loaded"
        return self._framecount
        
    def SetFrameCount(self,n):
        self._resize((self.frameheight,self.framewidth,n))
        
    def GetFrameHeight(self):
        assert self.vid,"Video not loaded"
        return self._frameheight

    def SetFrameHeight(self,n):
        self._resize((n,self.framewidth,self.framecount))

    def GetFrameWidth(self):
        assert self.vid,"Video not loaded"
        return self._framewidth

    def SetFrameWidth(self,n):
        self._resize((self.frameheight,n,self.framecount))    
    
    def _initialise(self):
        """Initialises an empty video object"""
        assert self.framecount > 0, "Frame count must be set"
        assert self.frameheight > 0, "Frame height must be set"
        assert self.framewidth > 0, "Frame width must be set"
        self._cached = np.zeros(self.frameheight,self.framewidth,self.framecount)
        
    def addFrame(self,frame):
        '''Add a 2D np.array to the frame cache'''
        assert isinstance(frame,np.ndarray), "Must provide an np array"
        assert len(frame.shape) == 2, "frame must be a 2D array"
        assert frame.shape[0] == self.frameheight, "Must resize before adding frames"
        assert frame.shape[1] == self.framewidth, "Must resize before adding frames"
        if self._cache is None:
            self._cache = frame
        else:
            self._cache=np.dstack((self._cache,frame))
        self.framecount += 1
        
    def _cacheVideo(self):
        '''Load the video from a file into memory'''
        assert self.vid,"Video not opened"
        
        self._cache = np.zeros((self.frameheight,self.framewidth,self.framecount),'uint8')
        cnt = 0
        if not self.vid.isOpened():
            self.vid.open(self.filename)
        self.vid.set(cv2.cv.CV_CAP_PROP_POS_FRAMES,0)
        
        while True:    
            ret, frame = self.vid.read()
            if not ret:
                if not cnt == self._framecount:
                    logger.warn('Not all frames read for file %s',self.filename)
                break
            self._cache[:,:,cnt] = frame[:,:,0]
            cnt += 1
        self.vid.release()
        
    def _MoveFirst(self):    
        self.currentframeidx=0 
        
    def GetCurrentFrameIdx(self):
        return self._currentframeidx
    
    def SetCurrentFrameIdx(self,n):
        if n < 0:
            raise ValueError('Frame must be > -1')
        if n > self.framecount:
            raise ValueError('Use resize to extend movie')
        self._currentframeidx = n
        
    def GetFrame(self,n):
        """Return frame index n
        frames are indexed from 0"""
        self.currentframeidx = n
        return self.currentframe
        
    def GetCurrentFrame(self):
        if isinstance(self._cache,np.ndarray):
            return self._cache[:,:,self.currentframeidx]
        else:
            self.vid.set(cv2.cv.CV_CAP_PROP_POS_FRAMES,self.currentframeidx)
            ret,frame = self.vid.read()
            return frame[:,:,0]
    
    def _resize(self,size):
        """Resize the avi
        params:
        size=(height,width,framecount)"""
        if size[0]<self.frameheight:
            raise ValueError('Invalid frame height')
        if size[1]<self.framewidth:
            raise ValueError('Invalid frame width')        
        if size[2]<self.framecount:
            raise ValueError('Invalid frame count')    
        newVid = np.zeros(size,type='uint8')
        if size[0] > self.frameheight:
            space=size[0] - self.frameheight
            tpad = space / 2
            bpad = space - tpad
        else:
            tpad,bpad=(0,0)
            
        if size[1] > self.framewidth:
            space=size[1] - self.framewidth
            lpad = space / 2
            rpad = space - lpad
        else:
            lpad,rpad=(0,0)
          
        newVid[tpad:-bpad,lpad:-rpad,0:self.framecount]=self._cache
        self.framecount = size[2]
        self.framewidth = size[1]
        self.frameheight = size[0]
        
        self._cache = newVid
        
    def _GetMeanFrameBrightness(self):
        return [f.mean() for f in self]
        
    def FilterBlinks(self):
        """removes frames with a mean brighness < 50% of the median frame brightness
        returns a new AOVideo object"""
        frameBrightness = self._GetMeanFrameBrightness()
        cutoff = np.median(frameBrightness) - (np.median(frameBrightness) * 0.5)
        keepframes = [i for i,j in enumerate(frameBrightness) if j > cutoff]   
        newVid = AOVideo(framecount = 0,
                         frameheight = self.frameheight,
                         framewidth = self.framewidth)
        for i in keepframes:
            newVid.addFrame(self.GetFrame(i))
        
        return newVid
    
    filename = property(fget=GetFilename, fset=SetFilename, doc="""Filename (string)""")
    framecount = property(fget=GetFrameCount, fset=SetFrameCount, doc="""Number of frames.""")
    frameheight = property(fget=GetFrameHeight, fset=SetFrameHeight, doc="""Height in pixels.""")
    framewidth = property(fget=GetFrameWidth, fset=SetFrameWidth, doc="""Width in pixels.""")
    currentframeidx = property(fget=GetCurrentFrameIdx,fset=SetCurrentFrameIdx,doc="""Set the current frame index""")
    currentframe = property(fget=GetCurrentFrame,doc="""returns the current frame as an hxwx1 np.array""")
    
if __name__ == '__main__':
    logger = logging.getLogger('AORegistration')
    formatter = logging.Formatter('%(module)s : %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)    
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug('XXXXXX')
    vid = AOVideo('../Data/sample_blinks.avi')
    vid_f = vid.FilterBlinks()
    pass