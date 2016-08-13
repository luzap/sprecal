# TODO Add beginning docstring + Sphinx ready

import os
import sys
import random
import datetime
from datetime import timedelta

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QCalendarWidget, QMenu, QSystemTrayIcon

import settings
from database import DbInterface


# TODO Write docstring
class MainWindow(QMainWindow):
    def __init__(self, db):
        super(MainWindow, self).__init__()

        self.date_selected = datetime.datetime.now().date()  # For internal settings
        self.db = db  # Each component that writes to the database has the same instance

        # Checks for tasks from the previous day, and transfers them over
        old_tasks = self.db.get_data(self.date_selected - timedelta(days=1))
        if len(old_tasks) != 0:
            for item in old_tasks:
                self.db.change_task(item[0], self.date_selected, item[-1])

        # Research does not outline any optimal intervals, but these work as well as any
        self.delta_time = [timedelta(days=1), timedelta(days=2), timedelta(days=7), timedelta(days=30),
                           timedelta(days=90), timedelta(days=180), timedelta(days=380)]
        self.icon = QIcon(os.path.join(os.path.curdir, "icon.png"))  # Icon can be custom. Persistent throughout

        # QTimer for reminders. Moved from function since it's unnecessary to call multiple times
        self.timer = QTimer(self)  # If QTimer called with parent=None, it quits after first interval
        self.timer.timeout.connect(self.display_message)
        self.timer.start(60000 * int(settings.load_setting("time", "interval")))

        self.setWindowTitle("Sprecal")  # Hard-coded program title
        self.setFixedSize(320, 520)  # These dimensions currently suffice, but could be played around with
        self.setWindowIcon(self.icon)
        self.setFocusPolicy(QtCore.Qt.TabFocus)

        # Main widget required to create a QMainWindow object, even if widget is never referenced
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Layouts
        self.horizontal_layout = QtWidgets.QHBoxLayout(self.central_widget)  # Fits grid layout to window
        self.grid_layout = QtWidgets.QGridLayout()  # Handles layout of widgets
        self.horizontal_layout.addLayout(self.grid_layout)

        # Add button, top left
        self.add_task = QtWidgets.QPushButton(self.central_widget)
        self.add_task.setText("Add task")
        self.add_task.clicked.connect(self.make_task_dialog)
        self.add_task.setShortcut(QKeySequence.New)
        self.add_task.setToolTip("Add a new task")
        self.grid_layout.addWidget(self.add_task, 0, 0, 1, 1)

        # Delete button, top right
        self.delete_task = QtWidgets.QPushButton(self.central_widget)
        self.delete_task.setText("Delete task")
        self.grid_layout.addWidget(self.delete_task, 0, 1, 1, 1)
        self.delete_task.clicked.connect(self.delete_selected_task)
        self.delete_task.setShortcut(QKeySequence.Delete)
        self.delete_task.setToolTip("Delete selected task")

        # TODO Make custom calendar widget
        # TODO Write comment
        self.calendar = QCalendarWidget(self.central_widget)
        self.calendar.setGridVisible(True)
        self.grid_layout.addWidget(self.calendar, 1, 0, 1, 2)
        self.calendar.clicked.connect(self.change_date)

        # Indicator of current day for QTableView
        self.label = QtWidgets.QLabel(self.central_widget)
        self.label.setText("The tasks for {}".format(self.calendar.selectedDate().toPyDate()))
        self.grid_layout.addWidget(self.label, 2, 0, 1, 2)

        # Display of data
        # Uses default AbstractItemView for data display (custom structure not needed)
        self.table = QtWidgets.QTableWidget(self.central_widget)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.grid_layout.addWidget(self.table, 3, 0, 1, 2)

        # Mark complete button, bottom right
        self.mark_complete = QtWidgets.QPushButton(self.central_widget)
        self.mark_complete.setText("Mark complete")
        self.mark_complete.setShortcut(QKeySequence("Ctrl+C"))
        self.grid_layout.addWidget(self.mark_complete, 4, 1, 1, 1)
        self.mark_complete.clicked.connect(self.mark_task_complete)

        # Displays success or error messages
        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # Setup of UI elements
        self.setup_table()
        self.system_tray()
        self.show()

    @QtCore.pyqtSlot()
    def setup_table(self, date=datetime.datetime.now().date()):
        """Call to update data in QTableWidget."""
        self.table.clearContents()  # Removes content, leaving column headers

        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # Visual selection of entire row
        header = self.db.get_columns()  # Number of columns and headers are constant, so not crucial
        data = self.db.get_data(date)  # List of tuples representing all of the data for that day

        # Table setup
        self.table.setColumnCount(len(header))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(header)

        # Hides columns for aesthetic purposes
        self.table.setColumnHidden(header.index("id"), True)
        self.table.setColumnHidden(header.index("date"), True)

        # If there is data, traverses the data "matrix"
        if len(data) > 0:
            for row in range(len(data)):
                for column in range(len(header)):
                    self.table.setItem(row, column, QtWidgets.QTableWidgetItem(str(data[row][column])))
        else:
            self.label.setText("This day has no tasks!")

    def system_tray(self):
        """Handle the system tray icon and associated slots."""
        self.tray_icon = QSystemTrayIcon(QIcon())
        self.tray_icon.setIcon(self.icon)

        # Menu and menu actions are not tied to class, since they only need to be referenced once
        menu = QMenu()
        open_window = menu.addAction("Open window")
        exit_entry = menu.addAction("Exit")
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("Sprecal")  # For easy system tray identification in case of custom icon

        open_window.triggered.connect(self.show_main)
        exit_entry.triggered.connect(QApplication.quit)  # Only way to exit the application
        self.tray_icon.activated.connect(self.show_main)  # Clicking on the systray icon shows MainWindow
        self.tray_icon.show()


    @QtCore.pyqtSlot()
    def display_message(self):
        """Take amount of tasks for the day, displays system notification."""
        number = len(self.db.get_data(datetime.datetime.now().date()))
        if number > 0:
            self.tray_icon.showMessage("Reminder", "{} task{}left to go!".format(number, (number > 1) * "s" + " "))
        else:
            self.tray_icon.showMessage("Congratulations", "You're done for the day!")

    @QtCore.pyqtSlot()
    def change_date(self):
        """Update UI upon date selection."""
        self.date_selected = self.calendar.selectedDate().toPyDate()
        self.label.setText("The tasks for {}".format(self.calendar.selectedDate().toPyDate()))
        self.setup_table(date=self.calendar.selectedDate().toPyDate())

    @QtCore.pyqtSlot()
    def make_task_dialog(self):
        """Add new task to database"""
        result = TaskDialog(self.db, self.date_selected).exec_()
        if result == 0:
            self.statusbar.showMessage("No new task added!")
        else:
            self.statusbar.showMessage("Added task {}".format(self.db.get_last()))
            self.change_date()

    @QtCore.pyqtSlot()
    def delete_selected_task(self):
        """Remove selected task from database"""
        try:
            row_num = self.table.currentItem().row()
            if row_num is not None:  # If no task is selected in the QTableWidget, row_num is None
                item = self.table.item(row_num, 0).text()
                self.db.delete_task(item)
                self.setup_table()
        except (AttributeError):
            self.label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def mark_task_complete(self):
        """Update counter and date of selected task."""
        try:  # Initially checked for None, but that was problematic
            row_num = self.table.currentItem().row()
            task_id = self.table.item(row_num, 0).text()
            counter = int(self.table.item(row_num, 4).text())
            if counter <= len(self.delta_time):
                new_date = self.date_selected + self.delta_time[counter]
            else:  #
                new_date = self.date_selected + datetime.timedelta(days=(round(random.random()) * 1000))
            self.db.change_task(task_id, new_date, counter + 1)
            self.setup_table()
        except (TypeError, AttributeError):
            self.label.setText("No Task selected! Please try again.")

    @QtCore.pyqtSlot()
    def show_main(self):
        """Show main window."""
        self.show()

    # TODO Show info message that this only minimizes it to tray, and doesn't close
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
    db = DbInterface(settings.load_setting("db options", "name") + ".db")  # Allows for custom database name in future
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Allows for the hiding of the MainWindow (?) without closing the application
    ex = MainWindow(db)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
