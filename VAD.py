#!/usr/bin/env python
# Author: Shriphani Palakodety
# spalakod@cs.cmu.edu


#import required modules
from numpy.fft import *
from numpy import log10, sqrt
import math
import wave
import struct


MLD_FRAME_DURATION = 30 #frame length in milliseconds for milanovic, lukac and domazetovic
MLD_SAMPLES_PER_SECOND = 44100
MLD_SAMPLES_PER_FRAME = int(MLD_SAMPLES_PER_SECOND * (MLD_FRAME_DURATION / 1000.0))

MH_FRAME_DURATION = 10 #frame length in milliseconds for Moattar & Homayounpour
MH_SAMPLES_PER_SECOND = 44100
MH_SAMPLES_PER_FRAME = int(MH_SAMPLES_PER_SECOND * (MH_FRAME_DURATION / 1000.0))


def chunk_frames_indices(samples, samples_per_frame):
    '''
    Args:
        - samples: 16 bit values representing a sampled point.

    Returns:
        - an array of <FRAME_DURATION> length chunks
    '''
    return zip(
        range(0, len(samples), samples_per_frame),
        range(samples_per_frame, len(samples), samples_per_frame)
    )

def energy(samples):
    '''
    Args:
        - samples of a signal
    '''
    return sum([x**2 for x in samples])

def real_imaginary_freq_domain(samples):
    '''
    Apply fft on the samples and return the real and imaginary
    parts in separate 
    '''
    freq_domain = fft(samples)
    freq_domain_real = [abs(x.real) for x in freq_domain]
    freq_domain_imag = [abs(x.imag) for x in freq_domain]

    return freq_domain_real, freq_domain_imag

def get_dominant_freq(real_freq_domain_part, imag_freq_domain_part):
    '''Returns the dominant frequency'''
    max_real = max(real_freq_domain_part)
    max_imag = max(imag_freq_domain_part)

    dominant_freq = 0

    if (max_real > max_imag):
        dominant_freq = abs(fftfreq(len(real_freq_domain_part), d=(1.0/44100.0))[real_freq_domain_part.index(max_real)])
    else:
        dominant_freq = abs(fftfreq(len(imag_freq_domain_part), d=(1.0/44100.0))[imag_freq_domain_part.index(max_imag)])

    return dominant_freq

def get_freq_domain_magnitudes(real_part, imaginary_part):
    '''Magnitudes of the real-imag frequencies'''
    return [sqrt(x**2 + y**2) for x, y in zip(real_part, imaginary_part)]

def get_sfm(frequencies):
    return 10 * log10(geometric_mean(frequencies) / arithmetic_mean(frequencies))

def geometric_mean(frame):
    prod = 1.0
    for value in frame:
        prod *= value

    return prod ** (1.0/len(frame))

def arithmetic_mean(frame):
    return float(sum(frame)) / float(len(frame))

def get_sample_intensity(samples):
    return 20.8 * log10(sqrt(sum([x ** 2 for x in samples])/float(len(samples))))


