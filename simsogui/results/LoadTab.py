from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QAbstractItemView
from ..QCopyTableWidget import QCopyTableWidget


class LoadTable(QCopyTableWidget):
    def __init__(self, parent, result):
        QTableWidget.__init__(
            self, len(result.model.processors) + 1, 3, parent)
        self.result = result
        self.setHorizontalHeaderLabels(["Total load", "Payload",
                                        "System load", "Theoric min"])
        self.setVerticalHeaderLabels(
            [x.name for x in result.model.processors] + ["Average"])
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.update()

    def update(self):
        sum_load = 0.0
        sum_overhead = 0.0

        curRow = 0
        for proc, load, overhead in self.result.calc_load():
            self.setItem(curRow, 0,
                         QTableWidgetItem("%.4f" % (load + overhead)))
            self.setItem(curRow, 1, QTableWidgetItem("%.4f" % (load)))
            self.setItem(curRow, 2, QTableWidgetItem("%.4f" % (overhead)))
            sum_load += load
            sum_overhead += overhead
            curRow += 1

        load = sum_load / len(self.result.model.processors)
        overhead = sum_overhead / len(self.result.model.processors)
        self.setItem(curRow, 0, QTableWidgetItem("%.4f" % (load + overhead)))
        self.setItem(curRow, 1, QTableWidgetItem("%.4f" % (load)))
        self.setItem(curRow, 2, QTableWidgetItem("%.4f" % (overhead)))
