import argparse
import os
import json

from album_detector import utils

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('--album-dirs', nargs='+', default=[]) 
    parser.add_argument('--output') 

    args = parser.parse_args()
    
    testdata = {}
    for album_dir in args.album_dirs:
        album_dir = os.path.normpath(album_dir)
        new_testdata = {}

        n_total = len(os.listdir(album_dir))
        n_processing = 0
        for d in os.listdir(album_dir):
            n_processing += 1
            print(f'Processing {n_processing}/{n_total}...')
            path = os.path.join(album_dir, d)
            try:
                cmds = utils.handle_path(path, '/tmp', False)
                cmds = '\n'.join(cmds)
                new_testdata[path] = cmds
            except KeyboardInterrupt:
                print(f'Interrupted...')
                exit(2)
            except:
                print(f'Skipping {path}')
        testdata.update(new_testdata)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(json.dumps(testdata))

if __name__ == '__main__':
    main()

