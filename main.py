#!/usr/bin/python

import wave
import time
import subprocess
import os.path
import json
import argparse
import webbrowser
import sys
import requests
import keyring
import pyaudio
import pygn
import giphypop
import urllib

# ---------------- Config -----------------

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 10
RECORD_INTERVAL_MIN = 1 
SAVE_PATH = os.path.dirname(__file__) + "recordings/"
GIF_PATH = os.path.dirname(__file__) + "gifs/"
GIF_LIMIT = 2
WAVE_OUTPUT_FILENAME = "temp_{}.wav".format(int(time.time()))
COMPLETE_NAME = os.path.join(SAVE_PATH, WAVE_OUTPUT_FILENAME)
CONFIG_PATH = "config.rc"

def load_user_config(path):
    user_config = {}
    try:
        with open(path, "r") as f:
            for line in f:
                split = line.split(" ")
                user_config[str(split[0])] = str(split[1]).strip()
    except:
        raise IOError("Unable to read config file")
    return user_config

config = load_user_config(CONFIG_PATH)

# ---------------- Setup ------------------

class GracenoteError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

p = pyaudio.PyAudio()

# ----------- Audio devices ---------------

def find_device(device_sought, device_list):
    for device in device_list:
        if device["name"] == device_sought:
            return device["index"]
    raise KeyError("Device {} not found.".format(device_sought))

def get_device_list():
    num_devices = p.get_device_count()
    device_list = [p.get_device_info_by_index(i) for i in range(0, num_devices)]
    return device_list

def get_soundflower_index():
    device_list = get_device_list()
    soundflower_index = find_device("Soundflower (2ch)", device_list)
    return soundflower_index

def get_current_output():
    device_list = get_device_list()
    try:
        find_device("USB Audio Device", device_list)
        return "USB Audio Device"
    except:
        return "Built-in Output"

def get_multi_device(output):
    if output == "USB Audio Device":
        return "Multi-Output Device (USB)"
    else:
        return "Multi-Output Device (Built-in)"

# ---------- Recording to file ------------
       
def record_audio(device_index, format, channels, rate, chunk, record_seconds):
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=chunk)

    log("Recording for {} seconds...".format(record_seconds))

    frames = []

    for i in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    return frames

def write_file(frames, path, format, channels, rate):
    wf = wave.open(path, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()
    return path

def empty_audio_folder():
    filelist = [ f for f in os.listdir(SAVE_PATH) if f.endswith(".wav") ]
    for f in filelist:
        os.remove(os.path.join(SAVE_PATH, f))

# ----------- Gracenote -------------------

def query_gracenote(sound_path):
    # TODO - handle double quotes in the output
    out = subprocess.check_output([config["APP_PATH"], config["GRACENOTE_LICENCE_PATH"], sound_path, config["GRACENOTE_CLIENT_ID"], config["GRACENOTE_CLIENT_TAG"]], stderr=subprocess.STDOUT)
    result = json.loads(out)
    try:
        error = result["error"]
    except:
        return result
    raise GracenoteError(error)

def log(statement):
    if not args["quiet"]:
        print(statement)

def query_mood(userID, artist, track):
    result = pygn.search(clientID=config["GRACENOTE_WEB_ID"], userID=userID, artist=artist, track=track)
    moods = []
    moods.append(result['mood']['1']['TEXT'])
    moods.append(result['mood']['2']['TEXT'])
    print("Found the following moods: "+ moods[0] +", " + moods[1])
    return moods

# ----------- Giphy------------------------

def fetch_gif(text, num):
    print("Searching for '"+text+"' GIFs")
    results = giphypop.search(term=text, limit=num, api_key=config["GIPHY_API_KEY"])
    for i in range(0, num):
        result = next(results)
        url = result.media_url
        new_text = text.replace('/', '-') 
        urllib.request.urlretrieve(url, "gifs/"+new_text+"_"+str(i)+".gif")

def empty_gif_folder():
    filelist = [ f for f in os.listdir(GIF_PATH) if f.endswith(".gif") ]
    for f in filelist:
        os.remove(os.path.join(GIF_PATH, f))

# ----------- Main ------------------------

def main():

    output = get_current_output()
    multi_out = get_multi_device(output)
    FNULL = open(os.devnull, "w")
    GRACENOTE_USER_ID = pygn.register(config["GRACENOTE_WEB_ID"])

    if subprocess.call(["SwitchAudioSource", "-s", multi_out], stdout=FNULL, stderr=FNULL) == 0:
        while True:
            length = RECORD_SECONDS
            match = False
            attempts = 0
            while not match and attempts <= 2:
                input_audio = record_audio(get_soundflower_index(), FORMAT, CHANNELS, RATE, CHUNK, length)
                try:
                    write_file(input_audio, COMPLETE_NAME, FORMAT, CHANNELS, RATE)
                except IOError:
                    log("Error writing the sound file.")
                resp = query_gracenote(COMPLETE_NAME)
                if resp["result"] is None:
                    log("The track was not identified.")
                    length += 3
                    attempts += 1
                    if attempts <= 2:
                        log("Retrying...")
                else:
                    match = True
            if match:
                match_response = json.dumps(resp["result"], indent=4, separators=("", " - "), ensure_ascii=False).encode("utf8")
                artist = resp["result"]["artist"]
                track = resp["result"]["track"]

                # remove all gifs in directory
                empty_gif_folder()

                # fetch gifs
                fetch_gif(artist, GIF_LIMIT)
                fetch_gif(track, GIF_LIMIT)

                moods = query_mood(GRACENOTE_USER_ID, artist, track)
                fetch_gif(moods[0], GIF_LIMIT)
                fetch_gif(moods[1], GIF_LIMIT)

            print("Waiting another "+str(RECORD_INTERVAL_MIN)+" minutes before guessing the song...")
            time.sleep(RECORD_INTERVAL_MIN * 60)
    else:
        raise RuntimeError("Couldn't switch to multi-output device.")
    p.terminate()
    os.remove(COMPLETE_NAME)
    if subprocess.call(["SwitchAudioSource", "-s", output], stdout=FNULL, stderr=FNULL) == 0:
        return
    else:
        raise RuntimeError("Couldn't switch back to output.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Identify currently playing audio")
    parser.add_argument("--discogs", "-d", action="store_true")
    parser.add_argument("--want", "-w", action="store_true")
    parser.add_argument("--open", "-o", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = vars(parser.parse_args())

    if args["verbose"]:
        main()
    else:
        try:
            main()
        except GracenoteError as e:
            print("Gracenote error: "+e)
            sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)
