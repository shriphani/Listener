#!/usr/bin/env python
#Author: Shriphani Palakodety
#Environment monitoring for the hearing impaired.

import logging
import pyaudio
import datetime
import wave
import sys
import numpy
import struct
import os
from gntp import notifier

from VAD import VAD

# VAD constants
INSTANCES_VAD_IS_RUN = 0
AVERAGE_INTENSITY_OF_RUNS = 0
DURATION = 3   # length of 1 recording
OUTPUT_FILE = 'analysis.wav'

# pyaudio constants
PYAUDIO_INSTANCE = pyaudio.PyAudio()
PYAUDIO_CHANNELS = 1
PYAUDIO_RATE = 44100
PYAUDIO_INPUT = True
PYAUDIO_FRAMES_PER_BUFFER = 1024

# Listener constants
NUM_FRAMES = PYAUDIO_RATE / PYAUDIO_FRAMES_PER_BUFFER
LAST_NOTIFICATION_TIME = None

#logging constants
LOG_FILE_NAME = 'decisions.log'
LOG_FILE_FD = open(LOG_FILE_NAME, 'w')
logging.basicConfig(level=logging.ERROR) # this guy exists because Growl is angry about something

#notifications using growl
GROWL = notifier.GrowlNotifier(
    applicationName = "Listener",
    notifications = ["Speech"],
    defaultNotifications = ["Speech"]
)

GROWL.register()


def record(duration):
    '''Records Input From Microphone Using PyAudio'''
    
    in_stream = PYAUDIO_INSTANCE.open(
        format=pyaudio.paInt16,
        channels=PYAUDIO_CHANNELS,
        rate=PYAUDIO_RATE,
        input=PYAUDIO_INPUT,
        frames_per_buffer=PYAUDIO_FRAMES_PER_BUFFER
    )

    out = []
    upper_lim = NUM_FRAMES * duration
    
    for i in xrange(0, upper_lim):
        data = in_stream.read(1024)
        out.append(data)
    
    #now the writing section where we write to file
    data = ''.join(out)
    out_file = wave.open(OUTPUT_FILE, "wb")
    out_file.setnchannels(1)
    out_file.setsampwidth(PYAUDIO_INSTANCE.get_sample_size(pyaudio.paInt16))
    out_file.setframerate(44100)
    out_file.writeframes(data)
    out_file.close()


def analyze():
    '''Invokes the VAD and logs the decision'''
    
    global AVERAGE_INTENSITY_OF_RUNS
    global INSTANCES_VAD_IS_RUN
    global LAST_NOTIFICATION_TIME

    (notify_or_not, AVERAGE_INTENSITY_OF_RUNS) =  VAD.moattar_homayounpour(OUTPUT_FILE, AVERAGE_INTENSITY_OF_RUNS, INSTANCES_VAD_IS_RUN)

    INSTANCES_VAD_IS_RUN += 1

    if notify_or_not:
        notify_time = datetime.datetime.now()
        GROWL.notify(
            noteType = "Speech",
            title = "Listener",
            description = "Speech Detected at %d:%d:%d" % (notify_time.hour, notify_time.minute, notify_time.second),
            sticky = False,
            priority = 1,
        )

def dump_to_log(time):
    '''The notifications module expects information of type <str:Notification> type per line'''
    LOG_FILE_FD.write('Speech detected at: %d:%d:%d\n' % (time.hour, time.minute, time.second))

def exit():
    LOG_FILE_FD.close()
    OUTPUT_FILE.close()


if __name__ == "__main__":
    
    while True:
        record(DURATION)
        analyze()
