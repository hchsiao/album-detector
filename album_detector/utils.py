import os
import subprocess
import signal

import chardet

from album_detector import file_info
from album_detector import album_info
from album_detector import knowledge
from album_detector import export

def detect_encoding(fpath):
    with open(fpath, 'rb') as f:
        charset = chardet.detect(f.read())
        encoding = charset['encoding']
        confidence = charset['confidence']
        language = charset['language']
        return encoding, confidence
    return None

def shell(cmd):
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) as p:
        p.wait()
        ercd = p.returncode
        assert ercd == 0, f'Exit code of {cmd} is {ercd}'
        retval = p.stdout.read().decode().strip()
    return retval

def mkfilelist(path: str, max_files: int = 200):
    files = shell(f'find "{path}" | head -n {max_files+1}').split('\n')
    assert not len(files) > max_files, 'Too many files for an album.'
    finfos = [file_info.FileInfo(fp) for fp in files]
    return finfos

def handle_path(path, output_dir, audio_only):
    path = os.path.normpath(path)
    finfos = mkfilelist(path)
    album = album_info.AlbumInfo(finfos)
    cmds = export.export_cmds(album, output_dir, audio_only=audio_only)
    return cmds

def handle_path_cue(path):
    path = os.path.normpath(path)
    finfos = mkfilelist(path)
    album = album_info.AlbumInfo(finfos)
    return export.export_cue(album)

def do_scan(album_set, album_cb, include_failed=False, limit=None):
    retval = {}
    album_set = os.path.normpath(album_set)
    n_total = len(os.listdir(album_set))
    n_processing = 0
    for d in os.listdir(album_set):
        n_processing += 1
        print(f'Processing {n_processing}/{n_total}...')
        path = os.path.join(album_set, d)
        try:
            retval[path] = album_cb(path)
        except KeyboardInterrupt:
            print(f'Interrupted...')
            return None
        except:
            print(f'Skipping {path}')
            if include_failed:
                retval[path] = None
        if type(limit) is int and n_processing >= limit:
            break
    return retval
