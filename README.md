## Recorder

Recorder is a program designed to record and loop music clips.
As more clips are added, older clips will decrease in volume gradually until they stop playing.
The app will create `.wav` files named `recording_.wav` in the directory it is run.

Installation
------------

You need python 3.6 as well as two other modules.

First install python 3.6 (if you don't already have it):
https://www.python.org/

Then go into your command prompt (start -> type "cmd.exe" -> hit enter).

Then type:
`python -m pip install pyaudio`


Usage
-----

Double click recorder.py (it should automatically open in python 3).
You can change some parameters by editing recorder.py in a text-editor.


Changelog
---------

* v1.4:
    - Now syncs each loop
    - Handle python recording delay offset
* v1.3:
    - Now caches audio data in memory instead of writing to disk
    - Writing to disk now a toggleable feature
    - Added feature to listen to yourself while recording
    - Removed pydub dependency
* v1.2:
    - Fixed issue with queuing extra records when already recording
    - Fixed a bug with removal of songs
    - Added more informative logs during runtime
    - Added button to see currently looping songs
* v1.1.1:
    - Code clean up
* v1.1:
    - Removed background music functionality (Simplifies running)
    - Fixed a bug with looping
* v1.0:
    - Initial release
