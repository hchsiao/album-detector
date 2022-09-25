import argparse
import os
import json

def main():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument('path') 
    args = parser.parse_args()
    with open(args.path, 'r') as f:
        indexes = json.load(f)
    by_path = indexes
    by_artist = {}
    for path, info in by_path.items():
        artist = info['artist']
        by_artist.setdefault(artist, {})
        by_artist[artist][info['album']] = path
    print(json.dumps(by_artist))

if __name__ == "__main__":
    main()
