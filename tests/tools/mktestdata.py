import argparse
import os
import json

from album_detector import utils

def album_cb(path):
    cmds = utils.handle_path(path, '/tmp', False)
    cmds = '\n'.join(cmds)
    return cmds

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--album-dirs', nargs='+', default=[]) 
    parser.add_argument('--output') 

    args = parser.parse_args()
    
    testdata = {}
    for album_dir in args.album_dirs:
        new_testdata = utils.do_scan(album_dir, album_cb)
        testdata.update(new_testdata)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(json.dumps(testdata))

if __name__ == '__main__':
    main()

