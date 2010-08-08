#!/usr/bin/env python
#Author: Shriphani Palakodety
#mail: spalakod@purdue.edu

import Skype4Py

class SkypeCallChecker():
    '''Simple class that uses Skype4Py to detect if a call
       is in progress'''

    def __init__(self):
        '''So far, we only open a connection to Skype'''
        self.connection = Skype4Py.Skype()
        self.connected = False

        if self.connection.Client.IsRunning:
            try:
                self.connection.Attach()
            except RuntimeError:
                #print "Fuck you Skype4Py\n"
                pass
                
            self.connected = True

    def __checkCallStatus__(self):
        '''Checks if there is a call in progress'''
        if self.connected:
            try:
                return self.connection.ActiveCalls.Count
            except RuntimeError:
                #print "Fuck you Skype4Py\n"
                pass
        return 0
        