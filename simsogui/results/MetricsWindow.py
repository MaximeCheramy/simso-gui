from PyQt4.QtGui import QTabWidget, QVBoxLayout, QDialog, QButtonGroup, \
    QRadioButton, QPushButton, QWidget, QHBoxLayout, QLabel, QGroupBox
from ..QxtSpanSlider import QxtSpanSliderWidget
from .LoadTab import LoadTable
from .TasksTab import TasksTab
from .Logs import Logs
from .SchedulerTab import SchedulerTab
from .ProcessorsTab import ProcessorsTab


class ObservationWindowConfigure(QDialog):
    def __init__(self, result):
        QDialog.__init__(self)
        self.layout = QVBoxLayout(self)
        self.result = result
        observation_window = result.observation_window

        group = QButtonGroup(self)
        use_simu_duration = QRadioButton("Use entire simulation.")
        use_simu_duration.setChecked(
            observation_window[0] == 0
            and observation_window[1] == result.model.duration)
        group.addButton(use_simu_duration)
        self.layout.addWidget(use_simu_duration)

        use_custom = QRadioButton("Use a custom observation window:")
        use_custom.setChecked(not use_simu_duration.isChecked())
        group.addButton(use_custom)
        self.layout.addWidget(use_custom)

        self._slider = QxtSpanSliderWidget(
            0, result.model.now() // result.model.cycles_per_ms, self)
        self._slider.setSpan(
            observation_window[0] // result.model.cycles_per_ms,
            observation_window[1] // result.model.cycles_per_ms)
        self._slider.setEnabled(use_custom.isChecked())
        group.buttonClicked.connect(
            lambda x: self._slider.setEnabled(x == use_custom))

        self.layout.addWidget(self._slider)

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

    def getObservationWindow(self):
        if self._slider.isEnabled():
            return (self._slider.lowerValue * self.result.model.cycles_per_ms,
                    self._slider.upperValue * self.result.model.cycles_per_ms)
        else:
            return None


class GeneralTab(QTabWidget):
    def __init__(self, parent, result):
        QTabWidget.__init__(self, parent)
        self.result = result
        self.parent = parent

        obs_box = QGroupBox("Observation Window:", self)

        obs = QHBoxLayout()
        self.obs_label = QLabel()
        obs.addWidget(self.obs_label)
        obs_conf = QPushButton("Configure...")
        obs_conf.clicked.connect(self.setObservationWindow)
        obs.addWidget(obs_conf)

        obs_box.setLayout(obs)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(obs_box)
        self.load_table = LoadTable(self, result)
        self.layout().addWidget(self.load_table)
        self.update()

    def setObservationWindow(self):
        dialog = ObservationWindowConfigure(self.result)
        if dialog.exec_():
            self.result.observation_window = dialog.getObservationWindow()
            self.parent.update()

    def update(self):
        cycles_per_ms = self.result.model.cycles_per_ms
        self.obs_label.setText('from {:.2f} to {:.2f} ms'.format(
            self.result.observation_window[0] / float(cycles_per_ms),
            self.result.observation_window[1] / float(cycles_per_ms)))
        self.load_table.update()


class ResultsWindow(QTabWidget):
    def __init__(self, result):
        QTabWidget.__init__(self)
        self.setWindowTitle("Results")
        self.setMinimumSize(400, 300)

        self.general_tab = GeneralTab(self, result)
        self.logs_tab = Logs(self, result)
        self.tasks_tab = TasksTab(self, result)
        self.scheduler_tab = SchedulerTab(result)
        self.processors_tab = ProcessorsTab(result)

        self.addTab(self.general_tab, "General")
        self.addTab(self.logs_tab, "Logs")
        self.addTab(self.tasks_tab, "Tasks")
        self.addTab(self.scheduler_tab, "Scheduler")
        self.addTab(self.processors_tab, "Processors")

    def closeEvent(self, event):
        self.parent().hide()
        event.ignore()

    def update(self):
        self.general_tab.update()
        self.logs_tab.update()
        self.tasks_tab.update()
        self.scheduler_tab.update()
        self.processors_tab.update()
