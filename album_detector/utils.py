import os
import subprocess
import signal

from . import FileInfo, AlbumInfo

def shell(cmd):
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) as p:
        p.wait()
        ercd = p.returncode
        assert ercd == 0, f'Exit code of {cmd} is {ercd}'
        retval = p.stdout.read().decode().strip()
    return retval

def mkfilemap(path):
    files = shell(f'find "{path}"').split('\n')
    finfo = [FileInfo.FileInfo(fp) for fp in files]

    # Assume basenames are unique
    basenames = [f.basename for f in finfo]
    assert len(set(basenames)) == len(basenames)

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
            'audio(lossless)': [f for f in finfo if 'audio(lossless)' == f.ftype],
            'audio(lossy)': [],
            'booklets': [f for f in finfo if 'image' == f.ftype],
            }

    # Select one of the covers as the only cover
    filemap['cover'] = filemap['cover'][0] if filemap['cover'] else None

    return filemap

def mkalbum(filemap):
    return AlbumInfo.AlbumInfo(filemap)
