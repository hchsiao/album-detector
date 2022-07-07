from functools import cached_property
import os
import json
import re

from album_detector import utils

def smart_read(filename, encoding='utf-8'):
    try:
        with open(filename, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError as e:
        if encoding.lower().startswith('gb') and encoding != 'gb18030':
            return smart_read(filename, 'gb18030')
        else:
            raise e

def parse_cue(cue_str):
    cue_str = cue_str.replace('\ufeff', '') # Remove BOM
    cue_str = cue_str.replace('\r\n', '\n')
    d = cue_str.split('\n')
    general = {}
    tracks = []
    
    for line in d:
        if not line:
            continue
        elif line.startswith('REM GENRE '):
            general['genre'] = ' '.join(line.split(' ')[2:])
        elif line.startswith('REM DATE '):
            general['date'] = ' '.join(line.split(' ')[2:])
        elif line.startswith('REM DISCID '):
            pass
        elif line.startswith('REM COMMENT '):
            pass
        elif line.startswith('REM COMPOSER '):
            pass
        elif line.startswith('CATALOG '):
            pass
        elif line.startswith('PERFORMER '):
            general['artist'] = ' '.join(line.split(' ')[1:]).replace('"', '')
        elif line.startswith('TITLE '):
            general['album'] = ' '.join(line.split(' ')[1:]).replace('"', '')
        elif line.startswith('FILE '):
            general['file'] = ' '.join(line.split(' ')[1:-1]).replace('"', '')
        elif line.startswith('  TRACK '):
            track = general.copy()
            track['track'] = int(line.strip().split(' ')[1], 10)
            tracks.append(track)
        elif line.startswith('    ISRC '):
            pass
        elif line.startswith('    REM COMPOSER '):
            pass
        elif line.startswith('    FLAGS DCP'):
            pass # digital copy permitted
        elif line.startswith('    TITLE '):
            tracks[-1]['title'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
        elif line.startswith('    PERFORMER '):
            tracks[-1]['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
        elif line.startswith('    INDEX 00 '):
            # TODO: https://wiki.hydrogenaud.io/index.php?title=EAC_Gap_Settings
            # TODO: https://wiki.hydrogenaud.io/index.php?title=EAC_and_Cue_Sheets
            pass
        elif line.startswith('    INDEX 01 '):
            t = [int(n) for n in ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':')]
            tracks[-1]['start'] = 100 * (60 * t[0] + t[1]) + t[2]
        else:
            assert False, f'Unknown cue line: {line} (bytes: {line.encode()})'
    
    for i in range(len(tracks)):
        if i != len(tracks) - 1:
            tracks[i]['duration'] = tracks[i + 1]['start'] - tracks[i]['start']
    
    return general, tracks

class FileInfo:
    def __init__(self, fpath):
        self.fpath = fpath

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'{self.basename}'

    @cached_property
    def basename(self):
        return os.path.basename(self.fpath)

    @cached_property
    def dirname(self):
        return os.path.dirname(self.fpath)

    @cached_property
    def fext(self):
        return self.basename.split('.')[-1].lower()

    @cached_property
    def type_str(self):
        return utils.shell(
                f'file "{self.fpath}"').replace(f'{self.fpath}: ', '')

    @cached_property
    def _ffprobe(self):
        if not self.is_audio:
            return None
        jsn = utils.shell('ffprobe '
                '-loglevel 0 '
                '-print_format json '
                '-show_format '
                f'"{self.fpath}"')
        return json.loads(jsn)
    
    @cached_property
    def audio_info(self):
        if not self.is_audio:
            return None
        fmt = self._ffprobe['format']
        if 'tags' in fmt:
            return {k.lower(): v for k, v in fmt['tags'].items()}
        else:
            return None
    
    @cached_property
    def track_no(self):
        if not self.is_audio or 'track' not in self.audio_info:
            return None
        match = re.match(r'(\d+)/\d+', self.audio_info['track'])
        if match:
            return int(match.group(1))
        else:
            return int(self.audio_info['track'])
    
    @cached_property
    def embedded_cue(self):
        if self.is_tta_audio or self.is_ape_audio:
            # cannot carry embedded CUE
            return None
        tags = self.audio_info
        if tags and 'Cuesheet' in tags:
            return tags['Cuesheet'] 
        if tags and 'cuesheet' in tags:
            return tags['cuesheet'] 
        return None

    @cached_property
    def is_video(self):
        if 'iso' == self.fext: # TODO: not necessarily a video
            return True
        if 'mkv' == self.fext:
            return True
        return False

    @cached_property
    def is_image(self):
        if 'TIFF image' in self.type_str:
            return True
        if 'JPEG 2000' in self.type_str:
            return True
        if 'JPEG image' in self.type_str:
            return True
        if 'PNG image' in self.type_str:
            return True
        if 'data' == self.type_str and 'bmp' == self.fext:
            return True
        if 'PC bitmap' in self.type_str and 'bmp' == self.fext:
            return True
        return False

    @cached_property
    def is_file(self):
        return os.path.isfile(self.fpath)

    @cached_property
    def is_cue(self):
        return 'cue' == self.fext and 'text' in self.type_str

    @cached_property
    def is_log(self):
        if 'txt' == self.fext:
            return True
        if 'log' == self.fext:
            return True
        return False

    @cached_property
    def is_garbage(self):
        if 'lrc' == self.fext and 'text' in self.type_str:
            return True
        if 'fpl' == self.fext and 'data' == self.type_str:
            return True
        if 'Thumbs.db' == self.basename:
            return True
        if 'url' == self.fext:
            return True
        if 'm3u' == self.fext:
            return True
        if 'm3u8' == self.fext:
            return True
        if 'inf.xml' == self.basename:
            return True
        if 'Apple Desktop Services Store' == self.type_str:
            # .DS_Store
            return True
        if 'AppleDouble encoded Macintosh file' == self.type_str:
            return True
        return False

    @cached_property
    def is_cover_image(self):
        if not self.is_image:
            return False
        if self.basename.lower().startswith('cover'):
            return True
        if self.basename.lower().startswith('folder'):
            return True
        return False

    @cached_property
    def is_audio(self):
        return self.is_lossy_audio or self.is_lossless_audio

    @cached_property
    def is_lossy_audio(self):
        if 'mp3' == self.fext and 'MPEG ADTS, layer III' in self.type_str:
            return True
        if 'mp3' == self.fext and 'Audio file with ID3' in self.type_str:
            return True
        return False

    @cached_property
    def is_lossless_audio(self):
        _fmt = [
                self.is_tak_audio,
                self.is_ape_audio,
                self.is_flac_audio,
                self.is_tta_audio,
                self.is_wav_audio,
                ]
        return any(_fmt)

    @cached_property
    def is_flac_audio(self):
        return "FLAC audio" in self.type_str

    @cached_property
    def is_ape_audio(self):
        return "Monkey's Audio" in self.type_str

    @cached_property
    def is_tta_audio(self):
        return "True Audio Lossless Audio" in self.type_str

    @cached_property
    def is_tak_audio(self):
        return 'data' == self.type_str and 'tak' == self.fext

    @cached_property
    def is_wav_audio(self):
        return 'WAVE audio' in self.type_str

    @cached_property
    def ftype(self):
        """ TODO: Avoid string literals """
        if not self.is_file:
            return 'not_file'
        if self.is_garbage:
            return 'garbage'
        if self.is_log and not self.is_cue:
            return 'log'
        if self.is_video:
            return 'video'
        if self.is_cue:
            return 'cue'
        if self.is_lossless_audio:
            return 'audio(lossless)'
        if self.is_lossy_audio:
            return 'audio(lossy)'
        if self.is_image:
            return 'image' if not self.is_cover_image else 'image(cover)'
        return 'unknown'

    @cached_property
    def cue_info(self):
        if self.is_cue:
            try:
                cue_str = smart_read(self.fpath)
            except UnicodeDecodeError:
                encoding, confidence = utils.detect_encoding(self.fpath)
                if encoding is None:
                    encoding = utils.get_hint('encoding', f'Need hint for charset: {self.fpath}')
                elif confidence < 90:
                    for f in os.listdir(self.dirname):
                        if f.lower().endswith('.cue'):
                            p = os.path.join(self.dirname, f)
                            enc, confid = utils.detect_encoding(p)
                            hit = False
                            _cue = smart_read(p, enc)
                            _info, _trk = parse_cue(_cue)
                            hit = os.path.isfile(os.path.join(self.dirname, _info['file']))
                            if hit:
                                encoding = enc
                                break
                assert encoding, f"Debug info: {self.fpath}"
                cue_str = smart_read(self.fpath, encoding)
        elif self.is_audio:
            cue_str = self.embedded_cue
        return parse_cue(cue_str)

