🎶 MUSIC MOOD GIFS 🎶
=======================================

![Marcos Valle](https://media.giphy.com/media/rbJkxEUGJKsa4/giphy.gif)

Identify any audio playing on your computer (or microphone) and automatically download GIFs relevant to artist, track and mood. Audio is fingerprinted and identified using Gracenote, which also provides metadata on the mood/emotion, then GIPHY is used to download GIFs based on the artist, track and mood keywords. The program runs on a loop in the background, checking every minute for the current song and generating GIFs.

Installation (OSX 64 bit)
---------------------

1. Install PyAudio, [Soundflower](https://github.com/mattingalls/Soundflower) and [SwitchAudioSource](https://github.com/deweller/switchaudio-osx).  

2. Install the dependencies: `pip install -r requirements.txt`

3. In Audio MIDI settings, create a multi-output device. The master device should be "Soundflower (2ch)" and it should use "Soundflower (2ch)" and "Built-in Output". This will allow the script to listen to the audio through the Soundflower device while you continue to hear it through the computer's output. Name the multi-output device "Multi-Output Device (Built-in)" by double-clicking on the name. The script will look for a device with this exact name.  

4. The script will look for configuration details in a config.rc file that you need to create. You'll also need to create your own Gracenote app and GIPHY app through each of their web interfaces (for free), and replace the details below in the file:  

> APP_PATH /gracenote/identify-audio  
> GRACENOTE_LICENCE_PATH gracenote/license.txt
> GRACENOTE_CLIENT_ID your_details
> GRACENOTE_CLIENT_TAG your_details
> GRACENOTE_WEB_ID your_details
> GIPHY_API_KEY your_details

5. If you do not have OS X 64-bit you will need to recompile the executable using the Gracenote SDK (it's free).   

Usage
-----

Run using `python main.py` while music is playing. 
It will try a few times to identify the track and download GIFs to the `gif/` folder if a match is found. 
Each time a new song found, the folder is emptied and replaced with the new song gifs. The program will continue to run every minute, until you stop it. The interval time for when a song is identified can be changed by setting the `RECORD_INTERVAL_MIN` value in `main.py`. The amount of GIFs downloaded for each term can also be changed through the `GIF_LIMIT` value.

TODO
------------
- [] Sync speed of GIF to the song BPM

