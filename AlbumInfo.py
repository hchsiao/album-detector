from functools import cached_property
import json
import os

import utils

class AlbumInfo:
    def __init__(self, files):
        self.files = files
        self.audio_with_cue = [
                f for f in self.files['audio(lossless)']
                if self._embedded_cue_str(f.fpath)]

        # TODO: don't assume there's only one disc
        # TODO: search for '[0]' when fixing
        assert len(self.files['cue']) <= 1
        assert len(self.audio_with_cue) <= 1

        if self.cue:
            self.info, self.tracks = self._parse_cue(self.cue)
        else:
            # TODO: handle case: both implicit/explicit cue not exist
            # e.g. Splitted flacs
            raise NotImplementedError()

        if self.audio_with_cue:
            self.info['file'] = self.audio_with_cue[0].fpath
        else:
            self.info['file'] = os.path.join(self.cue_file.dirname, self.info['file'])

        if not os.path.exists(self.info['file']):
            print(self.info['file'])
            # TODO: adjust cue pointed audio file
            raise NotImplementedError()

    def _tags(self, f):
        jsn = utils.shell('ffprobe '
                '-loglevel 0 '
                '-print_format json '
                '-show_format '
                f'"{f}"')
        fmt = json.loads(jsn)['format']
        return fmt['tags'] if 'tags' in fmt else None

    def _embedded_cue_str(self, f):
        tags = self._tags(f)
        if tags and 'Cuesheet' in tags:
            return tags['Cuesheet'] 
        if tags and 'cuesheet' in tags:
            return tags['cuesheet'] 
        return None

    def _parse_cue(self, cue):
        d = cue.splitlines()
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

    @cached_property
    def cue(self):
        """Returns cue string (embedded cue are preferred)."""
        if self.audio_with_cue:
            embedded_cue = self._embedded_cue_str(self.audio_with_cue[0].fpath)
            self.cue_file = self.files['audio(lossless)'][0]
            return embedded_cue
        elif self.files['cue']:
            retval = open(self.files['cue'][0].fpath, 'r').read()
            self.cue_file = self.files['cue'][0]
            return retval.replace('\ufeff', '') # Remove BOM
        else:
            return None

    @cached_property
    def album_dirname(self):
        return f"{self.info['artist']} - {self.info['album']}"

    def cmds(self, output_dir):
        retval = []
        album_dir = os.path.join(output_dir, self.album_dirname)
        cover_img = self.files['cover'].fpath
        retval.append(f'mkdir -p "{album_dir}/logs"')
        retval.append(f'mkdir -p "{album_dir}/images"')
        for f in self.files['booklets']:
            retval.append(f'cp "{f.fpath}" "{album_dir}/images"')
        retval.append(f'cp "{cover_img}" "{album_dir}/images"')
        for f in self.files['logs']:
            retval.append(f'cp "{f.fpath}" "{album_dir}/logs"')
        retval += self.ffmpeg_cmds(output_dir)
        return retval

    def ffmpeg_cmds(self, output_dir):
        retval = []
        for track in self.tracks:
            metadata = {
                'artist': track['artist'],
                'title': track['title'],
                'album': track['album'],
                'track': str(track['track']) + '/' + str(len(self.tracks))
            }
            if self.audio_with_cue: # TODO: single disc assumption
                metadata['cuesheet'] = ''
        
            if 'genre' in track:
                track['genre'] = track['genre']
            if 'date' in track:
                track['date'] = track['date']
        
            cmd = 'ffmpeg'
            cmd += ' -i "%s"' % self.info['file']
            cmd += ' -ss %.2d:%.2d:%.2d' % (track['start'] / 60 / 60, track['start'] / 60 % 60, int(track['start'] % 60))
        
            if 'duration' in track:
                cmd += ' -t %.2d:%.2d:%.2d' % (track['duration'] / 60 / 60, track['duration'] / 60 % 60, int(track['duration'] % 60))
        
            cmd += ' ' + ' '.join('-metadata %s="%s"' % (k, v) for (k, v) in metadata.items())
            out_fname = '%.2d.flac' % track['track']
            out_fname = os.path.join(output_dir, self.album_dirname, out_fname)
            cmd += f' "{out_fname}"'
        
            retval.append(cmd)
        return retval

