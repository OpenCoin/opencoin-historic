#
# TopWindow
#
# Copyright 2008 
#
# Authors: Sergiy Krukovskyy <temer69@ukr.net>
#

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 

"""
wxPython emulation of TopWindow module from Python for S60
""" 

import sysinfo, appuifw, graphics
import wx

class TopWindow(object):
   def __init__(self):
      self._position = (0,0)            # RW, position = (100,100)
      self._size = self.maximum_size    # RW, size = (100,100)
      self._images = []                 # RW, images = [(image1,(x1,y1)), (image2,(x1,y1,x2,y2)), (image3,(50,50,100,100))]
      self._shadow = 0                  # RW, NOT SUPPORTED, shadow = 5
      self._corner_type = 0             # RW, NOT SUPPORTED, square, corner1 - corner5
      self._background_color = 0xFFFFFF # RW, int, background_color = 0xFFFFFF
      self._visible = 0                 # RW, 0 or 1
      self._fading = 0                  # ?? absent in pdf spec from Nokia but present in TopWindow object
      
      self._frame = wx.Frame(appuifw.app.frame, -1, "TopMost", appuifw.app.frame.ClientToScreen(self.position), self.size, \
         style = wx.FRAME_FLOAT_ON_PARENT|wx.FRAME_NO_TASKBAR)
      self._frame.Bind(wx.EVT_PAINT, self.OnPaint)
      # TODO: process main window OnMove event: move the topmost window too

   # --------------------------------------------------------------------------
   def position():
      doc = "Specifies the coordinates of the top left corner of the window. Can be read and written."
      def fget(self):
         return self._position
      def fset(self, value):
         self._position = value
         self._frame.SetPosition(appuifw.app.frame.ClientToScreen(self._position))
      return locals()
   position = property(**position())
   # --------------------------------------------------------------------------
   def maximum_size():
      doc = "Returns the maximum size of the window as a tuple (width, height). Read only property."
      def fget(self):
         return sysinfo.display_pixels()
      return locals()
   maximum_size = property(**maximum_size())
   # --------------------------------------------------------------------------
   def size():
      doc = "Specifies the size of the window. Can be read and written."
      def fget(self):
         return self._size
      def fset(self, x):
         self._size = x
         self._frame.SetSize(self._size)
      return locals()
   size = property(**size())
   # --------------------------------------------------------------------------
   def get_images(self):
      return self._images

   def set_images(self, x):
      self._images = x
      self._frame.Refresh()
      self._frame.Update()

   images = property(get_images, set_images)
   # --------------------------------------------------------------------------
   # WARNING: NOT SUPPORTED
   def get_shadow(self):
      return self._shadow

   def set_shadow(self, x):
      self._shadow = x

   shadow = property(get_shadow, set_shadow)
   # --------------------------------------------------------------------------
   # WARNING: NOT SUPPORTED
   def get_corner_type(self):
      return self._corner_type

   def set_corner_type(self, x):
      self._corner_type = x

   corner_type = property(get_corner_type, set_corner_type)
   # --------------------------------------------------------------------------
   def get_background_color(self):
      return self._background_color

   def set_background_color(self, x):
      self._background_color = x
      self._frame.Refresh()
      self._frame.Update()

   background_color = property(get_background_color, set_background_color)
   # --------------------------------------------------------------------------
   def get_visible(self):
      return self._visible

   def set_visible(self, x):
      self._visible = x
      self._frame.Show(self._visible)

   visible = property(get_visible, set_visible)
   # --------------------------------------------------------------------------
   def get_fading(self):
      return self._fading

   def set_fading(self, x):
      self._fading = x

   fading = property(get_fading, set_fading)
   # --------------------------------------------------------------------------
   def hide(self):
      self.visible = False
   # --------------------------------------------------------------------------
   def show(self):
      self.visible = True
   # --------------------------------------------------------------------------
   def add_image(self, image, position):
      self.images.append((image,position[0],position[1]))
      self._frame.Refresh()
      self._frame.Update()
   # --------------------------------------------------------------------------
   def remove_image(self, image, position=None):
      for i in self._images:
         if i[0] == image:
            self.images.remove(i)
      self._frame.Refresh()
      self._frame.Update()
   # --------------------------------------------------------------------------
   def OnPaint(self, evt):
      dc = wx.PaintDC(self._frame)
      dc.SetBackground(wx.Brush(wx.ColourRGB(self._background_color), wx.SOLID)) 
      dc.Clear()
      for i in self.images:
        i_size = i[0].dc.GetSizeTuple()
        dc.Blit(i[1], i[2], i_size[0], i_size[1], i[0].dc, 0, 0, wx.COPY, True) 

if __name__=="__main__":
    # a simple test
    app = wx.PySimpleApp()
    
    tw = TopWindow()
    print "Maximum_size: ",tw.maximum_size
    tw.position = (tw.maximum_size[0]/4, tw.maximum_size[1]/4)
    tw.size = (tw.maximum_size[0]/2, tw.maximum_size[1]/2)
    print "setting position", tw.position, "and size", tw.size
    tw.show()
   
    app.MainLoop()
   