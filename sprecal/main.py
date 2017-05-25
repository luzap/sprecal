# TODO Change the dialog window so that it does not require the database to be passed
# TODO Work on custom calendar widget that either highlights days
# TODO Change the __populate_table method so that it does not require the date as a parameter

import os
import sys
import random
import datetime
from datetime import timedelta

import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui

import settings
from database import DbInterface


class TABLE:
    """Basic enum that corresponds to the database columns."""
    TASK_ID = 0
    NAME = 1
    DESC = 2
    DATE = 3
    COUNTER = 4


class SprecalWindow(QtWidgets.QMainWindow):
    """Main application window. Handles user interaction with the calendar and delegates both the creation 
    and manipulation of tasks to the database interface and dialog windows."""

    # Research outlines only the general periods needed for the topic to sink in
    delta_time = [timedelta(days=day) for day in [1, 2, 7, 30, 90, 180, 380]]

    def __init__(self):
        super(SprecalWindow, self).__init__()

        self.date_selected = datetime.datetime.now().date()  # For internal settings
        self._db = DbInterface(settings.load_setting("db options", "name") + ".sqlite")

        # Checks for tasks from the previous day, and transfers them over
        old_tasks = self._db.get_data(self.date_selected - timedelta(days=1))
        if len(old_tasks):
            for item in old_tasks:
                self._db.change_task(item[0], self.date_selected, item[-1])

        # NB: If QTimer is instantiated with parent=None, it quits after first interval. Is this because there are
        # no more references to it?
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.__display_message)
        self._timer.start(60000 * int(settings.load_setting("time", "interval")))

        self.setWindowTitle("Sprecal")
        self.setFixedSize(340, 600)

        self._icon = QtGui.QIcon(os.path.join(os.path.curdir, "icon.png"))
        self.setWindowIcon(self._icon)

        # Determines how widgets accept keyboard focus. Read more here:
        # https://doc.qt.io/qt-4.8/qwidget.html#focusPolicy-prop
        self.setFocusPolicy(QtCore.Qt.TabFocus)

        # Main widget required to create a QMainWindow object, even if widget is never referenced
        self._central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self._central_widget)

        self._horizontal_layout = QtWidgets.QHBoxLayout(self._central_widget)  # Fits grid layout to window
        self._grid_layout = QtWidgets.QGridLayout()  # Handles layout of widgets
        self._horizontal_layout.addLayout(self._grid_layout)

        self._add_task_button = QtWidgets.QPushButton(self._central_widget)
        self._add_task_button.setText("Add task")
        self._add_task_button.clicked.connect(self.make_task_dialog)
        self._add_task_button.setToolTip("Add a new task")
        self._grid_layout.addWidget(self._add_task_button, 0, 0, 1, 1)

        self._delete_task_button = QtWidgets.QPushButton(self._central_widget)
        self._delete_task_button.setText("Delete task")
        self._grid_layout.addWidget(self._delete_task_button, 0, 1, 1, 1)
        self._delete_task_button.clicked.connect(self.delete_selected_task)
        self._delete_task_button.setToolTip("Delete selected task")

        self._calendar = QtWidgets.QCalendarWidget(self._central_widget)
        self._calendar.setGridVisible(True)
        self._grid_layout.addWidget(self._calendar, 1, 0, 1, 2)
        self._calendar.clicked.connect(self.change_date)

        self._table_label = QtWidgets.QLabel(self._central_widget)
        self._table_label.setText("The tasks for {}".format(self._calendar.selectedDate().toPyDate()))
        self._grid_layout.addWidget(self._table_label, 2, 0, 1, 2)

        self._table = QtWidgets.QTableWidget(self._central_widget)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._grid_layout.addWidget(self._table, 3, 0, 1, 2)

        self.mark_complete = QtWidgets.QPushButton(self._central_widget)
        self.mark_complete.setText("Mark complete")
        self._grid_layout.addWidget(self.mark_complete, 4, 1, 1, 1)
        self.mark_complete.clicked.connect(self.mark_task_complete)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # Setup of data in UI elements
        self.__populate_table()
        self.__sys_tray()
        self.show()

    def __populate_table(self, date=datetime.datetime.now().date()):
        """Call to update data in QTableWidget."""
        self._table.clearContents()  # Removes content, leaving column headers

        # Visually select the entire row
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        header = self._db.get_columns()  # Number of columns and headers are constant, so not crucial
        data = self._db.get_data(date)  # List of tuples representing all of the data for that day

        # Table setup
        self._table.setColumnCount(len(header))
        self._table.setRowCount(len(data))
        self._table.setHorizontalHeaderLabels(header)

        # Hides columns for aesthetic purposes
        self._table.setColumnHidden(header.index("id"), True)
        self._table.setColumnHidden(header.index("date"), True)

        # If there is data, traverses the data "matrix". Might become bottleneck if there are enough entries, so be
        # careful
        if len(data):
            for row in range(len(data)):
                for column in range(len(header)):
                    self._table.setItem(row, column, QtWidgets.QTableWidgetItem(str(data[row][column])))
        else:
            self._table_label.setText("This day has no tasks!")

    def __sys_tray(self):
        """Handle the system tray icon and associated slots."""
        self._tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon())
        self._tray_icon.setIcon(self._icon)

        # Menu and menu actions are not tied to class, since they only need to be referenced once
        _menu = QtWidgets.QMenu()
        _open_window = _menu.addAction("Open window")
        _exit_entry = _menu.addAction("Exit")
        self._tray_icon.setContextMenu(_menu)
        self._tray_icon.setToolTip("Sprecal")  # For easy system tray identification in case of custom icon

        _open_window.triggered.connect(self.show_main)
        _exit_entry.triggered.connect(PyQt5.QtWidgets.QApplication.quit)  # Only way to exit the application
        self._tray_icon.activated.connect(self.show_main)  # Clicking on the systray icon shows MainWindow
        self._tray_icon.show()

    @QtCore.pyqtSlot()
    def __display_message(self):
        """Take amount of tasks for the day, displays system notification."""
        number = len(self._db.get_data(datetime.datetime.now().date()))
        if number:
            self.startTimer()
            self._tray_icon.showMessage("Reminder", "{} task{}left to go!".format(number, (number > 1) * "s" + " "))
        else:
            self._tray_icon.showMessage("Congratulations", "You're done for the day!")
            self._timer.stop()

    @QtCore.pyqtSlot()
    def change_date(self):
        """Update UI upon date selection."""
        self.date_selected = self._calendar.selectedDate().toPyDate()
        self._table_label.setText("The tasks for {}".format(self._calendar.selectedDate().toPyDate()))
        self.__populate_table(date=self._calendar.selectedDate().toPyDate())

    @QtCore.pyqtSlot()
    def make_task_dialog(self):
        """Add new task to database"""
        result = TaskDialog(self._db, self.date_selected).exec_()
        print(result)
        if result == 0:
            self.statusbar.showMessage("No new task added!")
        else:
            self.statusbar.showMessage("Added task {}".format(self._db.get_last()))
            self.change_date()

    @QtCore.pyqtSlot()
    def delete_selected_task(self):
        """Remove selected task from database"""
        row_num = self._table.currentItem().row()

        # If no task is selected in the QTableWidget, row_num is None
        if row_num is not None:
            self._db.delete_task(self._table.item(row_num, 0).text())
            self.__populate_table(date=self.date_selected)
        else:
            self._table_label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def mark_task_complete(self):
        """Update counter and date of selected task."""
        try:  # Initially checked for None, but that was problematic
            row_num = self._table.currentItem().row()
            task_id = self._table.item(row_num, TABLE.TASK_ID).text()
            counter = int(self._table.item(row_num, TABLE.COUNTER).text())
            if counter <= len(self.delta_time):
                new_date = self.date_selected + self.delta_time[counter]
            else:
                # Even if first several reviews are done, that does not mean the individual can rest easy.
                # The next review should occur sometime in the next three years, to make sure it sticks,
                # thought it is mostly said that at the six month mark, things are pretty much embedded
                # in memory
                new_date = self.date_selected + datetime.timedelta(days=(round(random.random()) * 1000))
            self._db.change_task(task_id, new_date, counter + 1)
            self.__populate_table()
        except (TypeError, AttributeError):
            self._table_label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def show_main(self):
        """Show main window."""
        self.show()

    # TODO Show info message that this only minimizes it to tray, and doesn't close
    # TODO Allow this to be optional
    def closeEvent(self, event):
        """Hide main window. Overrides default closeEvent"""
        self.hide()


