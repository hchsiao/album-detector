from functools import cached_property
import os
import re

import utils

def norm_album_name(name):
    name = re.sub(r'[（(]?Disc\d[)）]?', '', name)
    return name.strip()

class DiscInfo:
    def __init__(self, album, cue=None, audio=None):
        assert cue is not None or audio is not None
        assert cue or audio.embedded_cue # TODO: shouldn't enforce
        self.album = album
        self.cue_embedded = cue is None

        cue_info = audio.cue_info if audio and audio.embedded_cue else cue.cue_info
        self.info, self.tracks = cue_info

        if self.cue_embedded:
            self.info['file'] = audio.fpath
        else:
            self.info['file'] = os.path.join(cue.dirname, self.info['file'])

    def ffmpeg_cmds(self, output_dir):
        retval = []
        for track in self.tracks:
            metadata = {
                'artist': track['artist'],
                'title': track['title'],
                'album': track['album'],
                'track': str(track['track']) + '/' + str(len(self.tracks))
            }
            if self.cue_embedded:
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
            out_fname = os.path.join(output_dir, out_fname)
            cmd += f' "{out_fname}"'
        
            retval.append(cmd)
        return retval

class AlbumInfo:
    def __init__(self, files):
        self._files = files
        self.cover = files['cover']
        self.logs = files['logs']
        self.booklets = files['booklets']
        if files['audio(lossless)']:
            self.audio = files['audio(lossless)']
            assert not files['audio(lossy)']
        else:
            self.audio = files['audio(lossy)']
            assert files['audio(lossy)']
            assert not files['audio(lossless)']

        cues = files['cue']
        cue_audios = [
                os.path.join(cue.dirname, cue.cue_info[0]['file'])
                for cue in cues]
        # TODO: may need to fix filename if all are wrong

        embedded_cues = [a.embedded_cue for a in self.audio]
        assert self.audio
        if any(embedded_cues):
            # Merged audio (embedded cue)
            assert all(embedded_cues)
            self.discs = [DiscInfo(album=self, audio=a) for a in self.audio]
        elif any([os.path.isfile(ca) for ca in cue_audios]):
            # Merged audio (explicit cue)
            self.discs = []
            for i in range(len(cues)):
                cue, ca = cues[i], cue_audios[i]
                if os.path.isfile(ca):
                    self.discs.append(DiscInfo(album=self, cue=cue))
        else:
            # TODO: decern the following
            # Splitted audio && Single disc
            # Splitted audio && Multiple disc
            raise NotImplementedError()

        disc_albums = [norm_album_name(disc.info['album']) for disc in self.discs]
        disc_artists = [disc.info['artist'] for disc in self.discs]
        assert len(set(disc_albums)) == 1, str(disc_albums)
        assert len(set(disc_artists)) == 1, str(disc_artists) # TODO: shouldn't enforce
        self.album = disc_albums[0]
        self.artist = disc_artists[0]

    @cached_property
    def album_dirname(self):
        return f"{self.artist} - {self.album}"

    def cmds(self, output_dir):
        retval = []
        album_dir = os.path.join(output_dir, self.album_dirname)
        retval.append(f'mkdir -p "{album_dir}"')

        if self.cover or self.booklets:
            retval.append(f'mkdir -p "{album_dir}/images"')
        for f in self.booklets:
            retval.append(f'cp "{f.fpath}" "{album_dir}/images"')
        if self.cover:
            cover_img = self.cover.fpath
            retval.append(f'cp "{cover_img}" "{album_dir}/images"')

        if self.logs:
            retval.append(f'mkdir -p "{album_dir}/logs"')
        for f in self.logs:
            retval.append(f'cp "{f.fpath}" "{album_dir}/logs"')

        # TODO: Add disc no to filenames in addition to the track no
        for disc in self.discs:
            retval += disc.ffmpeg_cmds(album_dir)

        retval.append(f'find "{album_dir}" -type f -exec chmod 0644 {{}} \\;')

        return retval

