from xls2obj import XlsObjs
from conf import *
from itertools import groupby, chain
from functools import reduce
from functools import lru_cache
from datetime import datetime
import sys
import re
import json

# To analyze canonicalization errors set this to true, it will print all VR names
# of funds and those from CAMS for which VR name was not found
DBGCAN = False

def dt2fy(dt):
    y = dt.year
    fmt1 = '%4d'
    fmt2 = '%02d'
    return fmt1%y+'-'+fmt2%((y+1)%100) if dt.month > 3 else fmt1%(y-1)+'-'+fmt2%(y%100)

# Cannonicalizer Constructor accepts a list of tuples of form
# (pattern,replacement) or (patternlist,replacement). Operations are applied in
# the same sequence as in the list and an extra strip is applied in the end
class Canizer:
    def xform(self,s): return reduce(lambda s,pr: re.sub(*pr,s),self.spec,s).strip()
    def __init__(self,spec): self.spec = [ (re.compile(p),r) for p1,r in spec for p in (
            p1 if isinstance(p1,list) else [p1]) ]

class FData():
    fncaner = Canizer([
        ([
        r'\(\w+\)',
        r'\([Ee]rstwhile.*$',
        r'\([Ff]ormerly.*$',
        r'\(Earlier.*$',
        r'[)(]',
        r'\bFund\b',
        r'\bFd\b',
        r'\bF\b',
        r'\bPl\b',
        r'\bPln\b',
        r'\bPlan\b',
        r'Gr\.',
        r'GR',
        r'\bGrowth Option\b',
        r'\bGrowth\b',
        r'\bGrow\b',
        r'\bG\b',
        r'\bGr\b',
        r'\bGr\.\b',
        r'\bGro\b',
        r'\bGroOp\b',
        ],''),

        ( [r'-', r' +'], ' ' ),

        (['Mid Cap','MidCap'],'Midcap'),
        ('Small Cap','Smallcap'),
        ('SENSEX','Sensex'),
        ([r'\bDP\b',r'\bDir\b',r'\bDIRECT\b',r'\bDG\b',r'\bDrt\b',r'\bDIR\b',r'\bDr\b'],'Direct'),
        ('Blue Chip','Bluechip'),
        (r'\bTreas\b','Treasury'),
        ([r'\bAdv\b',r'\bAd\b'],'Advantage'),
        (['P/E',r'\bPEF\b'],'PE'),
        ([r'Eq\.',r'Equity\.',r'\bEq\b'],'Equity'),
        ('ABSL','Aditya Birla Sun Life'),
        (r'Equity&Debt','Equity & Debt'),
        (r'SensexPlan','Sensex'),
        (r'\bCF\b','Cash'),
        (r'\bEF\b','Equity'),
        (r'\bFEF\b','Focused Equity'),
        (r'Val\.','Value'),
        (r'\bFoc\b','Focused'),
        ])
    ttypcanner = Canizer([
        ([r'-', r' +'],' '),
        ([r'\(.*\)'],''),
        ('^.*Purchase.*$','Purchase'),
        ])
    # not all AMCs require prefixing
    amcprefix = {
        'DSP Mutual Fund' : 'DSP',
        'ICICI Prudential Mutual Fund' : 'ICICI Prudential',
        }

    def cname(self,fname,amc=''): return ' '.join([ self.amcprefix.get(amc,''), self.fncaner.xform(fname) ]).strip()
    def ctxntyp(self,s): return self.ttypcanner.xform(s)

class VRMFData(FData):
    def get(self,cnm,p): return self.cnvo[cnm].__dict__[p] if cnm in self.cnvo else None
    def typ(self,cname):
        if cname not in self.cnvo: return '-'
        cat,subcat = self.cnvo[cname].cat.split('-')
        return cat if cat in {'EQ','DT'} else 'EQ' if subcat in {'AH','AR','DAA'} else 'DT'
    def __init__(self):
        # convention prior to Aug 23, remove this after waiting for a while if they don't revert to this
        #csvfiles = list(mfdocsdir.glob('all-*-funds-*.csv'))
        # In Aug 2023 VR changed their file naming convention
        csvfiles = [
            next(mfdocsdir.glob( typ + '-*.csv' )) for typ in ['equity','debt','hybrid']
            ]
        if len(csvfiles) != 3:
            print('VRMFData: xls file count mismatch',len(csvfiles))
            sys.exit(1)
        objs = [ o for csv in csvfiles for o in XlsObjs(csv,specname='vrmf') ]
        self.cnvo = { self.cname(o.fname) : o for o in objs }
        if DBGCAN:
            for fname in self.cnvo: print('VR entry with fname',fname)