# TODO Add docstring
# TODO Arrange auto-generated code nicely
# TODO Add comments
class TaskDialog(QtWidgets.QDialog):
    def __init__(self, db, date_selected, parent=None):
        super(TaskDialog, self).__init__(parent)

        self.date_selected = date_selected  # Date of the selected day for task creation
        self.db = db  # Reference to the database interface

        self.setWindowTitle("Add task")
        self.setFixedSize(220, 100)

        # Main widget is necessary for all windows?
        self.widget = QtWidgets.QWidget(self)

        self.widget.setGeometry(QtCore.QRect(9, 11, 194, 77))  # ?
        self.grid_layout = QtWidgets.QGridLayout(self.widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)  # ?

        # Label that accompanies the QLineEdit
        self.title_label = QtWidgets.QLabel(self)
        self.title_label.setText("Task name")
        self.grid_layout.addWidget(self.title_label, 0, 0, 1, 1)

        # QLineEdit for the title of the task
        self.title_line_edit = QtWidgets.QLineEdit(self.widget)
        self.grid_layout.addWidget(self.title_line_edit, 0, 1, 1, 1)

        # Label that accompanies the following QLineEdit (maybe switch to QTextEdit?)
        self.description_label = QtWidgets.QLabel(self.widget)
        self.description_label.setText("Description")
        self.grid_layout.addWidget(self.description_label, 1, 0, 1, 1)

        # Allows for the adding of a task description
        self.description_line_edit = QtWidgets.QLineEdit(self.widget)
        self.grid_layout.addWidget(self.description_line_edit, 1, 1, 1, 1)

        self.push_button = QtWidgets.QPushButton(self.widget)
        self.push_button.setText("Save")
        self.push_button.clicked.connect(self.add_task)
        self.grid_layout.addWidget(self.push_button, 2, 0, 1, 2)

        self.show()

    @QtCore.pyqtSlot()
    def add_task(self):
        """Connect to database, add task row and quit dialog."""
        # Column values, in order, are: id (auto-increments so not needed), name, description, current date, counter
        data = (None, self.title_line_edit.text(), self.description_line_edit.text(), self.date_selected, 0)
        self.db.make_task(data)
        self.accept()  # Closes the window (hides the dialog)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Allows for the hiding of the MainWindow (?) without closing the application
    ex = SprecalWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
