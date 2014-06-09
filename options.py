# Copyright (C) 2010  Alex Yatskov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from PyQt4 import QtGui, QtCore

from copy import deepcopy

from image import ImageFlags
from ui.options_ui import Ui_DialogOptions


class DialogOptions(QtGui.QDialog, Ui_DialogOptions):
    def __init__(self, parent, book):
        QtGui.QDialog.__init__(self, parent)
        self.book = book
        self.setupUi(self)
        self.connect(self, QtCore.SIGNAL('accepted()'), self.onAccept)
        self.moveOptionsToDialog()

    def onAccept(self):
        self.moveDialogToOptions()

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Slot called when the "Save Defaults" button is clicked.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def save_defaults(self):
        do_save = QtGui.QMessageBox.question(self,
            "Save Defaults",
            "Are you sure you want to save the current settings as default for all books?",
            QtGui.QMessageBox.No | QtGui.QMessageBox.Yes,
            QtGui.QMessageBox.No)

        if do_save == QtGui.QMessageBox.Yes:
            # We need to send our currently set options out to a book object and have it save
            # them out to file. However, we don't want to *apply* the selected options
            # unless they click OK, so we make a copy of the book, apply the settings, output
            # to file, and then restore the book object to what it was when the dialog loaded.
            temp_book = self.book

            # Because the title isn't stored in the defaults, we want to keep track of
            # if the user made any changes to the title before clicking this, and
            # then restore those changes, rather than what's in the book object.
            temp_title = self.lineEditTitle.text()

            self.book = deepcopy(self.book)
            self.moveDialogToOptions()
            self.book.save_defaults()
            self.book = temp_book

            # Restore the title to whatever it was when they clicked the button.
            self.lineEditTitle.setText(temp_title)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Slot called when the "Restore Defaults" button is clicked.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def restore_defaults(self):
        do_restore = QtGui.QMessageBox.question(self,
          "Restore Defaults",
          "Are you sure you want to restore the default settings for this book?",
          QtGui.QMessageBox.No | QtGui.QMessageBox.Yes,
          QtGui.QMessageBox.No)

        if do_restore == QtGui.QMessageBox.Yes:
            # Similar to what we do for the save button, we copy the existing book object
            # before modifying it so we can load the settings and apply them here.
            temp_book = self.book

            # Because the title isn't stored in the defaults, we want to keep track of
            # if the user made any changes to the title before clicking this, and
            # then restore those changes, rather than what's in the book object.
            temp_title = self.lineEditTitle.text()

            self.book = deepcopy(self.book)
            self.book.load_defaults()
            self.moveOptionsToDialog()
            self.book = temp_book

            # Restore the title to whatever it was when they clicked the button.
            self.lineEditTitle.setText(temp_title)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Slot called when the CBZ checkbox is changed.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def cbz_changed(self, value):
        if value == QtCore.Qt.Checked:
            self.checkboxOverwrite.setDisabled(True)
        else:
            self.checkboxOverwrite.setDisabled(False)

            
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Slot called when the EPUB checkbox is changed.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def epub_changed(self, value):
        if value == QtCore.Qt.Checked:
            self.checkboxOverwrite.setDisabled(True)
        else:
            self.checkboxOverwrite.setDisabled(False)
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Slot called when the Orient checkbox is changed.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def orient_changed(self, value):
        if value == QtCore.Qt.Checked:
            self.checkboxSplit.setChecked(QtCore.Qt.Unchecked)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Slot called when the Split checkbox is changed.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def split_changed(self, value):
        if value == QtCore.Qt.Unchecked:
            self.checkboxRightToLeft.setDisabled(True)
        else:
            self.checkboxOrient.setChecked(QtCore.Qt.Unchecked)
            self.checkboxRightToLeft.setDisabled(False)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Takes the options stored in a book object and changes the UI
    # objects to reflect those options.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def moveOptionsToDialog(self):
        self.lineEditTitle.setText(self.book.title or 'Untitled')
        self.comboBoxDevice.setCurrentIndex(max(self.comboBoxDevice.findText(self.book.device), 0))
        self.checkboxOverwrite.setChecked(QtCore.Qt.Checked if self.book.overwrite else QtCore.Qt.Unchecked)
        self.checkboxCBZ.setChecked(QtCore.Qt.Checked if self.book.cbz else QtCore.Qt.Unchecked)
        self.checkboxEpub.setChecked(QtCore.Qt.Checked if self.book.epub else QtCore.Qt.Unchecked)
        self.checkboxOrient.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.Orient else QtCore.Qt.Unchecked)
        self.checkboxSplit.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.Split else QtCore.Qt.Unchecked)
        self.checkboxShrink.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.Shrink else QtCore.Qt.Unchecked)
        self.checkboxEnlarge.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.Enlarge else QtCore.Qt.Unchecked)
        self.checkboxQuantize.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.Quantize else QtCore.Qt.Unchecked)
        self.checkboxFrame.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.Frame else QtCore.Qt.Unchecked)
        self.checkboxRightToLeft.setChecked(QtCore.Qt.Checked if self.book.imageFlags & ImageFlags.RightToLeft else QtCore.Qt.Unchecked)
        
        # No need for the option if splitting is disabled. And it won't signal
        # the "changed" event if it starts out disabled.
        if self.checkboxSplit.checkState() == QtCore.Qt.Unchecked:
            self.checkboxRightToLeft.setDisabled(True)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Stores the selected options in the book object.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def moveDialogToOptions(self):
        title = self.lineEditTitle.text()
        device = self.comboBoxDevice.itemText(self.comboBoxDevice.currentIndex())
        overwrite = self.checkboxOverwrite.checkState() == QtCore.Qt.Checked
        cbz = self.checkboxCBZ.checkState() == QtCore.Qt.Checked
        epub = self.checkboxEpub.checkState() == QtCore.Qt.Checked

        imageFlags = 0
        if self.checkboxOrient.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.Orient
        if self.checkboxSplit.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.Split
        if self.checkboxShrink.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.Shrink
        if self.checkboxEnlarge.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.Enlarge
        if self.checkboxQuantize.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.Quantize
        if self.checkboxFrame.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.Frame
        if self.checkboxRightToLeft.checkState() == QtCore.Qt.Checked:
            imageFlags |= ImageFlags.RightToLeft

        modified = (
            self.book.title != title or
            self.book.device != device or
            self.book.overwrite != overwrite or
            self.book.imageFlags != imageFlags or
            self.book.cbz != cbz or
            self.book.epub != epub
        )

        if modified:
            self.book.modified = True
            self.book.title = title
            self.book.device = device
            self.book.overwrite = overwrite
            self.book.imageFlags = imageFlags
            self.book.cbz = cbz
            self.book.epub = epub
