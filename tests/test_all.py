import unittest
import json

from album_detector import mkalbum

class TestAll(unittest.TestCase):
    def setUp(self):
        super().setUp()

    def test_all(self):
        f = open('testdata.json', 'r')
        testdata = json.loads(f.read())
        f.close()

        n_total = len(testdata)
        n_processing = 0
        for path, golden in testdata.items():
            n_processing += 1
            print(f'Processing {n_processing}/{n_total}...')
            album = mkalbum(path)
            cmds = album.cmds('/tmp', audio_only=False)
            cmds = '\n'.join(cmds)
            try:
                self.assertEqual(cmds, golden)
            except:
                with open('a', 'w') as f:
                    f.write(cmds)
                with open('b', 'w') as f:
                    f.write(golden)
                raise

if __name__ == '__main__':
    unittest.main()

