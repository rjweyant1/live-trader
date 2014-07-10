#!/usr/bin/python
'''
This class follows manages several observer classes...
need something more helpful here
'''
from observer import *
from common import *
import btceapi
import pickle
import time
from datetime import datetime
import os.path
import sys, getopt, shutil
from collections import deque
import csv
from trades import trades

from get_btce_price import *

# dirrectorys
overlord_dir = 'results/overlord-files/'
grandobs_dir = 'results/grandobserver-files/'

class overlord:
    # constructor
    def __init__(self,smooths=[],mas=[],mds=[],percents=[],riseTols=[],lossTols=[],historical_data='data/btc_usd_btce.txt'):
        self.mas = mas
        self.mds = mds
        self.smooths = smooths
        self.percents = percents
        self.riseTols = riseTols
        self.lossTols = lossTols
        
        self.workers = dict()       # blank
        self.curTime = 0
        
        n_mas = len(mas)
        n_mds = len(mds)
        n_smooths = len(smooths)
        n_percents = len(percents)
        n_riseTols = len(riseTols)
        n_lossTols = len(lossTols)
        
        self.numWorkers = n_mas*n_mds*n_smooths*n_percents*n_riseTols*n_lossTols
        self.data_source = historical_data
        self.price_data= loadData(data=historical_data) 
        self.firstTime = self.price_data[1][0]
        print '----'
        print self.price_data[1][0]
        print '----'
        self.getID()
        self.numSynched = 0

    def getID(self):
        min_mas,max_mas,len_mas = (str(min(self.mas)),str(max(self.mas)),str(len(self.mas)))
        min_mds,max_mds,len_mds = (str(min(self.mds)),str(max(self.mds)),str(len(self.mds)))
        min_smooths,max_smooths,len_smooths = (str(min(self.smooths)),str(max(self.smooths)),str(len(self.smooths)))
        min_precents,max_percents,len_percents = (str(min(self.percents)),str(max(self.percents)),str(len(self.percents)))
        min_rise, max_rise,len_rise = (str(min(self.riseTols)),str(max(self.riseTols)),str(len(self.riseTols)))
        min_loss,max_loss,len_loss = (str(min(self.lossTols)),str(max(self.lossTols)),str(len(self.lossTols)))
        
        tmp_id = len_mas+min_mas+max_mas+min_mds+max_mds+len_mds+min_smooths+max_smooths+len_smooths +min_precents+max_percents+len_percents +min_rise+ max_rise+len_rise +min_loss+max_loss+len_loss 
        self.id = str(self.numWorkers) + tmp_id.replace('.','')
        
    def initializeWorkers(self):
        '''
        initializes workers from scratch
        '''
        # how many initial data points to load so that moving windows are defined.
        initialLoadN = 2*max(max(self.mas),max(self.mds),max(self.smooths))
        
        # time this process
        timer= time.time()        
        # creates 7 dimensional array
        for ma in self.mas:
            for md in self.mds:
                for smooth in self.smooths:
                    for percent in self.percents:
                        for riseTol in self.riseTols:
                            for lossTol in self.lossTols:
                                curKey = (ma,md,smooth,percent,riseTol,lossTol)
                                
                                # visual to see that things are running.
                                print curKey
                                # initialize
                                self.workers[curKey] = observer(smooth,md,ma,percent,lossTol,riseTol)
                                
                                # take the first 100 points in data file
                                self.workers[curKey].loadData(self.price_data[0,0:initialLoadN ].tolist(),self.price_data[1,0:initialLoadN ].tolist())
                                
                                # cycle over the rest of the historical data
                                for i in xrange(initialLoadN,len(self.price_data[0,:])):
                                    self.workers[curKey].step(self.price_data[0,i],self.price_data[1,i])
        # Display how long the initialization took.
        duration = round((time.time() - timer)/60,1)
        print 'It took %s minutes to intiialize %s observer.  %s minutes per observer.' % (duration,self.numWorkers,round(duration/self.numWorkers,2))                                    

    def loadWorkers(self):  
        '''
        Loads Workers from backups
        '''
        pass

    def updateWorkers(self,price,time):
        '''
        updates each worker under this overlord's control
        '''
       
        # cycle through each worker, do 1-step for current (price,time)
        for key in self.workers.keys():
            self.workers[key].step(price,time)
            self.curTime = time

    def synchronizeData(self):
        '''
        after loading backup, check for new data in big file.
        '''
        try:    
            # Update data every time.
            collect_data()
            i = 0
            timer = time.time()
            self.price_data = loadData(self.data_source)
            orig_time = self.curTime
            for (price,new_time) in self.price_data.transpose():
                if new_time > self.curTime:
                    self.updateWorkers(price,new_time)
                    i = i+1
                    
            duration = round((time.time() - timer ) ,1)
            self.numSynched = i
            key = self.workers.keys()[0]
            #print summary
            print 'It took %s seconds to synchronize with current data' % round(duration,1)
            #print '%s prices updated.' % self.numSynched
            print 'Synchronized all values between %s and %s' % (datetime.fromtimestamp(orig_time ).strftime('%m-%d %H:%M'),datetime.fromtimestamp(new_time).strftime('%m-%d %H:%M'))
            
            parameterSummary =  '| SMOOTH:%s | MA:%s | MD:%s | PERCENT:%s | RISE:%s | LOSS:%s |'  % (self.workers[key].smooth,self.workers[key].ma,self.workers[key].md,self.workers[key].percent,self.workers[key].riseTolerance,self.workers[key].lossTolerance)
            parameterSummaryLine = '-'*len(parameterSummary)
            print '%s\n%s\n%s' % (parameterSummaryLine,parameterSummary,parameterSummaryLine)
            print 'Currently using %s values' % len(self.price_data[0])
            print 'Current BTC: %s' % round(self.workers[key].btc,3)
            print 'Current USD: %s' % round(self.workers[key].usd,2)
            percentDiff = (float(self.price_data[0][-1]) - float(self.workers[key].orders[-1][0])) / float(self.workers[key].orders[-1][0])
            print 'Current Profit: %s'  %   round(self.workers[key].current_worth[-1],3)
            print '%s orders executed' % len(self.workers[key].actions)
            print 'Last trade at %s at %s' % (round(self.workers[key].orders[-1][0],2), datetime.fromtimestamp(self.workers[key].orders[-1][1]).strftime('%Y-%m-%d %H:%M:%S'))
            for i in range(len(self.workers[key].orders)-10,len(self.workers[key].orders)):
                if self.workers[key].orders[i][2] == -1: orderType = 'Buy'
                if self.workers[key].orders[i][2] == 1: orderType = 'Sell'
                print '  Order %s: [%s] %s at %s' % (i+1,orderType,self.workers[key].orders[i][0],datetime.fromtimestamp(self.workers[key].orders[i][1]).strftime('%H:%M %m/%d/%Y'))
            print 'Current price: %s' % round(float(self.price_data[0][-1]),2)
            print 'Percent Difference: %s' % round(percentDiff,4)

            return True
        except:
            print 'Synchronization failed.'
            return False

    def quickBackup(self):            
        ''' 
        write out a file that has parameter list + windowd profits and total profit 
        '''
        #try:
        if True:
            quick_filename = 'short_status_'+self.id+'.txt'
            with open(overlord_dir+quick_filename,'w') as quick_file:
                for key in self.workers.keys():
                    line = str(self.workers[key].time[-1])+','+','.join([str(i) for i in key])+','+str(self.workers[key].current_worth[-1])+','+str(len(self.workers[key].orders))+'\n'
                    quick_file.write(line)
            
            # to prevent simultaneous read-write problems, create in different directory, copy over
            dp_filename = 'short_dp_'+self.id+'_'+str(int(self.workers[key].time[-1]))+'.txt'
            with open(overlord_dir + dp_filename,'w') as dp_file:
                for key in self.workers.keys():
                    for j in xrange(-1-self.numSynched,0):
                        line = str(self.workers[key].time[j])+','+','.join([str(i) for i in key])+','+str(self.workers[key].daily_percent_increase[j])+','+str(self.workers[key].actions[j])+'\n'
                        dp_file.write(line)
            shutil.copyfile(overlord_dir + dp_filename, grandobs_dir+dp_filename)
            
            order_sum_file='order_summary_'+self.id+'.txt'
            with open(overlord_dir+order_sum_file,'w') as order_file:
                order_file.write('number,type,price,time\n')
                for i in range(len(self.workers[key].orders)):
                    # order number, order type, price, time
                    order_file.write('%s,%s,%s,%s\n' % (i+1,self.workers[key].orders[i][2],self.workers[key].orders[i][0],int(self.workers[key].orders[i][1])))
            
            os.remove(overlord_dir + dp_filename)
            print 'Quick backup successful.'
            return True
        #except:
        if False:
            print 'Quick backup failed.'
            return False
    def fullBackup(self):
        '''
        writes the full overlord object, with all the historical data
        '''
        try:
            timer = time.time()
            # overwrite previous back-up
            full_backup_filename = 'full_backup_'+self.id+'.pkl'
            with open(overlord_dir+full_backup_filename,'wb') as full_backup:
                pickle.dump(self,full_backup)
            
            tmp_daily_percent = dict()
            for key in self.workers.keys():
                tmp_daily_percent[key]=np.array((self.workers[key].daily_percent_increase,self.workers[key].actions))
                
            # overwrite old daily-percent
            daily_filename = 'daily_percent_'+self.id+'.pkl'
            with open(grandobs_dir+daily_filename,'wb') as daily:
                pickle.dump(tmp_daily_percent,daily)
                
            duration = round((time.time() - timer ) / 60,1)
            print 'Full backup successful.  It took %s minutes to backup.' % duration
            return True
        except: 
            print 'Full backup failed.'
            return False
    def updatePrice(self):
        '''
        checks for a new price, and if it's new, update all workers
        '''
        try:
            # load new data file
            tmp_data = open('data/btc_usd_btce.tmp','r')
            for line in tmp_data:
                (pair,time,price) = line.split(',')
            
            # If the current time is new, then update
            if float(time) != self.curTime:
                self.curTime = float(time)             # new time = current time
                self.updateWorkers(float(price),float(time))  # update everyone
                
                #   True if updated
                return True                             
            
            #   False if not
            else:   return False                        
        except: return False

    def continuous_run(self,wait_time = 60, cycle_length = 60, load=False):
        '''
        continuously update this overlord's workers
        '''
        i = cycle_length
        while True:
            updated = self.synchronizeData()
            if updated: print 'Price updated at %s.' % datetime.now().strftime("%H:%M:%S on %m-%d-%Y")
            
            # Every 10 wait_times make a 'quick' update
            if i % 10 == 0:
                self.quickBackup()
            # every cycle make a full backup
            if i == 0 :
                self.fullBackup()
                i = cycle_length
            i = i-1
            # sleep 1 minute
            time.sleep(wait_time)