vd = VRMFData()
cii = json.load(ciifile.open()) if ciifile.exists() else {}

class CAMSData(FData):
    #prodre = re.compile('\(\w+\)')
    # In May 2022 CMS broke the compatibility between product code in
    # transaction sheet and scheme code in balances. Have reported the issue
    # but usually futile to expect them to do something about it. Covering it
    # up by prefixing hand written amc codes.

    amccode = {
        '360 ONE Mutual Fund'               : 'IF',
        'Aditya Birla Sun Life Mutual Fund' : 'B',
        'Bandhan Mutual Fund'               : 'G',
        'DSP Mutual Fund'                   : 'D',
        'HDFC Mutual Fund'                  : 'H',
        'HSBC Mutual Fund'                  : 'O',
        'ICICI Prudential Mutual Fund'      : 'P',
        'IDFC Mutual Fund'                  : 'G',
        'IIFL Mutual Fund'                  : 'IF',
        'Kotak Mutual Fund'                 : 'K',
        'L&T Mutual Fund'                   : 'F',
        'PPFAS Mutual Fund'                 : 'PP',
        'SBI Mutual Fund'                   : 'L',
        'Tata Mutual Fund'                  : 'T',
        'Union Mutual Fund'                 : 'UK',
        }

    def cashflow(self):
        yta = sorted( [ (dt2fy(t.txndt), self.ctxntyp(t.txntyp),t.amt)
            for f in self.cntxns.values() for t in f if t.amt ],
            reverse = True
            )
        return [ (*yt,sum(t[2] for t in yta)) for yt,yta in groupby(yta,lambda to:to[0:2]) ]
    #def prodid(self,fname): return self.prodre.search(fname).group()[1:-1]
    def prodid(self,bo): return self.amccode[bo.amc] + bo.prodid
    def __init__(self):
        balsfile = pfdatdir.joinpath('bals.xls')
        txnsfile = pfdatdir.joinpath('txns.xls')
        bobjs = [ bo for bo in XlsObjs(balsfile,specname='camsbals') if bo.value ]
        pidbal = { self.prodid(bo): bo for bo in bobjs }
        tobjs = XlsObjs(txnsfile,specname='camstxns')
        # Unclear why, but groupby produced wrong results when 1 product was in 2 folios
        #pidtxns = { pid:list(txns) for pid,txns in groupby(tobjs,lambda to:to.fid) }
        pidtxns = {}
        for t in tobjs: pidtxns.setdefault(t.fid,[]).append(t)
        pidcname = { pid:self.cname(ts[0].fname,ts[0].amc) for pid,ts in pidtxns.items() }
        self.cnbal = { pidcname[pid]:bo for pid,bo in pidbal.items() }
        self.cntxns = { pidcname[pid]:to for pid,to in pidtxns.items() }

class GFNAV(dict,FData):
    gfdate = datetime(2018,1,31)
    def __init__(self):
        gfnav = json.load(gfgfile.open()) if gfgfile.exists() else {}
        cngfnav = { self.cname(f):n for f,n in gfnav.items() }
        self.update(cngfnav)

gfnav = GFNAV()

