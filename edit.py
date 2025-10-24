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
import atexit
import signal



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


def readFileContent(path):
    content = ""
    if path is None: return ""
    f = codecs.open(path, "r")
    if f:
        content = f.read()
        f.close()
    return content


def fetchFileResult(dict):
    dataSet = None;
    # dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        file = dict["file"]
        if file is None: return None
        fp = open(file, 'r')
        if fp:
            dataSet = json.load(fp)
            fp.close()
        os.system('rm -f "%s"' % file)
    return dataSet


def cmdMoveFile(path, reverse):
    global cmdDir
    assert(cmdDir is not None)
    command = None
    filename = os.path.basename(path)
    destpath = "%s/%s" % (cmdDir, filename)
    if reverse:
        if os.path.exists(destpath):
            command = 'mv "%s" "%s"' % (destpath, path)
    else:
        if os.path.exists(path):
            command = 'mv "%s" "%s"' % (path, destpath)
    if command is not None: os.system(command)

def moveFileToAccessible(path):
    cmdMoveFile(path, False)

def moveBackFile(path):
    cmdMoveFile(path, True)

def removeFile(path):
    command = 'rm -rf "%s"' % path
    os.system(command)


#pragma mark -
def isAccessible(path):
    global rootUrls
    assert(rootUrls is not None)
    for url in rootUrls:
        if path.startswith(url):
            return True
    return False


def exit_handler(message):
    global inputSources
    if inputSources is not None:
        for file in inputSources:
            moveBackFile(file)
    inputSources = None
    sys.exit(0) # Exit the program after cleanup


def signal_handler(sig, frame):
    exit_handler("exit")


def runFileCommand(command, path, fileResult):
    global accesscode, inputSources
    fileArgCmd = """
    {
      \"msgtype\": \"%s\",
      \"accesscode\": \"%s\",
      \"path\": \"%s\",
      \"filename\": \"%s\"
    }
    """

    if not os.path.exists(path):
        print("Error, '%s' does not exist." % path)
        return None

    # cmd = None
    # ac = isAccessible(path)
    # if not ac:
    filename = os.path.basename(path)
    moveFileToAccessible(path)
    inputSources = []
    inputSources.append(path)
    cmd = fileArgCmd % (command, accesscode, "", filename)
    # else:
    #   cmd = fileArgCmd % (command, accesscode, path, "")
    try:
        dict = runCommand(cmd)
    except KeyboardInterrupt: pass
    except: pass
    finally:
        moveBackFile(path)
        inputSources = None
    if not fileResult: return dict
    dataSet = fetchFileResult(dict)
    return dataSet


def fetchRootUrls():
    global noArgCmd, accesscode
    dataSet = None
    cmd = noArgCmd % ("rooturls", accesscode)
    dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        dataSet = dict["data"]
    return dataSet


# Note: accessible list + root urls = all accessible paths
def fetchAccessibleList():
    global noArgCmd, accesscode
    dataSet = None
    cmd = noArgCmd % ("accessiblelist", accesscode)
    dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        dataSet = dict["data"]
    return dataSet


def removeRootItem(path):
    return runWithPath("rmrootitem", path)


def getCommandDir():
    global noArgCmd, accesscode
    dir = None
    cmd = noArgCmd % ("cmddir", accesscode)
    dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        dir = dict["file"]
        if not os.path.exists(dir):
            print("Error, '%s' does not exist." % dir)
            dir = None
    return dir


def fetchFileLines(path, f, t):
    global accesscode, inputSources
    content = None

    boilerplate = """
    {
      \"msgtype\": \"filelines\",
      \"accesscode\": \"%s\",
      \"path\": \"%s\",
      \"filename\": \"%s\",
      \"from\": \"%d\",
      \"to\": \"%d\"
    }
    """

    if not os.path.exists(path):
        print("Error, '%s' does not exist." % path)
        return None

    if (f < 1) or (f > 1000000):
        print("invalid from: %d" % f)
        return None

    if ( (t < 1) or (t > 1000000) ) or (t < f):
        print("invalid to: %d" % t)
        return None

    if (t - f) > 500:
        print("invalid line range (%d %d)" % (f, t))
        return None

    # cmd = None
    # ac = isAccessible(path)
    # if not ac:
    filename = os.path.basename(path)
    cmd = boilerplate % (accesscode, "", filename, f, t)
    moveFileToAccessible(path)
    inputSources = []
    inputSources.append(path)
    #else:
    #   cmd = boilerplate % (accesscode, path, "", f, t)

    try:
        dict = runCommand(cmd)
    except KeyboardInterrupt: pass
    except: pass
    finally:
        # if not ac:
        moveBackFile(path)
        inputSources = None
    if dict is None: return None
    if dict["result"] == "true":
        data = dict["data"]
        if data: content = decodeB64Data(data)
    return content


# replace all invisible characters with whitespace except line breaks
def repInvisibles(path, destDir):
    ext = os.path.splitext(path)[1]
    return fileConverter(path, "repInvisibles", destDir, ext)


