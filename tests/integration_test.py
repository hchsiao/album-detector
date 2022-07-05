import unittest
import json

from album_detector import utils

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        f = open('tests/testdata.json', 'r')
        self.testdata = json.loads(f.read())
        f.close()
        self.maxDiff = None

    def test_export_cmds(self):
        n_total = len(self.testdata)
        n_processing = 0
        self.assertNotEqual(n_total, 0)

        for path, golden in self.testdata.items():
            n_processing += 1
            print(f'Processing {n_processing}/{n_total}...')
            print(f'{path}')
            cmds = utils.handle_path(path, '/tmp', False)
            cmds = '\n'.join(cmds)
            try:
                self.assertEqual(cmds, golden)
            except:
                with open('a', 'w') as f:
                    f.write(cmds)
                with open('b', 'w') as f:
                    f.write(golden)
                raise

    def test_export_cue(self):
        from album_detector import album_info
        from album_detector import export
        #for path, golden in self.testdata.items():
        #    fileinfos = utils.mkfilelist(path)
        #    album = album_info.AlbumInfo(fileinfos)
        #    print(export.export_cue(album))
        #    break


if __name__ == '__main__':
    unittest.main()

