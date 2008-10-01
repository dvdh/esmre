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

class RootState(object):
    def __init__(self):
        self.hints        = [""]
        self.to_append    = ""
        self.group_level  = 0
        self.in_class     = False
        self.in_backslash = False
        self.in_braces    = False


def hints(regex):
    state = RootState()
    
    for ch in regex:
        if state.in_backslash:
            state.in_backslash = False
            
        elif state.in_class:
            if ch == "]":
                state.in_class = False
                
            elif ch == "\\":
                state.in_backslash = True
            
            else:
                pass
            
        elif state.group_level > 0:
            if ch == ")":
                state.group_level -= 1
                
            elif ch == "(":
                state.group_level += 1
                
            elif ch == "[":
                state.in_class = True
                
            elif ch == "\\":
                state.in_backslash = True
                
            else:
                pass
        
        elif state.in_braces:
            if ch == "}":
                state.in_braces = False
            
            else:
                pass
        
        else:
            if ch in "?*":
                state.to_append = ""
                state.hints.append("")
            
            elif ch in "+.^$":
                if state.to_append:
                    state.hints[-1] += state.to_append
                
                state.to_append = ""
                state.hints.append("")
            
            elif ch == "(":
                if state.to_append:
                    state.hints[-1] += state.to_append
                    
                state.to_append = ""
                state.hints.append("")
                state.group_level += 1
            
            elif ch == "[":
                if state.to_append:
                    state.hints[-1] += state.to_append
                
                state.to_append = ""
                state.hints.append("")
                state.in_class = True
            
            elif ch == "{":
                if state.to_append:
                    state.hints[-1] += state.to_append[:-1]
                
                state.to_append = ""
                state.hints.append("")
                state.in_braces = True
                
            elif ch == "\\":
                if state.to_append:
                    state.hints[-1] += state.to_append
                
                state.to_append = ""
                state.hints.append("")
                state.in_backslash = True
                
            elif ch == "|":
                return []
                
            else:
                if state.to_append:
                    state.hints[-1] += state.to_append
                
                state.to_append = ch
            
    if state.to_append:
        state.hints[-1] += state.to_append
            
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
