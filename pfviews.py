#!/usr/bin/env python3

from pfdata import PFData
from reports import printTbl
from functools import lru_cache

class PFViews(PFData):
    @lru_cache(maxsize=1)
    def value(self): return sum(o.value() for o in self.pfobjs)
    @lru_cache(maxsize=1)
    def cost(self): return sum(o.cost() for o in self.pfobjs)
    def gain(self): return self.value() - self.cost()
    def cagr(self): return sum(o.cost()*o.cagr() for o,po in self.buymatches())/self.cost()
    def pshare(self,l): return [ (p,v,v*100/self.value()) for p,v in l ]
    def aggr(self,p): return [ (p,sum(o.value() for o in os)) for p,os in self.by(p) ]
    def pfgainreport(self):
        fp = open('pfgainreport.txt','w')
        printTbl([[
            'EQ' if o.iseq else 'DT', #1
            o.isfree, #2
            po.shortf(), #3
            o.bt.txndt.strftime('%y%m%d'), #4
            o.units, #5
            o.cost(), #6
            o.value(), #7
            o.value() - o.cost(), #8
            ((o.value()-o.cost())*100/o.cost()) if o.cost() else '-', #9
            o.cagr(), #10
            str(po.rating()), #11
            po.oyret(), #12
            po.subcat(), #13
            ]
            for o,po in self.buymatches()],
            title = 'PFGAIN',
            colnames = ['Typ','Free','Fund','Date','Units','Cost','Value','Gain','%Gain','CAGR','Rat',
                '1YRet','Subcat'],
            sort = [-1,-2,11,3],
            formaters = {5:'%9.4f',6:'%8.0f',7:'%8.0f',8:'%8.0f',9:'%5.2f',10:'%5.2f',12:'%5.2f',
                13:'%-11s'},
            file=fp
            )
        fp.close()
    def pfreport(self):
        fp = open('pfreport.txt','w')
        print('\n',file=fp)
        printTbl([[self.cost(),self.value(),self.gain(),self.gain()*100/self.cost(),self.cagr()]],
            title = 'TOTAL VALUE',
            colnames = ['Cost','Value','Gain','%Gain','CAGR'],
            formaters = {1:'%8.0f',2:'%8.0f',3:'%8.0f',4:'%5.2f',5:'%5.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl([[
            o.shortf(), o.cost(), o.value(), o.value()-o.cost(),
            ((o.value()-o.cost())*100/o.cost()) if o.cost() else '-',
            o.cagr(), o.oyret(), o.rating(), o.value()*100/self.value(), o.subcat()
            ] for o in self.pfobjs],
            title = 'FUND WISE',
            sort = [10,-4],
            colnames = ['Fund','Cost','Value','Gain','%Gain','CAGR','1YRet','Rat','%pf','Subcat'],
            formaters = {5:'%5.2f', 6:'%5.2f', 7:'%5.2f', 9:'%4.2f', 10:'%-11s'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('amc')),
            title = 'AMC WISE',
            sort = [-2],
            colnames = ['AMC','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('rating')),
            title = 'RATING WISE',
            sort = [-2],
            colnames = ['RATING','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('cat')),
            title = 'CATEGORY WISE',
            sort = [-2],
            colnames = ['CATEGORY','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('subcat')),
            title = 'SUBCATEGORY WISE',
            sort = [-2],
            colnames = ['SUBCATEGORY','AMOUNT','% share'],
            formaters = {1:'%-11s',2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        fp.close()

if __name__ == '__main__':
    pfv = PFViews()
    pfv.pfreport()
    pfv.pfgainreport()
