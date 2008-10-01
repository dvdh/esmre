#!/usr/bin/env python
# encoding: utf-8

# esmre.py - clue-indexed regular expressions module
# Copyright (C) 2007 Tideway Systems Limited.
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import esm
import threading

class InBackslashState(object):
    def __init__(self, parent_state):
        self.parent_state = parent_state
    
    def process_byte(self, ch):
        return self.parent_state


class InClassState(object):
    def __init__(self, parent_state):
        self.parent_state = parent_state
    
    def process_byte(self, ch):
        if ch == "]":
            return self.parent_state
            
        elif ch == "\\":
            return InBackslashState(self)
        
        else:
            return self


class InBracesState(object):
    def __init__(self, parent_state):
        self.parent_state = parent_state
    
    def process_byte(self, ch):
        if ch == "}":
            return self.parent_state
        
        else:
            return self


class InGroupState(object):
    def __init__(self, parent_state):
        self.parent_state = parent_state
    
    def process_byte(self, ch):
        if ch == ")":
            return self.parent_state
            
        elif ch == "(":
            return InGroupState(self)
            
        elif ch == "[":
            return InClassState(self)
            
        elif ch == "\\":
            return InBackslashState(self)
            
        else:
            return self


class RootState(object):
    def __init__(self):
        self.hints        = [""]
        self.to_append    = ""

    def process_byte(self, ch):
        if ch in "?*":
            self.to_append = ""
            self.hints.append("")
            
            return self
        
        elif ch in "+.^$":
            if self.to_append:
                self.hints[-1] += self.to_append
            
            self.to_append = ""
            self.hints.append("")
            
            return self
        
        elif ch == "(":
            if self.to_append:
                self.hints[-1] += self.to_append
                
            self.to_append = ""
            self.hints.append("")
            
            return InGroupState(self)
        
        elif ch == "[":
            if self.to_append:
                self.hints[-1] += self.to_append
            
            self.to_append = ""
            self.hints.append("")
            
            return InClassState(self)
        
        elif ch == "{":
            if self.to_append:
                self.hints[-1] += self.to_append[:-1]
            
            self.to_append = ""
            self.hints.append("")
            
            return InBracesState(self)
            
        elif ch == "\\":
            if self.to_append:
                self.hints[-1] += self.to_append
            
            self.to_append = ""
            self.hints.append("")
            
            return InBackslashState(self)
            
        elif ch == "|":
            self.hints = []
            raise StopIteration
            
        else:
            if self.to_append:
                self.hints[-1] += self.to_append
            
            self.to_append = ch
            
            return self

def hints(regex):
    state = RootState()
    
    try:
        for ch in regex:
            state = state.process_byte(ch)
        
        if state.to_append:
            state.hints[-1] += state.to_append
    
    except StopIteration:
        pass
            
    return [hint for hint in state.hints if hint]


def shortlist(hints):
    if not hints:
        return []
    
    best = ""
    
    for hint in hints:
        if len(hint) > len(best):
            best = hint
            
    return [best]


class Index(object):
    def __init__(self):
        self.esm = esm.Index()
        self.hintless_objects = list()
        self.fixed = False
        self.lock = threading.Lock()
        
        
    def enter(self, regex, obj):
        self.lock.acquire()
        try:
            
            if self.fixed:
                raise TypeError, "enter() cannot be called after query()"
            
            keywords = shortlist(hints(regex))
            
            if not keywords:
                self.hintless_objects.append(obj)
            
            for hint in shortlist(hints(regex)):
                self.esm.enter(hint.lower(), obj)
        
        finally:
            self.lock.release()
            
            
    def query(self, string):
        self.lock.acquire()
        try:
            
            if not self.fixed:
                self.esm.fix()
                self.fixed = True
            
        finally:
            self.lock.release()
        
        return self.hintless_objects + \
            [obj for (_, obj) in self.esm.query(string.lower())]
