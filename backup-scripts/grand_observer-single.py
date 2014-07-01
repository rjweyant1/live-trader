#!/usr/bin/python

'''
This class follows one strategy...
need something more helpful here
'''

from common import *
from observer import *
from overlord import *
import numpy as np
from numpy import mean
import matplotlib.pyplot as plttet
from operator import itemgetter
import smtplib  # for email
from datetime import datetime
from itertools import groupby

# extra GMAIL accoint
fromaddr = 'krangfromdimensionx@gmail.com'
toaddrs  = 'robert.weyant@gmail.com'

username = 'krangfromdimensionx@gmail.com'
password = 'bqurtgboktfjkfyh'

results_dir = 'results/grandobserver-files/'

class GrandObserver:
    # constructor
    def __init__(self,source=None):
        '''
        '''
        # what do here?
        self.worth=[]
        self.percents_list = []
        self.action_list = []
        self.keys = []

        self.absolute_max = []
        self.orders = []
        self.order_time_index=[]
        self.actions = []   
        self.daily_maxes=[]
        self.daily_max_method=[]
        self.btc = 0.0
        self.usd = 1.0
        
    def loadData(self):
        ''' 
        '''
        # read in price data
        price_data = loadData('data/btc_usd_btce.txt')
        self.max_time = price_data[1,:].tolist()
        self.price = price_data[0,:].tolist()
        
        # initial load
        x = dict()
        
        # open up every daily_percent* file and add it in.
        # store it in temporary dictionary x, eventually into x_array
        results_listing = [result for result in os.listdir(results_dir)  if 'daily_percent' in result]
        print 'Loading %s daily percents.' % len(results_listing)
        for result in results_listing:
            with open(results_dir+result,'rb') as f:
                while True:
                    try:
                        tmp = pickle.load(f)
                        x = dict(x.items() + tmp.items())
                    except EOFError:
                        print 'Done Loading %s%s' % (results_dir,result)
                        break
        print '\n'
                
        # extract daily percent increase and action lists from temporary dictionary x
        for key in x.keys():
            self.keys.append(key)
            #print len(x[key][0]),len(x[key][1])
            self.percents_list.append(x[key][0].tolist())
            self.action_list.append(x[key][1].tolist())
            
        del x
        # make everything the same length
        #self.individual_time = [self.max_time[len(i)] for i in self.percents_list ]
        #self.individual_time_index = [len(i) for i in self.percents_list]
        self.individual_time = []
        self.individual_time_index = []
        for i in self.percents_list:
            try:
                curLen = len(i)
                if curLen == len(self.max_time): curLen = curLen - 1 
                self.individual_time.append(self.max_time[curLen])
                self.individual_time_index.append(curLen)
            except:
                print 'Problem with current overlord load. Skipping.'
                
        self.timeFrame=min(self.individual_time_index)
        
        current_max_method_index = -1
        # go through whole history and make historical trades.  
        # update 3 lists: orders, actions, absolute_max.
        for i in xrange(self.timeFrame):
            
            # if we are past the first entry, and action in (-1,1)
            # then place a historical order
            if current_max_method_index != -1 and self.action_list[current_max_method_index][i] != 0:
                curAction = self.action_list[current_max_method_index][i]
                self.orders.append(self.price[i])
                self.order_time_index.append(i)
                self.actions.append(curAction)
                if curAction == 1:  self.sell(i)
                if curAction == -1: self.buy(i)

            # max VALUE at current time
            current_slice = [line[i] for line in self.percents_list]
            current_max_value=max(current_slice)
                        
            # INDEX strategy that maximuzes
            current_max_method_index= current_slice.index(current_max_value)
            current_max_method = self.keys[current_max_method_index]
            self.daily_max_method.append(current_max_method)
            self.daily_maxes.append(current_max_value)
            # add max value
            self.absolute_max.append((current_max_value,current_max_method_index))


    def update(self):
        '''
        '''
        price_data = loadData('data/btc_usd_btce.txt')
        self.max_time = price_data[1,:].tolist()
        self.price = price_data[0,:].tolist()
        # find all short_daily_percent files
        results_listing = [result for result in os.listdir(results_dir)  if 'short_dp' in result]
        print 'Loading %s files.' % len(results_listing)
        
        # load all short_daily_percent info
        initial_load = []
        for result in results_listing:
            # multiple line files
            # id, time, parameters,daily profit, action
            with open(results_dir+result,'r') as f:
                for line in f:
                    (time,ma,md,smooth,percent,riseTol,lossTol,dp, action) = line.split(',')
                    newLine = (time,(ma,md,smooth,percent,riseTol,lossTol),dp, action)
                    initial_load.append(newLine)
        print 'Updating %s parameter sets.' % len(initial_load)
       
        # remove short_daily_percent files
        for result in results_listing:
            os.remove(results_dir+result)
        
        # sort new entries by time
        if len(initial_load) > 1:
            initial_load = sorted(initial_load , key=itemgetter(0))

        # find unique parameter sets
        parameterSets = set([line[1] for line in initial_load])

        # for each unique parameter set, update in order.        
        for params in parameterSets:
            currentUpdates = [line for line in initial_load if line[1] == params]
            # step through short_daily_percent info and see load it into grand-observer
            for line in currentUpdates:
                (time,parameters,daily_profit,action) = line
                time = float(time)
                action = int(action.strip())
                parameters = tuple([float(i) for i in parameters])
                current_method = self.keys.index(parameters)
                # if current time beyond last time point
                if time > self.individual_time[current_method]:
                    #print 'updating %s for %s' % (time, current_method)
                    self.individual_time_index[current_method] = self.max_time.index(time)
                    self.individual_time[current_method] = time
                    self.action_list[current_method].append(action)
                    self.percents_list[current_method].append(daily_profit)


        # make everything the same length
        oldTimeFrame = self.timeFrame
        # action_list is actually what's getting read into files
        L = [len(i) for i in self.action_list]
        self.timeFrame=min(self.individual_time_index+L)
        current_max_method_index = -1
        first = 0
        
        print 'Old Time Frame: ', datetime.fromtimestamp(self.max_time[oldTimeFrame]).strftime('%m-%d %H:%M:%S')
        print 'New Time Frame: ', datetime.fromtimestamp(self.max_time[self.timeFrame]).strftime('%m-%d %H:%M:%S')
        # if any action needs to be taken, alert.
        for i in xrange(oldTimeFrame, self.timeFrame):
            
            #if current_max_method_index != -1: print self.action_list[current_max_method_index][i]
            
            # if we are past the first entry, and action in (-1,1)
            # then place a historical order
            if current_max_method_index != -1 and self.action_list[current_max_method_index][i] != 0:
                curAction = self.action_list[current_max_method_index][i]
                self.orders.append(self.price[i])
                self.order_time_index.append(i)
                self.actions.append(curAction)
                if curAction == 1:  self.sell(i)
                if curAction == -1: self.buy(i)

            
            # max VALUE at current time
            current_slice = [line[i] for line in self.percents_list]
            current_max_value=max(current_slice)
            
            # INDEX strategy that maximuzes
            current_max_method_index= current_slice.index(current_max_value)
            current_max_method = self.keys[current_max_method_index]
            # add max value
            self.absolute_max.append((current_max_value,current_max_method_index))
        print '\n============================\n'

    def buy(self,time_index=None):
        ''' 
        This function simulates buying BTC with USD
        Right now, it exchanges all USD for BTC.
        '''
        
        currentPrice = self.price[self.order_time_index[-1]]
        if time_index == None:    
            currentTime = datetime.fromtimestamp(self.max_time[-1]).strftime('%Y-%m-%d %H:%M:%S')
        else: 
            currentTime = datetime.fromtimestamp(self.max_time[time_index]).strftime('%Y-%m-%d %H:%M:%S')
        print '***************************************'
        print '***************************************\n'            
        print 'Buy now.'
        print 'Current price is %s.' % currentPrice
        print 'Order time is %s.' % currentTime
        print '\n***************************************'
        print '***************************************\n'
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        
        msg = "\r\n".join([
          "From: user_me@gmail.com",
          "To: user_you@gmail.com",
          "Subject: *BUY* BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime),
          "",
          "BUY BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime)
          ])
          
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
       
    def sell(self,time_index=None):
        ''' 
        This function simulates selling BTC for USD
        Exchange ALL BTC for USD
        '''
        currentPrice = self.price[self.order_time_index[-1]]
        if time_index == None:    
            currentTime = datetime.fromtimestamp(self.max_time[-1]).strftime('%Y-%m-%d %H:%M:%S')
        else: 
            currentTime = datetime.fromtimestamp(self.max_time[time_index]).strftime('%Y-%m-%d %H:%M:%S')
            
        print '***************************************'
        print '***************************************\n'        
        print 'Sell now.'
        print 'Current price is %s.' % currentPrice
        print 'Order time is %s.' % currentTime
        print '***************************************'
        print '***************************************\n'
        
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        
        msg = "\r\n".join([
          "From: user_me@gmail.com",
          "To: user_you@gmail.com",
          "Subject: *SELL* BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime),
          "",
          "SELL BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime)
          ])
          
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()

        
    def step(self,price,time,backup=0):
        pass

    def current_profit(self,start=0):
        ''' 
        quick calculation of current profit status 
        based off of self.orders list
        includes fees
        trade_type  = -1 for buys ($/price)
                    =  1 for sells ($*price)
        *** would be nice to find a way to window this to past X days or something
        '''
        pass

    def profit(self):
        print 'Initial USD', self.usd
        lastOrder = 0
        profit_percent=1
        firstOrder = True
        for i in xrange(len(test.orders)):
            if self.actions[i] == lastOrder: pass
            else:
                if firstOrder and (lastOrder == 1 or lastOrder == 0): pass
                else:
                    print '=============='
                    # buy
                    if self.actions[i] == -1 and self.usd > 0:
                        print 'Current USD', self.usd
                        print 'Buying BTC @ ', self.orders[i]
                        newUSD = 0
                        newBTC = self.usd/self.orders[i]
                        # update
                        self.btc = newBTC
                        self.usd = newUSD
                    elif self.actions[i] == 1 and self.btc > 0:
                        print 'Current BTC', self.btc
                        print 'Selling BTC @ ', self.orders[i]
                        newBTC = 0
                        newUSD = self.btc*self.orders[i]
                        # update
                        self.btc = newBTC
                        self.usd = newUSD
                    new_profit = self.btc*self.orders[i] + self.usd
                    lastOrder = self.actions[i]
                    print 'simple profit: ', new_profit
                if self.actions[i] == -1:   firstOrder = False

