from sys import byteorder
from array import array
from struct import pack, unpack
from datetime import datetime, timedelta

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
TIME_TO_RECORD = 5              # time per recording in seconds
VOLUME_REDUCTION = 0.25          # how much to reduce volume per iteration
BUTTON_PRESS = "a"               # which button to press to start recording
TIMING_OFFSET = -180             # How much to offset each recording.
VERBOSE_TIMING = False           # Enable to show logs related to timing, for debugging

################################################################################################

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
START_TIME = datetime.now()
PYAUDIO = pyaudio.PyAudio()

def millis():
   dt = datetime.now() - START_TIME
   ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
   return ms

class Songplay(threading.Thread):
    volume = 1
    path = ""
    data = []
    sample = 0
    timeOffset = 0
    stream = 0
    
    def __init__(self, path, data, sample_width, timeOffset, stream):
        threading.Thread.__init__(self)
        self.path = path
        self.data = data
        self.sample = sample_width
        self.timeOffset = timeOffset
        self.stream = stream
        self.start()

    def run(self):
        currOffset = millis() % (TIME_TO_RECORD * 1000)
        diff = currOffset - self.timeOffset
        if (diff < 0):
           diff = (TIME_TO_RECORD * 1000) + diff
        if VERBOSE_TIMING:
            print("curr: " + str(millis() % (TIME_TO_RECORD * 1000)) + ", time: " + str(self.timeOffset))
        reduce_and_play(self.data, self.volume, self.stream, diff / 1000)
        while (self.volume > 0):
            diff = 0
            currOffset = millis() % (TIME_TO_RECORD * 1000)
            if (self.timeOffset > currOffset):
                if VERBOSE_TIMING:
                    print("waiting " + str((self.timeOffset - currOffset)/1000))
                time.sleep((self.timeOffset - currOffset)/1000)
            else:
                diff = currOffset - self.timeOffset

            if VERBOSE_TIMING:
                print("curr: " + str(millis() % (TIME_TO_RECORD * 1000)) + ", time: " + str(self.timeOffset))
            reduce_and_play(self.data, self.volume, self.stream, diff / 1000)
            
    def end(self):
        self.stream.stop_stream()
        self.stream.close()

    def reduceVolume(self):
        self.volume = self.volume - VOLUME_REDUCTION

    def getVolume(self):
        return self.volume

class Recorder(threading.Thread):
    name = ""
    time = 0
    stream = 0

    def __init__(self, name, time, playback, stream):
        threading.Thread.__init__(self)
        self.name = name
        self.time = time
        self.playback = playback
        self.stream = stream
        self.start()

    def callback(self, sample_width, file, data, timeOffset, stream):
        print("Looping " + self.name)
        song = Songplay(self.name, data, sample_width, timeOffset, stream)
        if SAVETOFILE:
            record_to_file(self.name, sample_width, file)
        playback.addSong(song)

    def run(self):
        sample_width, file, data, timeOffset, stream = record(self.time, self.stream)
        print("Finished recording")
        self.callback(sample_width, file, data, timeOffset, stream)

class PlayBack:
    i = 0
    songs = []
    canRecord = True
    stream = 0

    def __init__(self):
        self.stream = PYAUDIO.open(format=FORMAT, channels=1, rate=RATE,
               input=True, output=True,
               frames_per_buffer=CHUNK_SIZE)
    def recordSong(self):
        if not self.canRecord:
            print("Please wait until current recording is finished.")
            return
        self.canRecord = False
        self.i = self.i + 1
        name = "recording_" + str(self.i)
        print("Adding song " + name)
        stream = self.stream
        Recorder(name, TIME_TO_RECORD, self, stream)

    def addSong(self, song):
        self.songs.append(song)
        while (self.songs[0].getVolume() <= 0):
            gone = self.songs.pop(0)
            print("Removing " + gone.path)
        if len(self.songs) > CONCURRENT_SONGS:
            for i in range(0, len(self.songs) - CONCURRENT_SONGS):
                self.songs[i].reduceVolume()
        self.stream = PYAUDIO.open(format=FORMAT, channels=1, rate=RATE,
            input=True, output=True,
            frames_per_buffer=CHUNK_SIZE)
        self.canRecord = True
        print("")

def record(timeSec, stream):
    startTime = millis()

    r = array('h')
    d = []
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

    startTime = startTime + TIMING_OFFSET
    sample_width = PYAUDIO.get_sample_size(FORMAT)
    return sample_width, r, d, (startTime % (timeSec*1000)), stream

def record_to_file(path, sample_width, data):
    data = pack('<' + ('h'*len(data)), *data)
    path = path + ".wav"
    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def reduce_and_play(data, reduction, stream, timeDiff):
    if VERBOSE_TIMING:
        print("skipping first " + str(timeDiff) + " of song")
    for d in range(int(RATE / CHUNK_SIZE * timeDiff), len(data)):
        int_data = array('h', data[d])
        if byteorder == 'big':
            snd_data.byteswap()
        r = array('h')
        for i in int_data:
            r.append(int(i * reduction))
        
        stream.write(bytes(r), CHUNK_SIZE)

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
    print("BUTTON_PRESS = " + BUTTON_PRESS)
    print("TIMING_OFFSET = " + str(TIMING_OFFSET)+ "\n")

    playback = PlayBack()
    root = tk.Tk()
    button = tk.Button(root, text='Record clip', command=lambda: record_new(playback))
    button2 = tk.Button(root, text='List looping clips', command=lambda: get_loops(playback))
    root.bind(BUTTON_PRESS,lambda event: record_new(playback))
    button.pack()
    button2.pack()
    root.mainloop()
