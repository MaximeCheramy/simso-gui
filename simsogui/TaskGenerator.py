from PyQt4.QtGui import QDialog, QSlider, QVBoxLayout, QHBoxLayout, \
    QDoubleSpinBox, QSpinBox, QRadioButton, QWidget, QLineEdit, \
    QRegExpValidator, QDialogButtonBox, QMessageBox, QGroupBox, QCheckBox, \
    QComboBox, QLabel
from PyQt4.QtCore import pyqtSignal, QRegExp
from PyQt4 import QtCore
from simso.generator.task_generator import StaffordRandFixedSum, \
    gen_periods_loguniform, gen_periods_uniform, gen_periods_discrete, \
    gen_tasksets, UUniFastDiscard, gen_kato_utilizations


class _DoubleSlider(QSlider):
    doubleValueChanged = pyqtSignal([float])

    def __init__(self, orient, parent):
        QSlider.__init__(self, orient, parent)

        self.valueChanged.connect(
            lambda x: self.doubleValueChanged.emit(x / 100.0))

    def setMinimum(self, val):
        QSlider.setMinimum(self, val * 100)

    def setMaximum(self, val):
        QSlider.setMaximum(self, val * 100)

    def setValue(self, val):
        QSlider.setValue(self, val * 100)


class IntervalSpinner(QWidget):
    def __init__(self, parent, min_=1, max_=1000, step=1, round_option=True):
        QWidget.__init__(self, parent)
        layout = QVBoxLayout(self)
        hlayout = QHBoxLayout()
        self.start = QDoubleSpinBox(self)
        self.start.setMinimum(min_)
        self.start.setMaximum(max_)
        self.end = QDoubleSpinBox(self)
        self.end.setMinimum(min_)
        self.end.setMaximum(max_)
        self.end.setValue(max_)
        self.start.setSingleStep(step)
        self.end.setSingleStep(step)

        self.start.valueChanged.connect(self.on_value_start_changed)
        self.end.valueChanged.connect(self.on_value_end_changed)

        hlayout.addWidget(self.start)
        hlayout.addWidget(self.end)
        layout.addLayout(hlayout)

        if round_option:
            self.integerCheckBox = QCheckBox("Round to integer values", self)
            layout.addWidget(self.integerCheckBox)

    def on_value_start_changed(self, val):
        if self.end.value() < val:
            self.end.setValue(val)

    def on_value_end_changed(self, val):
        if self.start.value() > val:
            self.start.setValue(val)

    def getMin(self):
        return self.start.value()

    def getMax(self):
        return self.end.value()

    def getRound(self):
        return self.integerCheckBox.isChecked()


