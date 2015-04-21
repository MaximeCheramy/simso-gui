#!/usr/bin/python
# coding=utf-8

from PyQt4.QtWebKit import QWebView
from PyQt4.QtCore import Qt, QUrl, QSettings, QFileInfo
from PyQt4.QtGui import QMainWindow, QMenu, QAction, QStyle, \
    QToolBar, QFileDialog, qApp, QTabWidget, QDockWidget, QMessageBox

import os.path
import simso

from .SimulationTab import SimulationTab


class SimulatorWindow(QMainWindow):
    def __init__(self, argv):
        QMainWindow.__init__(self)
        self.setWindowTitle("SimSo: Real-Time Scheduling Simulator")

        # Possible actions:
        style = qApp.style()

        # New
        self._newAction = QAction(
            style.standardIcon(QStyle.SP_FileDialogNewFolder), '&New', None)
        self._newAction.setShortcut(Qt.CTRL + Qt.Key_N)
        self._newAction.triggered.connect(self.fileNew)

        # Open
        self._openAction = QAction(
            style.standardIcon(QStyle.SP_DialogOpenButton), '&Open', None)
        self._openAction.setShortcut(Qt.CTRL + Qt.Key_O)
        self._openAction.triggered.connect(self.fileOpen)

        # Save
        self._saveAction = QAction(
            style.standardIcon(QStyle.SP_DialogSaveButton), '&Save', None)
        self._saveAction.setShortcut(Qt.CTRL + Qt.Key_S)
        self._saveAction.triggered.connect(self.fileSave)

        # Save As
        self._saveAsAction = QAction(
            style.standardIcon(QStyle.SP_DialogSaveButton), 'Save &As', None)
        self._saveAsAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        self._saveAsAction.triggered.connect(self.fileSaveAs)

        # Run
        self._runAction = QAction(
            style.standardIcon(QStyle.SP_MediaPlay), '&Run', None)
        self._runAction.setShortcut(Qt.CTRL + Qt.Key_R)
        self._runAction.triggered.connect(self.fileRun)

        # Show Model data
        self._modelAction = QAction('&Model data', None)
        self._modelAction.setShortcut(Qt.CTRL + Qt.Key_M)
        #self._ganttAction.setCheckable(True)
        self._modelAction.triggered.connect(self.showModelWindow)

        # Show Gantt
        self._ganttAction = QAction('&Gantt', None)
        self._ganttAction.setShortcut(Qt.CTRL + Qt.Key_G)
        self._ganttAction.setEnabled(False)
        #self._ganttAction.setCheckable(True)
        self._ganttAction.triggered.connect(self.showGantt)

        # Show Results
        self._metricsAction = QAction('&Results', None)
        self._metricsAction.setShortcut(Qt.CTRL + Qt.Key_I)
        self._metricsAction.setEnabled(False)
        #self._metricsAction.setCheckable(True)
        self._metricsAction.triggered.connect(self.showResults)

        # Show Doc
        self._docAction = QAction('&Documentation', None)
        self._docAction.triggered.connect(self.showDocumentation)

        self._aboutAction = QAction('&About SimSo', None)
        self._aboutAction.triggered.connect(self.showAbout)

        # Recent files
        self._recentFileActions = []
        for i in range(5):
            act = QAction(self)
            act.setVisible(False)
            act.triggered.connect(self.openRecentFile)
            self._recentFileActions.append(act)

        # File Menu:
        file_menu = QMenu('&File', self)
        file_menu.addAction(self._newAction)
        file_menu.addAction(self._openAction)
        file_menu.addAction(self._saveAction)
        file_menu.addAction(self._saveAsAction)
        file_menu.addAction(self._runAction)
        file_menu.addSeparator()
        for act in self._recentFileActions:
            file_menu.addAction(act)
        file_menu.addSeparator()
        file_menu.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)
        self.updateRecentFileActions()

        # View Menu:
        view_menu = QMenu('&View', self)
        view_menu.addAction(self._modelAction)
        view_menu.addAction(self._ganttAction)
        view_menu.addAction(self._metricsAction)

        # Help Menu:
        help_menu = QMenu('&Help', self)
        help_menu.addAction(self._docAction)
        help_menu.addAction(self._aboutAction)

        # Add menus to menuBar:
        self.menuBar().addMenu(file_menu)
        self.menuBar().addMenu(view_menu)
        self.menuBar().addMenu(help_menu)

        # ToolBar:
        self.toolBar = QToolBar("Main ToolBar")
        self.addToolBar(self.toolBar)
        self.toolBar.addAction(self._newAction)
        self.toolBar.addAction(self._openAction)
        self.toolBar.addAction(self._saveAction)
        self.toolBar.addAction(self._runAction)
        self.toolBar.addAction(self._ganttAction)
        self.toolBar.addAction(self._metricsAction)

        # Tab:
        self.main_tab = QTabWidget()
        self.main_tab.setTabsClosable(True)
        self.main_tab.setMovable(True)
        self.main_tab.tabCloseRequested.connect(self.tabCloseRequested)
        self.main_tab.currentChanged.connect(self.tabChanged)
        self.setCentralWidget(self.main_tab)

        # Init statusBar:
        self.statusBar().showMessage("", 2000)

        self._documentation = None

        if argv:
            for arg in argv:
                try:
                    self.open_file(arg)
                except Exception as e:
                    print(e)
        else:
            self.fileNew()

    def openRecentFile(self):
        try:
            self.open_file(self.sender().data().toString())
        except AttributeError:
            self.open_file(self.sender().data())

    def updateRecentFileActions(self):
        settings = QSettings()
        files = settings.value("recentFileList", defaultValue=[],
                               type='QString')
        for i in range(5):
            if i < len(files):
                text = "&{} {}".format(i + 1, QFileInfo(files[i]).fileName())
                self._recentFileActions[i].setText(text)
                self._recentFileActions[i].setData(files[i])
                self._recentFileActions[i].setVisible(True)
            else:
                self._recentFileActions[i].setVisible(False)

    def setCurrentFile(self, filename):
        filename = QFileInfo(filename).absoluteFilePath()
        settings = QSettings()
        files = settings.value("recentFileList", defaultValue=[],
                               type='QString')

        if filename in files:
            files.remove(filename)
        files.insert(0, filename)
        while len(files) > 5:
            del files[-1]

        settings.setValue("recentFileList", files)
        self.updateRecentFileActions()

    def showAbout(self):
        QMessageBox.about(
            self, "About SimSo",
            "<b>SimSo {} - Simulation of Multiprocessor Scheduling with Overheads</b><br/><br/>"
            "SimSo is a free software developed by Maxime Cheramy (LAAS-CNRS).<br/>"
            "This software is distributed under the <a href='http://www.cecill.info'>CECILL license</a>, "
            "compatible with the GNU GPL.<br/><br/>"
            "Contact: <a href='mailto:maxime.cheramy@laas.fr'>maxime.cheramy@laas.fr</a>".format(simso.__version__)
#            "<br/><hr/><br/>"
#            "The Code Editor, copyright the <a href='http://www.iep-project.org/'>IEP development team</a>, "
#            "was reproduced and integrated into SimSo in respect of the (new) BSD license."
        )

    def showDocumentation(self):
        if self._documentation is None:
            doc = QWebView(self)
            doc.load(QUrl("doc/html/index.html"))
            self._documentation = QDockWidget("Documentation", self)
            self._documentation.setWidget(doc)
            self._documentation.closeEvent = lambda _: self.hide_documentation()

        self.addDockWidget(Qt.LeftDockWidgetArea, self._documentation)

    def showGantt(self):
        self.main_tab.currentWidget().showGantt()

    def showModelWindow(self):
        self.main_tab.currentWidget().showModelWindow()

    def showResults(self):
        self.main_tab.currentWidget().showResults()

    def hide_documentation(self):
        self._documentation = None

    def fileNew(self):
        self.main_tab.addTab(SimulationTab(self), 'Unsaved')

    def fileOpen(self):
        simulation_file = QFileDialog.getOpenFileName(
            filter="*.xml", caption="Open XML simulation file.")
        if simulation_file:
            self.open_file(simulation_file)

    def open_file(self, simulation_file):
        try:
            simulation_file = unicode(simulation_file)
        except NameError:
            pass

        try:
            self.setCurrentFile(simulation_file)
            sim = SimulationTab(self, simulation_file)
            if (self.main_tab.currentWidget()
                    and not self.main_tab.currentWidget().simulation_file
                    and self.main_tab.currentWidget().configuration.is_saved()
                    and self.main_tab.count() == 1):
                self.main_tab.removeTab(0)
            self.main_tab.addTab(sim, os.path.split(simulation_file)[1])
            self.main_tab.setCurrentWidget(sim)
            self.updateMenus()
        except Exception as e:
            QMessageBox.critical(
                self, "Could not open file",
                "The file {} could not be opened.".format(simulation_file))
            print(e)

    def fileSave(self):
        try:
            self.main_tab.currentWidget().save()
        except:
            self.fileSaveAs()

    def fileSaveAs(self):
        simulation_file = QFileDialog.getSaveFileName(
            filter="*.xml", caption="Save XML simulation file.")
        try:
            simulation_file = unicode(simulation_file)
        except NameError:
            pass
        if simulation_file:
            if simulation_file[-4:] != '.xml':
                simulation_file += '.xml'
            self.main_tab.currentWidget().save_as(simulation_file)

    def fileRun(self):
        self._runAction.setEnabled(False)
        self.main_tab.currentWidget().run()

    def fileQuit(self):
        self.close()

    def setTabText(self, tab, text):
        self.main_tab.setTabText(self.main_tab.indexOf(tab), text)

    def tabChanged(self, index):
        self.updateMenus()

    def tabCloseRequested(self, index):
        if self.main_tab.widget(index).close():
            self.main_tab.removeTab(index)
            self.updateMenus()

    def closeEvent(self, event):
        while self.main_tab.count() > 0:
            if self.main_tab.widget(0).close():
                self.main_tab.removeTab(0)
            else:
                event.ignore()
                return

    def updateMenus(self):
        if self.main_tab.count() > 0:
            widget = self.main_tab.currentWidget()
            self._runAction.setEnabled(True)
            self._modelAction.setEnabled(True)
            self._ganttAction.setEnabled(widget._model is not None)
            self._metricsAction.setEnabled(widget._model is not None)
        else:
            self._runAction.setEnabled(False)
            self._modelAction.setEnabled(False)
            self._ganttAction.setEnabled(False)
            self._metricsAction.setEnabled(False)
