from PyQt5.QtCore import pyqtProperty, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPen, QPalette, QLinearGradient
from PyQt5.QtWidgets import QAbstractSlider, QHBoxLayout, QSlider, QSpinBox, QStyleFactory, QStyleOptionSlider, QStylePainter, QStyle, QWidget
from PyQt5 import QtCore


def clamp(v, lower, upper):
    return min(upper, max(lower, v))


class QxtSpanSliderWidget(QWidget):
    def __init__(self, low, upp, parent=None):
        QWidget.__init__(self, parent)
        self.layout = QHBoxLayout(self)
        self._spin_start = QSpinBox(self)
        self._spin_end = QSpinBox(self)
        self.layout.addWidget(self._spin_start)

        self._slider = QxtSpanSlider(self)
        self._slider.setHandleMovementMode(QxtSpanSlider.NoOverlapping)

        self._slider.lowerPositionChanged.connect(lambda x: self._spin_start.setValue(x))
        self._slider.upperPositionChanged.connect(lambda x: self._spin_end.setValue(x))
        self._spin_start.valueChanged.connect(
            lambda x: self._slider.setLowerPosition(x)
            if x < self._slider.upperValue
            else self._spin_start.setValue(self._slider.upperValue - 1))
        self._spin_end.valueChanged.connect(
            lambda x: self._slider.setUpperPosition(x)
            if x > self._slider.lowerValue
            else self._spin_end.setValue(self._slider.lowerValue + 1))

        self.layout.addWidget(self._slider)
        self.layout.addWidget(self._spin_end)

        self.setRange(low, upp)
        self.setSpan(low, upp)

    @property
    def lowerValue(self):
        return self._slider.lowerValue

    @property
    def upperValue(self):
        return self._slider.upperValue

    def setRange(self, low, upp):
        self._slider.setRange(low, upp)
        self._spin_start.setRange(low, upp)
        self._spin_end.setRange(low, upp)

    def setSpan(self, low, upp):
        self._spin_start.setValue(low)
        self._spin_end.setValue(upp)
        self._slider.setSpan(low, upp)


