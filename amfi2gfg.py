url = 'https://www.amfiindia.com/spages/NAVAll_31Jan2018.txt'
gfnavfile = 'gfnav.json'

from urllib.request import urlopen, Request
import json

ls = [ l.decode().split(';')[3:5] for l in urlopen(url).readlines() ][1:]
d = { l[0]:float(l[1]) for l in ls if l != [] and l[1] != 'N.A.' }
json.dump(d,open(gfnavfile,'w'),indent=4)
