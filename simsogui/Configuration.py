from PyQt4.QtCore import QObject, pyqtSignal

import simso.configuration as conf


class Configuration(QObject, conf.Configuration):
    """Wrapper for configuration"""

    configurationChanged = pyqtSignal()
    configurationSaved = pyqtSignal()

    def __init__(self, filename=None):
        QObject.__init__(self)
        conf.Configuration.__init__(self, filename)
        self._saved = True

    def save(self, simulation_file=None):
        conf.Configuration.save(self, simulation_file)
        self._saved = True
        self.configurationSaved.emit()

    def is_saved(self):
        return self._saved

    def conf_changed(self):
        self._saved = False
        self.configurationChanged.emit()
