from overlord import *
from observer import *
from common import *

import os.path
import sys, getopt

def main(argv):        
    param_dir = ''
    # Accept command line argument -i
    try:
        opts, args = getopt.getopt(argv,'hi:o',['ifile='])
    except getopt.GetoptError:
        print 'Usage: overlord.py -i <parameter-directory>'
        sys.exit(2)
    for opt,arg in opts:
        if opt == '-h':
            print 'Usage: overlord.py -i <parameter-directory>'
            sys.exit()
        elif opt in ('-i','--ifile'):
            param_dir=arg.strip().replace(' ','')
        
    #print 'Input file is ', param_dir
    if param_dir != '' and os.path.exists(param_dir):
        param_files = [i for i in os.listdir(param_dir) if 'pkl' in i and 'param' in i]
        overlords = []
        
        print '\n\n==============================================='
        print '   Starting data load. Managing %s overlords.' % len(param_files)
        print '===============================================\n'
        # Load all overlords
        for param_f in param_files:
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