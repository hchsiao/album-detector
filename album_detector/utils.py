import os
import subprocess
import signal
import json

# For entering hints interactively
import inquirer

# For charset detection
import chardet
import icu

from album_detector import file_info
from album_detector import album_info
from album_detector import knowledge
from album_detector import export

def get_hint(path, name, message, guess=None):
    hint_file = os.path.join(os.path.dirname(path), 'album-hint.json')
    hints = {}
    if os.path.isfile(hint_file):
        with open(hint_file, 'r') as f:
            hints = json.load(f)
    if name not in hints:
        hints[name] = _get_new_hint(name, message, guess)
        with open(hint_file, 'w') as f:
            f.write(json.dumps(hints))
    return hints[name]

def _get_new_hint(name, message, guess):
    if guess:
        questions = [
            inquirer.List(
                name,
                message=message,
                choices=guess,
            ),
        ]
    else:
        questions = [
            inquirer.Text(
                name,
                message=message,
            ),
        ]
    hints = inquirer.prompt(questions)
    if hints is None:
        exit(1)
    return hints[name]

def detect_encoding(fpath):
    with open(fpath, 'rb') as f:
        data = f.read()
        icu_encoding = icu.CharsetDetector(data).detect().getName()
        icu_confidence = icu.CharsetDetector(data).detect().getConfidence()
        icu_language = icu.CharsetDetector(data).detect().getLanguage()
        if icu_confidence > 60:
            return icu_encoding, icu_confidence
        else:
            charset = chardet.detect(data)
            chardet_encoding = charset['encoding']
            chardet_confidence = int(charset['confidence'] * 100)
            chardet_language = charset['language']
            if icu_confidence < 45 and chardet_confidence < 45:
                return get_hint(fpath, 'encoding', f'Need hint for charset: {fpath}'), -1
            elif icu_confidence > chardet_confidence:
                return icu_encoding, icu_confidence
            else:
                return chardet_encoding, chardet_confidence
    raise RuntimeError()

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
