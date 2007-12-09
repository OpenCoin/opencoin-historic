"""
window.py

Open Coin prototype GUI 

Copyright (C) 2007 Andrew Nicholson <andy@infiniterecursion.com.au>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""


import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from opencoin_ui import Ui_openCoin_MainWindow

from constants import __version__

class Window(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.ui = Ui_openCoin_MainWindow()
        self.ui.setupUi(self)

        # Set up signal-slot connections defined in the .ui files and
        # those providing higher-level functionality.
        QMetaObject.connectSlotsByName(self)

	#connect signals and methods
   	self.connect(self.ui.actionAbout_Open_Coin, SIGNAL("triggered()"), self.about)
        self.connect(self.ui.actionAbout_QT, SIGNAL("triggered()"), self.aboutQt)
        self.connect(self.ui.actionQuit, SIGNAL("triggered()"), self.deleteWindow)

	#custom tests
	a = QListWidgetItem()
	a.setText('a')
	self.ui.opencoin_listWidget.addItem(a)

    def about(self):

        QMessageBox.about(self,
            self.tr("About Open Coin %1").arg(__version__),
            self.tr("<qt><h3>About Open Coin %1</h3>"
                    "<p> Open Coin is blah blah blah "
                    "</p></qt>").arg(__version__)
                    )

    def aboutQt(self):

        QMessageBox.aboutQt(self)

    def deleteWindow(self):

        self.destroy()