def continuous_run():
    for i in xrange(2000):
        test.update()
        time.sleep(65)


best = [(150, 40, 10, 0.01, 0.05, 0.1), (100, 40, 10, 0.01, 0.15, 0.05), (60, 60, 5, 0.03, 0.15, 0.15), (150, 40, 1, 0.03, 0.15, 0.05), (150, 60, 5, 0.01, 0.15, 0.05), (100, 40, 5, 0.03, 0.05, 0.1), (40, 40, 10, 0.02, 0.15, 0.05), (40, 80, 10, 0.02, 0.05, 0.1), (100, 40, 10, 0.01, 0.05, 0.1), (60, 60, 1, 0.02, 0.15, 0.1), (100, 40, 10, 0.01, 0.15, 0.1), (60, 60, 1, 0.02, 0.15, 0.15), (150, 40, 10, 0.01, 0.05, 0.05), (100, 150, 1, 0.03, 0.05, 0.05), (100, 40, 1, 0.02, 0.1, 0.1), (100, 40, 10, 0.01, 0.05, 0.05)]
test = GrandObserver()
test.loadData()
continuous_run()

x = [(i,test.daily_max_method.count(i)) for i in set(test.daily_max_method)]
count = [test.daily_max_method.count(i) for i in set(test.daily_max_method)]


if False:
    best = open('results/overlord-files/full_backup_1140406060110101005005101501510050051.pkl','rb')
    bestObs = pickle.load(best)
    curbest = bestObs.workers[bestObs.workers.keys()[0]]
    (40, 60, 10, 0.05, 0.15, 0.05)
    getID(smooths=[10],mas = [40],mds=[60],percents =[.05],riseTols=[0.15],lossTols=[.05])
            