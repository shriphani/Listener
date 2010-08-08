#!/usr/bin/env python
#Author: Shriphani Palakodety
#Tool to aid those with noise cancellation headphones

#import the required modules
import pyaudio
import wave
import sys
import struct
import numpy
import time
import SkypeCallChecker

#import Skype4Py move Skype specific part of code to new class

#variable that checks if Growl is installed. This is used for notifications.
Growl_exists = True

#try to import growl
try:
	import Growl
	
except ImportError:
	print "Growl is not installed.\n I will dump output in /var/tmp/audio.log\n"
	Growl_exists = False

skype_on_call = False
notifier = 0

#obtain a GrowlNotifier
if Growl_exists:
	notifier = Growl.GrowlNotifier('Listener',  ['Attention', 'test'])
	notifier.register()

def record():
    '''Records Input From Microphone Using PyAudio'''
    duration = 3 #record for 1 second. Pretty long duration don't you think
    outfile = "analysis.wav"
    
    p = pyaudio.PyAudio()
    
    inStream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,input=True, frames_per_buffer=1024)

    out = []
    upper_lim = 44100 / 1024 * duration #upper limit of the range we record to. 44100 / 1024 sized chunk * 5 seconds
    
    for i in xrange(0, upper_lim):
        data = inStream.read(1024)
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
    if skype_on_call:
    	print "\n"
    	print "Skype Call In Progress"
	print "Listener On Hold"
	return
    inFile = wave.open("analysis.wav", "rb") #open a wav file in read mode
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
	    print "Speech Detected Nearby!\nSomeone might be calling you"
    inFile.close()

if __name__ == "__main__":
	skypeCallChecker = SkypeCallChecker.SkypeCallChecker()
	while True:
		if skypeCallChecker.__checkCallStatus__():
			#print "Ma ki kir kiri\n"
			#This essentially means that a call is taking place
			#Right now Skype4Py isn't working as intended and I
			#cannot fix it.

			#Make the app sleep for 20 seconds
			time.sleep(20)
			
		else:   #Either Skype4Py is broken or there isn't a call
			record()
			time.sleep(2)
		
			


