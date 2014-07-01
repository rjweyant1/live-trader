#!/usr/bin/python

'''
This class follows one strategy...
need something more helpful here
'''

from common import *
import numpy as np
from numpy import mean
import matplotlib.pyplot as plt


class observer:
    # constructor
    def __init__(self,smooth=1,md=1,ma=1,percent=0.1,lossTolerance=0.1,riseTolerance=0.1,method=1):
        self.n = 0
        self.btc = 0
        self.usd = 1
        self.current_worth = [1]
        self.daily_raw_increase = []
        self.daily_percent_increase = []
        self.smooth=smooth
        self.md = md
        self.ma = ma
        self.percent=percent
        self.lossTolerance = lossTolerance
        self.riseTolerance = riseTolerance
        self.orders=np.array([])
        self.lastBuy = -9999
        self.lastSell = 9999
        self.BUYFEE = 0.002
        self.SELLFEE = 0.002
        
        self.depth = 2*max(self.smooth,self.ma,self.md)
        
        self.actions = []
        
    def loadData(self,price,time):
        ''' 
        loads price/time from lists 
        '''
        # initial load
        self.price = price
        self.time = time
        
        # smoothing
        self.price_smooth = moving_average(self.price,self.smooth)
        self.d1 = moving_derivative(self.price_smooth,self.time,self.md)
        self.d1_smooth = moving_average(self.d1,self.ma)
        self.n = len(self.price)-1
        
        # move starting btc and usd forward
        #self.btc = self.btc*(self.n+1)
        #self.usd = self.usd*(self.n+1)
        self.current_worth = (np.array(self.btc*(self.n+1))*np.array(self.price) + np.array(self.usd*(self.n+1))).tolist()
        self.actions = [0]*(self.n+1)
        self.daily_percent_increase = [0]*(self.n+1)
        

    def update(self,price,time):
        '''
        Given a single price/time pair, this updates the data set 
        '''
        
        # drop old data -- resize list 
        if self.n > self.depth:
            self.price = self.price[-self.depth:]
            self.price_smooth = self.price_smooth[-self.depth:]
            self.d1 = self.d1[-self.depth:]
            self.d1_smooth = self.d1_smooth[-self.depth:]
            #self.time = self.time[-self.depth:]
        
        self.price.append(price)
        self.time.append(time)
        #self.btc.append(self.btc[self.n])
        #self.usd.append(self.usd[self.n])
        self.n=self.n+1
        
        # update price, derivatives and smooth functions
        # only look at last window.
        self.price_smooth.append(mean(self.price[-self.smooth:]))
        self.d1.append(get_slope(self.price_smooth[-self.md:],self.time[-self.md:]))
        self.d1_smooth.append(mean(self.d1[-self.ma:]))

        
    def check_current_extreme(self):
        ''' 
        Identify if the CURRENT price shows evidence of a minimum or maximum.
        Also checks if an apparent previous execution was premature (SAFEGUARD)        
        '''

        # CHECK IF LAST D1 WAS NEGATIVE AND CURRENT D1 IS POSITIVE 
        # AND THE PRICE HAS DECREASED BY A CERTAIN PERCENT SINCE LAST SELL
        # also requires that number of dollars is positive -- as in the last action was a SELL
        if self.d1_smooth[-2] <0 and self.d1_smooth[-1] >0 and self.price[-1] < (1-self.percent)*self.lastSell and self.usd > 0:
            #print 'Buy\t', round(self.lastSell,1),round(self.price[self.n],1)
            self.buy()
            
        # CHECK IF LAST D1 IS POSITIVE AND CURRENT D1 IS NEGATIVE
        # AND THE PRICE HAS INCREASED BY A CERTAIN PERCENT SINCE LAST BUY
        # also requires that number of BTC is positive -- as in last action was a BUY
        elif self.d1_smooth[-2]>0 and self.d1_smooth[-1]<0 and self.price[-1] > (1+self.percent)*self.lastBuy and self.btc>0:
            #print 'Sell\t', round(self.lastBuy,1), round(self.price[self.n],1)
            self.sell()

        #### SAFE GUARDS -- RISK TOLERANCE ####
        # if we dip below our risk tolerance, sell.
        elif self.price_smooth[-1] < (1-self.lossTolerance)*self.lastBuy and self.btc>0:
            #print 'BOUGHT at %s and price is now %s Still going down, SELLING' % (round(self.lastBuy,1),round(self.price[self.n],1))
            self.sell()

        # if the price keeps going up after peak, then buy?
        # I have not seen evidence of this happening, and actually acting on it seems slightly harder to implement.
        elif self.price_smooth[-1]>(1+self.riseTolerance)*self.lastSell and self.usd>0:
            #print 'SOLD at %s and price is now %s Still going up, BUYING' % (round(self.lastSell,1),round(self.price[self.n],1))
            self.buy()

        else:
            self.actions.append(0)

    def buy(self):
        ''' 
        This function simulates buying BTC with USD
        Right now, it exchanges all USD for BTC.
        '''
        
        # These are temporary amounts calculated before updating 
        newUSD = 0
        newBTC = exchange_usd_to_btc(self.usd*(1-self.BUYFEE),self.price[-1])
        
        #    reset new last-buy price.
        self.lastBuy=self.price[-1]
        self.lastSell=9999        

        # set all future values to current value
        self.btc = newBTC
        self.usd = newUSD
        
        # stores price, time and -1 for buys.
        # use -1 to summarize final status (raise to -1 power)
        if self.orders.size == 0:
            self.orders = np.array([[self.price[-1],self.time[-1],-1]])
        elif self.orders.size > 0:
            self.orders = np.concatenate([self.orders,np.array([[self.price[-1],self.time[-1],-1]])])
            
        self.actions.append(-1)
        
    def sell(self,ALERT=False, EXECUTE=False):
        ''' 
        This function simulates selling BTC for USD
        Exchange ALL BTC for USD
        '''
        # These are temprorary amounts calculated before updating.
        newUSD = exchange_btc_to_usd(self.btc*(1-self.SELLFEE),self.price[-1])
        newBTC = 0
        
        # Set last sell in case price keeps increasing.
        self.lastSell=self.price[-1]
        self.lastBuy=-9999
        
        # change all future values
        self.btc = newBTC
        self.usd = newUSD
        
        # stores price, time and -1 for buys.
        # use -1 to summarize final status (raise to 1 power)
        if self.orders.size == 0:
            self.orders = np.array([[self.price[-1],self.time[-1],1]])
        elif self.orders.size > 0:
            self.orders = np.concatenate([self.orders,np.array([[self.price[-1],self.time[-1],1]])])

        self.actions.append(1)
        
    def step(self,price,time,backup=0):
        # update current price/time
        self.update(price,time)
        
        # Check if evidence that price is currently at a minimum or maxmium
        # Execute theoretical trade at this point.
        self.check_current_extreme()
        
        # update current worth based on current BTC and USD amounts
        self.current_worth.append(self.btc*self.price[-1] + self.usd)
        daily_raw_increase,daily_percent_increase = self.moving_worth(i=1440)
        self.daily_raw_increase.append(daily_raw_increase)
        self.daily_percent_increase.append(daily_percent_increase)
        
    def moving_worth(self,i=1440):
        '''
        '''
        if len(self.time) > i:
            raw_increase = (self.current_worth[-1] - self.current_worth[-i])
            percent_increase = raw_increase / self.current_worth[-i]
        else:
            raw_increase = (self.current_worth[-1] - self.current_worth[0])
            percent_increase = raw_increase / self.current_worth[0]
            
        return raw_increase,percent_increase

    def current_profit(self,start=0):
        ''' 
        quick calculation of current profit status 
        based off of self.orders list
        includes fees
        trade_type  = -1 for buys ($/price)
                    =  1 for sells ($*price)
        *** would be nice to find a way to window this to past X days or something
        '''
        profit_percent = 1
        trade_sum=0
        for (price,date,trade_type) in self.orders:
            if date >= start:
                profit_percent = profit_percent*((trade_type == -1) * (1-self.BUYFEE) + (trade_type == 1) * (1-self.SELLFEE)) * price**trade_type
                trade_sum = trade_sum+trade_type
        print last_trade
        if last_trade == -1:
            profit_percent = profit_percent*self.price[-1]
        return profit_percent
