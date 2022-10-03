from functools import cached_property
import os

from album_detector import knowledge
from album_detector import file_info
from album_detector import utils

class DiscInfo:
    def __init__(self, album, cue=None, audio=None):
        self.album = album
        assert cue is not None or audio is not None

        if type(audio) is list:
            self.audio_splitted = True
            self.cue_embedded = False
            track_albums = [a.audio_info['album'] for a in audio]
            track_artists = [a.audio_info['artist'] for a in audio if 'artist' in a.audio_info]
            assert len(set(track_albums)) == 1, str(track_albums)
            self.info = {'album': track_albums[0]}
            if len(set(track_artists)) == 1:
                self.info['artist'] = track_artists[0]
            else:
                self.info['artist'] = knowledge.various_artist_name()
        else:
            self.audio_splitted = False
            supported_case = cue or audio.embedded_cue
            if not supported_case:
                raise NotImplementedError()
            self.cue_embedded = cue is None

            cue_info = audio.cue_info if audio and audio.embedded_cue else cue.cue_info
            self.info, self.tracks = cue_info
            if 'artist' not in self.info:
                self.info['artist'] = self.tracks[0]['artist']
            if 'album' not in self.info:
                self.info['album'] = utils.get_hint(audio.fpath, 'album_name', 'Fill missing album name')
                for track in self.tracks:
                    assert 'album' not in track
                    track['album'] = self.info['album']

            if self.cue_embedded:
                if utils.has_hint(audio.fpath, 'audio_file'):
                    replaced_audio_map = utils.get_hint(audio.fpath, 'audio_file')
                    replaced_audio = replaced_audio_map[audio.basename]
                    self.info['file'] = os.path.join(audio.dirname, replaced_audio)
                else:
                    self.info['file'] = audio.fpath
            else:
                if utils.has_hint(cue.fpath, 'audio_file'):
                    replaced_audio_map = utils.get_hint(cue.fpath, 'audio_file')
                    replaced_audio = replaced_audio_map[self.info['file']]
                    self.info['file'] = os.path.join(cue.dirname, replaced_audio)
                else:
                    self.info['file'] = os.path.join(cue.dirname, self.info['file'])

        album.n_disc += 1
        self.disc_no = album.n_disc
        # slashs are not supported in filesystems
        self.info['album'] = self.info['album'].replace('/', '／')
        self.info['artist'] = self.info['artist'].replace('/', '／')

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
            self.audio = files['audio(lossless)']
            if files['audio(lossy)']:
                allow_lossless_lossy_mix = utils.get_hint(
                        self.audio[0].fpath,
                        'allow_lossless_lossy_mix',
                        'Containing both lossless and lossy audios. Confirm?',
                        )
                assert allow_lossless_lossy_mix.lower() == 'yes'
            if utils.has_hint(self.audio[0].fpath, 'audio_file'):
                replaced_audio_map = utils.get_hint(self.audio[0].fpath, 'audio_file')
                replaced_audios = list(replaced_audio_map.values())
                self.audio = [a for a in self.audio if a.basename not in replaced_audios]
        else:
            assert files['audio(lossy)'], 'no audio file at all?'
            self.audio = files['audio(lossy)']

        cues = files['cue']
        cue_audios = []
        for cue in cues:
            cue_audio = os.path.join(cue.dirname, cue.cue_info[0]['file'])
            if os.path.isfile(cue_audio):
                cue_audios.append(cue_audio)
            else: # Try to fix audio file suffix
                audio_found = []
                for f in os.listdir(cue.dirname):
                    f = file_info.FileInfo(os.path.join(cue.dirname, f))
                    if f.is_audio:
                        assert f.fpath not in audio_found, 'same disc audio with different format?'
                        audio_found.append(f.fpath)
                        cue_audios.append(f.fpath)
        if len(set(cue_audios)) == 1 and len(cue_audios) > 1: # many cue point to same audio
            cue_audios = [cue_audios[0]] + [''] * (len(cues) - 1)

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
        else: # Splitted audio
            assert not cues
            self.discs = []
            attr_cb_list = [lambda a: a.audio_info['album'], lambda a: a.dirname]
            for attr_cb in attr_cb_list:
                attr_is_good = True
                track_list_by_disc = self.cluster_splitted_audio(attr_cb)
                for track_list in track_list_by_disc:
                    assert 'track' in track_list[0].audio_info, 'Not implemented: try to recover this piece of info'
                    track_num_list = [a.track_no for a in track_list]
                    if len(set(track_num_list)) != len(track_num_list):
                        attr_is_good = False
                if attr_is_good:
                    break
            assert attr_is_good, 'Failed to divide audios into discs'
            for track_list in track_list_by_disc:
                self.discs.append(DiscInfo(album=self, audio=track_list))

        disc_albums = [knowledge.norm_album_name(disc.info['album']) for disc in self.discs]
        disc_artists = [disc.info['artist'] for disc in self.discs]
        most_freq_artist = max(set(disc_artists), key = disc_artists.count)
        album_names = set(disc_albums)
        if len(album_names) == 1:
            self.name = disc_albums[0]
        else:
            self.name = utils.get_hint(self.audio[0].fpath, 'album_name', 'Choose album name for discs', album_names, find_common=True)
        assert disc_artists.count(most_freq_artist) >= 1
        self.name = disc_albums[0]
        self.artist = most_freq_artist

    def cluster_splitted_audio(self, get_attr_cb):
        track_list_by_attr = {}
        for a in self.audio:
            track_list = track_list_by_attr.setdefault(get_attr_cb(a), [])
            track_list.append(a)
        discs = []
        for album, track_list in track_list_by_attr.items():
            track_num_list = [a.track_no for a in track_list]
            discs.append(track_list)
        return discs

