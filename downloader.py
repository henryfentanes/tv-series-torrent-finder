# coding: utf-8
import sys
import requests
import re
import os
import json
from bs4 import BeautifulSoup
from requests.auth import HTTPDigestAuth
from datetime import datetime


class Downloader(object):
    '''A downloader object fed by Watchlist and Settings to Crawl for
    tv series and run the action on Settings'''

    def __init__(self, **kwargs):
        self.series = Watchlist()
        self.download_list = self.series.load_downloadable_watchlist()
        settings = Settings()
        self.download_url = settings.remote_settings['download_url']
        self.username = settings.remote_settings['username']
        self.password = settings.remote_settings['password']
        self.search_engine = settings.search_engine
        self.retries = int(settings.retries)
        self.action = settings.action
        self.ep_pattern = re.compile('([sS]\d{2}[eE]\d{2})')
        if settings.download_folder:
            self.download_folder = settings.download_folder
        else:
            self.download_folder = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}

    def change_dir(self, dirname):
        if dirname not in os.getcwd():
            try:
                os.chdir(dirname)
            except:
                os.mkdir(dirname)
                os.chdir(dirname)
        return

    def push_magnet_link(self, magnet_link):
        '''Push the magnet url to a remote torrent client'''
        response = requests.post(
            self.download_url, {'urls': magnet_link},
            auth=HTTPDigestAuth(self.username, self.password))
        if not response.ok:
            response.raise_for_status()
        response.content

    def run(self):
        '''Runs the action defined on the settings file'''
        torrent_list = self.gather_torrent_list()
        magnet_list = [torrent['magnet_link'] for torrent in torrent_list]
        if self.action == 'show_magnets':
            return('\n'.join(magnet_list))
        elif self.action == 'download_from_magnets':
            for magnet in magnet_list:
                if 'magnet' in magnet:
                    self.push_magnet_link(magnet)
        elif self.action == 'download_torrent_files':
            old_dir = os.getcwd()
            if self.download_folder:
                self.change_dir(self.download_folder)
            for t in torrent_list:
                with open(t['name'] + '.torrent', 'wb') as file:
                    file.write(
                        requests.get(
                            t['torrent_url'], headers=self.headers).content)
            os.chdir(old_dir)

    def gather_torrent_list(self):
        '''Gather a torrent list for each series in download_list'''
        result_list = []
        for serie in self.download_list:
            retried = 0
            retry = True
            while retried < self.retries and retry is True:
                result = self.get_torrent(
                    serie['name'], serie['next_episode'], serie['quality'])
                retried += 1
                if result:
                    retry = False
                    result_list.append(result)
                    self.series.update_watchlist(
                        serie['name'], result['episode'])
            # If episode not found:
            if retry is True:
                self.log('{0} - {1} (may be quality) not found'.format(
                    serie['name'], serie['next_episode']))
        return result_list

    def get_torrent(self, name, episode, quality):
        '''Return torrent for the given series and episode'''
        try:
            download = self.select_download(
                self.search_for(name, episode), quality)
            if not download:
                download = self.select_download(
                    self.search_for(
                        name, self.series.next_season(episode)), quality)
            return download
        except:
            return None

    def search_for(self, name, episode):
        '''Search for the tv series name and episode'''
        query = '"' + name + '.' + episode + '"'
        request = requests.get(self.search_engine + query + '/')
        download_options = []
        if request.status_code == 200:
            soup = BeautifulSoup(request.content, 'html.parser')
            download_options = self.fetch_download_table(soup, name, episode)
        return download_options

    def fetch_download_table(self, soup, serie, episode, limit=5):
        '''Crawls the searched webpage and return a list of download options'''
        table = soup.findAll('table')[1].findAll('tr')
        download_list = []
        for row in table[1:limit + 1]:
            try:
                magnet_link = row.findAll('td')[0].find(
                    'a', {'title': 'Torrent magnet link'}).attrs['href']
                torrent_file = row.findAll('td')[0].find(
                    'a', {'title': 'Download torrent file'}).attrs['href']
                main_link = row.findAll('td')[0].find(
                    'a', {'class': 'cellMainLink'}).attrs['href']
                size = row.findAll('td')[-5].contents[0]
                seeds = row.findAll('td')[-2].contents[0]
                quality = re.findall('(\d{3,4}p)', magnet_link)
                if quality:
                    quality = quality[0]
                elif float(size) >= 110.00 and float(size) <= 380.00:
                    quality = 'SD'

                maches_serie = serie.replace('.', '+').lower() in magnet_link
                matches_episode = episode.lower() in magnet_link
                if maches_serie and matches_episode:
                    download_list.append({
                        'name': serie + '.' + episode,
                        'episode': episode,
                        'magnet_link': magnet_link,
                        'torrent_file': torrent_file,
                        'main_link': main_link,
                        'size': size,
                        'seeds': seeds,
                        'quality': quality})
            except:
                pass
        return download_list

    def select_download(self, download_options, quality):
        for item in download_options:
            if item['quality'] == quality:
                return {
                    'name': item['name'],
                    'episode': item['episode'],
                    'magnet_link': item['magnet_link'],
                    'torrent_url': 'http:' + item['torrent_file']}

    def log(self, line):
        now = datetime.now().strftime('%d/%m/%Y (%H:%M:%S)\n')
        try:
            with open('log.txt', 'a+') as file:
                file.write(' - '.join([line, now]))
        except:
            pass


