from PyQt4.QtCore import Qt, QRect, QRectF, QLineF, QPointF
from PyQt4.QtGui import QDialog, QVBoxLayout, QListWidget, QToolBar, QWidget, \
    QHBoxLayout, QPushButton, qApp, QStyle, QSizePolicy, QBrush,\
    QScrollArea, QFileDialog, QPainter, QColor, QPen, QFont,\
    QImage, QListWidgetItem

from .QxtSpanSlider import QxtSpanSliderWidget

from simso.core import JobEvent, ProcEvent


class GanttConfigure(QDialog):
    def __init__(self, sim, start, end):
        QDialog.__init__(self)
        #self.setCaption("Gantt configuration")
        self.layout = QVBoxLayout(self)

#        self._slider = QxtSpanSliderWidget(
#            sim.observe_window[0] // sim.cycles_per_ms,
#            min(sim.now(), sim.observe_window[1]) // sim.cycles_per_ms,
#            self)
        self._slider = QxtSpanSliderWidget(
            0,
            min(sim.now(), sim.duration) // sim.cycles_per_ms,
            self)
        self._slider.setSpan(start, end)
        self.layout.addWidget(self._slider)

        self._list_elements = QListWidget(self)
        for processor in sim.processors:
            item = QListWidgetItem(processor.name, self._list_elements)
            item.setData(Qt.UserRole, processor)
            self._list_elements.addItem(item)
        for task in sim.task_list:
            item = QListWidgetItem(task.name, self._list_elements)
            item.setData(Qt.UserRole, task)
            self._list_elements.addItem(item)
        #self._list_elements.setDragDropMode(QListWidget.InternalMove)
        for row in range(0, self._list_elements.count()):
            self._list_elements.item(row).setCheckState(Qt.Checked)
        self.layout.addWidget(self._list_elements)

        buttons = QWidget(self)
        buttons_layout = QHBoxLayout()
        buttons.setLayout(buttons_layout)
        buttons_layout.addStretch()
        ok_button = QPushButton("Ok")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        self.layout.addWidget(buttons)

    def get_start_date(self):
        return self._slider.lowerValue

    def get_end_date(self):
        return self._slider.upperValue

    def get_selected_items(self):
        res = []
        for row in range(0, self._list_elements.count()):
            if self._list_elements.item(row).checkState() == Qt.Checked:
                try:
                    data = self._list_elements.item(row).data(Qt.UserRole).toPyObject()
                except AttributeError:
                    data = self._list_elements.item(row).data(Qt.UserRole)

                res.append(data)
        return res


