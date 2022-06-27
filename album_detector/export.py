import os

def export_cmds(album, output_dir, audio_only=False):
    retval = []
    album_dir = os.path.join(output_dir, album.artist, album.name)
    retval.append(f'mkdir -p "{album_dir}"')

    if album.cover:
        retval.append(f'cp "{album.cover.fpath}" "{album_dir}/cover.{album.cover.fext}"')

    if not audio_only:
        if album.cover or album.booklets:
            retval.append(f'mkdir -p "{album_dir}/images"')
        for f in album.booklets:
            retval.append(f'cp "{f.fpath}" "{album_dir}/images"')

        if album.logs:
            retval.append(f'mkdir -p "{album_dir}/logs"')
        for f in album.logs:
            retval.append(f'cp "{f.fpath}" "{album_dir}/logs"')

        if album.mv:
            retval.append(f'mkdir -p "{album_dir}/mv"')
        for f in album.mv:
            retval.append(f'cp "{f.fpath}" "{album_dir}/mv"')

    for disc in album.discs:
        retval += audio_cmds(disc, album_dir)

    retval.append(f'find "{album_dir}" -type f -exec chmod 0644 {{}} \\;')

    return retval

def export_cue(album):
    retval = []
    return retval

def _output_filename(disc, track_no, ext):
    return 'disc%d-%.2d.%s' % (disc.disc_no, track_no, ext)

def audio_cmds(disc, output_dir):
    if not disc.audio_splitted:
        return ffmpeg_cmds(disc, output_dir)
    else:
        retval = []
        for a in disc.album.audio:
            out_fname = _output_filename(disc, a.track_no, a.fext)
            retval.append(f'cp "{a.fpath}" "{output_dir}/{out_fname}"')
        return retval

def ffmpeg_cmds(disc, output_dir):
    retval = []
    for track in disc.tracks:
        metadata = {
            'artist': track['artist'],
            'title': track['title'],
            'album': track['album'],
            'track': str(track['track']) + '/' + str(len(disc.tracks))
        }
        if disc.cue_embedded:
            metadata['cuesheet'] = ''
    
        if 'genre' in track:
            track['genre'] = track['genre']
        if 'date' in track:
            track['date'] = track['date']
    
        cmd = 'ffmpeg'
        cmd += ' -i "%s"' % disc.info['file']
        cmd += ' -ss %.2d:%.2d:%.2d' % (track['start'] / 60 / 60, track['start'] / 60 % 60, int(track['start'] % 60))
    
        if 'duration' in track:
            cmd += ' -t %.2d:%.2d:%.2d' % (track['duration'] / 60 / 60, track['duration'] / 60 % 60, int(track['duration'] % 60))
    
        cmd += ' ' + ' '.join('-metadata %s="%s"' % (k, v) for (k, v) in metadata.items())
        out_fname = _output_filename(disc, track['track'], 'flac')
        out_fname = os.path.join(output_dir, out_fname)
        cmd += f' "{out_fname}"'
    
        retval.append(cmd)
    return retval
