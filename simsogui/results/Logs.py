#!/usr/bin/python
# coding=utf-8

from PyQt4.QtGui import QTableWidgetItem, QTableWidget, QHeaderView, QColor


class Logs(QTableWidget):
    def __init__(self, parent, result):
        QTableWidget.__init__(self, len(result.model.logs), 3, parent=parent)
        self.setWindowTitle("Logs")
        self.setHorizontalHeaderLabels(["Date (cycles)", "Date (ms)", "Message"])
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMinimumSectionSize(60)
        self.verticalHeader().hide()
        self._sim = result.model
        self.result = result
        self.update()

    def update(self):
        self.setRowCount(len(self._sim.logs))
        row = 0
        for msg in self._sim.logs:
            if (msg[0] < self.result.observation_window[0] or
                    msg[0] > self.result.observation_window[1]):
                continue
            self.setItem(row, 0, QTableWidgetItem(str(msg[0])))
            self.setItem(row, 1, QTableWidgetItem(str(float(msg[0]) / self._sim.cycles_per_ms)))
            self.setItem(row, 2, QTableWidgetItem(str(msg[1][0])))
            if msg[1][1]:
                self.item(row, 0).setBackgroundColor(QColor(180, 220, 255))
                self.item(row, 1).setBackgroundColor(QColor(180, 220, 255))
                self.item(row, 2).setBackgroundColor(QColor(180, 220, 255))
            else:
                self.item(row, 0).setBackgroundColor(QColor(220, 255, 180))
                self.item(row, 1).setBackgroundColor(QColor(220, 255, 180))
                self.item(row, 2).setBackgroundColor(QColor(220, 255, 180))
            row += 1
        self.setRowCount(row)