class QxtSpanSlider(QSlider):
    spanChanged = pyqtSignal(int, int)
    lowerPositionChanged = pyqtSignal(int)
    upperPositionChanged = pyqtSignal(int)
    sliderPressed = pyqtSignal('PyQt_PyObject')
    NoHandle = None
    LowerHandle = 1
    UpperHandle = 2

    FreeMovement = None
    NoCrossing = 1
    NoOverlapping = 2

    __pyqtSignals__ = ("spanChanged(int, int)",
                       "lowerValueChanged(int)", "upperValueChanged(int)",
                       "lowerPositionChanged(int)", "upperPositionChanged(int)",
                       "sliderPressed(PyQt_PyObject)")
    __pyqtSlots__ = ("setLowerValue(int)",
                     "setUpperValue(int)",
                     "setSpan(int, int)",
                     "setLowerPosition(int)",
                     "setUpperPosition(int)",
                     "setGradientLeftColor(PyQt_PyObject)",
                     "setGradientRightColor(PyQt_PyObject)")

    def __init__(self, parent=None):
        QSlider.__init__(self, QtCore.Qt.Horizontal, parent)
        self.rangeChanged[int, int].connect(self.updateRange)
        self.sliderReleased.connect(self.movePressedHandle)

        self.setStyle(QStyleFactory.create('Plastique'))

        self.lower = 0
        self.upper = 0
        self.lowerPos = 0
        self.upperPos = 0
        self.offset = 0
        self.position = 0
        self.lastPressed = QxtSpanSlider.NoHandle
        self.upperPressed = QStyle.SC_None
        self.lowerPressed = QStyle.SC_None
        self.movement = QxtSpanSlider.FreeMovement
        self.mainControl = QxtSpanSlider.LowerHandle
        self.firstMovement = False
        self.blockTracking = False
        self.gradientLeft = self.palette().color(QPalette.Dark).lighter(110)
        self.gradientRight = self.palette().color(QPalette.Dark).lighter(110)

    def lowerValue(self):
        return min(self.lower, self.upper)

    def setLowerValue(self, lower):
        self.setSpan(lower, self.upper)

    def upperValue(self):
        return max(self.lower, self.upper)

    def setUpperValue(self, upper):
        self.setSpan(self.lower, upper)

    def handleMovementMode(self):
        return self.movement

    def setHandleMovementMode(self, mode):
        self.movement = mode

    def setSpan(self, lower, upper):
        low = clamp(min(lower, upper), self.minimum(), self.maximum())
        upp = clamp(max(lower, upper), self.minimum(), self.maximum())
        changed = False
        if low != self.lower:
            self.lower = low
            self.lowerPos = low
            changed = True
        if upp != self.upper:
            self.upper = upp
            self.upperPos = upp
            changed = True
        if changed:
            self.spanChanged.emit(self.lower, self.upper)
            self.update()

    def lowerPosition(self):
        return self.lowerPos

    def setLowerPosition(self, lower):
        if self.lowerPos != lower:
            self.lowerPos = lower
            if not self.hasTracking():
                self.update()
            if self.isSliderDown():
                self.lowerPositionChanged.emit(lower)
            if self.hasTracking() and not self.blockTracking:
                main = (self.mainControl == QxtSpanSlider.LowerHandle)
                self.triggerAction(QxtSpanSlider.SliderMove, main)

    def upperPosition(self):
        return self.upperPos

    def setUpperPosition(self, upper):
        if self.upperPos != upper:
            self.upperPos = upper
            if not self.hasTracking():
                self.update()
            if self.isSliderDown():
                self.upperPositionChanged.emit(upper)
            if self.hasTracking() and not self.blockTracking:
                main = (self.mainControl == QxtSpanSlider.UpperHandle)
                self.triggerAction(QxtSpanSlider.SliderMove, main)

    def gradientLeftColor(self):
        return self.gradientLeft

    def setGradientLeftColor(self, color):
        self.gradientLeft = color
        self.update()

    def gradientRightColor(self):
        return self.gradientRight

    def setGradientRightColor(self, color):
        self.gradientRight = color
        self.update()

    def movePressedHandle(self):
        if self.lastPressed == QxtSpanSlider.LowerHandle:
            if self.lowerPos != self.lower:
                main = (self.mainControl == QxtSpanSlider.LowerHandle)
                self.triggerAction(QAbstractSlider.SliderMove, main)
        elif self.lastPressed == QxtSpanSlider.UpperHandle:
            if self.upperPos != self.upper:
                main = (self.mainControl == QxtSpanSlider.UpperHandle)
                self.triggerAction(QAbstractSlider.SliderMove, main)

    def pick(self, p):
        if self.orientation() == QtCore.Qt.Horizontal:
            return p.x()
        else:
            return p.y()

    def triggerAction(self, action, main):
        value = 0
        no = False
        up = False
        my_min = self.minimum()
        my_max = self.maximum()
        altControl = QxtSpanSlider.LowerHandle
        if self.mainControl == QxtSpanSlider.LowerHandle:
            altControl = QxtSpanSlider.UpperHandle

        self.blockTracking = True

        isUpperHandle = (
            main and self.mainControl == QxtSpanSlider.UpperHandle) \
            or (not main and altControl == QxtSpanSlider.UpperHandle)

        if action == QAbstractSlider.SliderSingleStepAdd:
            if isUpperHandle:
                value = clamp(self.upper + self.singleStep(), my_min, my_max)
                up = True
            else:
                value = clamp(self.lower + self.singleStep(), my_min, my_max)
        elif action == QAbstractSlider.SliderSingleStepSub:
            if isUpperHandle:
                value = clamp(self.upper - self.singleStep(), my_min, my_max)
                up = True
            else:
                value = clamp(self.lower - self.singleStep(), my_min, my_max)
        elif action == QAbstractSlider.SliderToMinimum:
            value = my_min
            if isUpperHandle:
                up = True
        elif action == QAbstractSlider.SliderToMaximum:
            value = my_max
            if isUpperHandle:
                up = True
        elif action == QAbstractSlider.SliderMove:
            if isUpperHandle:
                up = True
            no = True
        elif action == QAbstractSlider.SliderNoAction:
            no = True

        if not no and not up:
            if self.movement == QxtSpanSlider.NoCrossing:
                value = min(value, self.upper)
            elif self.movement == QxtSpanSlider.NoOverlapping:
                value = min(value, self.upper - 1)

            if self.movement == QxtSpanSlider.FreeMovement and value > self.upper:
                self.swapControls()
                self.setUpperPosition(value)
            else:
                self.setLowerPosition(value)
        elif not no:
            if self.movement == QxtSpanSlider.NoCrossing:
                value = max(value, self.lower)
            elif self.movement == QxtSpanSlider.NoOverlapping:
                value = max(value, self.lower + 1)

            if self.movement == QxtSpanSlider.FreeMovement and value < self.lower:
                self.swapControls()
                self.setLowerPosition(value)
            else:
                self.setUpperPosition(value)

        self.blockTracking = False
        self.setLowerValue(self.lowerPos)
        self.setUpperValue(self.upperPos)

    def swapControls(self):
        self.lower, self.upper = self.upper, self.lower
        self.lowerPressed, self.upperPressed = self.upperPressed, self.lowerPressed

        if self.lastPressed == QxtSpanSlider.LowerHandle:
            self.lastPressed = QxtSpanSlider.UpperHandle
        else:
            self.lastPressed = QxtSpanSlider.LowerHandle

        if self.mainControl == QxtSpanSlider.LowerHandle:
            self.mainControl = QxtSpanSlider.UpperHandle
        else:
            self.mainControl = QxtSpanSlider.LowerHandle

    def updateRange(self, lower, upper):
        # setSpan() takes care of keeping span in range
        self.setSpan(lower, upper)

    def paintEvent(self, event):
        painter = QStylePainter(self)

        # ticks
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.subControls = QStyle.SC_SliderTickmarks
        painter.drawComplexControl(QStyle.CC_Slider, opt)

        # groove
        opt.sliderPosition = 20
        opt.sliderValue = 0
        opt.subControls = QStyle.SC_SliderGroove
        painter.drawComplexControl(QStyle.CC_Slider, opt)

        # handle rects
        opt.sliderPosition = self.lowerPos
        lr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        lrv = self.pick(lr.center())
        opt.sliderPosition = self.upperPos
        ur = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        urv = self.pick(ur.center())

        # span
        minv = min(lrv, urv)
        maxv = max(lrv, urv)
        c = self.style().subControlRect(QStyle.CC_Slider, opt,
                                        QStyle.SC_SliderGroove, self).center()
        spanRect = QRect(QPoint(c.x() - 2, minv), QPoint(c.x() + 1, maxv))
        if self.orientation() == QtCore.Qt.Horizontal:
            spanRect = QRect(QPoint(minv, c.y() - 2), QPoint(maxv, c.y() + 1))
        self.drawSpan(painter, spanRect)

        # handles
        if self.lastPressed == QxtSpanSlider.LowerHandle:
            self.drawHandle(painter, QxtSpanSlider.UpperHandle)
            self.drawHandle(painter, QxtSpanSlider.LowerHandle)
        else:
            self.drawHandle(painter, QxtSpanSlider.LowerHandle)
            self.drawHandle(painter, QxtSpanSlider.UpperHandle)

    def setupPainter(self, painter, orientation, x1, y1, x2, y2):
        highlight = self.palette().color(QPalette.Highlight)
        gradient = QLinearGradient(x1, y1, x2, y2)
        gradient.setColorAt(0, highlight.darker(120))
        gradient.setColorAt(1, highlight.lighter(108))
        painter.setBrush(gradient)

        if orientation == QtCore.Qt.Horizontal:
            painter.setPen(QPen(highlight.darker(130), 0))
        else:
            painter.setPen(QPen(highlight.darker(150), 0))

    def drawSpan(self, painter, rect):
        opt = QStyleOptionSlider()
        QSlider.initStyleOption(self, opt)

        # area
        groove = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        if opt.orientation == QtCore.Qt.Horizontal:
            groove.adjust(0, 0, -1, 0)
        else:
            groove.adjust(0, 0, 0, -1)

        # pen & brush
        painter.setPen(QPen(self.gradientLeftColor, 0))
        if opt.orientation == QtCore.Qt.Horizontal:
            self.setupPainter(painter, opt.orientation, groove.center().x(),
                              groove.top(), groove.center().x(),
                              groove.bottom())
        else:
            self.setupPainter(painter, opt.orientation, groove.left(),
                              groove.center().y(), groove.right(),
                              groove.center().y())

        # draw groove
        intersected = QtCore.QRectF(rect.intersected(groove))
        gradient = QLinearGradient(intersected.topLeft(), intersected.topRight())
        gradient.setColorAt(0, self.gradientLeft)
        gradient.setColorAt(1, self.gradientRight)
        painter.fillRect(intersected, gradient)

    def drawHandle(self, painter, handle):
        opt = QStyleOptionSlider()
        self._initStyleOption(opt, handle)
        opt.subControls = QStyle.SC_SliderHandle
        pressed = self.upperPressed
        if handle == QxtSpanSlider.LowerHandle:
            pressed = self.lowerPressed

        if pressed == QStyle.SC_SliderHandle:
            opt.activeSubControls = pressed
            opt.state |= QStyle.State_Sunken
        painter.drawComplexControl(QStyle.CC_Slider, opt)

    def _initStyleOption(self, option, handle):
        self.initStyleOption(option)

        option.sliderPosition = self.upperPos
        if handle == QxtSpanSlider.LowerHandle:
            option.sliderPosition = self.lowerPos

        option.sliderValue = self.upper
        if handle == QxtSpanSlider.LowerHandle:
            option.sliderPosition = self.lower

    def handleMousePress(self, pos, control, value, handle):
        opt = QStyleOptionSlider()
        self._initStyleOption(opt, handle)
        oldControl = control
        control = self.style().hitTestComplexControl(QStyle.CC_Slider, opt, pos, self)
        sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
        if control == QStyle.SC_SliderHandle:
            self.position = value
            self.offset = self.pick(pos - sr.topLeft())
            self.lastPressed = handle
            self.setSliderDown(True)
            self.sliderPressed.emit(handle)
        if control != oldControl:
            self.update(sr)
        return control

    def mousePressEvent(self, event):
        if self.minimum() == self.maximum() or event.buttons() ^ event.button():
            event.ignore()
            return

        self.upperPressed = self.handleMousePress(
            event.pos(), self.upperPressed, self.upper,
            QxtSpanSlider.UpperHandle)
        if self.upperPressed != QStyle.SC_SliderHandle:
            self.lowerPressed = self.handleMousePress(event.pos(), self.lowerPressed, self.lower,
                                                      QxtSpanSlider.LowerHandle)

        self.firstMovement = True
        event.accept()

    def mouseMoveEvent(self, event):
        if self.lowerPressed != QStyle.SC_SliderHandle and self.upperPressed != QStyle.SC_SliderHandle:
            event.ignore()
            return

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        m = self.style().pixelMetric(QStyle.PM_MaximumDragDistance, opt, self)
        newPosition = self.pixelPosToRangeValue(self.pick(event.pos()) - self.offset)
        if m >= 0:
            r = self.rect().adjusted(-m, -m, m, m)
            if not r.contains(event.pos()):
                newPosition = self.position

        # pick the preferred handle on the first movement
        if self.firstMovement:
            if self.lower == self.upper:
                if newPosition < self.lowerValue:
                    self.swapControls()
                    self.firstMovement = False
            else:
                self.firstMovement = False

        if self.lowerPressed == QStyle.SC_SliderHandle:
            if self.movement == QxtSpanSlider.NoCrossing:
                newPosition = min(newPosition, self.upper)
            elif self.movement == QxtSpanSlider.NoOverlapping:
                newPosition = min(newPosition, self.upper - 1)

            if (self.movement == QxtSpanSlider.FreeMovement and
                    newPosition > self.upper):
                self.swapControls()
                self.setUpperPosition(newPosition)
            else:
                self.setLowerPosition(newPosition)
        elif self.upperPressed == QStyle.SC_SliderHandle:
            if self.movement == QxtSpanSlider.NoCrossing:
                newPosition = max(newPosition, self.lowerValue)
            elif self.movement == QxtSpanSlider.NoOverlapping:
                newPosition = max(newPosition, self.lowerValue + 1)

            if (self.movement == QxtSpanSlider.FreeMovement and
                    newPosition < self.lower):
                self.swapControls()
                self.setLowerPosition(newPosition)
            else:
                self.setUpperPosition(newPosition)
        event.accept()

    def mouseReleaseEvent(self, event):
        QSlider.mouseReleaseEvent(self, event)
        self.setSliderDown(False)
        self.lowerPressed = QStyle.SC_None
        self.upperPressed = QStyle.SC_None
        self.update()

    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        gr = self.style().subControlRect(QStyle.CC_Slider, opt,
                                         QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.CC_Slider, opt,
                                         QStyle.SC_SliderHandle, self)
        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1

        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos - slider_min,
                                              slider_max - slider_min, opt.upsideDown)

    lowerValue = pyqtProperty("int", lowerValue, setLowerValue)
    upperValue = pyqtProperty("int", upperValue, setUpperValue)
    upperPosition = pyqtProperty("int", upperPosition, setUpperPosition)
    lowerPosition = pyqtProperty("int", lowerPosition, setLowerPosition)
    handleMovementMode = pyqtProperty("PyQt_PyObject", handleMovementMode, setHandleMovementMode)
    gradientLeftColor = pyqtProperty("PyQt_PyObject", gradientLeftColor, setGradientLeftColor)
    gradientRightColor = pyqtProperty("PyQt_PyObject", gradientRightColor, setGradientRightColor)
