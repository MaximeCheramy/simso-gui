from PyQt5.QtCore import Qt, QByteArray, QMimeData
from PyQt5.QtWidgets import QApplication, QTableWidget


class QCopyTableWidget(QTableWidget):
    def keyPressEvent(self, event):
        if(event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier):
            indexes = self.selectionModel().selectedIndexes()
            previous = indexes[0]
            values = QByteArray()
            for index in sorted(indexes):
                if index.row() != previous.row():
                    values += '\n'
                elif index != indexes[0]:
                    values += '\t'
                values += self.itemFromIndex(index).text()
                previous = index
            mimeData = QMimeData()
            mimeData.setData("text/plain", values)
            QApplication.clipboard().setMimeData(mimeData)
        else:
            return QTableWidget.keyPressEvent(self, event)
