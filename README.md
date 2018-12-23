# youtubepicast
youtubepicast is a program to make your own YouTube TV player on any television.

It's based on the [gotubecast](https://github.com/CBiX/gotubecast) project.

It uses the Youtube API to connect your command device to the pi, so you can control the play/pause/seek/volume commands. 
It requires [youtube-dl](https://youtube-dl.org/).
Just connect your raspberry pi to your TV and control it with your mobile.

## Install youtube-dl
Check [youtube-dl](https://youtube-dl.org/) page to install. On rapsberry pi just run:

    pip install youtube_dl

## Run
On the first time run:

    python youtubepicast.py
    
And copy the pairing code and the screen id.
Open the youtube application on your device and go to settings -> Wartch on TV -> ENTER TV CODE, and add the pairing code.
Now you can play any video.

Next time you run, you can use the screen id so you don't have to add the pairing code:

    python youtubepicast.py -s <SCREEN_ID>
    
    Ex: python youtubepicast.py -s f84e7dehf6q46u0hd7ge5qvpjqe

Usage help:

	python youtubepicast.py -h
    usage: youtubepicast.py [-h] [-d DEBUGLEVEL] [-n SCREENNAME] [-i SCREENAPP]
                   [-s SCREENID]

    Cast youtube to your tv

    optional arguments:
      -h, --help     show this help message
      -d DEBUGLEVEL  Debug information level. 0 = off; 1 = full cmd info; 2 =
                     timestamp prefix
      -n SCREENNAME  Display Name
      -i SCREENAPP   App Name
      -s SCREENID    Screen ID (will be generated if empty)


## Known Issues
* Delay on video start
* Delay on play/pause
* Video ends and doesn´t play next

## TODO
* play next on video end
* Remove delay on video start
