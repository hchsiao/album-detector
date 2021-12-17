# TODO: check https://github.com/flacon/flacon/issues/41
import argparse
import os

from utils import mkfilemap, mkalbum

parser = argparse.ArgumentParser(description='TODO')
parser.add_argument('path') 
parser.add_argument('--output-dir', default='.') 

args = parser.parse_args()

path = os.path.normpath(args.path)

filemap = mkfilemap(path)
album = mkalbum(filemap)

cmds = album.cmds(args.output_dir)
for cmd in cmds:
    print(cmd)
