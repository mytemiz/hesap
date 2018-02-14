import json
import pprint
import time
from datetime import datetime
import sqlite3
import os

ENTRY_INFLOW = 1
ENTRY_OUTFLOW = 2

config = {'DBNAME':'hesap.db'}

class Entry:
    def __init__(self, entrytuple=None):
        self.data = {'id':None,
                'date':None,
                'entryId':None,
                'description':None,
                'amount':None,
                'currencyId':None
                }
        if entrytuple is not None:
            self.data['id'], self.data['date'], self.data['entryId'], self.data['description'], self.data['amount'], self.data['currencyId'] = entrytuple
    
    def toTuple(self):
        return (self.data['id'], self.data['date'], self.data['entryId'], self.data['description'], self.data['amount'], self.data['currencyId'])

    def data(self):
        return self.data


class AccountController:
    def __init__(self):
        self.conn = self.getDb()
        self.showCli()

    def showCli(self):
        while(True):
            command = input('> ')
            print('[DEBUG] komut: ', command)
            if command == 'kapat' or command == 'k':
                break
            elif command == 'help' or command == 'h':
                self.showHelp()
            elif command == 'GirişEkle' or command == 'g':
                self.newEntry(ENTRY_INFLOW)
            elif command == 'ÇıkışEkle' or command == 'c':
                self.newEntry(ENTRY_OUTFLOW)
            elif command == 'GünSonuHesapla' or command == 'gs':
                self.dailyReport(self.getDateStr())
        self.closeDb()

    def showHelp(self):
        print('Komut Listesi: ')
        print('              (h)Yardım ')
        print('              (g)GirişEkle ')
        print('              (ç)ÇıkışEkle ')
        print('              (gs)GünSonuHesapla ')
        print('              (k)Kapat ')

    def dailyReport(self, date):
        c = self.conn.cursor()

        ################## PRINT INFLOWS ##################
        c.execute("SELECT * FROM accounts WHERE date=? AND entryId=?", (date,ENTRY_INFLOW,))
        inflows = c.fetchall()

        lens = [0]
        for i in inflows:
            lens.append(len(i[3]))
        colwidth = max(lens)
        if colwidth < 12:
            colwidth = 12
        print()
        print('+' +  '-'*colwidth + '-'*(12+1) + '+')
        print('|' + 'GİRİŞLER'.center(colwidth+12+1, '*') + '|')
        print('+' +  '-'*colwidth + '+' + '-'*12 + '+')
        header = '|' + 'Açıklama'.center(colwidth) + '|' + 'Tutar'.center(12) + '|'
        print(header)
        print('+' +  '-'*colwidth + '+' + '-'*12 + '+')
        totalinflow = 0
        for entrytuple in inflows:
            entry = Entry(entrytuple)
            totalinflow += entry.data['amount']
            print ('|' + '{d}'.format(d=entry.data['description']).ljust(colwidth) + '|' + '{a:.2f}'.format(a=entry.data['amount']).rjust(12) + '|')
        
        print('+' +  '='*colwidth + '+' + '='*12 + '+')
        print('|' + 'TOPLAM'.rjust(colwidth) + '|' +'{t:.2f}'.format(t=totalinflow).rjust(12) + '|')
        print('+' +  '-'*colwidth + '+' + '-'*12 + '+')

        c.execute("SELECT * FROM accounts WHERE date=? AND entryId=?", (date,ENTRY_OUTFLOW,))
        outflows = c.fetchall()
        
        ################## PRINT OUTFLOWS ##################
        lens = [0]
        for i in outflows:
            lens.append(len(i[3]))
        colwidth = max(lens)
        if colwidth < 12:
            colwidth = 12
        print()
        print('+' +  '-'*colwidth + '-'*(12+1) + '+')
        print('|' + 'ÇIKIŞLAR'.center(colwidth+12+1, '*') + '|')
        print('+' +  '-'*colwidth + '+' + '-'*12 + '+')
        header = '|' + 'Açıklama'.center(colwidth) + '|' + 'Tutar'.center(12) + '|'
        print(header)
        print('+' +  '-'*colwidth + '+' + '-'*12 + '+')
        totaloutflow = 0
        for entry in outflows:
            _id, date, et, desc, amount, cur = entry
            totaloutflow += amount
            print ('|' + '{d}'.format(d=desc).ljust(colwidth) + '|' + '{a:.2f}'.format(a=-amount).rjust(12) + '|')
        
        print('+' +  '='*colwidth + '+' + '='*12 + '+')
        print('|' + 'TOPLAM'.rjust(colwidth) + '|' +'{t:.2f}'.format(t=-totaloutflow).rjust(12) + '|')
        print('+' +  '-'*colwidth + '+' + '-'*12 + '+')
        
        ################## PRINT SUMMARY ##################
        print()
        print('+' +  '-'*12 + '-'*(12+1) + '+')
        print('|' + 'ÖZET'.center(12+12+1, '*') + '|')
        print('+' +  '-'*12 + '+' + '-'*12 + '+')
        header = '|' + 'Açıklama'.center(12) + '|' + 'Tutar'.center(12) + '|'
        print(header)
        print('+' +  '-'*12 + '+' + '-'*12 + '+')
        print('|' + 'Girişler'.rjust(12) + '|' +'{t:.2f}'.format(t=totalinflow).rjust(12) + '|')
        print('|' + 'Çıkışlar'.rjust(12) + '|' +'{t:.2f}'.format(t=-totaloutflow).rjust(12) + '|')
        print('|' + 'TOPLAM'.rjust(12) + '|' +'{t:.2f}'.format(t=totalinflow-totaloutflow).rjust(12) + '|')
        print('+' +  '-'*12 + '+' + '-'*12 + '+')
 

    def monthlyReport(self, date):
        date = date[:6] + '00'
        uplimit = int(date[4:6])+1
        c = self.conn.cursor()
        c.execute("SELECT * FROM accounts WHERE date=?", (date,))
        daily = c.fetchall()
        print (daily)
        
    def closeDb(self):
        self.conn.close()

    def getDb(self):
        if not os.path.isfile(config['DBNAME']):
            self.initDb()
        
        conn = sqlite3.connect(config['DBNAME'])
            
        return conn

    def initDb(self):
        conn = sqlite3.connect(config['DBNAME'])
        c = conn.cursor()

        c.execute('''CREATE TABLE currencies(id integer primary key,
                                            name text)''')

        c.execute('''CREATE TABLE entries(id integer primary key,
                                        name text)''')

        c.execute('''CREATE TABLE accounts(id integer primary key,
                                        date real, 
                                        entryId int REFERENCES entries(id), 
                                        description text,
                                        amount real,
                                        currencyId int REFERENCES currencies(id))''')

        c.execute('''CREATE TABLE case(id integer primary key,
                                       date real,
                                       entryId int REFERENCESentries(id),
                                       currencyId int REFERENCESE currencies(id),
                                       description text)''')

        c.execute('''INSERT INTO currencies(name) VALUES('tl')''')
        c.execute('''INSERT INTO currencies(name) VALUES('dolar')''')
        c.execute('''INSERT INTO currencies(name) VALUES('euro')''')

        c.execute('''INSERT INTO entries(name) VALUES('Giriş')''')
        c.execute('''INSERT INTO entries(name) VALUES('Çıkış')''')

        conn.commit()
        conn.close()

    def saveEntry(self, data):
        c = self.conn.cursor()
        c.execute('''INSERT INTO accounts(date, entryId, description, amount, currencyId) 
                VALUES(?,?,?,?,?)''', (data['date'], 
                                        data['entryType'], 
                                        data['description'],
                                        data['amount'],
                                        data['currencyId']))
        self.conn.commit()

    def deleteEntry(self, _id):
        c = self.conn.cursor()
        c.execute('''DELETE FROM accounts WHERE id=?''', (_id,))
        self.conn.commit()

    def updateEntry(self, _id, data):
        c = self.conn.cursor()
        c.execute('''UPDATE accounts set date=?, 
                                     entryId=?, 
                                     description=?,
                                     amount=?,
                                     currencyId=?) 
                VALUES(?,?,?,?,?)''', (data['date'], 
                                        data['entryType'], 
                                        data['description'],
                                        data['amount'],
                                        data['currencyId']))
        self.conn.commit()

    def getDateStr(self):
        date = datetime.now()
        return date.strftime("%Y%m%d") 

    def newEntry(self, entryType=None):
        print('Tarih: ', self.getDateStr())
        if entryType == None:
            entryType = int(input('İşlem (1)giriş, (2)çıkış: '))
        desc = input('Açıklama: ')
        amount = input('Tutar: ')
        currency = input('tl,dolar,euro(default=1,2,3): ')
        if currency == '':
            currency = 1

        data = {}
        data['entryType'] = entryType
        data['date'] = time.time()
        data['description'] = desc
        data['amount'] = float(amount)
        data['currencyId'] = int(currency)
        
        self.saveEntry(data)

    def getEntry(self):
        print('Tarih', self.getDateStr())
