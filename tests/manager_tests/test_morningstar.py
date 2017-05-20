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
        intervals = [
            P_1_Month,
            P_3_Month,
            -1,
            P_1_Year,
            P_3_Year,
            P_5_Year,
            P_10_Year
        ]
        header = str(datetime.date.today()) + ",1 Month,3 Month,6 Month,1 Year,3 Year,5 Year,10 Year,"
        items = [
            {
                "group": "ARCX",
                "symbol": "SCHD",
                "field": "NAV"
             },
            {
                "group": "XNAS",
                "symbol": "FLPSX,FCNTX",
                "field": "NAV"
            },
            {
                "group": "ARCX",
                "symbol": "VOO,SPYV,ITOT,IJH,VOE,IJR,VBR,IWM,XLK,VIG,VYM",
                "field": "NAV"
            },
            {
                "group": "XNAS",
                "symbol": "QQQ",
                "field": "NAV"
            },
            {
                "group": "ARCX",
                "symbol": "SPLV,AGG,SHY",
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
            for symbol in symbols:
                line = self.getPerformanceDataForItem(group, symbol, dataField, intervals)
                data.append(line)
                time.sleep(1)

        print("\nFinished")


    def getPerformanceDataForItem(self, group, symbol, dataField, intervals):
        line = None
        key = "{0}:{1}".format(group, symbol)
        baseUrl = "http://performance.morningstar.com/perform/Performance/cef/trailing-total-returns.action?&t={0}&region=usa&culture=en-US&cur=&ops=clear&s=0P00001G5L&ndec=2&ep=true&align=d&annlz=true&comparisonRemove=false&benchmarkSecId=&benchmarktype=" + key
        url = baseUrl.format(key)
        r = requests.get(url)
        if r.status_code == 200:
            line = self.findPerformanceData(dataField, r, symbol, intervals)
            if line == None:
                line = symbol + ',PARSE ERROR,'
        else:
            line = symbol + ',code=' + str(r.status_code) + ','

        print(line)
        return line

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

    def getContents(self, rowHeader):
        contents = rowHeader.stripped_strings
        descriptor = None
        for string in contents:
            descriptor = string
            break
        return descriptor

if __name__ == "__main__":
    unittest.main()
