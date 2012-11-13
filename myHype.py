#!/usr/bin/env python
from __future__ import division
import sys, json, time, threading, urlparse

from bs4 import BeautifulSoup
import requests

EXTENSION_MAP = {'audio/mpeg' : 'mp3', 'audio/mp4': 'mp4', 'audio/vnd.wave': 'wav'}

class Scraper(object):
    "Gets a list of songs that could be downloaded, and manages their downloads through spawning DL threads"
    
    def __init__(self, path='popular/'):
        self.get_songs(path)    

    def get_page(self, path):
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15'}
        self.session = requests.session()
        req = self.session.get(urlparse.urljoin('http://www.hypem.com/', path), headers=headers)
        return req.text

    def get_songs(self, path):
        results = BeautifulSoup(self.get_page(path))
        song_map = {}
        self.song_list = json.loads(results.find('script', id='displayList-data').get_text())['tracks']
        [track.__setitem__('rank', i+1) for i, track in enumerate(self.song_list)]

    def download(self, song_numbers):
        [Downloader(self.song_list[selected], self.session).start() for selected in song_numbers]
        Downloader.printer()

class Downloader(threading.Thread):
    tracker = {}

    def __init__(self, song, session):
        threading.Thread.__init__(self)
        self.song, self.session = song, session
        self.tracker[self.song['song']] = 0
        self.daemon = True

    def update(self, percent):
        self.tracker[self.song['song']] = percent

    def run(self):
        try:
            response, filename = self.get_song_file(self.song)
        except requests.HTTPError:
            print '\nSorry, "' + self.song['song'] + '" is not available.'
            self.tracker[self.song['song']] = -1
        else:
            self.save_file(response, filename, self.update)

    def request_song_url(self, song):
        url = 'http://hypem.com/serve/source/' +  song['id'] + '/' +  song['key']
        for i in range(3):
            response = self.session.get(url)
            if response.status_code != 404:
                break
            time.sleep(1)
        else:
            raise requests.HTTPError
        return response.json['url']

    def get_song_file(self, song):
        """Returns song file object, used as 'filer' in thread"""
        return self.session.get(self.request_song_url(song), prefetch=False), song['artist']+ ' - ' +song['song']

    def save_file(self, resp, filename, updater=None):
        """Returns song file object, used as 'saver' """
        size = int(resp.headers['content-length'])
        if '/' in filename:
            filename = filename.replace('/', '-')
        try:
            ext = EXTENSION_MAP[resp.headers['content-type']]
        except KeyError:
            print "The file type for " + filename + " was not recognized. We're going to assume it's an mp3."
            ext = 'mp3'
        f = open(filename + '.' + ext, 'w')
        bytes_read = 0
        while bytes_read < size:
            data = resp.raw.read(min(1024*64, size-bytes_read))
            bytes_read += len(data)
            f.write(data)
            updater(bytes_read/size)
        f.close()

    @classmethod
    def printer(kls):
        while any([abs(v) != 1 for v in kls.tracker.values()]):
            for k,v in kls.tracker.items():
                if abs(v) != 1:
                    sys.stdout.write( ' || '.join(['%s: %.f%% done' % (k, v*100) for k, v in kls.tracker.items() if v != -1]) + '\r')
                    sys.stdout.flush()
                    time.sleep(.1)
        print


def CLI():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'user:':
            path = '/' + sys.argv[2]
        else:
            path = '/search/%s/' % ' '.join(sys.argv[1:])
        scraper = Scraper(path)

    else:
        scraper = Scraper()
    if len(scraper.song_list) == 0:
        print 'Sorry, there are no songs matching your request'
        return
    else:
        for song in scraper.song_list:
            print str(song['rank']) + ') ' + song['artist']+ ' - ' +song['song']

    selections = raw_input('What numbers would you like to download? ')
    parsed = [int(x.strip())-1 for x in selections.split(',')]
    scraper.download(parsed)

if __name__ == '__main__':
    CLI()