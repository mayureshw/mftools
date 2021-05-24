from xls2obj import XlsObjs
from conf import *
from itertools import groupby
from functools import reduce
from functools import lru_cache
from datetime import datetime
import sys
import re

# TODO: Probably we want to merge noise and spacepats into adhocpats and call it something else
class FData():
    noise = []
    spacepats = []
    adhocpats = [
        ('Mid Cap','Midcap'),
        ('MidCap','Midcap'),
        ('Direct Plan','Direct'),
        ('Regular Plan','Regular'),
        ('Blue Chip','Bluechip'),
        ('P/E','PE'),
        ]
    def res(self,pats): return [ re.compile(p) for p in pats ]
    def cname(self,fname): return reduce(
        lambda s,srepl: re.sub(*srepl,s),[ (sre,repl) for sre,repl in (
            [(n,'') for n in self.res(self.noise)] + \
            [(s,' ') for s in self.res(self.spacepats)] + \
            [(re.compile(sre),repl) for sre,repl in self.adhocpats]
            )
        ],fname).strip()

class VRMFData(FData):
    noise = [ r'-' ]
    spacepats = [ r' +' ]
    def get(self,cnm,p): return self.cnvo[cnm].__dict__[p] if cnm in self.cnvo else None
    def typ(self,cname):
        if cname not in self.cnvo: return '-'
        cat,subcat = self.cnvo[cname].cat.split('-')
        return cat if cat in {'EQ','DT'} else 'EQ' if subcat=='AH' else 'DT'
    def __init__(self):
        csvfiles = list(mfdocsdir.glob('all-*-funds-*.csv'))
        if len(csvfiles) != 3:
            print('VRMFData: xls file count mismatch',len(csvfiles))
            sys.exit(1)
        objs = [ o for csv in csvfiles for o in XlsObjs(csv,specname='vrmf') ]
        self.cnvo = { self.cname(o.fname) : o for o in objs }
vd = VRMFData()

class CAMSData(FData):
    prodre = re.compile('\(\w+\)')
    noise = [
        r'\bGrowth Option\b',
        r'\bGrowth\b',
        r'\(\w+\)',
        r'\(Erstwhile.*$',
        r'\([Ff]ormerly.*$',
        r'\(Earlier.*$',
        r'[)(]',
        ]
    spacepats = [ '-', r' +' ]
    
    def prodid(self,fname): return self.prodre.search(fname).group()[1:-1]
    def __init__(self):
        balsfile = pfdatdir.joinpath('bals.xls')
        txnsfile = pfdatdir.joinpath('txns.xls')
        bobjs = XlsObjs(balsfile,specname='camsbals')
        pidbal = { self.prodid(bo.fname): bo for bo in bobjs }
        tobjs = XlsObjs(txnsfile,specname='camstxns')
        pidtxns = { pid:list(txns) for pid,txns in groupby(tobjs,lambda to:to.fid) }
        pidcname = { pid:self.cname(ts[0].fname) for pid,ts in pidtxns.items() }
        self.cnbal = { pidcname[pid]:bo for pid,bo in pidbal.items() }
        self.cntxns = { pidcname[pid]:to for pid,to in pidtxns.items() }

class SBMatch:
    eqtyp = {'Equity','Balanced','Index Fund'}
    @lru_cache(maxsize=1)
    def curnav(self): return self.balo.value/self.balo.units
    @lru_cache(maxsize=1)
    def tnav(self,t): return t.amt/t.units
    @lru_cache(maxsize=1)
    def holdyrs(self,t,sdt): return (sdt-t.txndt).days/365
    @lru_cache(maxsize=1)
    def cost(self): return self.bt.amt*self.units/self.bt.units
    @lru_cache(maxsize=1)
    def value(self): return (self.st.amt*self.units/self.st.units) if self.st else \
        self.balo.value*self.units/self.balo.units
    @lru_cache(maxsize=1)
    def cagr(self):
        snav = self.tnav(self.st) if self.st else self.curnav()
        bnav = self.tnav(self.bt)
        hldyrs = self.holdyrs(self.bt,self.st.txndt if self.st else self.balo.navdt)
        return 100*( pow(snav/bnav,1/hldyrs) - 1 ) if bnav and hldyrs else 0
    def __init__(self,units,bt,balo,f,st=None):
        self.units = units
        self.bt = bt
        self.balo = balo
        self.f = f
        self.st = st
        self.typ = ('EQ' if self.balo.typ in self.eqtyp else 'DT') if self.balo else '-'
        self.isfree = '-' if self.typ == '-' else (
            (self.st.txndt if self.st else self.balo.navdt) - self.bt.txndt
            ).days > 365*(1 if self.typ=='EQ' else 3)

class Fund:
    def _wildcard(self): return 0
    def value(self): return self.bo.value
    def cost(self): return self.bo.cost
    def rating(self): return self.vo.rating if self.vo and self.vo.rating else '-'
    def oyret(self): return self.vo.oyret if self.vo else '-'
    def amc(self): return self._amc
    def cat(self): return self.vo.cat.split('-')[0] if self.vo else '-'
    def subcat(self): return self.vo.cat if self.vo else '-'
    def shortf(self): return self.f[:30]
    def get(self,p): return getattr(self,p)()
    @lru_cache(maxsize=1)
    def cagr(self): return sum(mo.cagr()*mo.units for mo in self.bq)/self.bo.units
    def handlebuy(self,t): self.bq = self.bq + [SBMatch(t.units,t,self.bo,self.f)]
    def _sbmatch(self,tgtu,matches,bq,st):
        if tgtu < 0.0001: return matches,bq
        if bq==[]:
            print('Warning: buy transactions not found',st.txndt.strftime('%y%m%d'),st.fname)
            return [],[]
        bq0 = bq[0]
        bu,bt = bq0.units,bq0.bt
        return (matches+[SBMatch(tgtu,bt,self.bo,self.f,st)],
            [SBMatch(bu-tgtu,bt,self.bo,self.f,st)]+bq[1:]) if tgtu < bu else \
            self._sbmatch(tgtu-bu,matches+[SBMatch(bu,bt,self.bo,self.f,st)],bq[1:],st)
    def handlesale(self,t):
        matches,rembq =  self._sbmatch(-t.units,[],self.bq,t)
        self.sbmatch = self.sbmatch + [(t,matches)]
        self.bq = rembq
    def buildmatch(self,txns):
        self.bq = []
        self.sbmatch = []
        [ self.handlebuy(t) if t.units > 0 else self.handlesale(t) for t in txns if t.units ]
    def __init__(self,f,cd):
        self.f = f
        self.bo = cd.cnbal.get(f,None)
        self._amc = cd.cntxns[f][0].amc
        self.vo = vd.cnvo.get(f,None)
        self.buildmatch(cd.cntxns[f])

class Portfolio:
    def by(self,p): return groupby(sorted(self.holdings,key=lambda o:str(o.get(p))),lambda o:o.get(p))
    def urg_sbmatches(self): return [ (po,mo) for po in self.holdings for mo in po.bq ]
    def rg_sbmatches(self): return [ (po,st,mos) for po in (self.holdings+self.nonholdings)
        for (st,mos) in po.sbmatch ]
    def __init__(self):
        cd = CAMSData()
        self.holdings = [ Fund(f,cd) for f in cd.cnbal ]
        self.nonholdings = [ Fund(f,cd) for f in cd.cntxns if f not in cd.cnbal ]