class GanttCanvas(QWidget):
    def __init__(self, sim, config, parent=None):
        super(GanttCanvas, self).__init__(parent)
        self._sim = sim
        self._start_date, self._end_date, self._selected_items = config
        self.plot()

    def plot(self):
        self._vwidth = (self._end_date - self._start_date) * 10
        self._width = self._vwidth + 40
        self._height = 20 + 80 * len(self._selected_items)
        if self._width < 200:
            self._width = 200
        self._update()

    def convX(self, x):
        return x * self._vwidth / float(self._end_date - self._start_date)

    def origGraph(self, c):
        offX = 20
        offY = 80
        return (offX, c * offY + 15)

    def paintEvent(self, event):
        qp = QPainter(self)
        dirtyRect = event.rect()
        i = dirtyRect.x() // (2 ** 15)
        rect = QRect(dirtyRect.x() % (2 ** 15), dirtyRect.y(), dirtyRect.width(), dirtyRect.height())
        qp.drawImage(dirtyRect, self._image[i], rect)

    def plot_graph(self, qp, name, start_date, end_date, step, substep, c):
        qp.save()
        convX = self.convX
        graph_height = 50
        qp.setBrush(QColor(255, 255, 255))
        x, y = self.origGraph(c)
        qp.drawRect(QRectF(x - 1, y, convX(end_date - start_date) + 1,
                           graph_height))

        qp.setFont(QFont('Decorative', 8))
        for i in range(start_date, end_date + 1, 1):
            h = 0
            if i % step == 0:
                text = str(i)
                fw = qp.fontMetrics().width(text)
                fh = qp.fontMetrics().height()
                qp.drawText(x + convX(i - start_date) - fw // 2,
                            graph_height + y + fh + 1, text)
                pen = qp.pen()
                if i != start_date and i != end_date:
                    qp.setPen(QPen(Qt.DotLine))
                    qp.drawLine(x + convX(i - start_date), y,
                                x + convX(i - start_date),
                                graph_height + y + 1)
                    qp.setPen(pen)

                h = 4
            elif i % substep == 0:
                h = 2
            if h:
                qp.drawLine(
                    x + convX(i - start_date), graph_height + 1 + y,
                    x + convX(i - start_date), graph_height + y + 1 + h)

        qp.translate(x - 20, y + 65)
        qp.rotate(-90)
        qp.setFont(QFont('Decorative', 10))
        qp.drawText(QRect(0, 0, 80, 20), Qt.AlignCenter, name)
        qp.restore()

    def plot_rect_graph(self, qp, start_x, end_x, color_style, c):
        if start_x < self._start_date:
            start_x = self._start_date
        if start_x >= end_x:
            return

        start_x -= self._start_date
        end_x -= self._start_date

        qp.save()
        qp.setPen(Qt.NoPen)
        x, y = self.origGraph(c)
        color, style = color_style
        color.setAlpha(200)
        qp.setBrush(QBrush(color, style))
        qp.drawRect(QRectF(x + self.convX(start_x), y + 10,
                           self.convX(end_x - start_x), 40))
        qp.restore()
        #qp.drawLine(x + self.convX(start_x), y + 10,
        #            x + self.convX(end_x), y + 10)

    def plot_vert_line_graph(self, qp, x_line, color, c, arrow_up=False,
                             arrow_down=False):
        if x_line < self._start_date or x_line > self._end_date:
            return

        x_line -= self._start_date

        qp.save()
        qp.setPen(color)
        qp.setBrush(color)
        qp.setRenderHint(QPainter.Antialiasing)
        arrowSize = 2.0
        x, y = self.origGraph(c)
        line = QLineF(x + self.convX(x_line), y + 10, x + self.convX(x_line),
                      y + 50)
        qp.drawLine(line)
        if arrow_up:
            arrowP1 = line.p1() + QPointF(arrowSize, arrowSize * 3)
            arrowP2 = line.p1() + QPointF(-arrowSize, arrowSize * 3)
            qp.drawLine(line.p1(), arrowP1)
            qp.drawLine(line.p1(), arrowP2)
        if arrow_down:
            arrowP1 = line.p2() + QPointF(arrowSize, - arrowSize * 3)
            arrowP2 = line.p2() + QPointF(-arrowSize, - arrowSize * 3)
            qp.drawLine(line.p2(), arrowP1)
            qp.drawLine(line.p2(), arrowP2)
        qp.restore()

    def plot_circle_graph(self, qp, x_circle, color, c):
        if x_circle < self._start_date:
            return
        x_circle -= self._start_date
        qp.save()
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(color)
        qp.setBrush(color)
        x, y = self.origGraph(c)
        qp.drawEllipse(x + self.convX(x_circle) - 1, y + 50 - 1, 3, 3)
        qp.restore()

    def get_color(self, i):
        colors = [(150, 50, 0), (20, 180, 20), (50, 200, 250), (240, 230, 0),
                  (190, 0, 250), (50, 50, 200), (238, 135, 178),
                  (40, 100, 100), (250, 180, 0), (0, 150, 100)]
        pattern = Qt.SolidPattern
        if i > len(colors):
            pattern = Qt.Dense2Pattern
        elif i > 2 * len(colors):
            pattern = Qt.BDiagPattern
        return (QColor(*colors[i % len(colors)]), pattern)

    def plot_gantt(self, event, qp, sim, start_date, end_date):
        c = -1

        zoom = self._vwidth / float(end_date - start_date)

        if zoom < 0.3:
            step = 200
        elif zoom < 0.5:
            step = 100
        elif zoom < 2:
            step = 50
        elif zoom < 3:
            step = 20
        elif zoom < 4.5:
            step = 10
        else:
            step = 5

        substep = step // 5

        # Plot processors
        for processor in [x for x in sim.processors
                          if x in self._selected_items]:
            c += 1
            self.plot_graph(qp, processor.name, start_date, end_date, step,
                            substep, c)

            x1 = start_date
            color = None
            for evt in processor.monitor:
                current_date = float(evt[0]) / sim.cycles_per_ms
                if current_date > end_date:
                    break

                if evt[1].event == ProcEvent.RUN:
                    ncolor = self.get_color(evt[1].args.task.identifier)
                elif evt[1].event == ProcEvent.OVERHEAD:
                    ncolor = (QColor(150, 150, 150), Qt.SolidPattern)
                elif evt[1].event == ProcEvent.IDLE:
                    ncolor = None

                if ncolor != color:
                    if current_date > x1 and color:
                        self.plot_rect_graph(qp, x1, current_date, color, c)
                    color = ncolor
                    x1 = current_date

            if color:
                self.plot_rect_graph(qp, x1, end_date, color, c)

        # Plot tasks
        for task in [x for x in sim.task_list if x in self._selected_items]:
            c += 1
            self.plot_graph(
                qp, task.name, start_date, end_date, step, substep, c)

            x1 = start_date
            color = None
            for evt in task.monitor:
                current_date = evt[0] / float(sim.cycles_per_ms)
                if current_date > end_date:
                    break

                if evt[1].event != JobEvent.ACTIVATE:
                    if color and x1 < current_date:
                        self.plot_rect_graph(qp, x1, current_date, color, c)

                    if evt[1].event == JobEvent.EXECUTE:
                        color = self.get_color(task.identifier)
                    elif evt[1].event == JobEvent.PREEMPTED:
                        color = None
                    elif evt[1].event == JobEvent.TERMINATED:
                        color = None
                    elif evt[1].event == JobEvent.ABORTED:
                        color = None

                    x1 = current_date

            if x1 < end_date and color:
                self.plot_rect_graph(qp, x1, end_date, color, c)

            # Draw activation lines.
            for evt in task.monitor:
                current_date = evt[0] / float(sim.cycles_per_ms)
                if current_date > end_date:
                    break

                if evt[1].event == JobEvent.ACTIVATE:
                    self.plot_vert_line_graph(qp, current_date,
                                              QColor(50, 50, 50),
                                              c, arrow_up=True)

            # Draw deadlines and dots.
            for evt in task.monitor:
                current_date = evt[0] / float(sim.cycles_per_ms)
                if current_date > end_date:
                    break

                if evt[1].event == JobEvent.ACTIVATE:
                    if current_date + task.deadline <= end_date:
                        job_end = evt[1].job.end_date or end_date
                        if (job_end > evt[1].job.absolute_deadline
                                * sim.cycles_per_ms or evt[1].job.aborted):
                            color = QColor(255, 0, 0)
                        else:
                            color = QColor(50, 50, 50)
                        self.plot_vert_line_graph(
                            qp, current_date + task.deadline, color, c,
                            arrow_down=True)
                elif evt[1].event == JobEvent.TERMINATED:
                    self.plot_circle_graph(
                        qp, current_date, QColor(0, 0, 0), c)
                elif evt[1].event == JobEvent.ABORTED:
                    self.plot_circle_graph(
                        qp, current_date, QColor(255, 0, 0), c)

    def saveImg(self):
        imageFile = QFileDialog.getSaveFileName(
            filter="*.png",
            caption="Image file name")
        if imageFile:
            if str(imageFile[-4:]) != ".png":
                imageFile += ".png"
            self._image[0].save(str(imageFile))

    def zoomDown(self):
        self._vwidth /= 1.2
        if self._vwidth < 200:
            self._vwidth = 200
        self._width = self._vwidth + 40
        self._update()

    def zoomUp(self):
        self._vwidth *= 1.2
        self._width = self._vwidth + 40
        self._update()

    def create_qimage(self):
        total_width = 0
        images = []
        while total_width < self._width:
            w = min(self._width - total_width, 2 ** 15)
            image = QImage(w, self._height, QImage.Format_ARGB32)
            image.fill(QColor(235, 235, 235, 255))
            total_width += w
            images.append(image)
        return images

    def _update(self):
        QWidget.setFixedWidth(self, self._width)
        QWidget.setFixedHeight(self, self._height)
        QWidget.setSizePolicy(self,
                              QSizePolicy.Fixed,
                              QSizePolicy.Fixed)

        QWidget.updateGeometry(self)

        qp = QPainter()
        self._image = self.create_qimage()
        for image in self._image:
            qp.begin(self._image[0])
            #qp.setRenderHint(QPainter.Antialiasing)
            self.plot_gantt(
                None, qp, self._sim, self._start_date, self._end_date)
            qp.end()

    def configure(self):
        gc = GanttConfigure(self._sim, self._start_date, self._end_date)
        if gc.exec_():
            self._start_date = gc.get_start_date()
            self._end_date = gc.get_end_date()
            self._selected_items = gc.get_selected_items()
        self.plot()


