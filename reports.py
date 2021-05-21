import sys

def multisort(tbl,l): return tbl if l==[] else \
    sorted(multisort(tbl,l[1:]),key=lambda x:x[abs(l[0])-1],reverse=l[0]<0)

# Pardon wrong / unsuitable format strings
def fmt(fmts,d):
    try: return fmts % d
    except Exception: return d

def printTbl(tbl,
    title=None,
    proj=None,      # 1 based columns to project in tbl
    sort=[],        # 1 based column no w/ -sign to indicate reverse in tbl
    colnames=None,
    formaters={},   # 1 based keys : formatstr in tbl
    file=sys.stdout
    ):
    if title:
        print(title,file=file)
        print('='*len(title),'\n',file=file)

    stbl = multisort(tbl,sort)

    effproj = [c-1 for c in proj] if proj else range(len(tbl[0]))

    projl = [ [ fmt(formaters.get(i+1,'%s'),r[i]) for i in effproj] for r in stbl ]

    projc = [colnames]+projl if colnames else projl

    widths = [ max([len(r[c]) for r in projc]) for c in range(len(projc[0])) ]
    ul = ['-'*widths[i] for i,t in enumerate(colnames)] if colnames else None
    projcul = [projc[0]] + [ul]  + projc[1:] + [ul] if colnames else projc

    print('\n'.join(
        '  '.join( c.rjust(widths[i]) for i,c in enumerate(r) ) for r in projcul
        ),file=file)
    
# Test driver
if __name__=='__main__':
    tbl = [
        (1,2,3,4,5),
        (5,4,3,2,1),
        (6,7,8,9,10),
        (10,9,8,7,6),
        ]
    printTbl(tbl,'test',proj=[0,4],sort=[2,-3],colnames=['abc','bcde'],formaters={0:'%05d'})
    printTbl(tbl,'test',proj=[0,4],sort=[2,-3],formaters={0:'%05d'})
