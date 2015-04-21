from PyQt4.QtCore import QThread, SIGNAL, QObject
from PyQt4.QtGui import QMdiArea, QProgressDialog, QMessageBox

import os.path
import sys
import traceback

from simso.core import Model

from .Gantt import create_gantt_window
from .ModelWindow import ModelWindow
from .results import ResultsWindow
from .Configuration import Configuration


class RunSimulation(QThread):
    class Console(object):
        def __init__(self):
            self.log = []

        def write(self, data):
            self.log.append(data)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self._finished = False
        self._error = False
        self._console = RunSimulation.Console()

    @property
    def error(self):
        return self._error

    def get_error(self):
        return self._console.log

    def set_model(self, model):
        self._model = model

    def updateProgressBar(self, value):
        self.emit(SIGNAL("updateProgressBar"), value)

    def run(self):
        try:
            self._model.run_model()
        except:
            self._error = True
            traceback.print_exc(file=self._console)
            traceback.print_exc(file=sys.stderr)
        self._finished = True


class SimulationTab(QMdiArea):
    def __init__(self, simulation_window, simulation_file=None, parent=None):
        QMdiArea.__init__(self, parent)

        if simulation_file:
            self._configuration = Configuration(simulation_file)
        else:
            self._configuration = Configuration()

        self.worker = None
        self._model = None
        self._gantt = None
        self._logs = None
        self._editor = None
        self._metrics_window = None
        self._model_window = None
        self._progress_bar = None
        self._documentation = None
        self._simulation_window = simulation_window

        self._configuration.configurationChanged.connect(
            self.configuration_changed)
        self._configuration.configurationSaved.connect(
            self.configuration_saved)

        self.showModelWindow()

    @property
    def simulation_file(self):
        return self._configuration.simulation_file

    @property
    def configuration(self):
        return self._configuration

    def configuration_saved(self):
        simulation_file = self._configuration.simulation_file
        self._simulation_window.setTabText(self,
                                           os.path.split(simulation_file)[1])
        self._simulation_window.updateMenus()

    def configuration_changed(self):
        simulation_file = self._configuration.simulation_file
        if not simulation_file:
            simulation_file = "Unsaved"
        self._simulation_window.setTabText(
            self, '* ' + os.path.split(simulation_file)[1])

    def showGantt(self):
        if not self._gantt and self._model:
            self._gantt = create_gantt_window(self._model)
            if self._gantt:
                self.addSubWindow(self._gantt)
        if self._gantt:
            self._gantt.parent().show()

    def showModelWindow(self):
        if not self._model_window and self._configuration:
            self._model_window = ModelWindow(self._configuration, self)
            self.addSubWindow(self._model_window)
        if self._model_window:
            self._model_window.parent().show()

    def showResults(self):
        if not self._metrics_window and self._model and self._model.results:
            self._metrics_window = ResultsWindow(self._model.results)
            self.addSubWindow(self._metrics_window)
        if self._metrics_window:
            self._metrics_window.parent().show()

    def _reinit_simu(self):
        self._model = None
        if self._gantt:
            self.removeSubWindow(self._gantt.parent())
        if self._logs:
            self.removeSubWindow(self._logs.parent())
        if self._metrics_window:
            self.removeSubWindow(self._metrics_window.parent())

        self._gantt = None
        self._logs = None
        self._metrics_window = None

    def save(self):
        self._configuration.save()

    def save_as(self, filename):
        self._configuration.save(filename)

    def run(self):
        if self._configuration:
            try:
                self._configuration.check_all()

                self._reinit_simu()

                self._progress_bar = QProgressDialog("Simulating...", "Abort",
                                                     0, 100)
                self._progress_bar.canceled.connect(self.abort)
                self._progress_bar.show()

                self.worker = RunSimulation()
                self._model = Model(self._configuration,
                                    callback=self.worker.updateProgressBar)
                self.worker.set_model(self._model)

                self.worker.finished.connect(self.runFinished)
                self.worker.start()
                QObject.connect(self.worker, SIGNAL("updateProgressBar"),
                                self.updateProgressBar)

            except Exception as msg:
                QMessageBox.warning(self, "Configuration error", str(msg))
                self._reinit_simu()
                self.runFinished()

    def abort(self):
        self._progress_bar = None
        self._model.stopSimulation()
        self._simulation_window.updateMenus()
        # Ultimate killer.
        self.worker.terminate()

    def runFinished(self):
        if self._progress_bar:
            self._progress_bar.hide()
        self._simulation_window.updateMenus()
        self.showResults()
        if self.worker and self.worker.error:
            QMessageBox.critical(None, "Exception during simulation",
                                 ''.join(self.worker.get_error()),
                                 QMessageBox.Ok | QMessageBox.Default,
                                 QMessageBox.NoButton)

    def updateProgressBar(self, value):
        if self._progress_bar:
            duration = self._configuration.duration
            p = 100.0 * value / duration
            self._progress_bar.setValue(int(p))

    def close(self):
        if not self._configuration.is_saved():
            ret = QMessageBox.warning(
                self, "Close without saving?", "The configuration of the "
                "simulation is not saved and the modifications will be lost.\n"
                "Are you sure you want to quit?",
                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if ret == QMessageBox.Cancel:
                return False
        return True
