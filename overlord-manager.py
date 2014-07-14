from overlord import *
from observer import *
from common import *

import os.path
import sys, getopt
from optparse import OptionParser

def loadParameters():
    '''
        options.param_file
        options.param_dir
    '''
    usage = 'Usage: %prog [options] arg'
    parser = OptionParser(usage)
    # Parameter File
    parser.add_option('-p','--param-file',dest='param_file',
                      help='which paramter file to load',default=None)
    # Parameter Directory
    parser.add_option('-d','--param-dir',dest='param_dir',
                      help='which paramter file to load',default='parameters-lists')
                      
    (options,args) = parser.parse_args()

    return options

def main(argv):        
    #   Load command-line parameters
    options = loadParameters()
    (param_file,param_dir) = (options.param_file,options.param_dir)
    
    # enough files specified exist, then continue
    if param_dir != '' and os.path.exists(param_dir) and (param_file == None or os.path.exists(param_file) or os.path.exists(param_dir+'/'+param_file)):
        # list all .pkl files in param_dir
        param_files = [i for i in os.listdir(param_dir) if 'pkl' in i and 'param' in i]
        overlords = []
        
        print '\n\n==============================================='
        if param_file == None: print '   Starting data load. Managing %s overlords.' % len(param_files)
        elif param_file != None: print '   Starting data load. Managing %s overlords.' % 1
        print '===============================================\n'
        # Load all overlords
        for param_f in param_files:
            # if one single file is NOT specified
            if param_file == None:
                overlords.append(loadOverlord(parmFile=param_dir+'/'+param_f,fullBackup=True))
            # if file specified contains directory 
            elif param_file != None and param_file == param_dir+'/'+param_f:
                overlords.append(loadOverlord(parmFile=param_dir+'/'+param_f,fullBackup=True))
            # if file specified is just the file name, iwthout the directory
            elif param_file != None and param_f == param_file:
                overlords.append(loadOverlord(parmFile=param_dir+'/'+param_f,fullBackup=True))
                
        print '\n==========================='
        print 'Starting continuous update.'
        print '===========================\n'
        i=0
        # update all overlords
        while True:
            i = i + 1
            roundTimer = time.time()
            if i % 10 == 0:
                print '\n====================================================';
                print 'Round %s.  Backing up all runs.  Will take longer.' % i
                print '====================================================';
            for j in xrange(len(overlords)):
                try:
                    print 'Updating overlord.  First data point at %s' % datetime.fromtimestamp(overlords[j].firstTime).strftime('%m-%d-%y %H:%M')
                    print 'Overlord started at %s' % datetime.fromtimestamp(overlords[j].startTime).strftime('%m-%d %H:%M')
                    overlords[j].synchronizeData()
                    overlords[j].quickBackup()
                    overlords[j].fullBackup()
                except:
                    print 'Problem in object %s during round %s' % j,i
                
            roundDuration = round(time.time() - roundTimer,1)
            waitTime = round(max(65-roundDuration,0),1)
            print 'Round took %s seconds.  Will be waiting %s seconds.' % (roundDuration, waitTime)
            print '\n=========================================================\n'                    
            time.sleep(waitTime)

            
    else: 
        print 'File does not exist!'   
        print len(param_dir)
        sys.exit()


if __name__=='__main__':
    # send command line args to main
    main(sys.argv[1:])        