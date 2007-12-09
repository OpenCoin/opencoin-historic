# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/OpenCoin.ui'
#
# Created: Fri Dec  7 20:55:38 2007
#      by: PyQt4 UI code generator 4.3.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_openCoin_MainWindow(object):
    def setupUi(self, openCoin_MainWindow):
        openCoin_MainWindow.setObjectName("openCoin_MainWindow")
        openCoin_MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,750,492).size()).expandedTo(openCoin_MainWindow.minimumSizeHint()))

        self.centralwidget = QtGui.QWidget(openCoin_MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.hboxlayout = QtGui.QHBoxLayout(self.centralwidget)
        self.hboxlayout.setObjectName("hboxlayout")

        self.opencoin_listWidget = QtGui.QListWidget(self.centralwidget)
        self.opencoin_listWidget.setObjectName("opencoin_listWidget")
        self.hboxlayout.addWidget(self.opencoin_listWidget)
        openCoin_MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtGui.QMenuBar(openCoin_MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0,0,750,24))
        self.menubar.setObjectName("menubar")

        self.menuWelcome = QtGui.QMenu(self.menubar)
        self.menuWelcome.setObjectName("menuWelcome")

        self.menuAbout = QtGui.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        openCoin_MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtGui.QStatusBar(openCoin_MainWindow)
        self.statusbar.setObjectName("statusbar")
        openCoin_MainWindow.setStatusBar(self.statusbar)

        self.action_New_Coin = QtGui.QAction(openCoin_MainWindow)
        self.action_New_Coin.setObjectName("action_New_Coin")

        self.actionQuit = QtGui.QAction(openCoin_MainWindow)
        self.actionQuit.setObjectName("actionQuit")

        self.actionAbout_Open_Coin = QtGui.QAction(openCoin_MainWindow)
        self.actionAbout_Open_Coin.setObjectName("actionAbout_Open_Coin")

        self.actionAbout_QT = QtGui.QAction(openCoin_MainWindow)
        self.actionAbout_QT.setObjectName("actionAbout_QT")
        self.menuWelcome.addAction(self.action_New_Coin)
        self.menuWelcome.addSeparator()
        self.menuWelcome.addAction(self.actionQuit)
        self.menuAbout.addAction(self.actionAbout_Open_Coin)
        self.menuAbout.addAction(self.actionAbout_QT)
        self.menubar.addAction(self.menuWelcome.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(openCoin_MainWindow)
        QtCore.QMetaObject.connectSlotsByName(openCoin_MainWindow)

    def retranslateUi(self, openCoin_MainWindow):
        openCoin_MainWindow.setWindowTitle(QtGui.QApplication.translate("openCoin_MainWindow", "Open Coin alpha 0.1", None, QtGui.QApplication.UnicodeUTF8))
        self.menuWelcome.setTitle(QtGui.QApplication.translate("openCoin_MainWindow", "Wallet", None, QtGui.QApplication.UnicodeUTF8))
        self.menuAbout.setTitle(QtGui.QApplication.translate("openCoin_MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.action_New_Coin.setText(QtGui.QApplication.translate("openCoin_MainWindow", " New Coin", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("openCoin_MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout_Open_Coin.setText(QtGui.QApplication.translate("openCoin_MainWindow", "About Open Coin", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout_QT.setText(QtGui.QApplication.translate("openCoin_MainWindow", "About QT", None, QtGui.QApplication.UnicodeUTF8))

