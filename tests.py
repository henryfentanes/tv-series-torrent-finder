# coding: utf-8
import unittest
import os
import shutil
import downloader as sad
from subprocess import call


class SADTestCase(unittest.TestCase):
    def setUp(self):
        test_dir = os.listdir(os.getcwd())
        if 'settings.json' in test_dir:
            os.rename('settings.json', 'settings.json.bkp')
        if 'watchlist.json' in test_dir:
            os.rename('watchlist.json', 'watchlist.json.bkp')
        self.settings = sad.Settings()
        self.wl = sad.Watchlist(
            series_list=['Breaking.Bad', 'The.Big.Bang.Theory'])
        self.downloader = sad.Downloader()

    def create_test_folders(self):
        if 'Series_Test' not in os.listdir(os.getcwd()):
            os.makedirs('Series_Test/The.Flash/')
            os.makedirs('Series_Test/Game of Thrones/')
            os.makedirs('Series_Test/The.100/')

    def tearDown(self):
        test_dir = os.listdir(os.getcwd())
        os.remove('settings.json')
        if 'settings.json.bkp' in test_dir:
            os.rename('settings.json.bkp', 'settings.json')
        os.remove('watchlist.json')
        if 'watchlist.json.bkp' in test_dir:
            os.rename('watchlist.json.bkp', 'watchlist.json')
        if 'log.txt' in test_dir:
            os.remove('log.txt')
        downloaded_list = [f for f in test_dir if '.torrent' in f]
        for f in downloaded_list:
            os.remove(f)
        if 'Series_Test' in test_dir:
            shutil.rmtree('Series_Test')


class TestWatchlist(SADTestCase):

    def test_watchlist(self):
        watchlist_keys = [k for k, v in self.wl.watchlist.items()]
        self.assertEqual(2, len(self.wl.watchlist))
        self.assertIn('Breaking.Bad', watchlist_keys)
        self.assertIn('The.Big.Bang.Theory', watchlist_keys)

    def test_create_watchlist_from_folder(self):
        self.create_test_folders()
        os.remove('watchlist.json')
        watchlist = sad.Watchlist(folder='Series_Test/')
        self.assertEqual(3, len(watchlist.watchlist))

    def test_update_watchlist(self):
        self.wl.update_watchlist('Breaking.Bad', 'S01E01')
        ep = self.wl.watchlist['Breaking.Bad']['latest-downloaded-episode']
        self.assertEqual('S01E01', ep)

    def test_update_watchlist_file(self):
        self.wl.update_watchlist('Breaking.Bad', 'S01E01')
        self.wl = sad.Watchlist()
        ep = self.wl.watchlist['Breaking.Bad']['latest-downloaded-episode']
        self.assertEqual('S01E01', ep)

    def test_append_new_series_list(self):
        '''User should be able to append new series using the cli'''
        call(['python', 'downloader.py', '-sl', 'The 100,True Detective'])
        call(['python', 'downloader.py', '-sl', 'Breaking Bad,The 100'])
        self.assertEqual(4, len(self.wl.load_watchlist()))

    def test_create_with_sl_and_sf(self):
        '''When creating new watchlist with -sf and -sl arguments must merge'''
        self.create_test_folders()
        os.remove('watchlist.json')
        call(['python', 'downloader.py', '-sl', 'The 100,True Detective',
              '-sf', 'Series_Test'])
        self.assertEqual(4, len(self.wl.load_watchlist()))

    def test_always_create_with_dotted_names(self):
        '''When watchlist is made, names must be separated by dots'''
        self.create_test_folders()
        os.remove('watchlist.json')
        call(['python', 'downloader.py', '-sl', 'The 100,True Detective',
              '-sf', 'Series_Test'])
        new_watchlist = self.wl.load_watchlist()
        # Test from Series Folder
        self.assertIn('Game.of.Thrones', new_watchlist)
        self.assertNotIn('Game of Thrones', new_watchlist)
        # Test from Series List
        self.assertIn('True.Detective', new_watchlist)
        self.assertNotIn('True Detective', new_watchlist)


class TestSettings(SADTestCase):
    def test_update_settings_with_download_folder(self):
        '''The download folder should be updatable via cli'''
        self.assertEqual('', sad.Settings().download_folder)
        call(['python', 'downloader.py', '-df', 'DownloadedTorrents'])
        self.assertEqual('DownloadedTorrents', sad.Settings().download_folder)

    def test_update_settings_with_action(self):
        '''CLI must be able to change the action on settings'''
        self.assertEqual('download_torrent_files', sad.Settings().action)
        call(['python', 'downloader.py', '-a', 'show_magnets'])
        self.assertEqual('show_magnets', sad.Settings().action)


class TestDownloader(SADTestCase):
    def test_search_for(self):
        self.assertGreater(
            len(self.downloader.search_for('Firefly', 'S01E01')), 0)

    def test_run_show_magnets(self):
        self.downloader.action = 'show_magnets'
        self.assertEqual(self.downloader.run().count('magnet'), 2)

    def test_torrent_not_found(self):
        self.downloader.download_list[0]['quality'] = '4K'
        s = self.downloader.download_list[0]['name']
        del self.downloader.download_list[1]
        self.downloader.run()
        le = self.downloader.series.watchlist[s]['latest-downloaded-episode']
        self.assertIn('log.txt', os.listdir(os.getcwd()))
        self.assertIn('not found', open('log.txt').readline())
        self.assertEqual(1, len(open('log.txt').readlines()))
        self.assertEqual('S01E00', le)

    def test_run_download_torrent_files(self):
        self.downloader.action = 'download_torrent_files'
        self.downloader.run()
        folder = os.listdir(os.getcwd())
        downloaded_list = [f for f in folder if '.torrent' in f]
        self.assertEqual(2, len(downloaded_list))

    def test_get_next_season(self):
        self.wl.update_watchlist('The.Big.Bang.Theory', 'S01E30')
        self.downloader = sad.Downloader()
        self.downloader.run()
        folder = os.listdir(os.getcwd())
        downloaded_list = [f for f in folder if '.torrent' in f]
        self.assertEqual(2, len(downloaded_list))
        self.assertIn('The.Big.Bang.Theory.S02E01.torrent', downloaded_list)

    def test_download_to_download_folder(self):
        os.remove('settings.json')
        self.settings = sad.Settings(download_folder='Downloaded_Test')
        self.downloader = sad.Downloader()
        self.downloader.run()
        self.assertEqual(2, len(os.listdir('Downloaded_Test')))
        shutil.rmtree('Downloaded_Test')

    def test_update_new_season_on_watchlist(self):
        '''When downloader finds a new season it should set it on watchlist'''
        self.wl.update_watchlist('The.Big.Bang.Theory', 'S01E30')
        self.downloader = sad.Downloader()
        self.downloader.run()
        tvseries = self.wl.load_watchlist()['The.Big.Bang.Theory']
        self.assertEqual('S02E01', tvseries['latest-downloaded-episode'])

    def test_fetched_download_returns_the_searched_tv_series(self):
        '''When downloader searches for a tv series it must garantee it is
           being returned by the fetcher'''
        os.remove('watchlist.json')
        name = 'The.100'
        self.wl = sad.Watchlist(series_list=[name])
        self.wl.update_watchlist(name, 'S03E00')
        self.downloader = sad.Downloader()
        self.downloader.action = 'show_magnets'
        magnet_list = self.downloader.run()
        self.assertIn(name.replace('.', '+').lower(), magnet_list)


if __name__ == '__main__':
    unittest.main()