def loadOverlord(parmFile=None,fullBackup=False):
    '''
    check for backup, if it doesn't exist, load from scratch
    '''
    
    if parmFile != None:
        with open(parmFile,'rb') as parms:
            [smooths,mas,mds,percents,riseTols,lossTols] = pickle.load(parms)
                
        # what ID will be with this parameter set
        curID = getID(smooths,mas,mds,percents,riseTols,lossTols)
        backupName = overlord_dir+'full_backup_'+curID+'.pkl'
    
        # Check for backup
        if os.path.isfile(backupName):
            print 'Loading from backup.'
            with open(backupName,'rb') as backup:
                timer= time.time()
                curObj = pickle.load(backup)
                duration = round((time.time() - timer)/60,1)
                print 'It took %s minutes to load backup.' % (duration)
                # check for new data
                curObj.synchronizeData()
                if fullBackup: 
                    print 'Creating backup.'
                    curObj.fullBackup()
                curObj.quickBackup()
                duration = round((time.time() - timer)/60,1)
                print 'It took %s minutes to complete load and update.' % (duration)
                
        # else create new object
        else:   
            print 'Creating new overlord object.'

            curObj = overlord(smooths=smooths,mas=mas,mds=mds,percents=percents,riseTols=riseTols,lossTols=lossTols)    
            print curObj.id
            curObj.initializeWorkers()
            curObj.curTime=time.mktime(time.localtime())
            curObj.startTime=time.mktime(time.localtime())
            curObj.fullBackup()
            curObj.quickBackup()

        return curObj
    
    else:
        print 'Need parameter file.'
        return None