class SBMatch:
    eqtyp = {'Equity','Balanced','Index Fund'}
    needgfnav = set()
    @lru_cache(maxsize=1)
    def curnav(self): return self.balo.value/self.balo.units
    @lru_cache(maxsize=1)
    def tnav(self,t): return t.amt/t.units
    @lru_cache(maxsize=1)
    def holdyrs(self,t,sdt): return (sdt-t.txndt).days/365
    @lru_cache(maxsize=1)
    def cost(self): return self.bt.amt*self.units/self.bt.units
    @lru_cache(maxsize=1)
    def icost(self):
        bfy = dt2fy(self.bt.txndt)
        if bfy not in cii: return '-'
        sfy = dt2fy(self.st.txndt if self.st else self.balo.navdt)
        if sfy not in cii: return '-'
        return self.cost()*cii[sfy]/cii[bfy]
    @lru_cache(maxsize=1)
    def gain(self): return self.value() - self.cost()
    @lru_cache(maxsize=1)
    def pgain(self): return self.gain()*100/self.cost() if self.cost() else '-'
    @lru_cache(maxsize=1)
    def igain(self):
        icost = self.icost()
        return icost if icost== '-' else self.value() - icost
    @lru_cache(maxsize=1)
    def gfgain(self):
        sdate = self.st.txndt if self.st else self.balo.navdt
        gfapplies = self.typ == 'EQ' and sdate > gfnav.gfdate and self.bt.txndt < gfnav.gfdate
        gfavailable = self.f in gfnav
        reported = self.f in SBMatch.needgfnav
        if gfapplies and not gfavailable and not reported:
            print('Entry needed in gfnav.json',self.f)
            SBMatch.needgfnav.add(self.f)
        # https://economictimes.indiatimes.com/wealth/tax/how-to-calculate-tax-on-ltcg-from-equity-shares-and-equity-mutual-funds/articleshow/70581749.cms
        return ( self.value() - max(
            self.bt.amt*self.units/self.bt.units,
            min( self.value(), gfnav[self.f]*self.units,)
            ) ) if gfavailable and gfapplies else self.gain()
    @lru_cache(maxsize=1)
    def value(self): return (self.st.amt*self.units/self.st.units) if self.st else \
        self.balo.value*self.units/self.balo.units
    @lru_cache(maxsize=1)
    def cagr(self):
        if self.deemedHoldDays() <= 365: return '-'
        snav = self.tnav(self.st) if self.st else self.curnav()
        bnav = self.tnav(self.bt)
        hldyrs = self.holdyrs(self.bt,self.st.txndt if self.st else self.balo.navdt)
        return 100*( pow(snav/bnav,1/hldyrs) - 1 ) if bnav and hldyrs else 0
    def deemedSaleDt(self): return self.st.txndt if self.st else self.balo.navdt
    def deemedHoldDays(self): return ( self.deemedSaleDt() - self.bt.txndt ).days
    def __init__(self,units,bt,balo,f,st=None):
        self.units = units
        self.bt = bt
        self.balo = balo
        self.f = f
        self.st = st
        self.typ = ('EQ' if self.balo.typ in self.eqtyp else 'DT') if self.balo else \
            vd.typ(self.f) if self.balo or self.st else '-'
        self.isfree = '-' if self.typ == '-' else self.deemedHoldDays() > 365*(
            1 if self.typ=='EQ' else 3)

class Fund:
    def _wildcard(self): return 0
    def value(self): return self.bo.value
    def cost(self): return self.bo.cost
    def rating(self): return self.vo.rating if self.vo and self.vo.rating else '-'
    def oyret(self): return self.vo.oyret if self.vo else '-'
    def amc(self): return self._amc
    def cat(self): return self.vo.cat.split('-')[0] if self.vo else '-'
    def subcat(self): return self.vo.cat if self.vo else '-'
    def shortf(self): return self.f[:30].strip()
    def get(self,p): return getattr(self,p)()
    @lru_cache(maxsize=1)
    def cagrCost(self): return sum(mo.cost() for mo in self.bq if mo.deemedHoldDays() > 365)
    @lru_cache(maxsize=1)
    def cagr(self):
        wtcagr = 0
        units = 0
        for mo in self.bq:
            if mo.deemedHoldDays() > 365:
                wtcagr += mo.cagr()*mo.units
                units += mo.units
        return ( wtcagr / units ) if units > 0 else '-'
    def handlebuy(self,t): self.bq = self.bq + [SBMatch(t.units,t,self.bo,self.f)]
    def _sbmatch(self,tgtu,matches,bq,st):
        if tgtu < 0.0001: return matches,bq
        if bq==[]:
            print('Warning: buy transactions not found',st.txndt.strftime('%y%m%d'),st.fname)
            return [],[]
        bq0 = bq[0]
        bu,bt = bq0.units,bq0.bt
        return (matches+[SBMatch(tgtu,bt,self.bo,self.f,st)],
            [SBMatch(bu-tgtu,bt,self.bo,self.f)]+bq[1:]) if tgtu < bu else \
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
        if DBGCAN and self.vo == None: print('Could not get VR entry for fund',f)
        self.buildmatch(cd.cntxns[f])

class Portfolio:
    def by(self,p): return groupby(sorted(self.holdings,key=lambda o:str(o.get(p))),lambda o:o.get(p))
    def urg_sbmatches(self): return [ (po,mo) for po in self.holdings for mo in po.bq ]
    def rg_sbmatches(self): return [ (po,st,mos) for po in (self.holdings+self.nonholdings)
        for (st,mos) in po.sbmatch ]
    def cashflow(self): return self.cd.cashflow()
    def __init__(self):
        self.cd = CAMSData()
        self.holdings = [ Fund(f,self.cd) for f in self.cd.cnbal ]
        self.nonholdings = [ Fund(f,self.cd) for f in self.cd.cntxns if f not in self.cd.cnbal ]
