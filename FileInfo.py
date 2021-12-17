from functools import cached_property
import os

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

