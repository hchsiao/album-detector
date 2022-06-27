import argparse
import os

from album_detector import utils

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('path') 
    parser.add_argument('--output-dir', default='.') 
    parser.add_argument('--audio-only', action='store_true')
    parser.add_argument('--doit', action='store_true')

    args = parser.parse_args()
    
    path = os.path.normpath(args.path)
    cmds = utils.handle_path(path, args.output_dir, args.audio_only)
    for cmd in cmds:
        if args.doit:
            os.system(cmd)
        else:
            print(cmd)

if __name__ == "__main__":
    main()
