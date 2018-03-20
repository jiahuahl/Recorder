from sys import byteorder
from array import array
from struct import pack, unpack

import asyncio
import tkinter as tk
import time
import pyaudio
import wave
import threading

################################################################################################
# Parameters you can edit

SAVETOFILE = False               # Set true to save recordings to file
FEEDBACK = False                 # Set true to listen to the recording during recording *WARNING: playback is slightly delayed*
CONCURRENT_SONGS = 10            # how many songs playing at full volume before the first song starts becoming softer
TIME_TO_RECORD = 60              # time per recording in seconds
VOLUME_REDUCTION = 0.25          # how much to reduce volume per iteration
BUTTON_PRESS = "a"               # which button to press to start recording

################################################################################################

CHUNK_SIZE = 256
FORMAT = pyaudio.paInt16
RATE = 44100

class Songplay(threading.Thread):
    volume = 1
    path = ""
    data = []
    sample = 0
    def __init__(self, path, data, sample_width):
        threading.Thread.__init__(self)
        self.path = path
        self.data = data
        self.sample = sample_width
        self.start()

    def run(self):
        while (self.volume > 0):
            reduce_and_play(self.data, self.volume)

    def reduceVolume(self):
        self.volume = self.volume - VOLUME_REDUCTION

    def getVolume(self):
        return self.volume

class Recorder(threading.Thread):
    name = ""
    time = 0

    def __init__(self, name, time, playback):
        threading.Thread.__init__(self)
        self.name = name
        self.time = time
        self.playback = playback
        self.start()

    def callback(self, sample_width, file, data):
        print("Looping " + self.name)
        song = Songplay(self.name, data, sample_width)
        if SAVETOFILE:
            record_to_file(self.name, sample_width, file)
        playback.addSong(song)

    def run(self):
        sample_width, file, data = record(self.time)
        print("Finished recording")
        self.callback(sample_width, file, data)

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
        name = "recording_" + str(self.i)
        print("Adding song " + name)
        Recorder(name, TIME_TO_RECORD, self)

    def addSong(self, song):
        self.songs.append(song)
        while (self.songs[0].getVolume() <= 0):
            gone = self.songs.pop(0)
            print("Removing " + gone.path)
        if len(self.songs) > CONCURRENT_SONGS:
            for i in range(0, len(self.songs) - CONCURRENT_SONGS):
                self.songs[i].reduceVolume()
        self.canRecord = True
        print("")

def record(timeSec):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    r = array('h')
    d = []
    startTime = time.clock()
    
    for i in range(0, int(RATE / CHUNK_SIZE * timeSec)):
        data = stream.read(CHUNK_SIZE)
        d.append(data)
        if FEEDBACK:
            stream.write(data, CHUNK_SIZE)

        if SAVETOFILE:
            snd_data = array('h', data)
            if byteorder == 'big':
                snd_data.byteswap()
            r.extend(snd_data)

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    return sample_width, r, d

def record_to_file(path, sample_width, data):
    data = pack('<' + ('h'*len(data)), *data)
    path = path + ".wav"
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def reduce_and_play(data, reduction):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)
        
    for d in data:
        int_data = array('h', d)
        if byteorder == 'big':
            snd_data.byteswap()
        r = array('h')
        for i in int_data:
            r.append(int(i * reduction))
        
        stream.write(bytes(r), CHUNK_SIZE)
        
    stream.stop_stream()
    stream.close()
    p.terminate()

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
    print("FEEDBACK = " + str(FEEDBACK))
    print("SAVING TO FILE = " + str(SAVETOFILE))
    print("CONCURRENT_SONGS = " + str(CONCURRENT_SONGS))
    print("TIME_TO_RECORD = " + str(TIME_TO_RECORD))
    print("VOLUME_REDUCTION = " + str(VOLUME_REDUCTION))
    print("BUTTON_PRESS = " + BUTTON_PRESS + "\n")

    playback = PlayBack()
    root = tk.Tk()
    button = tk.Button(root, text='Record clip', command=lambda: record_new(playback))
    button2 = tk.Button(root, text='List looping clips', command=lambda: get_loops(playback))
    root.bind(BUTTON_PRESS,lambda event: record_new(playback))
    button.pack()
    button2.pack()
    root.mainloop()
