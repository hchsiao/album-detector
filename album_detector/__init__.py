import argparse
import os
import json

from album_detector import utils
from album_detector import file_info

def album_cb(path):
    cmds = utils.handle_path(path, '/tmp', False)
    return bool(cmds)

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('path') 
    parser.add_argument('--output-dir', default='.') # TODO: check if still working with bazel?
    parser.add_argument('--audio-only', action='store_true')
    parser.add_argument('--doit', action='store_true')
    parser.add_argument('--playlist', action='store_true')
    parser.add_argument('--mkindex', action='store_true')
    parser.add_argument('--dump-fail', action='store_true')
    parser.add_argument('--check-fail', action='store_true')
    args = parser.parse_args()
    path = os.path.normpath(args.path)

    if args.mkindex:
        input_dir = os.path.normpath('/tmp')
        indexes = utils.do_scan(input_dir, utils.handle_index)
        with open(path, 'w') as f:
            f.write(json.dumps(indexes))
    elif args.check_fail:
        with open(args.path, 'r') as f:
            path_list = json.loads(f.read())
            for path in path_list:
                print(f'Challenging {path}')
                album_cb(path)
    elif args.dump_fail:
        utils.no_interact = True
        dump = utils.do_scan(path, album_cb, include_failed=True)
        failed = [p for p in dump if not dump[p]]
        with open('failed.json', 'w') as f:
            f.write(json.dumps(failed))
    else:
        if args.playlist:
            playlists, filetype = utils.handle_path_playlist(path)
            playlist_files = []
            for index, playlist in enumerate(playlists):
                filename = f'playlist_{index}.{filetype}'
                if args.doit:
                    playlist_files.append(filename)
                    with open(filename, 'w') as f:
                        f.write(playlist)
                else:
                    print(playlist)
            if args.doit:
                playlist_files = ' '.join(playlist_files)
                utils.shell(f'open {playlist_files}')
        else:
            cmds = utils.handle_path(path, args.output_dir, args.audio_only)
            for cmd in cmds:
                if args.doit:
                    os.system(cmd)
                else:
                    print(cmd)

if __name__ == "__main__":
    main()
