import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date , timedelta
from datetime import datetime
import itertools
import random

#UI
import tkinter as tk

#for earnings
from yahoo_earnings_calendar import YahooEarningsCalendar

#plotting
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter
from matplotlib.ticker import NullFormatter
from matplotlib.pyplot import figure
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

#options
#pd.options.display.max_rows = 999


def getPriceData(inp1):
    #inp = 'TSLA'
    #inp = entry1.get()
    inp = inp1.upper()
    print(inp)
    endDate = date.today()
    endYear = endDate.year
    day = endDate.day
    month = endDate.month
    startDate = date(endYear-2,month,day)
    tick = yf.Ticker(inp)
    #name = tick.info['shortName']
    data = tick.history(period='max',start=startDate, end=endDate)
    data = data.reset_index()
    #yahoo earnings
    yec = YahooEarningsCalendar()
    earningsRaw = yec.get_earnings_of(inp)
    earningsDF= pd.DataFrame([datetime.strptime(d['startdatetime'][:10],'%Y-%m-%d') for d in earningsRaw]).rename(columns = {0:"dates"})
    startTimeStamp = pd.Timestamp(startDate)
    endTimeStamp = pd.Timestamp(endDate)
    earningDates = earningsDF.loc[(earningsDF['dates']>=startTimeStamp) & (earningsDF['dates']<=endTimeStamp)]

    earningPriceList = []
    earningDateList = []
    earningDF = pd.DataFrame()
    for x in earningDates.itertuples():
        for d in data.itertuples():
            if d.Date == x.dates:
                data.at[d.Index,'earningDates'] = x.dates
                earningPriceList.append(d.Close)
                earningDateList.append(x.dates)      

    earningDF['Dates'] = earningDateList
    earningDF['Price'] = earningPriceList
    plottingDF = pd.DataFrame()
    dfPlot_collection = {}
    for i in range(len(earningDateList)):
        idx = data[data['earningDates']==earningDateList[i]].index.values.astype(int)[0]
        tempDF = data.iloc[idx - 10 : idx + 10]
        dfPlot_collection[i]=tempDF
        plottingDF = plottingDF.append(tempDF)
    
    #plots
    generateSubGraphs(earningDateList,earningPriceList,dfPlot_collection)
    #generateGraph(earningDateList,earningPriceList,dfPlot_collection,data,name)

def generateSubGraphs(earningDateList,earningPriceList,dfPlot_collection):
    print("generating....")
    fig, axes = plt.subplots(2,4, figsize=(20,7))
    for i in range(len(earningDateList)):
        ax = axes.flatten()[i]
        #main Plot Prices vs Dates
        ax.plot(dfPlot_collection[i]['Date'], dfPlot_collection[i]['Close'])
        #scatter earning dates and prices
        y = dfPlot_collection[i]['Close']
        x = dfPlot_collection[i]['earningDates']
        ax.vlines(x, 0, y, linestyle="dashed",color='red')
        ax.hlines(y, 0, x, linestyle="dashed" ,color='red')
        ax.scatter(x, y,color='red')

        #style modification
        labels = ' Date: {} \n Price: {}'.format(earningDateList[i].date(),earningPriceList[i])
        legend_elements = [
                           Line2D([0], [0], marker='o', color='w', label=labels,
                              markerfacecolor='r', markersize=10),
                           ]
        ax.set_xlim([min(dfPlot_collection[i]['Date']), max(dfPlot_collection[i]['Date'])])
        ax.set_ylim([min(dfPlot_collection[i]['Close'])-5, max(dfPlot_collection[i]['Close'])+5])
        ax.legend(handles=legend_elements)
        plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    fig.tight_layout()
    plt.show()
    print("DONE")

def generateGraph(earningDateList,earningPriceList,dfPlot_collection,data,name):
    plt.figure(figsize=(25, 8))

    xMax = max(dfPlot_collection[len(earningDateList)-1]['Date'])
    xMin = min(dfPlot_collection[0]['Date'])
    yMax = max(dfPlot_collection[len(earningPriceList)-1]['Close'])+5
    yMin = min(dfPlot_collection[0]['Close'])-5

    plt.plot(data['Date'], data['Close'] )
    plt.scatter(data['earningDates'],data['Close'],marker='o',color="red" )
    plt.axis([min(data['Date']), max(data['Date']), max(data['Close'])+10, 0])

    x1 = earningDateList
    y1 = earningPriceList
    plt.vlines(x1, 0, y1, linestyle="dashed",color='red')

    plt.title("{}'s' Stock Price".format(name), fontsize=14)
    plt.xlabel('Dates', fontsize=14)
    plt.ylabel('Closing Price', fontsize=14)
    for i in range(len(earningDateList)):
        plt.annotate(  '  Date: {} \n  Price: {}'.format(earningDateList[i].date(),earningPriceList[i])   
                 ,(earningDateList[i].date(),earningPriceList[i]))

    plt.xlim([xMin, xMax])
    plt.ylim([yMin, yMax])
    plt.axis([min(data['Date'])-timedelta(3), max(data['Date'])+timedelta(3)  ,min(data['Close'])-5, max(data['Close'])+5 ])
    plt.show()


inp = input("Enter tick code: ")
getPriceData(inp)
