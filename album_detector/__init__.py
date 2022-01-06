import argparse
import os

from .utils import mkalbum

def handle_item(path, output_dir, audio_only, dry_run):
    path = os.path.normpath(path)
    
    album = mkalbum(path)
    cmds = album.cmds(output_dir, audio_only=audio_only)
    for cmd in cmds:
        if dry_run:
            print(cmd)
        else:
            os.system(cmd)

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('path') 
    parser.add_argument('--output-dir', default='.') 
    parser.add_argument('--audio-only', action='store_true')
    parser.add_argument('--doit', action='store_true')

    args = parser.parse_args()
    
    path = os.path.normpath(args.path)
    handle_item(path, args.output_dir, args.audio_only, not args.doit)
