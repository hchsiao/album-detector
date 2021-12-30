import argparse
import os
import json

from album_detector import mkalbum

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('prefix') 
    parser.add_argument('--append', action='store_true')

    args = parser.parse_args()
    
    prefix = os.path.normpath(args.prefix)
    new_testdata = {}

    n_total = len(os.listdir(prefix))
    n_processing = 0
    for d in os.listdir(prefix):
        n_processing += 1
        print(f'Processing {n_processing}/{n_total}...')
        path = os.path.join(prefix, d)
        try:
            album = mkalbum(path)
            cmds = album.cmds('/tmp', audio_only=False)
            cmds = '\n'.join(cmds)
            new_testdata[path] = cmds
        except:
            print(f'Skipping {path}')
    
    if os.path.isfile('testdata.json') and args.append:
        with open('testdata.json', 'r') as f:
            testdata = json.loads(f.read())
        for k, v in new_testdata.items():
            testdata[k] = v
    else:
        testdata = new_testdata

    with open('testdata.json', 'w') as f:
        f.write(json.dumps(testdata))

if __name__ == '__main__':
    main()