class TaskGeneratorDialog(QDialog):
    def __init__(self, nbprocessors):
        QDialog.__init__(self)
        self.layout = QVBoxLayout(self)
        self.taskset = None

        # Utilizations:
        vbox_utilizations = QVBoxLayout()
        group = QGroupBox("Task Utilizations:")

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Generator:", self))
        self.comboGenerator = QComboBox()
        self.comboGenerator.addItem("RandFixedSum")
        self.comboGenerator.addItem("UUniFast-Discard")
        self.comboGenerator.addItem("Kato's method")
        self.comboGenerator.currentIndexChanged.connect(self.generator_changed)
        hbox.addWidget(self.comboGenerator)
        vbox_utilizations.addLayout(hbox)

        # Load slider + spinner:
        hbox_load = QHBoxLayout()
        sld = _DoubleSlider(QtCore.Qt.Horizontal, self)
        sld.setMinimum(0)
        sld.setMaximum(32)
        self.spin_load = QDoubleSpinBox(self)
        self.spin_load.setMinimum(0)
        self.spin_load.setMaximum(32)
        self.spin_load.setSingleStep(0.1)
        hbox_load.addWidget(QLabel("Total utilization: ", self))
        hbox_load.addWidget(sld)
        hbox_load.addWidget(self.spin_load)
        sld.doubleValueChanged.connect(self.spin_load.setValue)
        self.spin_load.valueChanged.connect(sld.setValue)
        self.spin_load.setValue(nbprocessors / 2.)
        vbox_utilizations.addLayout(hbox_load)

        # Number of periodic tasks:
        self.hbox_tasks = QHBoxLayout()
        self.spin_tasks = QSpinBox(self)
        self.spin_tasks.setMinimum(0)
        self.spin_tasks.setMaximum(999)  # That's arbitrary.
        self.hbox_tasks.addWidget(QLabel("Number of periodic tasks: ", self))
        self.hbox_tasks.addStretch(1)
        self.hbox_tasks.addWidget(self.spin_tasks)
        vbox_utilizations.addLayout(self.hbox_tasks)

        # Number of sporadic tasks:
        self.hbox_sporadic_tasks = QHBoxLayout()
        self.spin_sporadic_tasks = QSpinBox(self)
        self.spin_sporadic_tasks.setMinimum(0)
        self.spin_sporadic_tasks.setMaximum(999)  # That's arbitrary.
        self.hbox_sporadic_tasks.addWidget(
            QLabel("Number of sporadic tasks: ", self))
        self.hbox_sporadic_tasks.addStretch(1)
        self.hbox_sporadic_tasks.addWidget(self.spin_sporadic_tasks)
        vbox_utilizations.addLayout(self.hbox_sporadic_tasks)

        # Min / Max utilizations
        self.hbox_utilizations = QHBoxLayout()
        self.hbox_utilizations.addWidget(QLabel("Min/Max utilizations: ",
                                                self))
        self.interval_utilization = IntervalSpinner(
            self, min_=0, max_=1, step=.01, round_option=False)
        self.hbox_utilizations.addWidget(self.interval_utilization)
        vbox_utilizations.addLayout(self.hbox_utilizations)

        group.setLayout(vbox_utilizations)
        self.layout.addWidget(group)

        # Periods:
        vbox_periods = QVBoxLayout()
        group = QGroupBox("Task Periods:")

        # Log uniform
        self.lunif = QRadioButton("log-uniform distribution between:")
        vbox_periods.addWidget(self.lunif)
        self.lunif.setChecked(True)

        self.lunif_interval = IntervalSpinner(self)
        self.lunif_interval.setEnabled(self.lunif.isChecked())
        self.lunif.toggled.connect(self.lunif_interval.setEnabled)
        vbox_periods.addWidget(self.lunif_interval)

        # Uniform
        self.unif = QRadioButton("uniform distribution between:")
        vbox_periods.addWidget(self.unif)

        self.unif_interval = IntervalSpinner(self)
        self.unif_interval.setEnabled(self.unif.isChecked())
        self.unif.toggled.connect(self.unif_interval.setEnabled)
        vbox_periods.addWidget(self.unif_interval)

        # Discrete
        discrete = QRadioButton("chosen among these (space separated) values:")
        vbox_periods.addWidget(discrete)

        self.periods = QLineEdit(self)
        self.periods.setValidator(QRegExpValidator(
            QRegExp("^\\d*(\.\\d*)?( \\d*(\.\\d*)?)*$")))

        vbox_periods.addWidget(self.periods)
        self.periods.setEnabled(discrete.isChecked())
        discrete.toggled.connect(self.periods.setEnabled)
        vbox_periods.addStretch(1)

        group.setLayout(vbox_periods)
        self.layout.addWidget(group)

        buttonBox = QDialogButtonBox()
        cancel = buttonBox.addButton(QDialogButtonBox.Cancel)
        generate = buttonBox.addButton("Generate", QDialogButtonBox.AcceptRole)
        cancel.clicked.connect(self.reject)
        generate.clicked.connect(self.generate)
        self.layout.addWidget(buttonBox)

        self.show_randfixedsum_options()

    def generator_changed(self, value):
        if value == 2:
            self.show_kato_options()
        else:
            self.show_randfixedsum_options()

    def show_randfixedsum_options(self):
        for i in range(self.hbox_utilizations.count()):
            self.hbox_utilizations.itemAt(i).widget().hide()
        for i in range(self.hbox_tasks.count()):
            if self.hbox_tasks.itemAt(i).widget():
                self.hbox_tasks.itemAt(i).widget().show()
        for i in range(self.hbox_sporadic_tasks.count()):
            if self.hbox_sporadic_tasks.itemAt(i).widget():
                self.hbox_sporadic_tasks.itemAt(i).widget().show()

    def show_kato_options(self):
        for i in range(self.hbox_utilizations.count()):
            if self.hbox_utilizations.itemAt(i).widget():
                self.hbox_utilizations.itemAt(i).widget().show()
        for i in range(self.hbox_tasks.count()):
            if self.hbox_tasks.itemAt(i).widget():
                self.hbox_tasks.itemAt(i).widget().hide()
        for i in range(self.hbox_sporadic_tasks.count()):
            if self.hbox_sporadic_tasks.itemAt(i).widget():
                self.hbox_sporadic_tasks.itemAt(i).widget().hide()

    def get_min_utilization(self):
        return self.interval_utilization.getMin()

    def get_max_utilization(self):
        return self.interval_utilization.getMax()

    def generate(self):
        if self.comboGenerator.currentIndex() == 0:
            n = self.get_nb_tasks()
            u = StaffordRandFixedSum(n, self.get_utilization(), 1)
        elif self.comboGenerator.currentIndex() == 1:
            n = self.get_nb_tasks()
            u = UUniFastDiscard(n, self.get_utilization(), 1)
        else:
            u = gen_kato_utilizations(1, self.get_min_utilization(),
                                      self.get_max_utilization(),
                                      self.get_utilization())
            n = len(u[0])

        p_types = self.get_periods()
        if p_types[0] == "unif":
            p = gen_periods_uniform(n, 1, p_types[1], p_types[2], p_types[3])
        elif p_types[0] == "lunif":
            p = gen_periods_loguniform(n, 1, p_types[1], p_types[2],
                                       p_types[3])
        else:
            p = gen_periods_discrete(n, 1, p_types[1])
        if u and p:
            self.taskset = gen_tasksets(u, p)[0]
            self.accept()
        elif not u:
            QMessageBox.warning(
                self, "Generation failed",
                "Please check the utilization and the number of tasks.")
        else:
            QMessageBox.warning(
                self, "Generation failed",
                "Pleache check the periods.")

    def get_nb_tasks(self):
        return self.spin_tasks.value() + self.spin_sporadic_tasks.value()

    def get_nb_periodic_tasks(self):
        return self.spin_tasks.value()

    def get_nb_sporadic_tasks(self):
        return self.spin_sporadic_tasks.value()

    def get_utilization(self):
        return self.spin_load.value()

    def get_periods(self):
        if self.unif.isChecked():
            return ("unif", self.unif_interval.getMin(),
                    self.unif_interval.getMax(), self.unif_interval.getRound())
        elif self.lunif.isChecked():
            return ("lunif", self.lunif_interval.getMin(),
                    self.lunif_interval.getMax(),
                    self.lunif_interval.getRound())
        else:
            return ("discrete", map(float, str(self.periods.text()).split()))


if __name__ == "__main__":
    from PyQt4 import QtGui
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = TaskGeneratorDialog(5)
    if ex.exec_():
        print(ex.taskset)
