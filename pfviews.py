#!/usr/bin/env python3

from pfdata import Portfolio
from reports import printTbl
from functools import lru_cache

class PFViews(Portfolio):
    @lru_cache(maxsize=1)
    def value(self): return sum(o.value() for o in self.holdings)
    def _cagr(self,o): return sum(mo.cagr()*mo.cost() for mo in o.bq)
    def _aggr(self,os):
        costs,values,cagrs = zip(*[ (o.cost(),o.value(),self._cagr(o)) for o in os ])
        cost = sum(costs)
        value = sum(values)
        gain = value - cost
        pgain = gain*100/cost if cost else '-'
        pshare = value*100/self.value()
        cagr = sum(cagrs)/cost if cost else '-'
        return (cost,value,gain,pgain,cagr,pshare)
    @lru_cache(maxsize=16)
    def aggr(self,p): return [ (pv,*self._aggr(os)) for pv,os in self.by(p) ]
    def pfgainreport(self):
        fp = open('pfgainreport.txt','w')
        printTbl([[
            mo.typ, #1
            mo.isfree, #2
            po.shortf(), #3
            mo.bt.txndt.strftime('%y%m%d'), #4
            mo.units, #5
            mo.cost(), #6
            mo.icost(), #7
            mo.value(), #8
            mo.gain(), #9
            mo.pgain(), #10
            mo.igain(), #11
            mo.gfgain(), #12
            mo.cagr(), #13
            str(po.rating()), #14
            po.oyret(), #15
            po.subcat(), #16
            ]
            for po,mo in self.urg_sbmatches()],
            title = 'UNREALIZED GAIN',
            colnames = ['Typ','Free','Fund','Date','Units','Cost','iCost','Value','Gain','%Gain', 'iGain','gGain',
                'CAGR','Rat','1YRet','Subcat'],
            sort = [-1,-2,14,3],
            formaters = {5:'%9.4f',6:'%8.0f',7:'%8.0f',8:'%8.0f',9:'%8.0f',10:'%5.2f',11:'%8.0f',12:'%8.0f',
                13:'%5.2f',15:'%5.2f',16:'%-11s'},
            file=fp
            )
        fp.close()
    def rgainreport(self):
        fp = open('rgainreport.txt','w')
        printTbl([[
            mo.typ, #1
            mo.isfree, #2
            po.shortf(), #3
            st.txndt.strftime('%y%m%d'), #4
            mo.bt.txndt.strftime('%y%m%d'), #5
            mo.units, #6
            mo.cost(), #7
            mo.icost(), #8
            mo.value(), #9
            mo.gain(), #10
            mo.pgain(), #11
            mo.igain(), #12
            mo.gfgain(), #13
            mo.cagr(), #14
            po.subcat(), #15
            ]
            for po,st,mos in self.rg_sbmatches() for mo in mos ],
            title = 'REALIZED GAIN',
            colnames = ['Typ','Free','Fund','SDate','BDate','Units','Cost','iCost','Value','Gain','%Gain','iGain','gGain',
                'CAGR','Subcat'],
            sort = [-4,3],
            formaters = {6:'%9.4f',7:'%8.0f',8:'%8.0f',9:'%8.0f',10:'%8.0f',11:'%5.2f',12:'%8.0f',13:'%8.0f',14:'%5.2f',15:'%-11s'},
            file=fp
            )
        fp.close()
    def pfreport(self):
        fp = open('pfreport.txt','w')
        pname = {'amc':'AMC','rating':'RATING','cat':'CATEGORY','subcat':'SUBCATEGORY'}
        fmt = {2:'%8.0f',3:'%8.0f',4:'%8.0f',5:'%5.2f',6:'%5.2f',7:'%5.2f'}
        printTbl(self.aggr('_wildcard'),
            proj = [2,3,4,5,6],
            title = 'TOTAL',
            colnames = ['Cost','Value','Gain','%Gain','CAGR'],
            formaters = fmt,
            file=fp,
            )
        printTbl([[
            o.shortf(), o.cost(), o.value(), o.value()-o.cost(),
            ((o.value()-o.cost())*100/o.cost()) if o.cost() else '-',
            o.cagr(), o.oyret(), o.rating(), o.value()*100/self.value(), o.subcat()
            ] for o in self.holdings],
            title = 'FUND WISE',
            sort = [10,-4],
            colnames = ['Fund','Cost','Value','Gain','%Gain','CAGR','1YRet','Rat','%pf','Subcat'],
            formaters = {5:'%5.2f', 6:'%5.2f', 7:'%5.2f', 9:'%4.2f', 10:'%-11s'},
            file=fp,
            )
        [ printTbl(self.aggr(p),
            title = pname[p] + ' WISE',
            sort = [-6],
            colnames = [pname[p],'Cost','Value','Gain','%Gain','CAGR','%pf'],
            formaters = fmt,
            file=fp,
            ) for p in ['amc','rating','cat','subcat'] ]
        fp.close()

if __name__ == '__main__':
    pfv = PFViews()
    pfv.pfreport()
    pfv.pfgainreport()
    pfv.rgainreport()
