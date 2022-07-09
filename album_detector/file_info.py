from functools import cached_property
import os
import json
import re

from album_detector import utils

def parse_cue(cue_str):
    cue_str = cue_str.replace('\ufeff', '') # Remove BOM
    cue_str = cue_str.replace('\r\n', '\n')
    d = cue_str.split('\n')
    general = {}
    tracks = []
    
    for line in d:
        if not line:
            continue
        elif line.startswith('REM DISCNUMBER '):
            pass
        elif line.startswith('REM TOTALDISCS '):
            pass
        elif line.startswith('REM ACCURATERIPID '):
            pass
        elif line.startswith('REM CATALOG '):
            pass
        elif line.startswith('REM GENRE '):
            general['genre'] = ' '.join(line.split(' ')[2:])
        elif line.startswith('REM DATE '):
            general['date'] = ' '.join(line.split(' ')[2:])
        elif line.startswith('REM DISCID '):
            pass
        elif line.startswith('REM COMMENT '):
            pass
        elif line.startswith('REM REPLAYGAIN_TRACK_GAIN '):
            pass
        elif line.startswith('REM REPLAYGAIN_ALBUM_GAIN '):
            pass
        elif line.startswith('REM REPLAYGAIN_ALBUM_PEAK '):
            pass
        elif line.startswith('REM COMPOSER '):
            pass
        elif line.startswith('SONGWRITER '):
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
        elif line.startswith('    SONGWRITER '):
            pass
        elif line.startswith('    ISRC '):
            pass
        elif line.startswith('    REM GENRE '):
            pass
        elif line.startswith('    REM DATE '):
            pass
        elif line.startswith('    REM REPLAYGAIN_TRACK_PEAK '):
            pass
        elif line.startswith('    REM REPLAYGAIN_TRACK_GAIN '):
            pass
        elif line.startswith('    REM COMPOSER '):
            pass
        elif line.startswith('    FLAGS PRE'):
            pass
        elif line.startswith('    FLAGS DCP'):
            pass # digital copy permitted
        elif line.startswith('    TITLE '):
            tracks[-1]['title'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
        elif line.startswith('    PERFORMER '):
            tracks[-1]['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
        elif line.startswith('    PREGAP '):
            # TODO: https://wiki.hydrogenaud.io/index.php?title=EAC_Gap_Settings
            pass
        elif line.startswith('    INDEX 00 '):
            # TODO: https://wiki.hydrogenaud.io/index.php?title=EAC_and_Cue_Sheets
            pass
        elif line.startswith('    INDEX 01 '):
            t = [int(n) for n in ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':')]
            tracks[-1]['start'] = 100 * (60 * t[0] + t[1]) + t[2]
        elif line.startswith('    INDEX 02 '):
            pass
        elif line.startswith('    INDEX 03 '):
            pass
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
        if 'mpg' == self.fext and 'MPEG' in self.type_str:
            return True
        if 'mov' == self.fext and 'QuickTime' in self.type_str:
            return True
        if 'mds' == self.fext: # disc image
            return True
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
    def is_empty_dir(self):
        if not os.path.isdir(self.fpath):
            return False
        return not list(os.listdir(self.fpath))

    @cached_property
    def is_file(self):
        return os.path.isfile(self.fpath)

    @cached_property
    def is_cue(self):
        return 'cue' == self.fext and 'text' in self.type_str

    @cached_property
    def is_log(self):
        if 'accurip' == self.fext and 'text' in self.type_str:
            return True
        if 'sfv' == self.fext and 'text' in self.type_str:
            return True
        if 'nfo' == self.fext and 'text' in self.type_str:
            return True
        if 'txt' == self.fext:
            return True
        if 'log' == self.fext:
            return True
        if 'album-hint.json' == self.basename:
            return True
        return False

    @cached_property
    def is_garbage(self):
        if self.fext.startswith('doc') and 'Microsoft Word' in self.type_str:
            return True
        if 'pdf' == self.fext and 'PDF' in self.type_str:
            return True
        if 'QuickTimeInstall' in self.basename:
            return True
        if 'inf' == self.fext and 'Autorun' in self.type_str:
            return True
        if 'ico' == self.fext and 'icon' in self.type_str:
            return True
        if 'HTML document' in self.type_str:
            return True
        if 'lrc' == self.fext and 'text' in self.type_str:
            return True
        if 'srr' == self.fext and 'data' == self.type_str:
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
        if 'ogg' == self.fext and 'Vorbis audio' in self.type_str:
            return True
        if 'm4a' == self.fext and 'MP4' in self.type_str:
            return True
        if 'm4a' == self.fext and 'Apple iTunes' in self.type_str:
            return True # TODO: this can also be ALAC, which is lossless
        if 'mp3' == self.fext and 'MPEG ADTS, layer III' in self.type_str:
            return True
        if 'mp3' == self.fext and 'Audio file with ID3' in self.type_str:
            return True
        if 'wma' == self.fext and 'Microsoft' in self.type_str:
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
                cue_str = utils.smart_read(self.fpath)
            except UnicodeDecodeError:
                encoding, confidence = utils.detect_encoding(self.fpath)
                assert encoding is not None
                if confidence < 90:
                    for f in os.listdir(self.dirname):
                        if f.lower().endswith('.cue'):
                            p = os.path.join(self.dirname, f)
                            enc, confid = utils.detect_encoding(p)
                            hit = False
                            _cue = utils.smart_read(p, enc, robust=True)
                            _info, _trk = parse_cue(_cue)
                            hit = os.path.isfile(os.path.join(self.dirname, _info['file']))
                            if hit:
                                # TODO: review and remove this block
                                assert encoding == enc, 'If this never got triggered, this block can be safely removed'
                                encoding = enc
                                break
                assert encoding, f"Debug info: {self.fpath}"
                cue_str = utils.smart_read(self.fpath, encoding, robust=True)
        elif self.is_audio:
            cue_str = self.embedded_cue
        return parse_cue(cue_str)

