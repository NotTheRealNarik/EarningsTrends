import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date , timedelta
#SQL integration
from datetime import datetime
import itertools
import random
import math
from IPython.display import display
pd.options.display.max_rows = 999

#UI
import tkinter as tk

#for earnings
from yahoo_earnings_calendar import YahooEarningsCalendar

#SQL
import mysql.connector
import pymysql 
from sqlalchemy import create_engine

#plotting
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter
from matplotlib.ticker import NullFormatter
from matplotlib.pyplot import figure
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

# sql settings
MYSQL_USER     = 'root'
MYSQL_PASSWORD = 'Harsha123123'
MYSQL_HOST_IP  = 'localhost'
MYSQL_PORT     = 3306
MYSQL_DATABASE = 'stockData'

def checkTick(inp1,numEarnings):
    inp = inp1.upper()
    tick = yf.Ticker(inp)
    flag = tick.history()
    if flag.empty:
        print("Error: Ticker symbol does not exist!")
    else:
        print('Fetching data for the past {} earning dates'.format(numEarnings))
        getPriceData(inp,tick,numEarnings)    

def connectSql():
    mydb = mysql.connector.connect(host= MYSQL_HOST_IP, user= MYSQL_USER, passwd= MYSQL_PASSWORD, auth_plugin='mysql_native_password')
    cursor = mydb.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS stockData")
    engine = create_engine('mysql+pymysql://'+MYSQL_USER+':'+MYSQL_PASSWORD+'@'+MYSQL_HOST_IP+'/'+MYSQL_DATABASE, echo=False)
    print("connection established")
    cursor.execute("USE stockdata; SHOW TABLES", multi=True)
    return mydb,engine

def checkTableExists(dbcon,tableName):
    tableName = tableName.lower()
    cursor = dbcon.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tableName))
    if cursor.fetchone()[0] == 1:
        cursor.close()
        print("table exists")
        return True
    cursor.close()
    print("table does not exist")
    return False
    

def checkSql(inp,numEarnings):    
    inp = inp.lower()
    mydb,engine = connectSql()
    flag = checkTableExists(mydb,inp)
    cursor = mydb.cursor()
    if flag==True:
        #table exists Fetch data
        print("fetching from Database...")
        cursor.execute("SELECT * from "+MYSQL_DATABASE+"."+inp)
        sqlResult = cursor.fetchall()
        count=0
        for i in range(len(sqlResult)):
            if sqlResult[i][-1] is None:
                pass
            else:
                count+=1
        if count == numEarnings:
            # retrive data from sql
            df = pd.read_sql_table(inp,con=engine)
            return df,engine
        else:
            return None,engine
    else:
        #create table and add empty data
        print("creating empty table")
        cursor.execute("""
                        USE stockdata;
                        CREATE TABLE"""+inp+"""
                        (index, Date, Open, High, Low, Close, Volume,
                        Dividends, Splits, earningDates)
                        """,multi=True)
        return None,engine

def getPriceData(inp,tick,numEarnings):
    inp = inp.lower()
    endDate = date.today()
    endYear = endDate.year
    day = endDate.day
    month = endDate.month
    numYears = numEarnings/4
    numYears = math.ceil(numYears) 
    startDate = date(endYear-numYears,month,day)
    
    #get ticker info
    name = tick.info['shortName']
    
    #check if data exists in sql
    data,engine = checkSql(inp,numEarnings)

    if data is None:
        data = tick.history(period='max',start=startDate, end=endDate)
        data = data.reset_index()
        

       
    #yahoo earnings
    yec = YahooEarningsCalendar()
    earningsRaw = yec.get_earnings_of(inp)
    earningsDF= pd.DataFrame([datetime.strptime(d['startdatetime'][:10],'%Y-%m-%d') for d in earningsRaw]).rename(columns = {0:"dates"})
    startTimeStamp = pd.Timestamp(startDate)
    endTimeStamp = pd.Timestamp(endDate)

    #get alll earnings dates for 'numYears' years
    earningDates = earningsDF.loc[(earningsDF['dates']>=startTimeStamp) & (earningsDF['dates']<=endTimeStamp)]
    #get only 'numEarnigns' number of dates
    earningDates = earningDates[:numEarnings]
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
        if idx<10:
            tempDF = data.iloc[:idx+10]
        else:
            tempDF = data.iloc[idx - 10 : idx + 10]
        dfPlot_collection[i]=tempDF
        plottingDF = plottingDF.append(tempDF)
    
    #plots
    generateSubGraphs(earningDateList,earningPriceList,dfPlot_collection,numYears)
    generateGraph(earningDateList,earningPriceList,dfPlot_collection,data,name)
    
    #update SQL
    data.to_sql(inp, con=engine, if_exists='replace')
    print("Updated Database")




def generateSubGraphs(earningDateList,earningPriceList,dfPlot_collection,plottingRows):
    print("generating....")
    fig, axes = plt.subplots(plottingRows,4, figsize=(20,10))
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
        ax.legend(handles=legend_elements, fancybox=True, framealpha=0.1)
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
numEarnings = int(input("Enter number of earnings dates:"))
checkTick(inp, numEarnings)