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
# The app will open a database connection when run the following commands,
# and close that connection when app exit, FYI, this two operation requires
# more CPU time, they're: "tokenreference", "removereferences", "listbookmarks",
#  "importtokens", "parsedtime", "recentlist", "parsedfilelist".
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



def runFileCommand2(command, path, fileResult, args):
    global accesscode, inputSources
    fileArgCmd = """
    {
      \"msgtype\": \"%s\",
      \"accesscode\": \"%s\",
      \"path\": \"%s\",
      \"filename\": \"%s\",
      \"args\": \"%s\"
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
    cmd = fileArgCmd % (command, accesscode, "", filename, args)
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
    
 
def runFileCommand(command, path, fileResult):
    return runFileCommand2(command, path, fileResult, "")



#pragma mark -
def listBookmarks():
    global accesscode, noArgCmd
    cmd = noArgCmd % ("listbookmarks", accesscode)
    dict = runCommand(cmd)
    dataSet = fetchFileResult(dict)
    return dataSet


def runWithPath(command, path):
    global accesscode
    boilerplate = """
    {
      \"msgtype\": \"%s\",
      \"accesscode\": \"%s\",
      \"fullpath\": \"%s\"
    }
    """
    cmd = boilerplate % (command, accesscode, path)
    dict = runCommand(cmd)
    if dict is None: return False
    if dict["result"] == "true": return True
    return False


# whenever the app exit, it'll clean database for none-existing items in file
# system, but user can call this function to clean those records manually.
# a. input path can be directory or file
# b. no return value
def removerReferences(path):
    runWithPath("removereferences", path)


# If return nothing means that there's no index stored in database for the token
# by the backend parsing threads of the app, please give enough time to let the app
# parse source code files and then call this function.
def tokenReferences(token, withcontent):
    global accesscode
    boilerplate = """
    {
      \"msgtype\": \"tokenreference\",
      \"accesscode\": \"%s\",
      \"withcontent\": \"%s\",
      \"token\": \"%s\"
    }
    """
    cmd = boilerplate % (accesscode, withcontent, token)
    dict = runCommand(cmd)
    if dict is None: return None # no references
    # dataSet = None
    # try:
    #    dataSet = fetchFileResult(cmd)
    # except TypeError as e: pass
    # return dataSet
    if dict["result"] == "true":
        temp = dict["file"]
        if os.path.exists(temp):
            logname = os.path.expanduser('~') + '/Desktop/' + os.path.basename(temp)
            os.system("mv \"%s\" \"%s\"" % (temp, logname))
            return logname
    return None



def fetchParsedFileList(destDir):
    global noArgCmd, accesscode
    temp = None
    cmd = noArgCmd % ("parsedfilelist", accesscode)
    dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        temp = dict["file"]
        if os.path.exists(temp):
            command = "mv \"%s\" \"%s\"" % (temp, destDir)
            os.system(command)
    return temp
    

def fetchFileSymbols(path, destDir):
    boilerplate = """
    {
      \"msgtype\": \"filesymbols\",
      \"accesscode\": \"%s\",
      \"path\": \"%s\"
    }
    """
    temp = None
    cmd = boilerplate % (accesscode, path)
    dict = runCommand(cmd)
    if dict is None: return False
    if dict["result"] == "true":
        temp = dict["file"]
        if os.path.exists(temp):
            command = "mv \"%s\" \"%s\"" % (temp, destDir)
            os.system(command)
    return temp


def fetchRootUrls():
    global noArgCmd, accesscode
    dataSet = None
    cmd = noArgCmd % ("rooturls", accesscode)
    dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        dataSet = dict["data"]
    return dataSet
    

def fetchRecentList():
    global noArgCmd, accesscode
    dataSet = None
    cmd = noArgCmd % ("recentlist", accesscode)
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


def cleanRootItems(path):
    global accesscode, noArgCmd
    cmd = noArgCmd % ("cleanrootitems", accesscode)
    dict = runCommand(cmd)
    if dict is None: return False
    return True if dict["result"] == "true" else False


def removeRootItem(path):
    return runWithPath("rmrootitem", path)
    

def addRootItem(path):
    return runWithPath("addrootitem", path)


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


def fileConverter(path, command, destDir, ext):
    dict = runFileCommand(command, path, False)
    if dict is None: return False
    if dict["result"] == "true":
        temp = dict["file"]
        if not os.path.exists(temp): return False
        filename = os.path.basename(path)
        noextname = os.path.splitext(filename)[0]
        command = "mv \"%s\" \"%s/%s.%s\"" % (temp, destDir, noextname, ext)
        os.system(command)
        return True
    return False


# detect the file or folder ignored by filter or not
# a. the filter file ".lffignore" should put under one of the root folders.
# b. the input file or folder should be child of that root folder.
def isIgnoreFile(path):
    if not isAccessible(path):
        return False
    return runWithPath("isIgnoreFile", path)


# *** Caution!!! ***
# convert file encoding may cause unrestorable changes, please make a backup first.
# covert all files in a directory to utf-8 text encoding with '\n' line endings.
# automatically detect file is binary or not, convert to utf-8 text encoding from any text encoding.
def normaliseDir(path):
    runFileCommand("normalisedir", path, False)


def markdown2html(path, destDir):
    return fileConverter(path, "markdown", destDir, "html")


def prettyJSONFile(path):
    text = ""
    dict = runFileCommand("prettyjson", path, False)
    if dict is None: return ""
    if dict["result"] == "true":
        text = readFileContent(dict["file"])
        removeFile(dict["file"])
    return text


def binaryToBase64(path, destDir):
    ext = "txt"
    return fileConverter(path, "bin2base64", destDir, ext)


def base64ToBinary(path, destDir, ext):
    return fileConverter(path, "base64tobin", destDir, ext)


def parseFile(path):
    dataSet = runFileCommand("parsefile", path, True)
    return dataSet


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
    

# Call this function to check importing result or improve performance, whenever
# call importParsedSymbols(), the editor will update the "last parsed time", and
# already ignored the tokens importing if, "last parsed time" > modified time,
# so call this function to do a checking before importing is not necessary.
def getParsedtime(path):
    dict = runFileCommand("parsedtime", path, False)
    if dict is None: return None
    if dict["result"] == "0": return None # failed to fetch "last parsed time"
    return dict["result"]


# Import pre-parsed tokens into the "token indexing database", please refer the
# section "Support New Programming Language or Document" in help document.
# a. The input file is a plain text file with "ctags" extension name and must be
#    encoded with utf-8.
# b. The editor will parse the file line by line, line starts with "#" is comment.
#    Line format: token\tfullpath\tkind:xxx\tline:210 or
#                 token\tfullpath\tscope:xxx\tline:210
#           * one ".ctags" file ONLY be responsible for one source code file.
#           * token can contains '.' and ':' scope separator.
#           * scope => scope:class|implements|interface|package|module|...
#           * valid line must contains fullpath, line number and (kind|scope).
#           * token first and then fullpath, others are NOT order required.
# c. If call this function with a directory, the editor will loop all subfolder
#    and files, inspect and parsing all files that has a "ctags" extension name.

# * Note:
# Before import a file or directory, please ensure workspace is not empty first. For
# a fresh importing, please empty workspace and then open a sample text file in it.
def importParsedSymbols(path):
    runFileCommand("importtokens", path, False)


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
    

def base64Test():
    destDir = "/Users/yeung/Desktop"
    path = "/Users/yeung/Desktop/node.png"
    binaryToBase64(path, destDir)
    command = "mv \"%s\" \"%s/%s\"" % (path, destDir, "node_backup.png")
    os.system(command)
    path = "/Users/yeung/Desktop/node.txt"
    base64ToBinary(path, destDir, "png")


def removeBigFile():
    path = "/Users/yeung/Desktop/bigdata.json"
    removeRootItem(path)



# fetch maximum searching matches
def fetchMatchLimit():
    global noArgCmd, accesscode
    cmd = noArgCmd % ("maxmatches", accesscode)
    dict = runCommand(cmd)
    if dict is None: return 0
    return dict["result"]


#=====================================================================================
# taskType
# 0: searching by content matching
# 1: replacing by content matching
# 2: searching by extension and or name (without file content matching)
#
# scopeType
# 0: current selection, unused
# 1: current file
# 2: current folder
# 3: in active files
# 4: in root paths
#
# matchType (invalid when do RE)
# 0. Containing
# 1. Matching Word
# 2. Starting With
# 3. Ending With
#
# isRE: 0 or 1, Perl regular expression or not.
# String: normal string for searching or a RE.
# repString: replacement for replace operation.
# nameString: comma separated file names, can be a RE, excluded file has a prefix '!', case sensitive.
# extString: comma separated file extensions, excluded file types has a prefix '!', NOT case sensitive.
# rootPaths and activePaths: path array with JSON format.
# 
# High performance searching for very big project with powerful filters, please put ".lffsearch" filter
# file in root folders, more info please refer the section "Search & Replace" in help document.
# * Note:
# The input file and folders should be accessible
#=====================================================================================
def runSearching():
    global accesscode, inputSources

    boilerplate = """
    {
      \"msgtype\": \"searching\",
      \"accesscode\": \"%s\",
      \"taskType\": \"%d\",
      \"scopeType\": \"%d\",
      \"matchType\": \"%d\",
      \"String\": \"%s\",
      \"repString\": \"%s\",
      \"ignoreCase\": \"%d\",
      \"isRE\": \"%d\",
      \"nameString\": \"%s\",
      \"extString\": \"%s\",
      \"currentDir\": \"%s\",
      \"currentFile\": \"%s\",
      \"rootPaths\": \"%s\",
      \"activePaths\": \"%s\",
      \"maxMatches\": \"%d\"
    }
    """

    maxStr = fetchMatchLimit()
    print("maximum matches: %s" % maxStr) # matching limits
    
    max = int(maxStr)
    taskType = 0
    scopeType = 2
    matchType = 1
    extString = "" # "!cpp,c"
    token = "treeCallback" # content to match
    repString = ""
        
    dict = None
    noContentMatching = False # True # False
    if noContentMatching:
        taskType = 2
        token = "" # ignore

    nameString = "" # "btree.c" # file names to match, can be a regular expression
    currentDir = "/Users/yeung/Desktop/bamboo"
    inputSources = []
    inputSources.append(currentDir)
    moveFileToAccessible(currentDir)
 
    cmd = boilerplate % (accesscode, taskType, scopeType, matchType, token, repString,
        0, 0, nameString, extString, currentDir, "", "", "", max)
    try:
        dict = runCommand(cmd) # parse the searched result with postsearch.pl
    except KeyboardInterrupt: pass
    except: pass
    finally:
        moveBackFile(currentDir)
        inputSources = None
    if dict is None: return None
    if dict["result"] == "true":
        temp = dict["file"]
        if os.path.exists(temp):
            logname = os.path.expanduser('~') + '/Desktop/' + os.path.basename(temp)
            os.system("mv \"%s\" \"%s\"" % (temp, logname))
            return logname
    return None


def runTests():
    global cmdDir, rootUrls
#    initEnv()
#    if not cmdDir or not rootUrls:
#       return


    urls = fetchAccessibleList()
    print('-------accessible list-------\n')
    for url in urls:
        print(url)
    print('-----------------------------\n')

    records = fetchRecentList()
    for record in records:
        print(record)

    token = 'initialize'     # token name
    withcontent = "true"      # true or false, with or without line text
    logFile = tokenReferences(token, withcontent)
    print("logFile: %s" % logFile)
    dict = None
    fp = open(logFile, 'r')
    if fp:
        dict = json.load(fp)
        fp.close()
    if dict:
        records = dict['data']
        for record in records:
            print(record['file'])
            print(record['line'])
            content = decodeB64Data(record['content'])
            print(content)
            print('-------\n\n')


#    dict = listBookmarks()
#    # print(dict)
#    if dict:
#        records = dict['data']
#        for record in records:
#            print(record['file'])
#            bookmarks = record['bookmarks']
#            for mark in bookmarks:
#                print(mark['line'])
#                content = decodeB64Data(mark['content'])
#                print(content)
#            print('-------\n\n')

#   fetchParsedFileList("/Users/yeung/Desktop")
#   file = "/Users/yeung/Product/Lifofinn/Lifofinn.py"
#   fetchFileSymbols(file, "/Users/yeung/Desktop")

#    dict = parseFile(file)
#    # print(dict)
#    if dict:
#        records = dict['data']
#        for record in records:
#            for key, value in record.items():
#                print('kind:"%s"' % key)
#                for row in value:
#                    print(row)
#            print('-------\n\n')

#     destDir = "/Users/yeung/Desktop"
#     path = "/Users/yeung/Desktop/llvm-project/README.md"
#     markdown2html(path, destDir)
#
#     path = "/Users/yeung/Desktop/jsoneditor.json"
#     output = prettyJSONFile(path)
#     print(output)


# generate "File List" with filter file ".lffignore",
# please put the filter file under the directory.
def genFileList(path, meta):
    #meta: "1", with file meta info; "0", without file meta info.
    dataSet = runFileCommand2("genFileList", path, True, meta)
    if not dataSet: return None
    return dataSet['data']


# directly import references of parsed symbols in database
def testImport():
    path = "/Users/yeung/Desktop/Import/archive.ctags"
    importParsedSymbols(path)


def main():
    global cmdDir, rootUrls
    initEnv()
    if not cmdDir or not rootUrls:
        return
    atexit.register(exit_handler, "atexit called.")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)
    
    # base64Test()
    # removeBigFile()
    # runTests()
    # testImport()
    
    # meta = "0" # with file attributes or not
    # dir = '/Users/yeung/Desktop/uMachine-2.14.0'
    # list = genFileList(dir, meta)
    #if list:
    #    for item in list:
    #        print(item)
    
    logFile = runSearching()
    print(logFile)
    


if __name__ == "__main__":
    main()



