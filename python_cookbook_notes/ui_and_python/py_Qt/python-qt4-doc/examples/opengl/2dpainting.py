#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of py_Qt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


import sys
import math

from PyQt4 import QtCore, QtGui, QtOpenGL

try:
    from OpenGL import GL
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "OpenGL 2dpainting",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from sip import setdestroyonexit
setdestroyonexit(False)


class Helper(object):
    def __init__(self):
        gradient = QtGui.QLinearGradient(QtCore.QPointF(50, -20),
                QtCore.QPointF(80, 20))
        gradient.setColorAt(0.0, QtCore.Qt.white)
        gradient.setColorAt(1.0, QtGui.QColor(0xa6, 0xce, 0x39))

        self.background = QtGui.QBrush(QtGui.QColor(64, 32, 64))
        self.circleBrush = QtGui.QBrush(gradient)
        self.circlePen = QtGui.QPen(QtCore.Qt.black)
        self.circlePen.setWidth(1)
        self.textPen = QtGui.QPen(QtCore.Qt.white)
        self.textFont = QtGui.QFont()
        self.textFont.setPixelSize(50)

    def paint(self, painter, event, elapsed):
        painter.fillRect(event.rect(), self.background)
        painter.translate(100, 100)

        painter.save()
        painter.setBrush(self.circleBrush)
        painter.setPen(self.circlePen)
        painter.rotate(elapsed * 0.030)

        r = elapsed/1000.0
        n = 30
        for i in range(n):
            painter.rotate(30)
            radius = 0 + 120.0*((i+r)/n)
            circleRadius = 1 + ((i+r)/n)*20
            painter.drawEllipse(QtCore.QRectF(radius, -circleRadius,
                    circleRadius*2, circleRadius*2))

        painter.restore()

        painter.setPen(self.textPen)
        painter.setFont(self.textFont)
        painter.drawText(QtCore.QRect(-50, -50, 100, 100),
                QtCore.Qt.AlignCenter, "Qt")


class Widget(QtGui.QWidget):
    def __init__(self, helper, parent):
        super(Widget, self).__init__(parent)

        self.helper = helper
        self.elapsed = 0
        self.setFixedSize(200, 200)

    def animate(self):
        self.elapsed = (self.elapsed + self.sender().interval()) % 1000
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.helper.paint(painter, event, self.elapsed)
        painter.end()


class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, helper, parent):
        super(GLWidget, self).__init__(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)

        self.helper = helper
        self.elapsed = 0
        self.setFixedSize(200, 200)
        self.setAutoFillBackground(False)

    def animate(self):
        self.elapsed = (self.elapsed + self.sender().interval()) % 1000
        self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.helper.paint(painter, event, self.elapsed)
        painter.end()


class Window(QtGui.QWidget):
    def __init__(self):
        super(Window, self).__init__()

        helper = Helper()
        native = Widget(helper, self)
        openGL = GLWidget(helper, self)
        nativeLabel = QtGui.QLabel("Native")
        nativeLabel.setAlignment(QtCore.Qt.AlignHCenter)
        openGLLabel = QtGui.QLabel("OpenGL")
        openGLLabel.setAlignment(QtCore.Qt.AlignHCenter)

        layout = QtGui.QGridLayout()
        layout.addWidget(native, 0, 0)
        layout.addWidget(openGL, 0, 1)
        layout.addWidget(nativeLabel, 1, 0)
        layout.addWidget(openGLLabel, 1, 1)
        self.setLayout(layout)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(native.animate)
        timer.timeout.connect(openGL.animate)
        timer.start(50)

        self.setWindowTitle("2D Painting on Native and OpenGL Widgets")


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
