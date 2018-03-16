from sys import byteorder
from array import array
from struct import pack
from pydub import AudioSegment
from pydub.playback import play

import asyncio
import tkinter as tk
import time
import pyaudio
import wave
import threading

################################################################################################
# Parameters you can edit

CONCURRENT_SONGS = 10            # how many songs playing at full volume before the first song starts becoming softer
TIME_TO_RECORD = 60              # time per recording in seconds
VOLUME_REDUCTION = 10            # how much to reduce volume per iteration
MIN_VOLUME = 30                  # the lowest volume; if volume is lower than this, the song stops playing
BUTTON_PRESS = "a"               # which button to press to start recording

################################################################################################

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

class Songplay(threading.Thread):
    volumeReduce = 0
    path = ""
    def __init__(self, path):
        threading.Thread.__init__(self)
        self.path = path
        self.start()

    def run(self):
        while (self.volumeReduce <= MIN_VOLUME):
            reduce_and_play(self.path, self.volumeReduce)

    def reduceVolume(self):
        self.volumeReduce = self.volumeReduce + VOLUME_REDUCTION

    def getVolume(self):
        return self.volumeReduce

class Recorder(threading.Thread):
    name = ""
    time = 0

    def __init__(self, name, time, playback):
        threading.Thread.__init__(self)
        self.name = name
        self.time = time
        self.playback = playback
        self.start()

    def callback(self):
        print("Looping " + self.name)
        song = Songplay(self.name)
        playback.addSong(song)

    def run(self):
        record_to_file(self.name, self.time)
        print("Finished recording")
        self.callback()

class PlayBack:
    i = 0
    songs = []
    canRecord = True

    def __init__(self):
        pass

    def recordSong(self):
        if not self.canRecord:
            print("Please wait until current recording is finished.")
            return
        self.canRecord = False
        self.i = self.i + 1
        name = "recording" + str(self.i) + ".wav"
        print("Adding song " + name)
        Recorder(name, TIME_TO_RECORD, self)

    def addSong(self, song):
        self.songs.append(song)
        while (self.songs[0].getVolume() >= MIN_VOLUME):
            gone = self.songs.pop(0)
            print("Removing " + gone.path)
        if len(self.songs) > CONCURRENT_SONGS:
            for i in range(0, len(self.songs) - CONCURRENT_SONGS):
                self.songs[i].reduceVolume()
        self.canRecord = True
        print("")

def record(timeSec):
    """
    Record a word or words from the microphone and 
    return the data as an array of signed shorts.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    r = array('h')
    startTime = time.clock()

    while startTime + timeSec > time.clock():
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    return sample_width, r

def record_to_file(path, timeSec):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record(timeSec)
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def reduce_and_play(wavPath, reduction):  
    song = AudioSegment.from_wav(wavPath)
    song = song - reduction
    play(song)

def record_new(playback):
    playback.recordSong()

def get_loops(playback):
    for song in playback.songs:
        print(song.path + ", volume: -" + str(song.volumeReduce))
    print("")

if __name__ == '__main__':
    print("\n")
    print("Usage:")
    print("Click the button, or press the designated BUTTON_PRESS (default: a) on your keyboard to record.\n")
    print("Current parameters:")
    print("CONCURRENT_SONGS = " + str(CONCURRENT_SONGS))
    print("TIME_TO_RECORD = " + str(TIME_TO_RECORD))
    print("VOLUME_REDUCTION = " + str(VOLUME_REDUCTION))
    print("MIN_VOLUME = " + str(MIN_VOLUME))
    print("BUTTON_PRESS = " + BUTTON_PRESS + "\n")

    playback = PlayBack()
    root = tk.Tk()
    button = tk.Button(root, text='Record clip', command=lambda: record_new(playback))
    button2 = tk.Button(root, text='List looping clips', command=lambda: get_loops(playback))
    root.bind(BUTTON_PRESS,lambda event: record_new(playback))
    button.pack()
    button2.pack()
    root.mainloop()