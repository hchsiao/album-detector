import os
import subprocess

import FileInfo
import AlbumInfo

def shell(cmd):
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    res.wait()

    ercd = res.returncode
    assert ercd == 0, f'Exit code of {cmd} is {ercd}'
    return res.stdout.read().decode().strip()

def mkfilemap(path):
    files = shell(f'find "{path}"').split('\n')
    finfo = [FileInfo.FileInfo(fp) for fp in files]

    unknown = [f for f in finfo if 'unknown' == f.ftype]
    if unknown:
        for uf in unknown:
            print(f'Filename: {uf.basename}')
            print(f'Magic string: {uf.type_str}')
        assert not unknown

    filemap = {
            'cover': [f for f in finfo if 'image(cover)' == f.ftype],
            'logs': [f for f in finfo if 'log' == f.ftype or 'cue' == f.ftype],
            'cue': [f for f in finfo if 'cue' == f.ftype],
            'audio': [f for f in finfo if 'audio' == f.ftype],
            'booklets': [f for f in finfo if 'image' == f.ftype],
            }
    return filemap

def mkalbum(filemap):
    return AlbumInfo.AlbumInfo(filemap)
