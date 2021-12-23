from functools import cached_property
import os
import re

import utils

# TODO: metadata: maintain a single source of trust

def norm_album_name(name):
    name = re.sub(r'[（(]?[Dd]isc\d[)）]?', '', name)
    return name.strip()

class DiscInfo:
    n_instances = 0

    def __init__(self, album, cue=None, audio=None):
        self.album = album
        assert cue is not None or audio is not None

        if type(audio) is list:
            self.audio_splitted = True
            self.cue_embedded = False
            track_albums = [a.audio_info['album'] for a in audio]
            track_artists = [a.audio_info['artist'] for a in audio]
            assert len(set(track_albums)) == 1, str(track_albums)
            assert len(set(track_artists)) == 1, str(track_artists) # TODO: shouldn't enforce
            self.info = {
                    'album': track_albums[0],
                    'artist': track_artists[0],
                    }
        else:
            self.audio_splitted = False
            assert cue or audio.embedded_cue # TODO: shouldn't enforce
            self.cue_embedded = cue is None

            cue_info = audio.cue_info if audio and audio.embedded_cue else cue.cue_info
            self.info, self.tracks = cue_info

            if self.cue_embedded:
                self.info['file'] = audio.fpath
            else:
                self.info['file'] = os.path.join(cue.dirname, self.info['file'])

        DiscInfo.n_instances += 1
        self.disc_no = DiscInfo.n_instances

    @cached_property
    def _disc_no(self):
        # TODO: query music database
        raise NotImplementedError()

    def output_filename(self, track_no, ext):
        return 'disc%d-%.2d.%s' % (self.disc_no, track_no, ext)

    def audio_cmds(self, output_dir):
        if not self.audio_splitted:
            return self.ffmpeg_cmds(output_dir)
        else:
            retval = []
            for a in self.album.audio:
                out_fname = self.output_filename(a.track_no, a.fext)
                retval.append(f'cp "{a.fpath}" "{output_dir}/{out_fname}"')
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
            out_fname = self.output_filename(track['track'], 'flac')
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
            track_no_list = []
            for a in self.audio:
                track_no_list.append(a.track_no)
            if len(set(track_no_list)) == len(track_no_list):
                # Splitted audio && Single disc
                self.discs = [DiscInfo(album=self, audio=self.audio)]
            else:
                # Splitted audio && Multiple disc
                raise NotImplementedError()

        disc_albums = [norm_album_name(disc.info['album']) for disc in self.discs]
        disc_artists = [disc.info['artist'] for disc in self.discs]
        assert len(set(disc_albums)) == 1, str(disc_albums)
        assert len(set(disc_artists)) == 1, str(disc_artists) # TODO: shouldn't enforce
        self.name = disc_albums[0]
        self.artist = disc_artists[0]

    def cmds(self, output_dir, audio_only=False):
        retval = []
        album_dir = os.path.join(output_dir, self.artist, self.name)
        retval.append(f'mkdir -p "{album_dir}"')

        if self.cover:
            retval.append(f'cp "{self.cover.fpath}" "{album_dir}/cover.{self.cover.fext}"')

        if not audio_only:
            if self.cover or self.booklets:
                retval.append(f'mkdir -p "{album_dir}/images"')
            for f in self.booklets:
                retval.append(f'cp "{f.fpath}" "{album_dir}/images"')

            if self.logs:
                retval.append(f'mkdir -p "{album_dir}/logs"')
            for f in self.logs:
                retval.append(f'cp "{f.fpath}" "{album_dir}/logs"')

        for disc in self.discs:
            retval += disc.audio_cmds(album_dir)

        retval.append(f'find "{album_dir}" -type f -exec chmod 0644 {{}} \\;')

        return retval

