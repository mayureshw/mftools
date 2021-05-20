from xls2obj import XlsObjs
from conf import *
from itertools import groupby
from functools import reduce
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
    def __init__(self):
        csvfiles = list(mfdocsdir.glob('all-*-funds-*.csv'))
        if len(csvfiles) != 3:
            print('VRMFData: xls file count mismatch',len(csvfiles))
            sys.exit(1)
        objs = [ o for csv in csvfiles for o in XlsObjs(csv,specname='vrmf') ]
        self.cnvo = { self.cname(o.fname) : o for o in objs }

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
    def handlebuy(self,t): self.bq = self.bq + [(t.units,t)]
    def _sbmatch(self,tgtu,matches,bq):
        bu,bt = bq[0]
        return (matches,bq) if tgtu < 0.0001 else \
            ( matches+[(tgtu,bt)], [(bu-tgtu,bt)]+bq[1:] ) if tgtu < bu else \
            self._sbmatch(tgtu-bu,matches+[(bu,bt)],bq[1:])
    def handlesale(self,t):
        matches,rembq =  self._sbmatch(-t.units,[],self.bq)
        self.sbmatch = self.sbmatch + [(t,matches)]
        self.bq = rembq
    def __init__(self,txns):
        self.bq = []
        self.sbmatch = []
        [ self.handlebuy(t) if t.amt > 0 else self.handlesale(t) for t in txns if t.amt ]

class PFObj:
    def value(self): return self.bo.value
    def cagr(self): return 0
    def cost(self): return self.bo.cost
    def rating(self): return self.vo.rating if self.vo and self.vo.rating else '-'
    def oyret(self): return self.vo.oyret if self.vo else '-'
    def amc(self): return self._amc
    def cat(self): return self.vo.cat.split('-')[0] if self.vo else '-'
    def subcat(self): return self.vo.cat if self.vo else '-'
    def shortf(self): return self.f[:30]
    def get(self,p): return getattr(self,p)()
    def __init__(self,f,cd,vd):
        self.f = f
        self.bo = cd.cnbal[f]
        self._amc = cd.cntxns[f][0].amc
        self.vo = vd.cnvo.get(f,None)
        self.sbmatch = SBMatch(cd.cntxns[f])

class PFData:
    def by(self,p): return groupby(sorted(self.pfobjs,key=lambda o:str(o.get(p))),lambda o:o.get(p))
    def __init__(self):
        cd = CAMSData()
        vd = VRMFData()
        self.pfobjs = { PFObj(f,cd,vd) for f in cd.cnbal }