# detect the file or folder ignored by filter or not
# a. the filter file ".lffignore" should put under one of the root folders.
# b. the input file or folder should be child of that root folder.
def isIgnoreFile(path):
    if not isAccessible(path):
        return False
    return runWithPath("isIgnoreFile", path)


def isPlainTextFile(path):
    dict = runFileCommand("isplaintext", path, False)
    if dict is None: return False
    if dict["result"] == "true": return True
    return False
    
def isExecutableFile(path):
    dict = runFileCommand("isexecutable", path, False)
    if dict is None: return False
    if dict["result"] == "true": return True
    return False


def isAccessiblePath(path):
    dict = runFileCommand("accessible", path, False)
    if dict is None: return False
    if dict["result"] == "true": return True
    return False


def initEnv():
    global cmdDir, rootUrls
    cmdDir = getCommandDir()
    if not cmdDir:
        print("Can't get command dir.")
        return
    # print("The scripting support directory is:\n%s" % cmdDir)
    urls = fetchRootUrls()
    if urls: rootUrls = urls
    else:
        print("Can't fetch list of accessible root directory and files.")
    # print("=======rootUrls=========")
    # print(rootUrls)
    # print("========================")

    

def base64OfString(text):
    base64_bytes = base64.b64encode(text.encode('utf-8'))
    return base64_bytes.decode("ascii")


#=====================================================================================
#operation
#1. insert substr
#2. replace with range
#3. delete with range
#4. find substr in the line and replace with replacement
#   (delete substr if replacement is empty)
#5. replace number of lines with replacement
#   (delete number of lines if replacement is empty)
#anchor: "line:offset", i.e. range, line with offset
#count: length of range(offset, count) in anchor or 
#       number of lines for operation 5
#substr: find the string and replace or delete
#repString: replacement for substr, "" for delete
#isRE: 0 or 1, substr is regular expression or not
#ignoreCase: find substr case sensitive or not
#=====================================================================================
def editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase):
    global accesscode, inputSources

    boilerplate = """
    {
      \"msgtype\": \"editfile\",
      \"accesscode\": \"%s\",
      \"filename\": \"%s\",
      \"operation\": \"%d\",
      \"anchor\": \"%s\",
      \"count\": \"%d\",
      \"substr\": \"%s\",
      \"repString\": \"%s\",
      \"isRE\": \"%d\",
      \"ignoreCase\": \"%d\"
    }
    """

    filename = os.path.basename(path)
    cmd = boilerplate % (accesscode, filename, operation, anchor, count, \
          base64OfString(substr), base64OfString(repString), isRE, ignoreCase)
    moveFileToAccessible(path)
    inputSources = []
    inputSources.append(path)
    #
    try:
        dict = runCommand(cmd)
    except KeyboardInterrupt: pass
    except: pass
    finally:
        moveBackFile(path)
        inputSources = None
    if dict is None: return None
    if dict["result"] == "true":
        temp = dict["file"]
        if os.path.exists(temp):
            logname = os.path.expanduser('~') + '/Desktop/' + os.path.basename(temp)
            os.system("mv \"%s\" \"%s\"" % (temp, logname))
            return logname
    return None




def testEditFile():
    anchor = "2:5" # the second line and offset 5 characters
    count = 2
    substr = "new word"
    repString = ""
    isRE = 0
    ignoreCase = 1

#     path = "/Users/yeung/Desktop/qk0i8tCd.txt"
#     operation = 1 #insert at
#     count = len(substr)
#     logFile = editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase)
#     print(logFile)
    
#     operation = 3 #delete with range
#     count = len(substr)
#     logFile = editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase)
#     print(logFile)

   
#     path = "/Users/yeung/Desktop/qk0lA1rmd.txt"
#     operation = 2 #replace with range
#     count = len(substr)
#     repString = "@@@@@"
#     logFile = editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase)
#     print(logFile)

#     path = "/Users/yeung/Desktop/qk0lA1rmd.txt"
#     anchor = "5:0"
#     operation = 4 #replace with repString
#     substr = "2019"
#     repString = "2025"
#     logFile = editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase)
#     print(logFile)
    
    
#     path = "/Users/yeung/Desktop/qk0lA1rmd.txt"
#     anchor = "3:0"
#     count = 1
#     operation = 5 #delete line
#     repString = ""
#     logFile = editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase)
#     print(logFile)
    
    path = "/Users/yeung/Desktop/qk0lA1rmd.txt"
    anchor = "3:0"
    count = 1
    operation = 5 #replace lines
    repString = "new line\nnewline\n"
    logFile = editFile(path, operation, anchor, count, substr, repString, isRE, ignoreCase)
    print(logFile)



def main():
    global cmdDir, rootUrls
    initEnv()
    if not cmdDir or not rootUrls:
        return
    atexit.register(exit_handler, "atexit called.")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)
    
#    fromLine = 22
#    toLine = 22
#    file = '/full/path/of/file.c'
#    block = fetchFileLines(file, fromLine, toLine)
#    print(block)

#    more functions, please refer Lifofinn.py 
    testEditFile()
    


if __name__ == "__main__":
    main()



