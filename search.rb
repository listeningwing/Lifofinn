#!/usr/bin/env ruby

#    __   _ ___     ____
#   / /  (_) _/__  / _(_)__  ___
#  / /__/ / _/ _ \/ _/ / _ \/ _ \
# /____/_/_/ \___/_//_/_//_/_//_/
# The ultra small code editor.
# * Note:
# a. the scripting interface assume input file and data encoded with utf-8.
# b. all data and file output from app side was encoded with utf-8.
#

require 'open3'
require 'json'


$app = "/Applications/Lifofinn.app/Contents/MacOS/Lifofinn"
$inputSources = nil # catch ctrl+c
$cmdDir = nil       # scripting support directory
$rootUrls = nil     # accessible root directory and files
$accesscode = "***" # access code for automation scripts
                    # current ignored

$noArgCmd = '{ \"msgtype\": \"%s\", \"accesscode\": \"%s\" }'


def exit_handler(message)
    puts message if !message.nil?
    return if $inputSources.nil?
    $inputSources.each { |file|
         moveBackFile(file)
    }
    $inputSources = nil
    exit(0) # Exit the program after cleanup
end

Signal.trap("INT") do
   exit_handler('control + C')
end

at_exit do
  exit_handler('atexit')
end



#pragma mark -
def runCommand(cmd)
    opts = {}
    begin_mark = "_______BEGIN__JSON__MESSAGE_______"
    end_mark   = "_______END____JSON__MESSAGE_______"
 
    # https://ruby-doc.org/stdlib-2.6.1/libdoc/open3/rdoc/Open3.html
    a = [$app, "-c", "\"#{cmd}\""]
    command = a.join(" ")
    Open3.popen3(*command, opts) do |i, o, e, t|
      i.close
      readables = [o, e]
      stdout = []
      stderr = []
      until readables.empty?
        readable, = IO.select(readables)
        if readable.include?(o)
          begin
            stdout << o.read_nonblock(4096)
          rescue EOFError
            readables.delete(o)
          end
        end
        if readable.include?(e)
          begin
            stderr << e.read_nonblock(4096)
          rescue EOFError
            readables.delete(e)
          end
        end
      end

      # a = [stdout.join, stderr.join, t.value]
      lines = stdout.join
      # lines.each_line { |line| puts "#{line}" }
      textBlock = lines.match(/#{begin_mark}(.*)#{end_mark}/m)
      # puts "textBlock: #{textBlock}"
      if textBlock.nil?
        puts lines
        return
      end

      begin
          dict = JSON.parse(textBlock[1])
          return dict
      rescue Exception
          puts textBlock
      end
    end
end


def decodeB64Data(string)
    text = ""
    begin
        Base64.decode64(string).force_encoding('UTF-8')
    rescue Exception
        puts string
    end
    return text
end


def getCommandDir()
    dir = nil
    cmd = $noArgCmd % ["cmddir", $accesscode]
    dict = runCommand(cmd)
    return nil if dict.nil?
    return nil if dict["result"] != "true"
    dir = dict["file"]
    if !File.exist?(dir)
        puts "Error, #{dir} does not exist."
        dir = nil
    end
    return dir
end


def cmdMoveFile(path, reverse)
    # assert_not_nil($cmdDir, "cmdDir should not be nil")
    command = nil
    filename = File.basename(path)
    destpath = File.join($cmdDir, filename)
    if reverse
       command = 'mv "%s" "%s"' % [destpath, path] if File.exist?(destpath)
    else
       command = 'mv "%s" "%s"' % [path, destpath] if File.exist?(path)
    end
    system(command) if !command.nil?
end


def moveFileToAccessible(path)
    cmdMoveFile(path, false)
end


def moveBackFile(path)
    cmdMoveFile(path, true)
end


def fetchRootUrls()
    cmd = $noArgCmd % ["rooturls", $accesscode]
    dict = runCommand(cmd)
    return nil if dict.nil? 
    return nil if dict["result"] != "true"
    dataSet = dict["data"]
    return dataSet
end


def fetchFileResult(dict)
    return nil if dict.nil?
    return nil if dict["result"] != "true"
    file = dict["file"]
    return nil if file.nil? 
    fp = open(file)
    return nil if fp.nil?
    content = fp.read
    fp.close
    dataSet = nil
    begin
      dataSet = JSON.parse(content)
    rescue Exception
    end
    system('rm -f "#{file}"')
    return dataSet
end


# ===
# fetch maximum searching matches
def fetchMatchLimit()
    cmd = $noArgCmd % ["maxmatches", $accesscode]
    dict = runCommand(cmd)
    return 0 if dict.nil? 
    return dict["result"]
end


def fetchRecentList()
    cmd = $noArgCmd % ["recentlist", $accesscode]
    dict = runCommand(cmd)
    return nil if dict.nil? 
    return dict["data"] if dict["result"] == "true"
    return nil
end


#=====================================================================================
# taskType
# 0: searching by content matching
# 1: replacing by content matching
# 2: searching by extension and or name(noContentMatching set to 1)
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
# High performance searching for very big project with powerful filters, please put
# ".lffsearch" filter file in root folders, more info please refer the section
# "Search & Replace" in help document.
# * Note:
# The input file and folders should be accessible
#=====================================================================================
def runSearching()
    boilerplate = '{
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
    }'
    

    maxStr = fetchMatchLimit()
    print("maximum matches: %s\n" % maxStr) # matching limits
    
    max = maxStr.to_i
    taskType = 0
    scopeType = 2
    matchType = 1
    extString = "!cpp,c"
    token = "lookup_tree" # content to match
    repString = ""
    
    dict = nil
    noContentMatching = false # true # false
    if noContentMatching
        taskType = 2
        token = "" # ignore
    end

    nameString = "" # file name to match, can be a regular expression
    currentDir = "/Users/yeung/Public/git-2.49.0"
    $inputSources = []
    $inputSources.push(currentDir)
    moveFileToAccessible(currentDir)
 
    cmd = boilerplate % [$accesscode, taskType, scopeType, matchType, token, repString,
        0, 0, nameString, extString, currentDir, "", "", "", max]
    begin
        dict = runCommand(cmd) # parse the searched result with postsearch.pl
    rescue Exception
    ensure
        moveBackFile(currentDir)
        $inputSources = nil
    end
    return nil if dict == nil
    return nil if dict["result"] != "true"
    temp = dict["file"]
    return nil if !File.exist?(temp)
    logname = File.join(File.expand_path('~/Desktop'), File.basename(temp))
    system("mv \"%s\" \"%s\"" % [temp, logname])
    return logname
end


def initEnv()
    $cmdDir = getCommandDir()
    if $cmdDir.nil?
        puts "Can't get command dir."
        exit(0)
    end
    urls = fetchRootUrls()
    if urls 
        $rootUrls = urls
    else
        puts "Can't fetch list of accessible root directory and files."
    end
end



def runTests()
#     x = fetchMatchLimit()
#     puts "maximum matches: #{x}"
# 
#     list = fetchRecentList()
#     puts list
    return if $cmdDir.nil?
    logfile = runSearching()
    puts "seach result file: #{logfile}"
end


#TODO: please refer lifofinn.py for more functions

initEnv()
runTests()



