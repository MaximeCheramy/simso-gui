from PyQt4.QtGui import QWidget, QStatusBar, QVBoxLayout


class Tab(QWidget):
    def __init__(self, parent, configuration):
        QWidget.__init__(self, parent)
        self._configuration = configuration

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        main_widget = QWidget(self)
        self._layout_main = QVBoxLayout()
        self._layout_main.setContentsMargins(0, 0, 0, 0)
        self._layout_main.setSpacing(6)
        main_widget.setLayout(self._layout_main)
        layout.addWidget(main_widget)
        self._status_bar = QStatusBar()
        layout.addWidget(self._status_bar)
        self.setLayout(layout)

    def _add_widget(self, widget):
        self._layout_main.addWidget(widget)

    def set_error_message(self, msg):
        self._status_bar.showMessage(msg)
