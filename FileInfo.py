from functools import cached_property
import os
import json

import utils

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
    def _tags(self):
        if not self.is_audio:
            return None
        jsn = utils.shell('ffprobe '
                '-loglevel 0 '
                '-print_format json '
                '-show_format '
                f'"{self.fpath}"')
        fmt = json.loads(jsn)['format']
        return fmt['tags'] if 'tags' in fmt else None
    
    @cached_property
    def embedded_cue(self):
        if self.is_tta_audio or self.is_ape_audio:
            # cannot carry embedded CUE
            return None
        print(self)
        tags = self._tags()
        if tags and 'Cuesheet' in tags:
            return tags['Cuesheet'] 
        if tags and 'cuesheet' in tags:
            return tags['cuesheet'] 
        return None

    @cached_property
    def is_image(self):
        if 'JPEG' in self.type_str:
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
        if 'inf.xml' == self.basename:
            return True
        if 'Apple Desktop Services Store' == self.type_str:
            # .DS_Store
            return True
        return False

    @cached_property
    def is_cover_image(self):
        if not self.is_image:
            return False
        if 'cover' in self.basename.lower():
            return True
        return False

    @cached_property
    def is_audio(self):
        return self.is_lossy_audio or self.is_lossless_audio

    @cached_property
    def is_lossy_audio(self):
        return False

    @cached_property
    def is_lossless_audio(self):
        _fmt = [
                self.is_tak_audio,
                self.is_ape_audio,
                self.is_flac_audio,
                self.is_tta_audio,
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
    def ftype(self):
        if not self.is_file:
            return 'not_file'
        if self.is_garbage:
            return 'garbage'
        if self.is_log and not self.is_cue:
            return 'log'
        if self.is_cue:
            return 'cue'
        if self.is_lossless_audio:
            return 'audio(lossless)'
        if self.is_image:
            return 'image' if not self.is_cover_image else 'image(cover)'
        return 'unknown'

    @cached_property
    def cue_info(self):
        if self.is_cue:
            cue_str = open(self.fpath, 'r').read()
            cue_str = cue_str.replace('\ufeff', '') # Remove BOM
        elif self.is_audio:
            cue_str = self.embedded_cue
        d = cue_str.splitlines()
        general = {}
        tracks = []
        
        for line in d:
            if line.startswith('REM GENRE '):
                general['genre'] = ' '.join(line.split(' ')[2:])
            elif line.startswith('REM DATE '):
                general['date'] = ' '.join(line.split(' ')[2:])
            elif line.startswith('REM DISCID '):
                pass
            elif line.startswith('REM COMMENT '):
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
            elif line.startswith('    TITLE '):
                tracks[-1]['title'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('    PERFORMER '):
                tracks[-1]['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('    INDEX 00 '):
                pass
            elif line.startswith('    INDEX 01 '):
                t = [int(n) for n in ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':')]
                tracks[-1]['start'] = 60 * t[0] + t[1] + t[2] / 100.0
            else:
                assert False, f'Unknown cue line: {line}'
        
        for i in range(len(tracks)):
            if i != len(tracks) - 1:
                tracks[i]['duration'] = tracks[i + 1]['start'] - tracks[i]['start']
        
        return general, tracks

