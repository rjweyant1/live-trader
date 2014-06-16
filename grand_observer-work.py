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
import btceapi

# extra GMAIL accoint
fromaddr = 'krangfromdimensionx@gmail.com'
toaddrs  = 'robert.weyant@gmail.com'

username = 'krangfromdimensionx@gmail.com'
#password = 'bqurtgboktfjkfyh'
password = 'lcawhlwrmodhtmse'

results_dir = 'results/grandobserver-files/'
key_file = 'btce-api-key.txt'

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
        self.update_funds()
        
    def update_funds(self):
        try:        
            handler = btceapi.KeyHandler(key_file, resaveOnDeletion=True)
            key = handler.getKeys()[0]
    
            conn = btceapi.BTCEConnection()
            t = btceapi.TradeAPI(key, handler)

            r = t.getInfo(connection = conn)
            self.actual_btc = getattr(r, "balance_btc")
            self.actual_usd = getattr(r, "balance_usd")
        except: 
            self.actual_btc = -999
            self.actual_usd = -999

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
                if curAction == 1:  self.sell(realSell=False,time_index = i)
                if curAction == -1: self.buy(realBuy=False,time_index=i)

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
        #print 'Current Parameter set: MA:%s, MD:%s, SMOOTH:%s, PERCENT:%s, RISE:%s, LOSS:%s' % (initial_load[-1][1]) 
       
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
        L = [len(k) for k in self.action_list]
        self.timeFrame=min(self.individual_time_index+L)
        current_max_method_index = 0
        
        print 'Old Time Frame: ', datetime.fromtimestamp(self.max_time[oldTimeFrame]).strftime('%m-%d %H:%M:%S')
        print 'New Time Frame: ', datetime.fromtimestamp(self.max_time[self.timeFrame]).strftime('%m-%d %H:%M:%S')
        # if any action needs to be taken, alert.
        for index in xrange(oldTimeFrame, self.timeFrame):
            # if action in (-1,1)
            # then place a real order
            curAction = self.action_list[current_max_method_index][index]
            #print 'Current Time: ' , datetime.fromtimestamp(self.max_time[index]).strftime('%Y-%m-%d %H:%M:%S')
            print 'Current Action:', curAction
            #print 'current_max_method_index:', current_max_method_index
            #print 'len(action_list):', len(self.action_list[current_max_method_index])
            #print 'sum(action_list):', sum([abs(i) for i in self.action_list[current_max_method_index]])
            if curAction != 0:
                self.orders.append(self.price[index])
                self.order_time_index.append(index)
                self.actions.append(curAction)
                if curAction > 0:  self.sell(realSell=True,time_index=index)
                if curAction < 0: self.buy(realBuy=True,time_index=index)
            elif curAction == 0:
                print 'No action currently.'
            
        print self.summary_string()
        print '\n\n'

    def buy(self,realBuy=False,time_index=None):
        ''' 
        This function simulates buying BTC with USD
        Right now, it exchanges all USD for BTC.
        '''
        
        currentPrice = self.price[self.order_time_index[-1]]
        if time_index == None:    
            currentTime = datetime.fromtimestamp(self.max_time[-1]).strftime('%Y-%m-%d %H:%M:%S')
        else: 
            currentTime = datetime.fromtimestamp(self.max_time[time_index]).strftime('%Y-%m-%d %H:%M:%S')
        # update

        self.btc = self.usd*(1-0.002)/float(currentPrice)
        self.usd = 0

        print '***************************************'
        print '***************************************\n'            
        print 'Buy now.'
        print 'Current price is %s.' % currentPrice
        print 'Order time is %s.' % currentTime

        if realBuy:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            
            msg = "\r\n".join([
              "From: krangfromdimensionx@gmail.com",
              "To: robert.weyant@gmail.com",
              "Subject: *BUY* BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime),
              "",
              "BUY BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime)
              ])
              
            server.login(username,password)
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
            
            self.update_funds()
            
            handler = btceapi.KeyHandler(key_file, resaveOnDeletion=True)
            for key in handler.getKeys():
                print "Printing info for key %s" % key
                t = btceapi.TradeAPI(key, handler)
                print self.actual_usd
                print float(self.actual_usd) != -999 and float(self.actual_usd) > 0
                # trade if no problem with price update
                if float(self.actual_usd) != -999 and float(self.actual_usd) > 0:
                    print 'Making trade at %s,%s' % (currentPrice,float(self.actual_usd)*0.5)
                    self.lastBuy = t.trade('btc_usd','buy',float(currentPrice),(float(self.actual_usd)/currentPrice))
                    print self.lastBuy
        
        else:
            print '\nHistorical Alert Only.\n'
            
        print '\n***************************************'
        print '***************************************\n'    
        
        
    def sell(self,realSell=False,time_index=None):
        ''' 
        This function simulates selling BTC for USD
        Exchange ALL BTC for USD
        '''
        currentPrice = self.price[self.order_time_index[-1]]
        if time_index == None:    
            currentTime = datetime.fromtimestamp(self.max_time[-1]).strftime('%Y-%m-%d %H:%M:%S')
        else: 
            currentTime = datetime.fromtimestamp(self.max_time[time_index]).strftime('%Y-%m-%d %H:%M:%S')
        # update    
        self.usd = self.btc*float(currentPrice)*(1-0.002)
        self.btc = 0
        
        print '***************************************'
        print '***************************************\n'        
        print 'Sell now.'
        print 'Current price is %s.' % currentPrice
        print 'Order time is %s.' % currentTime

        
        if realSell:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            
            msg = "\r\n".join([
              "From: krangfromdimensionx@gmail.com",
              "To: robert.weyant@gmail.com",
              "Subject: *SELL* BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime),
              "",
              "SELL BTC @ " + str(currentPrice) + '. Action time is: ' + str(currentTime)
              ])
              
            server.login(username,password)
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
            
            self.update_funds()
            
            handler = btceapi.KeyHandler(key_file, resaveOnDeletion=True)
            for key in handler.getKeys():
                print "Printing info for key %s" % key
                t = btceapi.TradeAPI(key, handler)
                print self.actual_usd
                print float(self.actual_usd) != -999 and float(self.actual_btc) > 0
                # trade if no problem with price update
                if float(self.actual_btc) != -999 and float(self.actual_btc) > 0:
                    #self.lastSell = t.trade('btc_usd','sell',1000.0,self.actual_btc)
                    self.lastSell = t.trade('btc_usd','sell',float(currentPrice),float(self.actual_btc))            
                    print self.lastSell
                        
        else:
            print '\nHistorical Alert Only.\n'
            
        print '***************************************'
        print '***************************************\n'

    def summary_string(self):
        
        self.update_funds()
        RawDiff = round((float(self.price[-1]) - float(self.orders[-1])),3)
        percentDiff = 100*round((float(self.price[-1]) - float(self.orders[-1])) / float(self.orders[-1]),3)     
        if percentDiff < 0: percentDirection = '-'
        elif percentDiff > 0: percentDirection = '+'
        else:    percentDirection = '+'

        DailyPriceData = self.price[-1440:]
        dailyChangeDifference = round((float(self.price[-1]) - float(self.price[-1440])),3)
        dailyChangePercent = 100*round((float(self.price[-1]) - float(self.price[-1440])) / float(self.price[-1]),3)
        DailyMin,DailyMax = min(self.price[-1440:]),max(self.price[-1440:])
        if dailyChangeDifference < 0: DailyDirection = '-'
        elif dailyChangeDifference > 0: DailyDirection = '+'    
        else:   DailyDirection = '+'
        
        TwelveHPriceData = self.price[-720:]
        TwelveHChangeDifference = round((float(self.price[-1]) - float(self.price[-720])),3)
        TwelveHChangePercent = 100*round((float(self.price[-1]) - float(self.price[-720])) / float(self.price[-1]),3)
        TwelveHMin,TwelveHMax = min(self.price[-720:]),max(self.price[-720:])
        if TwelveHChangeDifference < 0: TwelveHDirection = '-'
        elif TwelveHChangeDifference > 0: TwelveHDirection = '+'
        else: TwelveHDirection = '+'
        
        OneHPriceData = self.price[-60:]
        OneHChangeDifference = round((float(self.price[-1]) - float(self.price[-60])),3)
        OneHChangePercent = 100*round((float(self.price[-1]) - float(self.price[-60])) / float(self.price[-1]),3)
        OneHMin,OneHMax = min(self.price[-60:]),max(self.price[-60:])
        if OneHChangeDifference <= 0: OneHDirection = '-'
        elif OneHChangeDifference >= 0: OneHDirection = '+'        
        else:   OneHDirection = '+'
        
        lastTradeTime = datetime.fromtimestamp(self.max_time[self.order_time_index[-1]])
        currentTime = datetime.now()
        timeBetween = currentTime - lastTradeTime
        daysBetween = timeBetween.days
        hoursBetween = round(timeBetween.seconds / 60.0**2,1)
      
        summary = ''
        summary += '***************************************\n***************************************\n'        
        summary +=  'Current Time: %s\n' % currentTime.strftime('%H:%M %m/%d/%Y')
        summary += 'Last trade at %s -- %s days, %s hours ago.\n' %  (lastTradeTime.strftime('%H:%M %m/%d/%Y'),daysBetween,hoursBetween)
        summary += 'Order summary\n=============\n'
        for i in range(len(self.orders)-10,len(self.orders)):
            if self.actions[i] == -1: orderType = 'Buy'
            if self.actions[i] == 1: orderType = 'Sell'        
            summary += '  Order %s:[%s] %s at %s\n' % (i+1,orderType,self.orders[i],datetime.fromtimestamp(self.max_time[self.order_time_index[i]]).strftime('%H:%M %m/%d/%Y'))
        summary += '=============\n'
        summary += 'Theoretical BTC: %s\nTheoretical USD: %s\n' % (round(self.btc,4),round(self.usd,3))
        summary += 'Actual BTC: %s\nActual USD: %s\n' % (self.actual_btc,self.actual_usd)
        summary += 'Current Profit: %s\n%s orders executed\n' % (self.profit(), len(self.orders))
        summary += 'Current price: $%s\nDifference: %s$%s (%s%s %%)\n' % (self.price[-1],percentDirection,RawDiff,percentDirection,percentDiff)
        summary += '1 hour change: %s$%s (%s%s %%) [$%s - $%s]\n' % (OneHDirection,abs(OneHChangeDifference),OneHDirection,abs(OneHChangePercent),OneHMin,OneHMax)
        summary += '12 hour change: %s$%s (%s%s %%) [$%s - $%s]\n' % (TwelveHDirection,abs(TwelveHChangeDifference),TwelveHDirection,abs(TwelveHChangePercent),TwelveHMin,TwelveHMax)
        summary += '24 hour change: %s$%s (%s%s %%) [$%s - $%s]\n' % (DailyDirection,abs(dailyChangeDifference),DailyDirection,abs(dailyChangePercent),DailyMin,DailyMax)
        summary += '***************************************\n***************************************\n'        

        return summary

    def send_daily_update(self):
        ''' 
        This function simulates selling BTC for USD
        Exchange ALL BTC for USD
        '''
        currentPrice = self.price[self.order_time_index[-1]]
        
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        
        msg = "\r\n".join([
          "From: krangfromdimensionx@gmail.com",
          "To: robert.weyant@gmail.com",
          "Subject: *DAILY UPDATE* BTC @ " + str(self.price[-1]) + '. Current time is: ' + str(datetime.now()),
          "",
          self.summary_string()
          ])
        
          
          
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        
        self.update_funds()
            
        print 'Daily Update Sent.'
    
    def test_mail(self):
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        
        msg = "\r\n".join([
          "From: krangfromdimensionx@gmail.com",
          "To: robert.weyant@gmail.com",
          "Subject: *SELL* BTC @   Action time is: ",
          "",
          "SELL BTC @ "
          ])
          
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        
    def step(self,price,time,backup=0):
        pass


    def profit(self):
        #print 'Initial USD', self.usd
        new_profit = self.btc*self.price[-1] + self.usd

        return round(new_profit,4)

def main():
    foundToday = False
    live_observer = GrandObserver()
    live_observer.loadData()
    while True:
        live_observer.update()
        current_time = datetime.now()
        # Somewhere around 6:30 PM send an email
        # Window given incase there are any hangups.
        if (current_time.hour == 18 or current_time.hour == 6) and 25 < current_time.minute < 35 and not foundToday :
            #send email update
            live_observer.send_daily_update()
            foundToday = True

        if (current_time.hour == 7 or current_time.hour == 19) and foundToday:
            foundToday = False
        time.sleep(65)        
        
        
if __name__=='__main__':
    main()