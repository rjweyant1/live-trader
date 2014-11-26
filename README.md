live-trader
===========
This program was designed to monitor BTC/USD Price and trade at local minima and maxima.  
The strategy is to fit a regression line in a moving window to estimate the derivative of 
the price function.  If the regression coefficient goes from below 0 to above 0 in two 
consecutive minutes, or above 0 to below, then we are at an extrema.
It is designed to take a variety of inputs, such as window size, and other tolerances to
prevent overactive trading due to high volatility times.  

The monitoring of the price happens in the observer.py, under a give set of parameters.  

overlord.py is designed take  a small set of observer objects and update and manage
them in sequence.  Additionally, this class collects price data.

overlord-manager.py is designed as a simple wrapper to run multiple overlord classes, 
but in practical use only is designed to run one.  Here is where parallalization could occur.

grand_observer-work.py monitors the output files from the overlords and determines if an action (buy/sell)
needs to be taken.  This was designed so that overlords and observers can work without 
consequence and testing.  But only when a GrandObserver is used with a command line argument
will money actually be traded.
