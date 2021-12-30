import argparse
import os

from .utils import mkalbum

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('path') 
    parser.add_argument('--output-dir', default='.') 
    parser.add_argument('--audio-only', action='store_true')
    parser.add_argument('--doit', action='store_true')

    args = parser.parse_args()
    
    path = os.path.normpath(args.path)
    
    album = mkalbum(path)
    cmds = album.cmds(args.output_dir, audio_only=args.audio_only)
    for cmd in cmds:
        if args.doit:
            os.system(cmd)
        else:
            print(cmd)
