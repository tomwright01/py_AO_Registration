import logging
import numpy as np
import scipy.signal
import scipy.interpolate
import scipy.fftpack

import threading
import Queue
logger = logging.getLogger('AORegistration.AOVideo')


class RegisterMovie():
    """Class for NCC frame registration"""
    def __init__(self,filename):
        self.loadArray(filename)
        
    def loadArray(self,fname):
        """Loads an ndarray binary save file
        inputs:
        fname - path to an npz file with keys frames and keyframe"""
        try:
            data=np.load(fname)
        except e:
            logger.error('Failed loading file:{0} with error:{1}'.format(fname,str(e)))
            raise IOError
        self.data = data['data']
        self.key_frame = data['key_frame']
        
    def launchThreads(self):
        q = Queue.Queue()
        
        if len(self.data.shape) < 3:
            nFrames = [0,]
        else:
            nFrames = xrange(self.data.shape[2])
        
        for i in nFrames:
            t = ThreadedFrame(q, self.data[:,:,self.key_frame], 64)
            t.setDaemon(True)
            t.start()
            
        for iFrame in nFrames:
            q.put((iFrame,self.data[:,:,iFrame]))
            
        q.join()
            
        
class ThreadedFrame(threading.Thread):
    """Threaded frame processing"""
    def __init__(self,queue,keyframe,nstrips):
        """
        queue object containing frames as ndarrays
        keyframe ndarray containing the keyframe
        nstrips int number of strips in each frame
        """
        threading.Thread.__init__(self)
        self.queue = queue
        self.keyframe = keyframe
        self.nstrips = nstrips
        
    def run(self):
        #grab the frame from the queue
        item = self.queue.get()
        self.frameidx = item[0]
        self.framedata = item[1]
        self.proc_frame()
        self.queue.task_done()
        
    def proc_frame(self):
        logger.debug('Processing frame:%s',self.frameidx)
        strip_idx = np.linspace(start=0,stop=self.framedata.shape[0],num=self.nstrips+1).round()
        xshifts=[]
        yshifts=[]
        yshifts_centered=[]
        for iloc in xrange(len(strip_idx)-1):
            logger.debug('Frame %s, strip %s',self.frameidx,iloc)
            #Calculate the padding required
            t_pad = b_pad = max_pad = 30
            t_line = strip_idx[iloc] - max_pad
            if t_line < 0:
                t_pad = max_pad - (max_pad-strip_idx[iloc])
                
            
            b_line = strip_idx[iloc+1] + max_pad
            b_pad = max_pad
            if b_line > self.framedata.shape[0]:
                b_pad = max_pad - (b_line - self.framedata.shape[0])
            
            #Create the test strip and the template
            strip = self.framedata[strip_idx[iloc]:strip_idx[iloc+1],100:-100] 
            template = self.keyframe[strip_idx[iloc] - t_pad:strip_idx[iloc+1]+b_pad,:] 

            #normalise the strip and template
            strip=strip-strip.mean()
            template=template-template.mean()
            
            #perform the correlation
            corr = scipy.signal.correlate2d(template, strip, mode='same')
            y,x = np.unravel_index(np.argmax(corr),corr.shape)
            
            #Calculate the x,y shifts
            x = x  -template.shape[1]/2
            y = y - t_pad - ((template.shape[0] - (t_pad+b_pad))/2)
            
            xshifts.append(x)
            yshifts.append(y)
            
            strip_center= strip_idx[iloc] + ((strip_idx[iloc+1] - strip_idx[iloc])/2)

            yshifts_centered.append(y+strip_center)
            
        newimg = self.rebuildFrame(xshifts, yshifts_centered)
        
        np.savez('createdFile{0}.npz'.format(self.frameidx),
                 strip_center = strip_center,
                 xshifts=xshifts,
                 yshifts=yshifts,
                 yshifts_centered=yshifts_centered,
                 newimg=newimg)
        logger.debug('Done processing frame:%s',self.frameidx)

    def rebuildFrame(self, xshifts, yshifts, transform=False):
        logger.debug('rebuilding frame: %s',self.frameidx)
        if transform:
            #calculate the cosine transform
            transform_x = scipy.fftpack.dct(np.float64(xshifts),type=2,norm='ortho')
            transform_y = scipy.fftpack.dct(yshifts,type=2,norm='ortho')        
            #and back again
            #there could be a filterstep here
            fit_x = scipy.fftpack.idct(transform_x,norm='ortho')
            fit_y = scipy.fftpack.idct(transform_y,norm='ortho')        
        else:
            fit_x = xshifts
            fit_y = yshifts
            
        #create interpolation functions
        old_x = np.linspace(0,self.framedata.shape[0] - 1,len(fit_y))
        new_x = np.arange(self.framedata.shape[0])
        
        fy = scipy.interpolate.InterpolatedUnivariateSpline(x=old_x,y=fit_y)
        fx = scipy.interpolate.InterpolatedUnivariateSpline(x=old_x,y=fit_x)        

        #create an array with the new x,y indices
        idx = np.empty((1024,1000,2))
        idx[:] = np.NAN
        
        for y in range(1024):
            for x in range(1000):
                idx[y,x,0]=fy(y)
                idx[y,x,1]=fx(y) + x  
                
        #resample with the new indices
        newimg = scipy.ndimage.interpolation.map_coordinates(self.framedata,
                                                             [idx[:,:,0].ravel(),idx[:,:,1].ravel()],
                                                             order=1)
        newimg=newimg.reshape((1024,1000))
        logger.debug('done rebuilding frame: %s',self.frameidx)        
        return newimg
    
if __name__ == '__main__':
    logger = logging.getLogger('AORegistration')
    formatter = logging.Formatter('%(module)s : %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)    
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug('XXXXXX')
    r = RegisterMovie('/home/tom/Documents/Projects/AO_Registration/Data/2frames.npz')
    r.launchThreads()