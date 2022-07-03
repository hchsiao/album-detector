from functools import cached_property
import os

from album_detector import knowledge

class DiscInfo:
    def __init__(self, album, cue=None, audio=None):
        self.album = album
        assert cue is not None or audio is not None

        if type(audio) is list:
            self.audio_splitted = True
            self.cue_embedded = False
            track_albums = [a.audio_info['album'] for a in audio]
            track_artists = [a.audio_info['artist'] for a in audio]
            assert len(set(track_albums)) == 1, str(track_albums)
            self.info = {'album': track_albums[0]}
            if len(set(track_artists)) == 1:
                self.info['artist'] = track_artists[0]
            else:
                self.info['artist'] = knowledge.various_artist_name()
        else:
            self.audio_splitted = False
            assert cue or audio.embedded_cue # TODO: shouldn't enforce
            self.cue_embedded = cue is None

            cue_info = audio.cue_info if audio and audio.embedded_cue else cue.cue_info
            self.info, self.tracks = cue_info
            if 'artist' not in self.info:
                self.info['artist'] = self.tracks[0]['artist']

            if self.cue_embedded:
                self.info['file'] = audio.fpath
            else:
                self.info['file'] = os.path.join(cue.dirname, self.info['file'])

        album.n_disc += 1
        self.disc_no = album.n_disc
        # slashs are not supported in filesystems
        self.info['album'] = self.info['album'].replace('/', '／')
        self.info['artist'] = self.info['artist'].replace('/', '／')

        # TODO: move to knowledge
        if '初回限定' in self.info['album']:
            self.info['album'] = knowledge.norm_album_name(album.discs[0].info['album'])

    @cached_property
    def _disc_no(self):
        # TODO: query music database
        raise NotImplementedError()

class AlbumInfo:
    def __init__(self, finfos):
        knowledge.check_fileinfos(finfos)

        files = {
                'cover': [f for f in finfos if 'image(cover)' == f.ftype],
                'logs': [f for f in finfos if 'log' == f.ftype or 'cue' == f.ftype],
                'cue': [f for f in finfos if 'cue' == f.ftype],
                'audio(lossless)': [f for f in finfos if 'audio(lossless)' == f.ftype],
                'audio(lossy)': [f for f in finfos if 'audio(lossy)' == f.ftype],
                'booklets': [f for f in finfos if 'image' == f.ftype],
                'mv': [f for f in finfos if 'video' == f.ftype],
                }

        # Select one of the covers as the only cover
        files['cover'] = files['cover'][0] if files['cover'] else None

        self._files = files
        self.cover = files['cover']
        self.logs = files['logs']
        self.mv = files['mv']
        self.booklets = files['booklets']
        if files['audio(lossless)']:
            assert not files['audio(lossy)']
            self.audio = files['audio(lossless)']
        else:
            assert files['audio(lossy)']
            self.audio = files['audio(lossy)']

        cues = files['cue']
        cue_audios = [
                os.path.join(cue.dirname, cue.cue_info[0]['file'])
                for cue in cues]
        # Try to fix audio file suffix
        #for ca in cue_audios:
        #    print(ca)
        #    raise NotImplementedError()

        self.n_disc = 0
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
            assert not cues
            track_no_list = []
            for a in self.audio:
                track_no_list.append(a.track_no)
            if len(set(track_no_list)) == len(track_no_list):
                # Splitted audio && Single disc
                self.discs = [DiscInfo(album=self, audio=self.audio)]
            else:
                # Splitted audio && Multiple disc
                # TODO: example PK6/wac...
                raise NotImplementedError()

        disc_albums = [knowledge.norm_album_name(disc.info['album']) for disc in self.discs]
        disc_artists = [disc.info['artist'] for disc in self.discs]
        most_freq_artist = max(set(disc_artists), key = disc_artists.count)
        assert len(set(disc_albums)) == 1, str(disc_albums)
        assert disc_artists.count(most_freq_artist) >= 1
        self.name = disc_albums[0]
        self.artist = most_freq_artist

