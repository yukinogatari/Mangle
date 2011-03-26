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


import os
from PyQt4 import QtGui, QtCore, QtXml

import image
from image import ImageFlags
from about import DialogAbout
from options import DialogOptions
from convert import DialogConvert
from ui.book_ui import Ui_MainWindowBook

class Book:
    DefaultDevice = 'Kindle 3'
    DefaultOverwrite = True
    DefaultCBZ = False
    DefaultImageFlags = ImageFlags.Orient | ImageFlags.Shrink | ImageFlags.Quantize
    DefaultsXML = 'defaults.xml'


    def __init__(self):
        self.images = []
        self.filename = None
        self.modified = False
        self.title = None
        self.load_defaults(Book.DefaultsXML)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Saves the current settings as the defaults.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def save_defaults(self, filename = DefaultsXML):
        document = QtXml.QDomDocument()

        root = document.createElement('defaults')
        document.appendChild(root)

        root.setAttribute('overwrite', 'true' if self.overwrite else 'false')
        root.setAttribute('device', self.device)
        root.setAttribute('orientImages', 'true' if self.imageFlags & ImageFlags.Orient else 'false')
        root.setAttribute('shrinkImages', 'true' if self.imageFlags & ImageFlags.Shrink else 'false')
        root.setAttribute('frameImages', 'true' if self.imageFlags & ImageFlags.Frame else 'false')
        root.setAttribute('ditherImages', 'true' if self.imageFlags & ImageFlags.Quantize else 'false')
        root.setAttribute('enlargeImages', 'true' if self.imageFlags & ImageFlags.Enlarge else 'false')
        root.setAttribute('splitImages', 'true' if self.imageFlags & ImageFlags.Split else 'false')
        root.setAttribute('rightToLeft', 'true' if self.imageFlags & ImageFlags.RightToLeft else 'false')
        root.setAttribute('cbz', 'true' if self.cbz else 'false')

        textXml = document.toString(4).toUtf8()

        try:
            fileXml = open(unicode(filename), 'w')
            fileXml.write(textXml)
            fileXml.close()
        except IOError:
            raise RuntimeError('Cannot create defaults file %s' % filename)

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Loads the default settings from a file.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def load_defaults(self, filename = DefaultsXML):
        try:
            fileXml = open(unicode(filename), 'r')
            textXml = fileXml.read()
            fileXml.close()
        except IOError:
            self.device = Book.DefaultDevice
            self.overwrite = Book.DefaultOverwrite
            self.imageFlags = Book.DefaultImageFlags
            self.cbz = Book.DefaultCBZ
            self.save_defaults(filename)
            return

        document = QtXml.QDomDocument()

        if not document.setContent(QtCore.QString.fromUtf8(textXml)):
            raise RuntimeError('Error parsing defaults file %s' % filename)

        root = document.documentElement()
        if root.tagName() != 'defaults':
            raise RuntimeError('Unexpected defaults format in file %s' % filename)

        self.overwrite = root.attribute('overwrite', 'true' if Book.DefaultOverwrite else 'false') == 'true'
        self.device = root.attribute('device', Book.DefaultDevice)
        
        orient = root.attribute('orientImages', 'true' if Book.DefaultImageFlags & ImageFlags.Orient else 'false') == 'true'
        split = root.attribute('splitImages', 'true' if Book.DefaultImageFlags & ImageFlags.Split else 'false') == 'true'
        shrink = root.attribute('shrinkImages', 'true' if Book.DefaultImageFlags & ImageFlags.Shrink else 'false') == 'true'
        enlarge = root.attribute('enlargeImages', 'true' if Book.DefaultImageFlags & ImageFlags.Enlarge else 'false') == 'true'
        frame = root.attribute('frameImages', 'true' if Book.DefaultImageFlags & ImageFlags.Frame else 'false') == 'true'
        dither = root.attribute('ditherImages', 'true' if Book.DefaultImageFlags & ImageFlags.Quantize else 'false') == 'true'
        rtl = root.attribute('rightToLeft', 'true' if Book.DefaultImageFlags & ImageFlags.RightToLeft else 'false') == 'true'
        self.imageFlags = (
            (ImageFlags.Orient if orient else 0) |
            (ImageFlags.Split if split else 0) |
            (ImageFlags.Shrink if shrink else 0) |
            (ImageFlags.Enlarge if enlarge else 0) |
            (ImageFlags.Frame if frame else 0) |
            (ImageFlags.Quantize if dither else 0) |
            (ImageFlags.RightToLeft if rtl else 0)
        )
        
        self.cbz = root.attribute('cbz', 'true' if Book.DefaultCBZ else 'false') == 'true'

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Saves the current state to a book file.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def save(self, filename):
        document = QtXml.QDomDocument()

        root = document.createElement('book')
        document.appendChild(root)

        root.setAttribute('title', self.title)
        root.setAttribute('overwrite', 'true' if self.overwrite else 'false')
        root.setAttribute('device', self.device)
        root.setAttribute('imageFlags', self.imageFlags)
        root.setAttribute('cbz', 'true' if self.cbz else 'false')

        for filenameImg in self.images:
            itemImg = document.createElement('image')
            root.appendChild(itemImg)
            itemImg.setAttribute('filename', filenameImg)

        textXml = document.toString(4).toUtf8()

        try:
            fileXml = open(unicode(filename), 'w')
            fileXml.write(textXml)
            fileXml.close()
        except IOError:
            raise RuntimeError('Cannot create book file %s' % filename)

        self.filename = filename
        self.modified = False

    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    # Loads a book file.
    #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    def load(self, filename):
        try:
            fileXml = open(unicode(filename), 'r')
            textXml = fileXml.read()
            fileXml.close()
        except IOError:
            raise RuntimeError('Cannot open book file %s' % filename)

        document = QtXml.QDomDocument()

        if not document.setContent(QtCore.QString.fromUtf8(textXml)):
            raise RuntimeError('Error parsing book file %s' % filename)

        root = document.documentElement()
        if root.tagName() != 'book':
            raise RuntimeError('Unexpected book format in file %s' % filename)

        self.title = root.attribute('title', 'Untitled')
        self.overwrite = root.attribute('overwrite', 'true' if Book.DefaultOverwrite else 'false') == 'true'
        self.device = root.attribute('device', Book.DefaultDevice)
        self.imageFlags = int(root.attribute('imageFlags', str(Book.DefaultImageFlags)))
        self.cbz = root.attribute('cbz', 'true' if Book.DefaultCBZ else 'false') == 'true'
        self.filename = filename
        self.modified = False
        self.images = []

        items = root.elementsByTagName('image')
        if items == None:
            return

        for i in xrange(0, len(items)):
            item = items.at(i).toElement()
            if item.hasAttribute('filename'):
                self.images.append(item.attribute('filename'))