class VAD(object):

    @staticmethod
    def moattar_homayounpour(wave_file, average_intensity, instances):
        '''
        Args:
            - wave_file : filename containing the audio to be processes
            - average_intensity : former average_intensity set by the user (we supply an updated value)
            - instances : number of times this VAD was run was previously
        '''
        in_file = wave.open(wave_file, 'rb')

        #set primary thresholds for energy, frequency and SFM
        #these values were determined using experiements by the authors
        #themselves
        energy_prim_thresh = 40
        freq_prim_thresh = 185
        sfm_prim_thresh = 5
        n_frames = in_file.getnframes()

        samples = in_file.readframes(n_frames)
        abs_samples = struct.unpack("%dh" % (n_frames), samples)

        #compute the intensity
        intensity = get_sample_intensity(abs_samples)

        #frame attribute arrays
        frame_energies = []  #holds the energy value for each frame
        frame_max_frequencies = []  #holds the dominant frequency for each frame
        frame_SFMs = []  #holds the spectral flatness measure for every frame
        frame_voiced = []  #tells us if a frame contains silence or speech

        #attributes for the entire sampled signal
        min_energy = 0
        min_dominant_freq = 0
        min_sfm = 0

        #check for the 30 frame mark
        thirty_frame_mark = False

        for i, frame_bounds in enumerate(chunk_frames_indices(abs_samples, MH_SAMPLES_PER_FRAME)):

            frame_start = frame_bounds[0]
            frame_end = frame_bounds[1]

            # marks if 30 frames have been sampled
            if i >= 30:
                thirty_frame_mark = True

            frame = abs_samples[frame_start:frame_end]
    
            #compute frame energy
            frame_energy = energy(frame)
            freq_domain_real, freq_domain_imag = real_imaginary_freq_domain(frame)
            freq_magnitudes = get_freq_domain_magnitudes(freq_domain_real, freq_domain_imag)
            dominant_freq = get_dominant_freq(freq_domain_real, freq_domain_imag)
            frame_SFM = get_sfm(freq_magnitudes)

            #now, append these attributes to the frame attribute arrays created previously
            frame_energies.append(energy)
            frame_max_frequencies.append(dominant_freq)
            frame_SFMs.append(frame_SFM)

            print frame_energies
            print frame_max_frequencies
            print frame_SFMs

            #the first 30 frames are used to set min-energy, min-frequency and min-SFM
            if not thirty_frame_mark and not i:
                min_energy = frame_energy
                min_dominant_freq = dominant_freq
                min_sfm = frame_SFM
    	        
            elif not thirty_frame_mark:
                min_energy = min(min_energy, frame_energy)
                min_dominant_freq = min(dominant_freq, min_dominant_freq)
                min_sfm = min(frame_SFM, min_sfm)

            #once we compute the min values, we compute the thresholds for each of the frame attributes
            print min_energy
            energy_thresh = energy_prim_thresh * log10(min_energy)
            dominant_freq_thresh = freq_prim_thresh
            sfm_thresh = sfm_prim_thresh

            counter = 0

            if (frame_energy - min_energy) > energy_thresh:
                counter += 1
            if (dominant_freq - min_dominant_freq) > dominant_freq_thresh:
                counter += 1
            if (frame_SFM - min_sfm) > sfm_thresh:
                counter += 1

            if counter > 1:     #this means that the current frame is not silence.
                frame_voiced.append(1)
            else:
                frame_voiced.append(0)
                min_energy = ((frame_voiced.count(0) * min_energy) + frame_energy)/(frame_voiced.count(0) + 1)

            #now update the energy threshold
            energy_thresh = energy_prim_thresh * log10(min_energy)

        #once the frame attributes are obtained, a final check is performed to determine speech.
        #at least 5 consecutive frames are needed for speech.

        in_file.close()

        instances += 1  #a new instance has been processed
        old_average_intensity = average_intensity   
        average_intensity = ((old_average_intensity * (instances-1)) + intensity) / float(instances)  #update average intensity

        if locateInArray(frame_voiced, [1, 1, 1, 1, 1]) >= 0 and intensity > old_average_intensity:
            return (True, average_intensity)

        return (False, average_intensity)
        

def locateInArray(list1, list2):
    x = 0
    y = 0
    for x in xrange(len(list1)):
        if list1[x] == list2[0]:
            counter = 0
            for y in xrange(len(list2)):
                try:
                    if list1[x+y] != list2[y]:
                        break
                    else:
                        counter += 1
                except IndexError:
                    return -1
            if counter == len(list2):
                return x
    return -1

    
if __name__ == "__main__":

    a, b = VAD.moattar_homayounpour('analysis.wav', 0, 0)
    print VAD.moattar_homayounpour('analysis.wav', 0, 1)