class Watchlist(object):
    '''Create a watchlist object containing a list of tv series and
    desired quality. Also tv series can be set to download False so it won't
    be seen by the Downloader'''
    series_folder = ''
    watchlist = {}

    def __init__(self, *args, **kwargs):
        self.sl = kwargs.get('series_list', [])
        self.sf = []
        if kwargs.get('folder', ''):
            self.sf = os.listdir(kwargs.get('folder'))
        self.series_list = [
            '.'.join(name.split(' ')) for name in self.sl + self.sf]
        self.watchlist = self.load_watchlist()
        for tvserie in self.series_list:
            self.create_tvseries(tvserie)

    def create_tvseries(self, name):
        if name not in self.watchlist:
            new_tvserie = {name: {
                'download': True,
                'quality': 'SD',
                'latest-downloaded-episode': 'S01E00'
            }}
            self.watchlist.update(new_tvserie)
            self.save_watchlist()

    def load_watchlist(self):
        try:
            with open('watchlist.json') as watchlist_file:
                watchlist = json.load(watchlist_file)
        except IOError:
            watchlist = self.create_raw_watchlist()
        return watchlist

    def save_watchlist(self):
        try:
            with open('watchlist.json', 'w') as watchlist_file:
                json.dump(self.watchlist, watchlist_file)
        except Exception as e:
            raise e

    def load_downloadable_watchlist(self):
        '''Retrieve a list of tv series flagged to Download from watchlist'''
        download_list = [
            {'name': k,
             'quality': v['quality'],
             'next_episode': self.next_episode(v['latest-downloaded-episode']),
             'next_season': self.next_season(v['latest-downloaded-episode'])}
            for k, v in self.watchlist.items() if v['download'] is True]
        return download_list

    def create_raw_watchlist(self):
        watchlist = {}
        for serie in self.series_list:
            watchlist.update({serie: {
                'download': True,
                'quality': 'SD',
                'latest-downloaded-episode': 'S01E00'
            }})
        with open('watchlist.json', 'w') as watchlist_file:
            json.dump(watchlist, watchlist_file)
        return watchlist

    def update_watchlist(self, key, episode):
        try:
            self.watchlist[key]['latest-downloaded-episode'] = episode
            self.save_watchlist()
        except Exception as e:
            raise e

    def next_episode(self, episode):
        return (episode[:-2] + str(int(episode[-2:]) + 1).zfill(2)).upper()

    def next_season(self, episode):
        return ('s' + str(int(episode[1:3]) + 1).zfill(2) + 'e01').upper()


class Settings(object):
    '''Create a settings object for the Downloader'''
    def __init__(self, *args, **kwargs):
        try:
            with open('settings.json') as settings_file:
                settings = json.load(settings_file)
        except:
            settings = self.create_raw_settings()

        if kwargs:
            self.update_settings(**kwargs)

        for item in settings:
            setattr(self, item, settings[item])

    def update_settings(self, **kwargs):
        with open('settings.json', 'r') as settings_file:
            settings = json.load(settings_file)
            settings.update(**kwargs)
        with open('settings.json', 'w') as settings_file:
            json.dump(settings, settings_file)

    def create_raw_settings(self):
        settings = {
            'search_engine': 'http://kat.cr/usearch/',
            'retries': '3',
            'action': 'download_torrent_files',
            'download_folder': '',
            'remote_settings': {
                'download_url': 'http://localhost:8181/command/download',
                'username': 'admin',
                'password': 'adminadmin'
            }
        }
        with open('settings.json', 'w') as settings_file:
            json.dump(settings, settings_file)
        return settings

if __name__ == '__main__':
    # run the script with -sl <series,separated,by,commas> to create a raw
    # watchlist based on the given tv series
    if '-sl' in sys.argv and len(sys.argv) > 2:
        Watchlist(series_list=sys.argv[sys.argv.index('-sl') + 1].split(','))

    # run the script with -sf <folder> to create a raw watchlist
    # based on a folder and its subfolders
    if '-sf' in sys.argv and len(sys.argv) > 2:
        Watchlist(folder=sys.argv[sys.argv.index('-sf') + 1])

    # run the script with -df to define the download folder on Settings file
    if '-df' in sys.argv and len(sys.argv) > 2:
        Settings(download_folder=sys.argv[sys.argv.index('-df') + 1])

    # run the script with -a to define the downloader action on Settings
    if '-a' in sys.argv and len(sys.argv) > 2:
        Settings(action=sys.argv[sys.argv.index('-a') + 1])

    # use run argument to execute the downloader
    if 'run' in sys.argv:
        downloader = Downloader()
        downloader.run()

    # Provide help with options to use the downloader cli
    if len(sys.argv) == 1:
        print('''Please use one of the following options as arguments:
            -sl <SeriesNames,Separated,By,Commas>: to create a raw watchlist
                based on the given tv series.
            -sf <Folder>: to create a raw watchlist based on a folder and
                its subfolders.
            -df <Folder>: to define the download folder for the
                download_torrent_files action. (Defaults to app's folder)
            -a <action>: define the downloader action on Settings.
                (Defaults to download_torrent_files)
            run: To execute the downloader based on your settings and
                watchlist. If there's no settings or watchlist file the
                downloader will create a new one based on
                its own folder (Not Pretty).
            The run argument is going to perform the action defined in the
            settings file (defaults to download_torrent_files).
            Action can be set to:
            download_torrent_files: Downloads found torrent files for tv series
                in watchlist flagged to download: true.
            show_magnets: Gather and print magnet urls for tv series
                in watchlist flagged to download: true.
            download_from_magnets: Push magnet urls to remote torrent client
                for tv series in watchlist flagged to download: true.''')
