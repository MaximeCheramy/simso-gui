from PyQt4.QtGui import QTabWidget, QLabel, QVBoxLayout, QGroupBox, \
    QScrollArea, QWidget


class ProcessorsTab(QTabWidget):
    def __init__(self, result):
        QTabWidget.__init__(self)
        self.result = result

        self.setLayout(QVBoxLayout())
        self.update()

    def update(self):
        for i in range(self.layout().count()):
            self.layout().itemAt(0).widget().close()
            self.layout().takeAt(0)

        qsa = QScrollArea()
        scroll_area_widget = QWidget()
        layout = QVBoxLayout()
        scroll_area_widget.setLayout(layout)

        model = self.result.model
        cycles_per_ms = model.cycles_per_ms
        for proc in model.processors:
            proc_r = self.result.processors[proc]
            gb = QGroupBox(proc.name)
            gb_layout = QVBoxLayout()
            gb.setLayout(gb_layout)
            gb_layout.addWidget(QLabel(
                "Cxt Save count: {}".format(proc_r.context_save_count)))
            gb_layout.addWidget(QLabel(
                "Cxt Load count: {}".format(proc_r.context_load_count)))
            gb_layout.addWidget(QLabel(
                "Cxt Save overhead: {0:.4f}ms ({1:.0f} cycles)".format(
                    float(proc_r.context_save_overhead) / cycles_per_ms,
                    proc_r.context_save_overhead)))
            gb_layout.addWidget(QLabel(
                "Cxt Load overhead: {0:.4f}ms ({1:.0f} cycles)".format(
                    float(proc_r.context_load_overhead) / cycles_per_ms,
                    proc_r.context_load_overhead)))

            layout.addWidget(gb)

        qsa.setWidget(scroll_area_widget)
        self.layout().addWidget(qsa)
