#!/usr/bin/env python3

from pfdata import PFData
from reports import printTbl
from functools import lru_cache

class PFViews(PFData):
    # TODO: Reuse aggr
    @lru_cache(maxsize=1)
    def value(self): return sum(o.value() for o in self.pfobjs)
    @lru_cache(maxsize=1)
    def cost(self): return sum(o.cost() for o in self.pfobjs)
    def gain(self): return self.value() - self.cost()
    def cagr(self): return sum(o.cost()*o.cagr() for o,po in self.buymatches())/self.cost() # TODO wrong, need match object level
    def _cagr(self,o): return sum(mo.cagr()*mo.cost() for mo in o.sbmatch.bq)
    def _aggr(self,os):
        costs,values,cagrs = zip(*[ (o.cost(),o.value(),self._cagr(o)) for o in os ])
        cost = sum(costs)
        value = sum(values)
        gain = value - cost
        pgain = gain*100/cost if cost else '-'
        pshare = value*100/self.value()
        cagr = sum(cagrs)/cost if cost else '-'
        return (cost,value,gain,pgain,cagr,pshare)
    def aggr(self,p): return [ (pv,*self._aggr(os)) for pv,os in self.by(p) ]
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
        printTbl([[self.cost(),self.value(),self.gain(),self.gain()*100/self.cost(),self.cagr()]],
            title = 'TOTAL VALUE',
            colnames = ['Cost','Value','Gain','%Gain','CAGR'],
            formaters = {1:'%8.0f',2:'%8.0f',3:'%8.0f',4:'%5.2f',5:'%5.2f'},
            file=fp,
            )
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
        pname = {'amc':'AMC','rating':'RATING','cat':'CATEGORY','subcat':'SUBCATEGORY'}
        [ printTbl(self.aggr(p),
            title = pname[p] + ' WISE',
            sort = [-3],
            colnames = [pname[p],'Cost','Value','Gain','%Gain','CAGR','% share'],
            formaters = {2:'%8.0f',3:'%8.0f',4:'%8.0f',5:'%5.2f',6:'%5.2f',7:'%5.2f'},
            file=fp,
            ) for p in ['amc','rating','cat','subcat'] ]
        fp.close()

if __name__ == '__main__':
    pfv = PFViews()
    pfv.pfreport()
    pfv.pfgainreport()
