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
            P_1_Year,
            P_3_Year,
            P_5_Year,
            P_10_Year
        ]
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
                    "symbol": "VOO,SPYV,ITOT,IJH,VOE,IJR,VBR,IWM,XLK,VIG,VYM,QQQ,SPLV,AGG,SHY",
                    "field": "NAV"
                }
            ]
        data = []
        for item in items:
            symbols = item["symbol"].split(',')
            group = item["group"]
            dataField = item["field"]
            for symbol in symbols:
                line = self.getPerformanceDataForItem(group, symbol, dataField, intervals)
                data.append(line)
                time.sleep(1)

        print("Final")
        for item in data.sort():
            print(item)

    print("done")


    def getPerformanceDataForItem(self, group, symbol, dataField, intervals):
        line = None
        key = "{0}:{1}".format(group, symbol)
        baseUrl = "http://performance.morningstar.com/perform/Performance/cef/trailing-total-returns.action?&t={0}&region=usa&culture=en-US&cur=&ops=clear&s=0P00001G5L&ndec=2&ep=true&align=d&annlz=true&comparisonRemove=false&benchmarkSecId=&benchmarktype=" + key
        url = baseUrl.format(key)
        r = requests.get(url)
        if r.status_code == 200:
            line = self.findPerformanceData(dataField, r, symbol, intervals)
            if line == None:
                line = symbol + ',ERROR,'
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
                        line = descriptor + ',' + str(datetime.date.today())  + ',' + symbol + ','
                        dataFields = row.findAll("td")
                        for interval in intervals:
                            data = self.getContents(dataFields[interval])
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

    def test_generate_dashboard(self):
        manager = TxManager()
        dashboard = manager.generate_dashboard()
        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        statusTable = soup.find('table', id="status")

        moduleName = 'module1'
        expectedRowCount = 12
        expectedSuccessCount = 2
        expectedWarningCount = 2
        expectedFailureCount = 1
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module2'
        expectedRowCount = 11
        expectedSuccessCount = 2
        expectedWarningCount = 0
        expectedFailureCount = 2
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module3'
        expectedRowCount = 9
        expectedSuccessCount = 0
        expectedWarningCount = 0
        expectedFailureCount = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module4'
        expectedRowCount = 0
        expectedSuccessCount = 0
        expectedWarningCount = 0
        expectedFailureCount = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'totals'
        expectedRowCount = 5
        expectedSuccessCount = 5
        expectedWarningCount = 2
        expectedFailureCount = 3
        expectedUnregistered = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount, expectedUnregistered)

        failureTable = soup.find('table', id="failed")
        expectedFailureCount = 3
        self.validateFailureTable(failureTable, expectedFailureCount)

    def test_generate_dashboard_max_two(self):
        expectedMaxFailures = 2
        manager = TxManager()
        dashboard = manager.generate_dashboard(expectedMaxFailures)

        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        statusTable = soup.find('table', id="status")

        moduleName = 'module1'
        expectedRowCount = 12
        expectedSuccessCount = 2
        expectedWarningCount = 2
        expectedFailureCount = 1
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module2'
        expectedRowCount = 11
        expectedSuccessCount = 2
        expectedWarningCount = 0
        expectedFailureCount = 2
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module3'
        expectedRowCount = 9
        expectedSuccessCount = 0
        expectedWarningCount = 0
        expectedFailureCount = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'totals'
        expectedRowCount = 5
        expectedSuccessCount = 5
        expectedWarningCount = 2
        expectedFailureCount = 3
        expectedUnregistered = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount, expectedUnregistered)

        failureTable = soup.find('table', id="failed")
        expectedFailureCount = expectedMaxFailures
        self.validateFailureTable(failureTable, expectedFailureCount)

    # helper methods #

    def validateFailureTable(self, table, expectedFailureCount):
        self.assertIsNotNone(table)
        module = table.findAll('tr', id=lambda x: x and x.startswith('failure-'))
        rowCount = len(module)
        self.assertEquals(rowCount, expectedFailureCount)

    def validateModule(self, table, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                       expectedWarningCount, expectedUnregistered = 0):
        self.assertIsNotNone(table)
        module = table.findAll('tr', id=lambda x: x and x.startswith(moduleName + '-'))
        rowCount = len(module)
        self.assertEquals(rowCount, expectedRowCount)
        if expectedRowCount > 0:
            successCount = self.getCountFromRow(table, moduleName + '-job-success')
            self.assertEquals(successCount, expectedSuccessCount)
            warningCount = self.getCountFromRow(table, moduleName + '-job-warning')
            self.assertEquals(warningCount, expectedWarningCount)
            failureCount = self.getCountFromRow(table, moduleName + '-job-failure')
            self.assertEquals(failureCount, expectedFailureCount)
            unregisteredCount = self.getCountFromRow(table, moduleName + '-job-unregistered')
            self.assertEquals(unregisteredCount, expectedUnregistered)
            expectedTotalCount = expectedFailureCount + expectedSuccessCount + expectedWarningCount + expectedUnregistered
            totalCount = self.getCountFromRow(table, moduleName + '-job-total')
            self.assertEquals(totalCount, expectedTotalCount)

    def getCountFromRow(self, table, rowID):
        rows = table.findAll('tr', id=lambda x: x == rowID)
        if len(rows) == 0:
            return 0

        dataFields = rows[0].findAll("td")
        strings = dataFields[1].stripped_strings # get data from second column
        count = -1
        for string in strings:
            count = int(string)
            break

        return count

    def call_args(self, mock_object, num_args, num_kwargs=0):
        """
        :param mock_object: mock object that is expected to have been called
        :param num_args: expected number of (non-keyword) arguments
        :param num_kwargs: expected number of keyword arguments
        :return: (args, kwargs) of last invocation of mock_object
        """
        mock_object.assert_called()
        args, kwargs = mock_object.call_args
        self.assertEqual(len(args), num_args)
        self.assertEqual(len(kwargs), num_kwargs)
        return args, kwargs


if __name__ == "__main__":
    unittest.main()
