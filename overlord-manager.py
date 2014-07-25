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
        options.direct_action
    '''
    usage = 'Usage: %prog [options] arg'
    parser = OptionParser(usage)
    # Parameter File
    parser.add_option('-p','--param-file',dest='param_file',
                      help='which paramter file to load',default=None)
    # Parameter Directory
    parser.add_option('-d','--param-dir',dest='param_dir',
                      help='which paramter file to load',default='parameters-lists')
    # Direct Action
    parser.add_option('-a','--direct-action',dest='direct_action',
                      help='if specific trade is wanted',default=None)                      
    (options,args) = parser.parse_args()

    return options

def main(argv):        
    #   Load command-line parameters
    options = loadParameters()
    (param_file,param_dir,direct_action) = (options.param_file,options.param_dir,options.direct_action)
    
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


        # execute action if asked to do so.
        if direct_action != None and os.path.exists(direct_action):
            with open(direct_action,'r') as action_file:
                price,action,amount = None,None,None
                for line in action_file:
                    if 'price' in line: price = float(line.strip().split('=')[1])
                    if 'action' in line:
                        if 'buy' in line:   action = int(line.strip().split('=')[1] == 'buy')
                        elif 'sell' in line:    action = 1-int(line.strip().split('=')[1] == 'sell')
                    if 'amount' in line: amount = float(line.strip().split('=')[1])
                if price!=None and action!=None and amount!=None:
                    firstKey=overlords[0].workers.keys()[0]
                    if action == 1 and overlords[0].workers[firstKey].usd >0:
                        overlords[0].workers[firstKey].buy()
                        print 'Bought!'
                        overlords[0].fullBackup()
                    elif action == 1 and overlords[0].workers[firstKey].usd == 0:
                        print 'Not enough USD to buy!'
                        
                    if action == 0 and overlords[0].workers[firstKey].btc >0:
                        overlords[0].workers[firstKey].sell()
                        print 'Sold!'
                        overlords[0].fullBackup()
                    elif action == 0 and overlords[0].workers[firstKey].btc == 0:
                        print 'Not enough BTC to sell!'
                        
            os.remove(direct_action)
        elif direct_action == None: pass                
        elif direct_action != None and not os.path.exists(direct_action):
            print 'Action file does not exist!\n Proceeding as normal'
            
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