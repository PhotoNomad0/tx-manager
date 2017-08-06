# This Python file uses the following encoding: utf-8

from __future__ import absolute_import, unicode_literals, print_function
import itertools
import unittest

import datetime
import mock
from six import StringIO
from bs4 import BeautifulSoup
import requests
import time

P_1_Day=0
P_1_Week=1
P_1_Month=2
P_3_Month=3
P_YTD=4
P_1_Year=5
P_3_Year=6
P_5_Year=7
P_10_Year=8
P_15_Year=9


class MorningstarTest(unittest.TestCase):

    def test_get_market_data(self):

        # http://performance.morningstar.com/funds/etf/total-returns.action?t=SHY
        # http://performance.morningstar.com/perform/Performance/cef/trailing-total-returns.action?&t=XNAS:FLPSX&region=usa&culture=en-US&cur=&ops=clear&s=0P00001MK8&ndec=2&ep=true&align=d&annlz=true&comparisonRemove=false&benchmarkSecId=&benchmarktype=
        # http://performance.morningstar.com/perform/Performance/cef/trailing-total-returns.action?&t={0}&region=usa&culture=en-US&cur=&ops=clear&s=0P00001G5L&ndec=2&ep=true&align=d&annlz=true&comparisonRemove=false&benchmarkSecId=&benchmarktype=SCHD
        # etf quote (<span id="Yield"> <span id="Expenses">:
        # http://etfs.morningstar.com/etfq/quote-banner?&t=ARCX:SCHD&region=usa&culture=en-US&version=RET&cur=&test=QuoteiFrame
        # Note: the above query also works for funds?
        # fund quote (<span vkey="ttmYield">  <span vkey="ExpenseRatio">:
        # http://quotes.morningstar.com/fundq/c-header?&t=XNAS:FLPSX&region=usa&culture=en-US&version=RET&cur=&test=QuoteiFrame

        intervals = [
            P_1_Month,
            P_3_Month,
            -1,
            P_1_Year,
            P_3_Year,
            P_5_Year,
            P_10_Year
        ]
        header = str(datetime.date.today()) + ",1 Month,3 Month,6 Month,1 Year,3 Year,5 Year,10 Year,Amount,Expense Ratio,Dividend"
        items = [
            {
                "group": "ARCX",
                "type": "ETFS",
                "symbol": "SCHD",
                "field": "NAV"
             },
            {
                "group": "XNAS",
                "type": "FUND",
                "symbol": "FLPSX,FCNTX",
                "field": "NAV"
            },
            {
                "group": "ARCX",
                "type": "ETFS",
                "symbol": "VOO,SPYV,ITOT,IJH,VOE,IJR,VBR,IWM,XLK,VIG,VYM",
                "field": "NAV"
            },
            {
                "group": "XNAS",
                "type": "ETFS",
                "symbol": "QQQ",
                "field": "NAV"
            },
            {
                "group": "ARCX",
                "type": "ETFS",
                "symbol": "SPLV,AGG",
                "field": "NAV"
            },
            {
                "group": "XNAS",
                "type": "ETFS",
                "symbol": "SHY",
                "field": "NAV"
            }
            ]
        data = []
        data.append(header)
        print(header)
        for item in items:
            symbols = item["symbol"].split(',')
            group = item["group"]
            dataField = item["field"]
            type = item["type"]
            for symbol in symbols:
                line = self.getPerformanceDataForItem(group, symbol, dataField, type, intervals)
                data.append(line)
                time.sleep(0.1)

        print("\nFinished")


    def getPerformanceDataForItem(self, group, symbol, dataField, type, intervals):
        line = None
        key = "{0}:{1}".format(group, symbol)
        baseUrl = "http://performance.morningstar.com/perform/Performance/cef/trailing-total-returns.action?&t={0}&region=usa&culture=en-US&cur=&ops=clear&s=0P00001G5L&ndec=2&ep=true&align=d&annlz=true&comparisonRemove=false&benchmarkSecId=&benchmarktype=" + key
        url = baseUrl.format(key)
        ttr_response = requests.get(url)
        if ttr_response.status_code == 200:
            line = self.findPerformanceData(dataField, ttr_response, symbol, intervals)
            if line == None:
                line = symbol + ',PARSE ERROR,'
        else:
            line = symbol + ',code=' + str(ttr_response.status_code) + ','

        time.sleep(0.1)
        line = self.getQuoteDataForItem(group, symbol, line, type)

        print(line)
        return line

    def getQuoteDataForItem(self, group, symbol, line, type):
        key = "{0}:{1}".format(group, symbol)
        baseUrl = "http://etfs.morningstar.com/etfq/quote-banner?&t={0}&region=usa&culture=en-US&version=RET&cur=&test=QuoteiFrame"
        url = baseUrl.format(key)
        quote_response = requests.get(url)
        if quote_response.status_code == 200:
            line = self.findQuoteData(line, type, quote_response, symbol)
        else:
            line += ',ERROR,ERROR'

        return line

    def findQuoteData(self, line, type, r, symbol):
        token = "span"
        key = "id"
        keyYield = "Yield"
        keyExpense = "Expenses"

        soup = BeautifulSoup(r.text, 'html.parser')

        yieldData = self.getQuoteItem(key, soup, token, keyYield)
        expenseData = self.getQuoteItem(key, soup, token, keyExpense)

        line += "" + ',' + expenseData + ',' + yieldData
        return line

    def getQuoteItem(self, key, soup, token, keyValue):
        attrs={};
        attrs[key] = keyValue
        data = soup.find(token, attrs)
        value = self.getContents(data)
        return value

    def findPerformanceData(self, dataField, r, symbol, intervals):
        findDescriptor = "{0} ({1})".format(symbol, dataField)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table')
        line = None
        if table != None:
            rows = table.findAll('tr')
            if (rows != None) and (len(rows) > 0):
                for row in rows:
                    rowHeader = row.find('th')
                    descriptor = self.getContents(rowHeader)

                    if descriptor == findDescriptor:
                        line = symbol + ','
                        dataFields = row.findAll("td")
                        for interval in intervals:
                            data = ""
                            if interval >= 0:
                                dataItem = dataFields[interval]
                                data = self.getContents(dataItem)
                                if data == u'—':
                                    data = ""
                            line += data + ','
                        break
        return line

    def getContents(self, item):
        if item == None:
            return "--"

        contents = item.stripped_strings
        text = None
        for string in contents:
            text = string
            break
        return text

if __name__ == "__main__":
    unittest.main()
