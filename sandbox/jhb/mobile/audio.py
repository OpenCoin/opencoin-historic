#http://svn.kryogenix.org/filedetails.php?repname=kryogenix.org&path=%2Fs60-compat-2%2Ftrunk%2Faudio.py&rev=183&sc=0
import os, threading, select, Queue
from subprocess import *

# check for mpg321 on the path
if not os.path.exists("/usr/bin/mpg321"):
  raise "mpg321 not found; audio module not available"

# Constants

ENotReady = 0
EOpen = 1
EPlaying = 2
ERecording = 3
KMdaRepeatForever = -1
TTS_PREFIX = "(tts)"

def say(text, prefix=TTS_PREFIX):
  raise NotImplementedError

class BackgroundPlayer:
  def play(self, filename, commandsToMe, commandsFromMe):
    return
    self.filename = filename
    self.commandsToMe = commandsToMe
    self.commandsFromMe = commandsFromMe
    self.buffer = ""
    cmd = (["/usr/bin/mpg321", "-R", "dummyarg"])
    self.process = Popen(cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    running = 1
    self.currentFrame = self.framesRemaining = self.currentTime = 0
    self.timeRemaining = 0
    self.process.stdin.write("LOAD %s\n" % filename)
    self.process.stdin.flush()
    while running:
      waiting, x, y = select.select([self.process.stdout],[],[])
      processing_commands = True
      while processing_commands:
        try:
          item = self.commandsToMe.get(block=False)
          self.process.stdin.write(item + "\n")
          self.commandsToMe.task_done()
        except Queue.Empty:
          processing_commands = False
      if waiting: 
        data = waiting[0].read(64)
        if data:
          self.thread_process_stdout(data)
  
  def thread_process_stdout(self,data):
    data = self.buffer + data
    self.buffer = ""
    for line in data.split('\n'):
      if line.startswith("@F"):
        parts = line.split()
        if len(parts) != 5:
          self.buffer = line
        else:
          (f, self.currentFrame, self.framesRemaining, self.currentTime, 
            self.timeRemaining) = parts
          self.sendCommand("updateTime",
            (self.currentFrame, self.framesRemaining,
            self.currentTime, self.timeRemaining))
  
  def sendCommand(self, command, arg):
    # clear the commandsFromMe queue
    itemsleft = True
    while itemsleft:
      try:
        self.commandsFromMe.get(block=False)
      except Queue.Empty:
        itemsleft = False
    self.commandsFromMe.put((command,arg))

class SoundObject:
  def __init__(self, filename):
    self.filename = filename
    self.state = EOpen
    self.position = 0
    self.durationInMicroseconds = 0
    
  def play(self, times=1,interval=0,callback=None):
    self.callback = callback
    if self.callback: self.callback(EOpen, EPlaying, 0)
    self.state = EOpen
    self.commandsToPlayer = Queue.Queue()
    self.commandsFromPlayer = Queue.Queue()
    self.backgroundPlayer = BackgroundPlayer()
    self.thread_player = threading.Thread(
      target = self.backgroundPlayer.play, 
      args = [self.filename, self.commandsToPlayer, self.commandsFromPlayer]
    )
    self.thread_player.setDaemon(True)
    self.thread_player.start()
    
  def state(self): return self.state

  def stop(self):
    self.commandsToPlayer.put("QUIT")
  def record(*args):
    raise NotImplementedError
  def max_volume(*args):
    raise NotImplementedError
  def set_volume(*args):
    raise NotImplementedError
  def current_volume(*args):
    raise NotImplementedError
  def duration(self):
    self.process_outstanding()
    return self.durationInMicroseconds
    raise NotImplementedError
  def set_position(self, ms):
    frameposition = int(ms / self.frameLength)
    self.commandsToPlayer.put("JUMP %s" % frameposition)
  def current_position(self):
    self.process_outstanding()
    return self.position

  def process_outstanding(self):
    processing_queue = True
    while processing_queue:
      try:
        command, arg = self.commandsFromPlayer.get(block=False)
        cmd = getattr(self, command)
        cmd(arg)
        self.commandsFromPlayer.task_done()
      except Queue.Empty:
        processing_queue = False
      
  def updateTime(self, tup):
    framePosition, framesRemaining, posSeconds, remainingSeconds = tup
    self.position = float(posSeconds) * 1000000
    self.durationInMicroseconds = (float(posSeconds) + float(remainingSeconds)) * 1000000
    self.frameLength = self.durationInMicroseconds / (float(framePosition) + float(framesRemaining))

class SoundWrapper(object):

    def open(self,filename):
        s = SoundObject(filename)
        return s

Sound = SoundWrapper()        


if __name__ == "__main__":
  import time
  filename = "superstition.mp3"
  s = Sound(filename)
  print "Main thread: playing"
  s.play()
  print "Main thread: sleeping 2 seconds"
  time.sleep(2)
  print "Main thread: position is",s.current_position()
  print "Main thread: duration is",s.duration()
  print "Main thread: seek to 10 seconds in"
  s.set_position(10 * 1000000)
  print "Main thread: sleeping 2 seconds"
  time.sleep(2)
  print "Main thread: position is",s.current_position()
  print "Main thread: sleeping 2 seconds"
  time.sleep(2)
  print "Main thread: stop sound"
  s.stop()
  print "Main thread: sleeping 2 seconds"
  time.sleep(2)
  print "Main thread: exit"

