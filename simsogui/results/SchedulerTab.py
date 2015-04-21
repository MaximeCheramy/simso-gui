from PyQt4.QtGui import QTabWidget, QLabel, QVBoxLayout, QGroupBox, QWidget, \
    QScrollArea


class SchedulerTab(QTabWidget):
    def __init__(self, result):
        QTabWidget.__init__(self)
        self.result = result
        self.setLayout(QVBoxLayout())
        self.update()

    def update(self):
        for i in range(self.layout().count()):
            self.layout().itemAt(0).widget().close()
            self.layout().takeAt(0)

        result = self.result
        scheduler = result.scheduler
        cycles_per_ms = float(result.model.cycles_per_ms)

        sg = QWidget()
        sg.setLayout(QVBoxLayout())

        count_layout = QVBoxLayout()
        count_group = QGroupBox("Scheduling events: ")
        count_group.setLayout(count_layout)

        count_layout.addWidget(QLabel(
            "schedule count: {}".format(scheduler.schedule_count)))
        count_layout.addWidget(QLabel(
            "on_activate count: {}".format(scheduler.activate_count)))
        count_layout.addWidget(QLabel(
            "on_terminate count: {}".format(scheduler.terminate_count)))

        overhead_layout = QVBoxLayout()
        overhead_group = QGroupBox("Scheduling overhead: ")
        overhead_group.setLayout(overhead_layout)

        overhead_layout.addWidget(QLabel(
            "schedule overhead: {:.4f}ms ({:.0f} cycles)".format(
                scheduler.schedule_overhead / cycles_per_ms,
                scheduler.schedule_overhead)))
        overhead_layout.addWidget(QLabel(
            "on_activate overhead: {:.4f}ms ({:.0f} cycles)".format(
                scheduler.activate_overhead / cycles_per_ms,
                scheduler.activate_overhead)))
        overhead_layout.addWidget(QLabel(
            "on_terminate overhead: {:.4f}ms ({:.0f} cycles)".format(
                scheduler.terminate_overhead / cycles_per_ms,
                scheduler.terminate_overhead)))
        sum_overhead = (scheduler.schedule_overhead +
                        scheduler.activate_overhead +
                        scheduler.terminate_overhead)
        overhead_layout.addWidget(QLabel(
            "Sum: {:.4f}ms ({:.0f} cycles)".format(
                sum_overhead / cycles_per_ms, sum_overhead)))

        timer_layout = QVBoxLayout()
        timer_group = QGroupBox("Timers")
        timer_group.setLayout(timer_layout)

        for proc in self.result.model.processors:
            timer_layout.addWidget(QLabel(
                "{}: {}".format(proc.name, result.timers[proc])
            ))

        sg.layout().addWidget(count_group)
        sg.layout().addWidget(overhead_group)
        sg.layout().addWidget(timer_group)

        qsa = QScrollArea()
        qsa.setWidget(sg)
        self.layout().addWidget(qsa)
