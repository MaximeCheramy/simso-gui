#!/usr/bin/python
# coding=utf-8

import re

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QTableWidget, QTableWidgetItem, QHeaderView, \
    QAbstractItemView, QMessageBox

from .AddRemoveButtonBar import AddRemoveButtonBar
from .Tab import Tab
from simso.core.Caches import Cache_LRU


class CachesTab(Tab):
    def __init__(self, parent, configuration):
        Tab.__init__(self, parent, configuration)
        self._caches_table = CachesTable(self, configuration)
        self._add_widget(self._caches_table)
        self._add_widget(CachesButtonBar(self, self._caches_table))

    def update_penalties(self):
        self._caches_table.update_penalties()


class CachesButtonBar(AddRemoveButtonBar):
    def __init__(self, parent, caches_table):
        AddRemoveButtonBar.__init__(self, parent, 'Remove selected cache(s)',
                                    caches_table.remove_selected_caches,
                                    'Add cache', caches_table.add_cache)


class CachesTable(QTableWidget):
    def __init__(self, parent, configuration):
        self._ignore_cell_changed = False
        self._manual_change = True
        self._configuration = configuration
        self._caches_list = configuration.caches_list
        QTableWidget.__init__(self, len(self._caches_list), 5, parent)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.setHorizontalHeaderLabels(["id", "Name", "Size", 'Access Time',
                                        "Miss penalty"])
        self.setVerticalHeaderLabels([""])
        self.verticalHeader().hide()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        curRow = 0
        for cache in self._caches_list:
            self._add_cache_to_table(curRow, cache)
            curRow += 1

        self.cellChanged.connect(self._cell_changed)

    def _add_cache_to_table(self, row, cache):
        self._ignore_cell_changed = True
        self.setItem(row, 0, QTableWidgetItem(str(cache.identifier)))
        self.item(row, 0).setTextAlignment(Qt.AlignCenter)
        self.setItem(row, 1, QTableWidgetItem(str(cache.name)))
        self.setItem(row, 2, QTableWidgetItem(str(cache.size)))
        self.item(row, 2).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, 3, QTableWidgetItem(str(cache.access_time)))
        self.item(row, 3).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        penalty_item = QTableWidgetItem(str(cache.penalty))
        penalty_item.setFlags(penalty_item.flags() ^ (Qt.ItemIsEditable | Qt.ItemIsEnabled))
        self.setItem(row, 4, penalty_item)
        self.item(row, 4).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._ignore_cell_changed = False

    def _cell_changed(self, row, col):
        if self._ignore_cell_changed:
            return
        if not self._manual_change:
            self._manual_change = True
            return

        cache = self._caches_list[row]

        if col == 0:
            old_value = str(cache.identifier)
        elif col == 1:
            old_value = cache.name
        elif col == 2:
            old_value = str(cache.size)
        elif col == 3:
            old_value = str(cache.access_time)

        try:
            if col == 0:
                identifier = int(self.item(row, col).text())
                cache.identifier = identifier
            elif col == 1:
                name = str(self.item(row, col).text()).strip()
                assert re.match('^[a-zA-Z][a-zA-Z0-9_-]+$', name)
                cache.name = name
            elif col == 2:
                size = int(self.item(row, col).text())
                assert size >= 0
                cache.size = size
            elif col == 3:
                access_time = int(self.item(row, col).text())
                assert access_time >= 0
                cache.access_time = access_time
                self._configuration.calc_penalty_cache()
                self.update_penalties()

            self._configuration.conf_changed()
        except (ValueError, AssertionError):
            self._manual_change = False
            self.item(row, col).setText(old_value)

    def update_penalties(self):
        for index, cache in enumerate(self._caches_list):
            self.item(index, 4).setText(str(cache.penalty))

    def _is_used(self, cache):
        for proc in self._configuration.proc_info_list:
            if cache in proc.caches:
                return True
        return False

    def _remove_cache(self, cache):
        for proc in self._configuration.proc_info_list:
            try:
                proc.caches.remove(cache)
            except ValueError:
                pass

    def keyPressEvent(self, event):
        QTableWidget.keyPressEvent(self, event)
        if event.key() == Qt.Key_Delete:
            self.remove_selected_caches()

    def remove_selected_caches(self):
        to_delete = sorted(set([x.row() for x in self.selectedIndexes()]), key=lambda x: -x)
        for index in to_delete:
            if self._is_used(self._caches_list[index]):
                reply = QMessageBox.question(
                    self, "Confirmation", "This cache is currently used, are "
                    "you sure you want to remove it?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self._remove_cache(self._caches_list[index])
                    self._configuration.calc_penalty_cache()
                else:
                    continue
            del self._caches_list[index]
            self.removeRow(index)
            self._configuration.conf_changed()

    def add_cache(self):
        row = self.rowCount()

        identifier = 1
        while identifier in [x.identifier for x in self._caches_list]:
            identifier += 1

        name = "Cache" + str(identifier)

        cache = Cache_LRU(name, identifier, 0, 0, 0)
        self._caches_list.append(cache)
        self.insertRow(row)
        self._add_cache_to_table(row, cache)

        self._configuration.conf_changed()
