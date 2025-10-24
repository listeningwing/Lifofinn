#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    __   _ ___     ____
#   / /  (_) _/__  / _(_)__  ___
#  / /__/ / _/ _ \/ _/ / _ \/ _ \
# /____/_/_/ \___/_//_/_//_/_//_/
# The ultra small code editor.
#
# THIS FILE IS PART OF LIFOFINN CODE EDITOR. USED IN
# ANY COMMERCIAL PRODUCT WITHOUT THE WRITTEN PERMISSION
# OF THE AUTHOR IS ILLEGAL.
#
# * Note:
# a. the scripting interface assume input file and data encoded with utf-8.
# b. all data and file output from app side was encoded with utf-8.
#
#

import re
import json
import os,sys
import locale
import codecs
import datetime
import random
import string
import subprocess
import base64


app = "/Applications/Lifofinn.app/Contents/MacOS/Lifofinn"
inputSources = None # catch ctrl+c
cmdDir = None      # scripting support directory
rootUrls = None    # accessible root directory and files
accesscode = "***" # access code for automation scripts
                   # current ignored

noArgCmd = """
{
  \"msgtype\": \"%s\",
  \"accesscode\": \"%s\",
}
"""

def decodeB64Data(string):
    text = ""
    try:
        decodedBytes = base64.b64decode(string)
        text = str(decodedBytes, "utf-8")
    except: pass
    return text


def runCommand(cmd):
    global app
    dict = None
    lines = []
    isJSON = False

    JSON_message_begin = "_______BEGIN__JSON__MESSAGE_______"
    JSON_message_end   = "_______END____JSON__MESSAGE_______"

    a = []
    a.append(app)
    a.append("-c")
    a.append(cmd)
    proc = subprocess.Popen(a, stdout=subprocess.PIPE)
    for line in proc.stdout:
        line = line.decode('utf-8')
        line = line.rstrip()
        line = re.sub("\s+", " ", line)
        if isJSON:
            if line.startswith(JSON_message_end): isJSON = False
            else: lines.append(line)
        else:
            if line.startswith(JSON_message_begin): isJSON = True
            else: print('%s\n' % line) # normal log message
    textBlock = '\n'.join(lines)
    try:
        dict = json.loads(textBlock)
    except:
        print(textBlock) # print raw message if stdout does not
                         # contain a well-formatted json block
    return dict


def base64OfString(text):
    base64_bytes = base64.b64encode(text.encode('utf-8'))
    return base64_bytes.decode("ascii")


def runTextBlockCommand(command, string, args):
    global accesscode, inputSources
    fileArgCmd = """
    {
      \"msgtype\": \"%s\",
      \"accesscode\": \"%s\",
      \"string\": \"%s\",
      \"args\": \"%s\"
    }
    """
        
    dict = None
    cmd = fileArgCmd % (command, accesscode, base64OfString(string), args)
    # else:
    #   cmd = fileArgCmd % (command, accesscode, path, "")
    try:
        dict = runCommand(cmd)
    except KeyboardInterrupt: pass
    except: pass
    finally: pass
    if dict == None: return None
    if command == "repInvisibles": return dict;
    return decodeB64Data(dict["data"])


def validateString(string, length):
    l = len(string)
    return False if l == 0 or l > length else True


def removeLineEndings(string):
    if not validateString(string, 1024): return
    return runTextBlockCommand("rmLineEndings", string, "")


# replace all invisible characters with whitespace except line breaks
def repInvisibles(string):
    if not validateString(string, 1024): return
    dict = runTextBlockCommand("repInvisibles", string, "")
    if dict == None: return string
    if dict['result'] == 'false': return string # wasn't replaced any character
    return decodeB64Data(dict["data"])


def printCharactersInfo(string):
    if not validateString(string, 64): return # fixed length
    return runTextBlockCommand("charactersInfo", string, "")
    
 
# convert \uxxxx\uxxx... to readable literals
def viewUnicodeString(string):
    if not validateString(string, 1024): return
    return runTextBlockCommand("viewUnicodeString", string, "")


def replaceSpacestoTabs(string, flag, spaces):
    if not validateString(string, 1024): return
    # direction: 1, spaces to tabs; 0, tabs to spaces
    args = "%d,%d" %(flag, spaces) # with number of spaces
    return runTextBlockCommand("convSpacestoTabs", string, args)


def shiftTextBlock(string, left, spaces):
    if not validateString(string, 1024): return
    # shift direction: 1, left; 0, right
    args = "%d,%d" %(left, spaces) # shift right or left with number of spaces
    return runTextBlockCommand("shiftTextBlock", string, args)


#replace multiple space with a single space, and also strip trailing spaces in each line.
def removeNeedlessWhitespaces(string):
    if not validateString(string, 1024): return
    return runTextBlockCommand("rmNeedlessWhitespaces", string, "")


def capitaliseTextBlock(string):
    if not validateString(string, 64): return
    return runTextBlockCommand("capitalise", string, "")
    

def convertHiragana(string, flag):
    if not validateString(string, 1024): return
    return runTextBlockCommand("convertHiragana", string, flag)


def japaneseAnnotate(string, flag):
    if not validateString(string, 1024): return
    return runTextBlockCommand("japaneseAnnotate", string, flag)


def testFunctions():
    #string = "特定多数のユーザ"
    #result = printCharactersInfo(string)
    #print(result)
    
    #string = "\u7279\u5B9A\u591A\u6570\u306E\u30E6\u30FC\u30B6"
    #result = viewUnicodeString(string)
    #print(result)
    
    string = """
    Write your code and syntax checking and run code and debugging immediately \n
	from within the editor, regardless they're written with JS, TS, Python, PHP, \n
	Ruby, Lua, Perl, AWK, Tcl, Go, Dart, Java, OC, Clojure, Kotlin, Swift, Rust, Erlang, \n
	Elixir, OCaml, Haskell, ..., almost any programming language.\n
	"""
   
   
    result = removeLineEndings(string)
    print(result)
    
    #0: Furigana annotating, "1": Romaji annotating
    #result = japaneseAnnotate(string, "0")
    #print(result)
    
    #0: Hiragana to Katakana, "1": Katakana to Hiragana
    #result = convertHiragana(string, "0")
    #print(result)
    
    #print(capitaliseTextBlock("capitalise text block"))
    
    #result = shiftTextBlock(string, 0, 4)
    #print(result)
    
    
    string = """
        Big software waste time to maintain, waste big storage and runtime memory, \n
        waste energy, waste time to upload and download. \n
        It's waste people's life! \n
        Waste resource of the planet! \n
    """

    #result = replaceSpacestoTabs(string, 1, 4)
    #print(result)
    
    
    #string = "invisible \t\v\f and silent rages\n";
    #result = repInvisibles(string)
    #newString = printCharactersInfo(result)
    #print("#%s#" % newString)
    
    string = """
        we can't together anymore     \n
        can't speak one word  to you anymore  \n
        only countless  sorrow   in heart    \n
        only only silence waving    on the surface of oceans   \n
    """
    
    #result = removeNeedlessWhitespaces(string)
    #print(result)
    


def main():
    testFunctions()


if __name__ == "__main__":
    main()
    
 


