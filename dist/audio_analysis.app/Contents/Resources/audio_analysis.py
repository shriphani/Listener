#!/usr/bin/env python
#Author: Shriphani Palakodety
#Tool to aid those with noise cancellation headphones

import Skype4Py
import pyaudio
import wave
import sys
import struct
import numpy
import time
import os

skype = Skype4Py.Skype()
skype.Attach()
#print skype.Call()
#print Skype4Py.clsInProgress

#CallFinishedSet = set ([Skype4Py.clsFailed, Skype4Py.clsFinished, Skype4Py.clsMissed, Skype4Py.clsRefused, Skype4Py.clsBusy, Skype4Py.clsCancelled])

Growl_exists = True

try:
	import Growl
except ImportError:
	print "No Growl"
	Growl_exists = False
	pass

skype_on_call = False
notifier = 0
if Growl_exists:
	notifier = Growl.GrowlNotifier('Listener',  ['Attention', 'test'])
	#notifier.applicationName = 'Listener'
    	notifier.register()

def record():
    '''Records Input From Microphone Using PyAudio'''
    duration = 3 #record for 1 second. Pretty long duration don't you think
    outfile = "/var/tmp/analysis.wav"
    
    p = pyaudio.PyAudio()
    
    inStream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,input=True, frames_per_buffer=1024)

    out = []
    upper_lim = 44100 / 1024 * duration #upper limit of the range we record to. 44100 / 1024 sized chunk * 5 seconds
    
    for i in xrange(0, upper_lim):
        data = 0
	try:
	    data = inStream.read(1024)
	except IOError:
	    return
        out.append(data)
    
    #now the writing section where we write to file
    data = ''.join(out)
    outFile = wave.open(outfile, "wb")
    outFile.setnchannels(1)
    outFile.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    outFile.setframerate(44100)
    outFile.writeframes(data)
    outFile.close()
    analyze()


def analyze():
    #if skype_on_call:
    #	print "\n"
    #	print "Skype Call In Progress"
	#print "Listener On Hold"
	#return
    inFile = wave.open("analysis.wav", "rb") #open a wav file in read mode
    logFile = open("/var/tmp/audio.log", "w")
    thresh = 1000  #establish a minimum threshold
    max_samp = 0		
    
    decision = [0]

    #for i in xrange(441):

    inactive_counter = 0
	
    vals = inFile.readframes(inFile.getnframes()) #read in 30 samples
    len(vals)
    results = struct.unpack("%dh"%(inFile.getnframes()), vals)  #unpack to get the samples
    results = [abs(x) for x in results]
    
    #now we need to pull 30 samples at a time (30 samples = 1 frame).

    for i in xrange(4404):
	frame = results[30*i: 30*(i+1)]
	print frame
	new_thresh = (thresh * (1 - (2.0 ** -7)))  +  ((2 ** -8) * max_samp)
         
	#check how many samples go above this new threshold
	count = 0

	for j in frame:
	    if j > new_thresh:
		count += 1
	if count / 30.0 >= 0.9 :   #need it to beat 90%
	    #frame is a candidate for speech
	    decision.append(1)
         
	else:
	    #this is where we use a counter based implementation for labelling inactiveness
	    if inactive_counter < 10 and decision[-1] == 1: #we ignore silence for 10 runs
		decision.append(1)
		inactive_counter += 1
	    else:
		inactive_counter = 0
		decision.append(0)
         
	#update the threshold and the max sample values
	thresh = new_thresh
	max_samp = max(frame)

    #final check for characterization as speech, we use another counter
    active_counter = 0 #since the inactive counter will cause silence to be recognized as speech, we only consider speech as 
    print decision
    final_num = 0
    for val in decision:
	if active_counter >= 18:
	    print "Speech!"
	    final_num += 1
	    active_counter = 0
	if val == 1:
	    active_counter += 1
	else:
	    active_counter = 0



    results = [x ** 2 for x in results]
    intensity = 20 * numpy.log10(numpy.sqrt(sum(results)/inFile.getnframes()))
    
    if final_num >= 3 and intensity > 48:
    	if Growl_exists:
	    notifier.notify('Attention','Listener', 'Speech Detected Nearby')
	else:
	    logFile.write("Speech Detected Nearby!\nSomeone might be calling you")
    logFile.close()
    inFile.close()

if __name__ == "__main__":
    
    #initiate daemon state.
    #Daemon processes have INIT as their parent
    #i.e. PPID = 1
    #This script can still run as a process associated with you
    #but it will die when you log out.

#    pid = 0
#    try:
#	pid = os.fork()
#    except OSError:
#	print "Cannot run as daemon\n"
#    
#    if pid != 0:
#	#parent process can quit
#	os._exit(0)
    
    while True:
	while skype.ActiveCalls.Count:
	    time.sleep(2)
	time.sleep(2)
	record()

