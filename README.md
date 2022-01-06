# album-detector
An expert system for recognizing/labeling musics, which may be scattered in the file system.

## TODO
- Check https://github.com/flacon/flacon/issues/41
- Extract embedded cover image (for airsonic)
- What happens if dummy CUE exists with splitted/CUE-embedded audio?
- metadata: maintain a single source of trust
  - Connect musicbrainz (Write a function to tell if a folder is an album)
    - Write a recursive scanner tool
    - Fail on multiple-album directory (total files less than 200)