class GanttToolBar(QToolBar):
    def __init__(self, parent, canvas):
        QToolBar.__init__(self, parent)
        self._canvas = canvas
        self.addAction(qApp.style().standardIcon(QStyle.SP_DialogSaveButton),
                       "Save", canvas.saveImg)
        self.addAction("Zoom +", canvas.zoomUp)
        self.addAction("Zoom -", canvas.zoomDown)
        self.addAction("Configure", canvas.configure)


class Gantt(QWidget):
    def __init__(self, sim, conf):
        QWidget.__init__(self)
        self.setWindowTitle("Gantt chart")
        layout1 = QVBoxLayout(self)
        self.setLayout(layout1)

        canvas = GanttCanvas(sim, conf)

        layout1.addWidget(GanttToolBar(self, canvas))

        scrollArea = QScrollArea(self)
        layout1.addWidget(scrollArea)
        scrollArea.setWidgetResizable(True)

        viewport = QWidget()
        scrollArea.setWidget(viewport)
        layout = QVBoxLayout(viewport)
        layout.addWidget(canvas)

    def closeEvent(self, event):
        self.parent().hide()
        event.ignore()


def create_gantt_window(sim):
    gc = GanttConfigure(sim, 0, min(sim.now(), sim.duration) // sim.cycles_per_ms)
    if gc.exec_():
        start_date = gc.get_start_date()
        end_date = gc.get_end_date()
        selected_items = gc.get_selected_items()
        return Gantt(sim, (start_date, end_date, selected_items))
    return None
