#!/usr/bin/env python
#Author: Shriphani Palakodety
#Environment monitoring for the hearing impaired.

#import the required modules
import pyaudio
import time
import VAD
import wave
import SkypeCallChecker
import sys
import numpy
import struct
import os

#VARIABLES
Growl_exists = True   #variable that checks if Growl is installed. This is used for notifications.
average_intensity = 0   #initially this sucker is 0
instances = 0   #initially, 0 3-second samples analyzed
lastSpeechAlertTime = time.gmtime() #record the last time speech was picked up

#try to import growl
try:
	import Growl
	
except ImportError:
	print "Growl is not installed.\n I will dump output in /var/tmp/audio.log\n"
	Growl_exists = False


#on unix machines, use /var/tmp/audio.log for the result.

if os.name == "posix":
    sys.stdout = open("/var/tmp/audio.log", "w")
else:
    sys.stdout = open("audio.log", "w")

skype_on_call = False
notifier = 0

#obtain a GrowlNotifier
if Growl_exists:
	notifier = Growl.GrowlNotifier('Listener',  ['Attention', 'test'])
	notifier.register()

def record(duration):
    '''Records Input From Microphone Using PyAudio'''
    #duration = 3 #record for 1 second. Pretty long duration don't you think
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


def analyze(duration):
    #First compare the obtained sample to every other recorded profile
    #f = open("profiles.txt", "r")
    #for profile in f:
    #    if pearsonCoeff('analysis.wav', profile.strip()) > 0.8:
    #        if Growl_exists:
    #            notifier.notify('Attention', 'Listener', 'Profile: '+profile+'matched')
    #        else:
    #            print "Sound profile matched: "+profile+"\n"
    #f.close()
    #run a VAD algorithm now
    
    global average_intensity
    global instances
    global lastSpeechAlertTime

    (speech, avg_intensity) =  VAD.Moattar_Homayounpour_VAD("analysis.wav", duration, average_intensity, instances)
    average_intensity = avg_intensity
    instances += 1
    #speech = VAD.Milanovic_Lukac_Domazetovic_VAD("analysis.wav") #uncomment to use this

    #print average_intensity
    #print instances

    if speech:
        lastSpeechAlertTime = time.gmtime()
        if Growl_exists:
			notifier.notify('Attention','Listener', 'Speech Detected Nearby')
        else:
			print "Speech Detected Nearby!\nSomeone might be calling you"
    else:
        print "Last call detected at " + time.strftime("%H:%M:%S on %b-%d", lastSpeechAlertTime)



def pearsonCoeff(signal1, signal2):
    samples1 = wave.open(signal1, "rb")
    samples2 = wave.open(signal2, "rb")
    vals1 = samples1.readframes(samples1.getnframes())
    results1 = list(struct.unpack("%dh" %(samples1.getnframes()), vals1))

    vals2 = samples2.readframes(samples2.getnframes())
    results2 = list(struct.unpack("%dh" %(samples2.getnframes()), vals2))
    
    #now pad the smaller array with 0s to equate in size
    if len(results1) > len(results2):
        results2 += [0] * (len(results1) - len(results2)) #need to pad results2
        #print results2
    else:
        results1 += [0] * (len(results2) - len(results1))
        #print results1
    #samples_size, S1, S2, Freq_Mult = len(results1), numpy.fft.rfft(results1), numpy.fft.rfft(results2), []
    #print samples_size
    #for i in range(samples_size):
    #    print i
    #    Freq_Mult.append(S1[i].conjugate() * S2[i])
    #
    #corr_S1_S2 = max(numpy.fft.irfft(Freq_Mult))
    #
    #
    #print ((numpy.fft.rfft(results1)),(numpy.fft.rfft((results2[::-1]))))		#correlate results1 and results2

    
    
    corr_S1_S2 = max(abs(numpy.fft.irfft(numpy.fft.rfft(results1)*numpy.fft.rfft(results2[::-1]))))		#correlate results1 and results2
    corr_S1_S1 = max(abs(numpy.fft.irfft(numpy.fft.rfft(results1)*numpy.fft.rfft(results1[::-1]))))		#correlate results1 and results2
    corr_S2_S2 = max(abs(numpy.fft.irfft(numpy.fft.rfft(results2)*numpy.fft.rfft(results2[::-1]))))		#correlate results1 and results2
   
    samples1.close()
    samples2.close()
    #print "#######"
    print corr_S1_S2
    print corr_S1_S1
    print corr_S2_S2
    print "#######"
    a = ((corr_S1_S2 ** 2.0) / (corr_S1_S1 * corr_S2_S2))
    print numpy.sqrt(a)
    return numpy.sqrt(a)


if __name__ == "__main__":
    
    
    #this script is meant to be run as a daemon.
    #fork first, and kill the parent process. 
    #Then the child becomes a child of init.
   
    #pid = os.fork()

    #if pid:
        #parent process
    #    exit()
    #else:
    try:
        record(3)
    except IOError:
        pass    
        
    analyze(3)
    skypeCallChecker = SkypeCallChecker.SkypeCallChecker()
    while True:
        if skypeCallChecker.__checkCallStatus__():
            #This essentially means that a call is taking place
            #Right now Skype4Py isn't working as intended and I
            #cannot fix it.
            print "\n"
            print "Skype Call In Progress"
            print "Listener On Hold"
            
            #Make the app sleep for 20 seconds
            time.sleep(20)
        
        else:   #Either Skype4Py is broken or there isn't a call
            try:
                record(3) #record for 3 seconds
            except IOError:
                continue 
            analyze(3)
            sys.stdout.flush()
            time.sleep(1)
		
			


