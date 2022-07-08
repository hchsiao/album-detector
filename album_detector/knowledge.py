import re

def various_artist_name():
    return 'Various'

def check_fileinfos(fileinfos):
    unknown = [f for f in fileinfos if 'unknown' == f.ftype]
    if unknown:
        for uf in unknown:
            print(f'Filename: {uf.basename}')
            print(f'Magic string: {uf.type_str}')
        assert not unknown


def norm_album_name(name):
    _left_brac = r'[＜（\(\[]'
    _right_brac = r'[＞）\)\]]'
    # Examples: Disc1, [DISC.1]
    name = re.sub(fr'{_left_brac}?[Dd](isc|ISC|isk|ISK)[ \.]*\d?{_right_brac}?', '', name)
    # Examples: CD1
    name = re.sub(fr'{_left_brac}?[Cc][Dd][ \.]*\d{_right_brac}?', '', name)
    name = re.sub(fr'{_left_brac}完全収録盤{_right_brac}', '', name)
    return name.strip()