class MainWindowBook(QtGui.QMainWindow, Ui_MainWindowBook):
    def __init__(self, filename=None):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.connect(self.actionFileNew, QtCore.SIGNAL('triggered()'), self.onFileNew)
        self.connect(self.actionFileOpen, QtCore.SIGNAL('triggered()'), self.onFileOpen)
        self.connect(self.actionFileSave, QtCore.SIGNAL('triggered()'), self.onFileSave)
        self.connect(self.actionFileSaveAs, QtCore.SIGNAL('triggered()'), self.onFileSaveAs)
        self.connect(self.actionBookOptions, QtCore.SIGNAL('triggered()'), self.onBookOptions)
        self.connect(self.actionBookAddFiles, QtCore.SIGNAL('triggered()'), self.onBookAddFiles)
        self.connect(self.actionBookAddDirectory, QtCore.SIGNAL('triggered()'), self.onBookAddDirectory)
        self.connect(self.actionBookShiftUp, QtCore.SIGNAL('triggered()'), self.onBookShiftUp)
        self.connect(self.actionBookShiftDown, QtCore.SIGNAL('triggered()'), self.onBookShiftDown)
        self.connect(self.actionBookRemove, QtCore.SIGNAL('triggered()'), self.onBookRemove)
        self.connect(self.actionBookExport, QtCore.SIGNAL('triggered()'), self.onBookExport)
        self.connect(self.actionHelpAbout, QtCore.SIGNAL('triggered()'), self.onHelpAbout)
        self.connect(self.actionHelpHomepage, QtCore.SIGNAL('triggered()'), self.onHelpHomepage)
        self.connect(self.listWidgetFiles, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.onFilesContextMenu)
        self.connect(self.listWidgetFiles, QtCore.SIGNAL('itemDoubleClicked (QListWidgetItem *)'), self.onFilesDoubleClick)
        self.listWidgetFiles.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.book = Book()
        if filename != None:
            self.loadBook(filename)

        self.current_dir = os.getcwd()

    def closeEvent(self, event):
        if not self.saveIfNeeded():
            event.ignore()


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()


    def dropEvent(self, event):
        directories = []
        filenames = []

        for url in event.mimeData().urls():
            filename = url.toLocalFile()
            if self.isImageFile(filename):
                filenames.append(filename)
            elif os.path.isdir(unicode(filename)):
                directories.append(filename)

        self.addImageDirs(directories)
        self.addImageFiles(filenames)


    def onFileNew(self):
        if self.saveIfNeeded():
            self.book = Book()
            self.listWidgetFiles.clear()


    def onFileOpen(self):
        if not self.saveIfNeeded():
            return

        filename = QtGui.QFileDialog.getOpenFileName(
            self,
            'Select a book file to open',
            self.current_dir,
            'Mangle files (*.mngl);;All files (*.*)'
        )
        if not filename.isNull():
            self.loadBook(self.cleanupBookFile(filename))
            # Keep track of wherever they moved to find this file.
            self.current_dir = os.path.split(str(filename))[0]


    def onFileSave(self):
        self.saveBook(False)


    def onFileSaveAs(self):
        self.saveBook(True)


    def onFilesContextMenu(self, point):
        menu = QtGui.QMenu(self)
        menu.addAction(self.menu_Add.menuAction())

        if len(self.listWidgetFiles.selectedItems()) > 0:
            menu.addAction(self.menu_Shift.menuAction())
            menu.addAction(self.actionBookRemove)

        menu.exec_(self.listWidgetFiles.mapToGlobal(point))


    def onFilesDoubleClick(self, item):
        services = QtGui.QDesktopServices()
        services.openUrl(QtCore.QUrl.fromLocalFile(item.text()))


    def onBookAddFiles(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(
            self,
            'Select image file(s) to add',
            self.current_dir,
            'Image files (*.jpeg *.jpg *.gif *.png);;All files (*.*)'
        )
        if filenames:
            self.addImageFiles(filenames)
            # Keep track of wherever they moved to find these files.
            self.current_dir = os.path.split(str(filenames[0]))[0]


    def onBookAddDirectory(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, 'Select an image directory to add', self.current_dir)
        if not directory.isNull():
            self.addImageDirs([directory])
            self.current_dir = str(directory)


    def onBookShiftUp(self):
        self.shiftImageFiles(-1)


    def onBookShiftDown(self):
        self.shiftImageFiles(1)


    def onBookRemove(self):
        self.removeImageFiles()


    def onBookOptions(self):
        dialog = DialogOptions(self, self.book)
        dialog.exec_()


    def onBookExport(self):
        if len(self.book.images) == 0:
            QtGui.QMessageBox.warning(self, 'Mangle', 'This book has no images to export')
            return

        if self.book.title == None:
            dialog = DialogOptions(self, self.book)
            if dialog.exec_() == QtGui.QDialog.Rejected:
                return

        # If exporting to CBZ, this is a filename. If not, this is a directory name.
        out_path = ""

        if self.book.cbz == False:
            out_path = QtGui.QFileDialog.getExistingDirectory(self, 'Select a directory to export book to', self.current_dir)
            # Keep track of wherever they moved to find this directory.
            self.current_dir = str(out_path)
        else:
            out_path = QtGui.QFileDialog.getSaveFileName(
                self,
                'Select image file(s) to add',
                # Default to the current directory + the book's title + the cbz extension.
                os.path.join(self.current_dir, "%s.cbz" % self.book.title),
                'Comic Book Archive File (*.cbz);;All files (*.*)'
            )
            # Keep track of wherever they moved to find this file.
            self.current_dir = os.path.split(str(out_path))[0]
        
        if not out_path.isNull():
            dialog = DialogConvert(self, self.book, out_path)
            dialog.exec_()


    def onHelpHomepage(self):
        services = QtGui.QDesktopServices()
        services.openUrl(QtCore.QUrl('http://foosoft.net/mangle'))


    def onHelpAbout(self):
        dialog = DialogAbout(self)
        dialog.exec_()


    def saveIfNeeded(self):
        if not self.book.modified:
            return True

        result = QtGui.QMessageBox.question(
            self,
            'Mangle',
            'Save changes to the current book?',
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel,
            QtGui.QMessageBox.Yes
        )

        return (
            result == QtGui.QMessageBox.No or
            result == QtGui.QMessageBox.Yes and self.saveBook()
        )


    def saveBook(self, browse=False):
        if self.book.title == None:
            QtGui.QMessageBox.warning(self, 'Mangle', 'You must specify a title for this book before saving')
            return False

        filename = self.book.filename
        if filename == None or browse:
            filename = QtGui.QFileDialog.getSaveFileName(
                self,
                'Select a book file to save as',
                self.current_dir,
                'Mangle files (*.mngl);;All files (*.*)'
            )
            if filename.isNull():
                return False
            filename = self.cleanupBookFile(filename)
            self.current_dir = os.path.split(str(filename))[0]

        try:
            self.book.save(filename)
        except RuntimeError, error:
            QtGui.QMessageBox.critical(self, 'Mangle', str(error))
            return False

        return True


    def loadBook(self, filename):
        try:
            self.book.load(filename)
        except RuntimeError, error:
            QtGui.QMessageBox.critical(self, 'Mangle', str(error))
        else:
            self.listWidgetFiles.clear()
            for image in self.book.images:
                self.listWidgetFiles.addItem(image)


    def shiftImageFile(self, row, delta):
        validShift = (
            (delta > 0 and row < self.listWidgetFiles.count() - delta) or
            (delta < 0 and row >= abs(delta))
        )
        if not validShift:
            return

        item = self.listWidgetFiles.takeItem(row)

        self.listWidgetFiles.insertItem(row + delta, item)
        self.listWidgetFiles.setItemSelected(item, True)

        self.book.modified = True
        self.book.images[row], self.book.images[row + delta] = (
            self.book.images[row + delta], self.book.images[row]
        )


    def shiftImageFiles(self, delta):
        items = self.listWidgetFiles.selectedItems()
        rows = sorted([self.listWidgetFiles.row(item) for item in items])

        for row in rows if delta < 0 else reversed(rows):
            self.shiftImageFile(row, delta)


    def removeImageFiles(self):
        for item in self.listWidgetFiles.selectedItems():
            row = self.listWidgetFiles.row(item)
            self.listWidgetFiles.takeItem(row)
            self.book.images.remove(item.text())
            self.book.modified = True


    def addImageFiles(self, filenames):
        filenamesListed = []
        for i in xrange(0, self.listWidgetFiles.count()):
            filenamesListed.append(self.listWidgetFiles.item(i).text())

        for filename in filenames:
            if filename not in filenamesListed:
                filename = QtCore.QString(filename)
                self.listWidgetFiles.addItem(filename)
                self.book.images.append(filename)
                self.book.modified = True


    def addImageDirs(self, directories):
        filenames = []

        for directory in directories:
            for root, subdirs, subfiles in os.walk(unicode(directory)):
                for filename in subfiles:
                    path = os.path.join(root, filename)
                    if self.isImageFile(path):
                        filenames.append(path)

        self.addImageFiles(filenames)


    def isImageFile(self, filename):
        imageExts = ['.jpeg', '.jpg', '.gif', '.png']
        filename = unicode(filename)
        return (
            os.path.isfile(filename) and
            os.path.splitext(filename)[1].lower() in imageExts
        )


    def cleanupBookFile(self, filename):
        if len(os.path.splitext(unicode(filename))[1]) == 0:
            filename += '.mngl'
        return filename
