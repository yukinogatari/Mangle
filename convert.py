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
from PyQt4 import QtGui, QtCore

import image
from zipfile import ZipFile, ZIP_DEFLATED
import StringIO

from epub import EpubBook
import mimetypes
import tempfile

class DialogConvert(QtGui.QProgressDialog):
    def __init__(self, parent, book, target):
        QtGui.QProgressDialog.__init__(self)

        self.book = book
        self.target = str(target)

        self.timer = None
        self.setWindowTitle('Exporting book...')
        self.setMaximum(len(self.book.images))
        self.setValue(0)
        
        # Since we can generate multiple images from a single source image,
        # we use this counter to determine how to name the files.
        self.counter = 0
      
        if self.book.epub:
          out_dir = os.path.join(unicode(self.target), unicode(self.book.title))
          epub = self.target
          self.epub_out = EpubBook()
          

    def showEvent(self, event):
        if self.timer == None:
            self.timer = QtCore.QTimer()
            self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.onTimer)
            self.timer.start(0)
    
    
    def onTimer(self):
        index = self.value()

        out_dir = ""
        cbz = ""
        epub = ""
        
        name_template = "%05d.png"

        if self.book.cbz:
          out_dir = os.path.split(self.target)[0]
          cbz = self.target
        else:
          out_dir = os.path.join(unicode(self.target), unicode(self.book.title))
        
        source = unicode(self.book.images[index])

        if index == 0:
            try:
                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)
            except OSError:
                QtGui.QMessageBox.critical(self, 'Mangle', 'Cannot create directory %s' % out_dir)
                self.close()
                return

            try:
                base = os.path.join(out_dir, unicode(self.book.title))

                # What, exactly, is this for? I never could figure it out.
                saveData = u'LAST=/mnt/us/pictures/%s/%s' % (self.book.title, name_template % self.counter)

                if not self.book.cbz | self.book.epub:

                    mangaName = '%s.manga' % base
                    mangaSaveName = '%s.manga_save' % base

                    if self.book.overwrite or not os.path.isfile(mangaName):
                        manga = open(mangaName, 'w')
                        manga.write('\x00')
                        manga.close()

                    if self.book.overwrite or not os.path.isfile(mangaSaveName):
                        mangaSave = open(mangaSaveName, 'w')
                        mangaSave.write(saveData.encode('utf-8'))
                        mangaSave.close()

                elif self.book.cbz:

                    mangaName = '%s.manga' % self.book.title
                    mangaSaveName = '%s.manga_save' % self.book.title

                    if os.path.isfile(cbz):
                        # If the file already exists, get rid of it before we start writing to it,
                        # since we open the zip file in append mode.
                        os.remove(cbz)
                    cbz_out = ZipFile(cbz, 'a', ZIP_DEFLATED, allowZip64 = True)
                    cbz_out.writestr(mangaName, '\x00')
                    cbz_out.writestr(mangaSaveName, saveData.encode('utf-8'))
                    cbz_out.close()
                
              

            except IOError:
                QtGui.QMessageBox.critical(self, 'Mangle', 'Cannot write manga file(s) to directory %s' % out_dir)
                self.close()
                return False

        self.setLabelText('Processing %s...' % os.path.split(source)[1])

        try:
            # Since splitting is an option, we can get multiple files back from
            # the convert operation, and it'll always be stored in a list.
            images = image.convertImage(source, str(self.book.device), self.book.imageFlags)
            # lol cheating
            #conv_img = images[0]
            
            for conv_img in images:

                # If we're exporting to file, we need the full path. Otherwise, we just need the filename.
                out_file = (
                    os.path.join(out_dir, name_template % self.counter) if not self.book.cbz
                    else (name_template % self.counter)
                )

                if (self.book.overwrite or not os.path.isfile(out_file)) and not self.book.cbz:

                    try:
                        conv_img.save(out_file)
                        
                        if self.book.epub:
                          epub_out = self.epub_out
                          epub_out.setTitle(unicode(self.book.title))
                 
                          item = epub_out.addImage(out_file, name_template % self.counter)
                          page = epub_out.addHtmlForImage(item)
                          epub_out.addSpineItem(page)
                          if self.counter == 0:
                            epub_out.addTocMapNode(page.destPath, "Page " + str(self.counter + 1))
                            
                
                    except IOError:
                        raise RuntimeError('Cannot write image file %s' % out_file)

                if self.book.cbz:
                    cbz_out = ZipFile(cbz, 'a', ZIP_DEFLATED, allowZip64 = True)

                    # Write the image in PNG format to an object pretending to be a file, so we can
                    # dump the string data into the CBZ file without saving to disk first.
                    out_str = StringIO.StringIO()
                    conv_img.save(out_str, format='PNG')
                    cbz_out.writestr(out_file, out_str.getvalue())
                    out_str.close()

                    cbz_out.close()
                
                # We're done with this image, so up the counter.
                self.counter = self.counter + 1
               
                
        except RuntimeError, error:
            result = QtGui.QMessageBox.critical(
                self,
                'Mangle',
                str(error),
                QtGui.QMessageBox.Abort | QtGui.QMessageBox.Ignore,
                QtGui.QMessageBox.Ignore
            )
            if result == QtGui.QMessageBox.Abort:
                self.close()
                return

        self.setValue(index + 1)
   
        if self.book.epub:
          epub_out.createArchiveNew(out_dir + ".epub")
