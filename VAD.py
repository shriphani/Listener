#!/usr/bin/env python
#Author: Shriphani Palakodety
#A list of VAD algorithms used for Listener.


#A list of algorithms used:
# ->  S. Milanovic, Z. Lukac, A. Domazetovic (I cannot find their paper anywhere)
# ->  M. H. Moattar and M. M. Homayounpour


#import required modules
from numpy.fft import *
from numpy import log10, sqrt
import math
import wave
import struct


def Milanovic_Lukac_Domazetovic_VAD(filename):
    '''Implements a simple VAD algorithm by
       Milanovic, Lukac, Domazetovic'''
    inFile = wave.open(filename, "rb") #open a wav file in read mode
    thresh = 1000  #establish a minimum threshold
    max_samp = 0		
    
    decision = [0]

    #for i in xrange(441):

    inactive_counter = 0
	
    vals = inFile.readframes(inFile.getnframes()) #read in 30 samples
    #len(vals)
    results = struct.unpack("%dh"%(inFile.getnframes()), vals)  #unpack to get the samples
    results = [abs(x) for x in results]
    
    #now we need to pull 30 samples at a time (30 samples = 1 frame).

    for i in xrange(4404):
	frame = results[30*i: 30*(i+1)]
	#print frame
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
    #print decision
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

    inFile.close()

    if final_num >= 3 and intensity > 48:
    	return True
    return False


def Moattar_Homayounpour_VAD(wave_file, duration):
    '''A simple VAD algorithm by Moattar and Homayounpour'''
    inFile = wave.open("analysis.wav", "rb")

    #set primary thresholds for energy, frequency and SFM
    #these values were determined using experiements by the authors
    #themselves
    energy_prim_thresh = 40
    freq_prim_thresh = 185
    SFM_prim_thresh = 5

    #frame details
    frame_size = 10  #10 ms per frame.
    samples_per_frame = int(44100 * (float(frame_size)/1000))
    

    #get all the stuff from the file.
    vals = inFile.readframes(inFile.getnframes())
    results = struct.unpack("%dh" %(inFile.getnframes()), vals)

    #compute the intensity
    intensity = 0
    for x in results:
        intensity += x ** 2
    intensity = 20 * log10(sqrt(intensity/inFile.getnframes()))

    #print results

    #We record for `duration` seconds.
    #Calculate number of frames using that
    
    num_frames = (duration * 1000) / frame_size

    #frame attribute arrays
    frame_energies = []  #holds the energy value for each frame
    frame_max_frequencies = []  #holds the dominant frequency for each frame
    frame_SFMs = []  #holds the spectral flatness measure for every frame
    frame_voiced = []  #tells us if a frame contains silence or speech

    #attributes for the entire sampled signal
    min_energy = 0
    min_dominant_freq = 0
    min_sfm = 0

    #a frame size here is 10 ms.

    for frame_index in xrange(num_frames):

        #print frame_index
        #gather values for the frames.
        frame = results[frame_index * samples_per_frame : (frame_index+1) * samples_per_frame]
        #frame = [abs(x) for x in frame]
        #compute frame energy
        energy = 0

        for sample in frame:
            energy += sample ** 2


        #now, apply FFT on this frame. This gives us an array of complex numbers.
        #both imaginary part and real part need to be split since they correspond to
        #amplitudes of different frequencies in the frequency domain.

        transformed = fft(frame)
        transformed_real = [abs(x.real) for x in transformed]
        transformed_imag = [abs(x.imag) for x in transformed]

        max_real = max(transformed_real)  #contains max value of real component
        max_imag = max(transformed_imag)  #contains max value of imag component

        dominant_freq = 0 #this holds the dominant frequency component


        #An explanation of fftfreq arguments:
        #No. of samples = length of frame
        #Between each frequency value, the step size is 1/44100 where 44100 Hz is the sampling
        #frequency
        if (max_real > max_imag):
            dominant_freq = abs(fftfreq(len(frame), d=(1.0/44100.0))[transformed_real.index(max_real)])
        else:
            dominant_freq = abs(fftfreq(len(frame), d=(1.0/44100.0))[transformed_imag.index(max_imag)])
            

        #next, compute the Spectral Flatness Measure
        #Spectral flatness measure = 10 log10(Geom_mean / Arith_mean)

        frame_SFM = 0

        try:
            frame_SFM = 10 * log10(geometric_mean(frame) / arithmetic_mean(frame))
        except ZeroDivisionError:
            return False


        #now, append these attributes to the frame attribute arrays created previously
        frame_energies.append(energy)
        frame_max_frequencies.append(dominant_freq)
        frame_SFMs.append(frame_SFM)


        #the first 30 frames are used to set min-energy, min-frequency and min-SFM
        if frame_index < 30:
	        if frame_index == 0:
	            min_energy = energy
	            min_dominant_freq = dominant_freq
	            min_sfm = frame_SFM
	        
	        else:
	            if energy < min_energy:
	                min_energy = energy
	            if dominant_freq < min_dominant_freq:
	                min_dominant_freq = dominant_freq
	            if frame_SFM < min_sfm:
	                min_sfm = frame_SFM

        #once we compute the min values, we compute the thresholds for each of the frame attributes
        energy_thresh = energy_prim_thresh * log10(min_energy)
        dominant_freq_thresh = freq_prim_thresh
        sfm_thresh = SFM_prim_thresh

        counter = 0

        if (energy - min_energy) > energy_thresh:
            counter += 1
        if (dominant_freq - min_dominant_freq) > dominant_freq_thresh:
            counter += 1
        if (frame_SFM - min_sfm) > sfm_thresh:
            counter += 1

        if counter > 1:     #this means that the current frame is not silence.
            frame_voiced.append(1)
        else:
            frame_voiced.append(0)
            min_energy = ((frame_voiced.count(0) * min_energy) + energy)/(frame_voiced.count(0) + 1)

        #now update the energy threshold
        energy_thresh = energy_prim_thresh * log10(min_energy)

    #once the frame attributes are obtained, a final check is performed to determine speech.
    #at least 5 consecutive frames are needed for speech.

    inFile.close()
    
    if locateInArray(frame_voiced, [1, 1, 1, 1, 1]) >= 0 and intensity > 50:
        return True
    return False
        

        
                
        
def geometric_mean(frame):
    prod = 1.0
    for value in frame:
        prod * value

    return prod ** (1.0/len(frame))

def arithmetic_mean(frame):
    return float(sum(frame)) / float(len(frame))

def locateInArray(list1, list2):
    x = 0
    y = 0
    for x in xrange(len(list1)):
        if list1[x] == list2[0]:
            counter = 0
            for y in xrange(len(list2)):
                if list1[x+y] != list2[y]:
                    break
                else:
                    counter += 1
            if counter == len(list2):
                return x
    return -1

    
if __name__ == "__main__":
    #a set of tests for the VAD algorithm.
    Moattar_Homayounpour_VAD("analysis.wav", 3)