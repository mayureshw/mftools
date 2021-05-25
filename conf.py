from pathlib import Path
import os

mfdocsdir = Path(os.environ.get('MFDOCSDIR','.'))
pfdatdir = Path(os.environ.get('PFDATDIR','.'))
ciifile = mfdocsdir.joinpath('cii.json')
gfgfile = mfdocsdir.joinpath('gfnav.json')
