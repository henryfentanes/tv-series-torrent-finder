# TV Series Auto Download
![Python Version](https://img.shields.io/badge/Python-2.7/3.5-green.svg)
![OS](https://img.shields.io/badge/OS-Windows_8/_Ubuntu_15.10-green.svg)

Tired of keeping up with your tv series on cable ?

Already past that and getting tired of searching torrent webpages ?

This app is for you :)

# Disclaimer:
Note that this app was made for the purpose of studying. If you plan on using it to really download tv shows,
be warned that it should infringe tv shows copyrights, therefore, use it by your own responsability.

### What it does:

The app aims to search your entire watchlist for new episodes, and then, you
can download all the torrent files, see all the magnet urls or directly
push the magnets into a remote torrent client with a single command.

### How to do it:

Download it as a zip and unzip it anywhere you want. In command line, install
the requirements with `pip install -r requirements.txt` and run the tests
to make sure its all fine with `python tests.py`.

After that take a look at the options with `python downloader.py`, to run should
as be easy as `python downloader.py run` but before you do that,
take the time to configure your watchlist.

> **Note**:
> If you're on Windows OS and don't care about installing python requests and
> beautifulsoup on you main python setup, you can just use the batch files
> in the contrib folder, to Setup and Run the app.

### The Watchlist

is a json file in the app's folder called watchlist.json and it looks like this:
```
{"Breaking.Bad": {"download": true, "latest-downloaded-episode": "S01E00", "quality": "SD"},
"The.Big.Bang.Theory": {"download": true, "latest-downloaded-episode": "S01E00", "quality": "SD"}}
```
The watchlist can be created based on a folder with series as subfolders or
you can pass the series list as an argument in command line. Either way
the app only creates a raw watchlist, so you'd still need to set the
latest-downloaded-episode by hand. Also, you can copy the example above and
craft on it yourself.

Just in case you want keep track of what you have watched, you can leave a tv
series in your watchlist and simply set it to download false, so it won't be
looked by the downloader.

You can also set the desired quality of each tv series (SD, 720p, 1080p) if
the desired quality can't be found, a log.txt file will be created in the app's
folder and you can see there which tv series and when.

```
Series folder should look like this:
Series
   |--How I Met Your Mother
   |  |---*Episodes*
   |--Game of Thrones
   |  |---*Episodes*

```

> **Note:**
> TV Series with spaces on their names must be separated by dots on watchlist.
> The app takes care of that when it creates your watchlist even based on
> folder names separated by spaces. But, remember that in case you go by hand.

### The Settings

is also a json file in the app's folder called settings.json and it looks like this:
```
{"search_engine": "http://kat.cr/usearch/", "retries": "3",
 "download_folder": "", "action": "download_torrent_files",
 "qTorrent_settings": {
    "username": "admin", "password": "adminadmin",
    "download_url": "http://localhost:8181/command/download"}}
```
For now the app only crawls on kickass torrents, as you can see the search_engine
on the settings file and there's a retry 3 just to make sure you will get
your torrent.

The download_folder can be specified so the app won't download all your torrents
on its own folder, which can also be useful to a torrent client watching a folder.

The remote_settings is used to push magnets into a remote torrent client. In
case you won't use it, just leave it there.

the action can be set to one of three options.
* download_torrent_files: download all torrent files found
* show_magnets: will print all the magnet urls found
* download_from_magnets: try to push the magnets into the remote torrent
client.
