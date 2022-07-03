import re

def various_artist_name():
    return 'Various'

def check_fileinfos(fileinfos):
    # Assume basenames are unique
    basenames = [f.basename for f in fileinfos]
    assert len(set(basenames)) == len(basenames)

    unknown = [f for f in fileinfos if 'unknown' == f.ftype]
    if unknown:
        for uf in unknown:
            print(f'Filename: {uf.basename}')
            print(f'Magic string: {uf.type_str}')
        assert not unknown


def norm_album_name(name):
    # Examples: Disc1, [DISC.1]
    name = re.sub(r'[\[（(]?[Dd](isc|ISC)\.?\d[)）\]]?', '', name)
    # Examples: CD1
    name = re.sub(r'[\[（(]?[Cc][Dd]\.?\d[)）\]]?', '', name)
    return name.strip()

