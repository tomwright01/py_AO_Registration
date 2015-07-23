import logging
import argparse
import os
import cv2
import numpy as np
import scipy.misc

class ProcessedVideo():
    '''Class for a registered AO video'''
    def __init__(self,**kwargs):
        '''
        Inputs:
        path: path to the folder containing the npz files'''

        self.frames = None
        self.path = None
        self.nFrames = 0 
        self.correlations = []
        self.curFrameIdx = -1
        self.frameheight = None
        self.framewidth = None
        
        if kwargs.has_key('path'):
            self.loadFrames(kwargs['path'])
    
    def __iter__(self):
        self.curFrameIdx = -1
        return self
    
    def next(self):
        self.curFrameIdx += 1
        if self.curFrameIdx >= self.nFrames:
            self.curFrameIdx = -1
            raise StopIteration
        return self.currentframe

    def GetCurrentFrame(self):
        #return the current frame as ndarray
        return(self.frames[:,:,self.curFrameIdx])

    def loadFrames(self,path):
        self.path = path

        self.files = [myfile for myfile in os.listdir(path) if os.path.splitext(myfile)[1] == '.npz']
        self.nFrames = len(self.files)        
        for filename in self.files:
            self._loadFrame(os.path.join(self.path,filename))
            
    def _loadFrame(self,file):
        data = np.load(file)
        if self.frames is None:
            self.frames = np.empty((data['newimg'].shape[0],
                                    data['newimg'].shape[1],
                                    self.nFrames))
            self.frameheight = data['newimg'].shape[0]
            self.framewidth = data['newimg'].shape[1]
        try:
            frameidx = data['frameidx']
        except KeyError:
            frameidx = int(os.path.basename(file)[11:-4])
            
        self.frames[:,:,frameidx] = data['newimg']
        self.correlations.append((frameidx,data['correlations']))
        self.curFrameIdx += 1
        
    def writeVideo(self,fname):
        h,w,s = self.frames.shape
        vid = cv2.VideoWriter(filename=fname,fourcc=0,fps=30,frameSize=(w,h),isColor=0)
        for iframe in range(self.nFrames):
            vid.write(np.uint8(self.frames[:,:,iframe]))
        vid.release()
        
        
    currentframe = property(fget=GetCurrentFrame)
if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description='Reassemble *.npz files into a movie')   
    parser.add_argument('source_dir',help="Path to the source directory")
    parser.add_argument('target_file',help="Path to the out")
    
    args=parser.parse_args()
    
    newVid = ProcessedVideo(path=args.source_dir)
    newVid.writeVideo(args.target_file)
