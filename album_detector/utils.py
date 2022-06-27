import os
import subprocess
import signal

from album_detector import file_info
from album_detector import album_info
from album_detector import knowledge
from album_detector import export

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

