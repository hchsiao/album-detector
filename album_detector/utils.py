import os
import sys
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

no_interact = False

def smart_read(filename, encoding='utf-8', robust=False):
    try:
        with open(filename, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        if encoding.lower().startswith('gb') and encoding != 'gb18030':
            return smart_read(filename, 'gb18030', robust)
        elif robust:
            with open(filename, 'rb') as f:
                data = f.read()
                return str(icu.CharsetDetector(data).detect())
        else:
            raise

_HINT_FILE = 'album-hint.json'

def has_hint(path, name):
    hint_file = os.path.join(os.path.dirname(path), _HINT_FILE)
    if os.path.isfile(hint_file):
        with open(hint_file, 'r') as f:
            hints = json.load(f)
            return name in hints
    return False

def erase_hint(path, name):
    hint_file = os.path.join(os.path.dirname(path), _HINT_FILE)
    if os.path.isfile(hint_file):
        with open(hint_file, 'r') as f:
            hints = json.load(f)
            del hints[name]
        with open(hint_file, 'w') as f:
            f.write(json.dumps(hints))

def get_hint(path, name, message, guess=None, find_common=False):
    hint_file = os.path.join(os.path.dirname(path), _HINT_FILE)
    hints = {}
    if os.path.isfile(hint_file):
        with open(hint_file, 'r') as f:
            hints = json.load(f)
    if name not in hints:
        hints[name] = _get_new_hint(name, message, guess, find_common)
        with open(hint_file, 'w') as f:
            f.write(json.dumps(hints))
    return hints[name]

def _get_new_hint(name, message, guess=None, find_common=False):
    assert not no_interact
    MANUALLY_ENTER = '<Manually enter>'
    if guess:
        guess = list(guess)
        if find_common:
            common_str = os.path.commonprefix(guess).strip()
            if common_str and common_str not in guess:
                guess.append(common_str)
        questions = [
            inquirer.List(
                name,
                message=message,
                choices=guess + [MANUALLY_ENTER],
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
    if hints[name] == MANUALLY_ENTER:
        return _get_new_hint(name, 'Please enter:')
    return hints[name]

def confirm(message):
    print(message)
    questions = [
        inquirer.Confirm('confirmed', message='Does it looks good?'),
    ]
    answers = inquirer.prompt(questions)
    return answers['confirmed']

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
                new_hint = not has_hint(fpath, 'encoding')
                while True:
                    guided_encoding = get_hint(fpath, 'encoding', f'Need hint for charset: {fpath}', ['shift_jis'])
                    if not new_hint:
                        break
                    elif confirm(smart_read(fpath, guided_encoding)):
                        break
                    else:
                        erase_hint(fpath, 'encoding')
                return guided_encoding, -1
            elif icu_confidence > chardet_confidence:
                return icu_encoding, icu_confidence
            else:
                return chardet_encoding, chardet_confidence
    raise RuntimeError()

def shell(cmd):
    cmd = cmd.replace('`', '\`')
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) as p:
        p.wait()
        ercd = p.returncode
        stdout = p.stdout.read()
        # Sometimes `file` command emits wierd bytes
        retval = stdout.decode(errors='ignore').strip()
        if ercd != 0:
            print(retval, file=sys.stderr)
            raise RuntimeError(f'Exit code of {cmd} is {ercd}')
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

def handle_path_playlist(path):
    path = os.path.normpath(path)
    finfos = mkfilelist(path)
    album = album_info.AlbumInfo(finfos)
    is_splitted = [disc.audio_splitted for disc in album.discs]
    assert len(set(is_splitted)) == 1
    is_splitted = is_splitted[0]
    if is_splitted:
        return export.export_m3u(album), 'm3u'
    else:
        return export.export_cue(album), 'cue'

def do_scan(album_set, album_cb, include_failed=False, limit=None):
    retval = {}
    album_set = os.path.normpath(album_set)
    n_total = len(os.listdir(album_set))
    n_processing = 0
    for d in os.listdir(album_set):
        n_processing += 1
        print(f'Processing {n_processing}/{n_total}...')
        path = os.path.join(album_set, d)
        finfo = file_info.FileInfo(path)
        if finfo.is_file or finfo.is_empty_dir:
            print(f'Ignoring {path}')
            continue
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
