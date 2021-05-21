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
    def pshare(self,l): return [ (p,v,v*100/self.value()) for p,v in l ]
    def aggr(self,p): return [ (p,sum(o.value() for o in os)) for p,os in self.by(p) ]
    def pfreport(self):
        fp = open('pfreport.txt','w')
        print('\n',file=fp)
        printTbl([[self.value(),self.cost(),self.gain()]],
            title='TOTAL VALUE',
            colnames = ['Value','Cost','Gain'],
            formaters={1:'%8.0f',2:'%8.0f',3:'%8.0f'},
            file=fp,
            )
        printTbl([[
            o.shortf(), o.cost(), o.value(), o.value()-o.cost(),
            ((o.value()-o.cost())*100/o.cost()) if o.cost() else '-',
            o.cagr(), o.value()*100/self.value(), o.rating(), o.oyret(), o.subcat()
            ] for o in self.pfobjs],
            title='FUND WISE',
            sort = [10,-4],
            colnames = ['Fund','Cost','Value','Gain','%Gain','CAGR','% pf','Rat','1YRet','Subcat'],
            formaters = {5:'%5.2f', 6:'%5.2f', 7:'%4.2f', 9:'%5.2f', 10:'%-11s'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('amc')),
            title='AMC WISE',
            sort = [-2],
            colnames = ['AMC','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('rating')),
            title='RATING WISE',
            sort = [-2],
            colnames = ['RATING','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('cat')),
            title='CATEGORY WISE',
            sort = [-2],
            colnames = ['CATEGORY','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        print('\n',file=fp)
        printTbl(self.pshare(self.aggr('subcat')),
            title='SUBCATEGORY WISE',
            sort = [-2],
            colnames = ['SUBCATEGORY','AMOUNT','% share'],
            formaters = {2:'%8.0f',3:'%4.2f'},
            file=fp,
            )
        fp.close()

if __name__ == '__main__':
    pfv = PFViews()
    pfv.pfreport()
