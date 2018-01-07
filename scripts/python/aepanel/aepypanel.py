import sys
import os
import re
import hou
import subprocess
import platform
from PySide2 import QtWidgets, QtUiTools, QtGui, QtCore

class ProjectManager( QtWidgets.QWidget ):
    def __init__(self):
        super(ProjectManager, self).__init__()

        self.job = hou.getenv('HIP')
        self.prevDirs = [self.job]

        # get path to ui file and load it
        path = os.path.dirname(os.path.realpath(__file__))
        loader = QtUiTools.QUiLoader()
        self.ui = loader.load(path + '/mypypanel.ui')

        # populate listwidget
        self.fileList = self.ui.findChild(QtWidgets.QListWidget, 'fileList')
        self.createFileList(self.fileList)
        self.fileList.doubleClicked.connect(self.openScene)

        # set image here as it doesnt load properly from the .ui file
        self.logo = self.ui.findChild(QtWidgets.QLabel, 'logo')
        pixmap = QtGui.QPixmap(path + '/res/aelib_logo_sm.png')
        self.logo.setPixmap(pixmap)

        # connect buttons to methods
        self.upBtn = self.ui.findChild(QtWidgets.QPushButton, 'upBtn')
        self.upBtn.clicked.connect(self.upDir)
        self.backBtn = self.ui.findChild(QtWidgets.QPushButton, 'backBtn')
        self.backBtn.clicked.connect(self.backDir)
        self.openSceneBtn = self.ui.findChild(QtWidgets.QPushButton, 'openBtn')
        self.openSceneBtn.clicked.connect(self.openSceneWithButton)
        self.gotoHipBtn = self.ui.findChild(QtWidgets.QPushButton, 'gotoHipBtn')
        self.gotoHipBtn.clicked.connect(self.gotoHip)
        self.incrBtn = self.ui.findChild(QtWidgets.QPushButton, 'incrBtn')
        self.incrBtn.clicked.connect(self.hipIncrementVersion)
        self.explorerBtn = self.ui.findChild(QtWidgets.QPushButton, 'explorerBtn')
        self.explorerBtn.clicked.connect(self.openInExplorer)

        # set the layout from the .ui file, placed in a scrollarea
        scrollarea = QtWidgets.QScrollArea(self)
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(self.ui)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(scrollarea)
        self.setLayout(layout)

    def openScene(self, item):
        # if dir, navigate to this
        data =  item.data()
        if str(data).startswith('/'):
            self.prevDirs.append(self.job)
            self.job = self.job + '/' + str(data)[1:]
            self.createFileList(self.fileList)
        else:
            hou.hipFile.load(self.job +'/'+ str(item.data()))

    def openSceneWithButton(self):
        curr = self.fileList.currentItem()
        hou.hipFile.load(self.job +'/'+ str(curr.data(0)))

    # Open in explorer window depending on OS
    def openInExplorer(self):
        platform = sys.platform
        if platform == "win32":
            # subprocess.Popen(["explorer", self.job])
            os.startfile(self.job)
        elif platform == "darwin": #osx
            subprocess.Popen(["open", self.job])
        else: #linux
            subprocess.Popen(["xdg-open", self.job])

    def gotoHip(self):
        self.prevDirs.append(self.job)
        self.job = hou.getenv('HIP')
        self.createFileList(self.fileList)

    def upDir(self):
        self.prevDirs.append(self.job)
        self.job = os.path.dirname(self.job)
        self.createFileList(self.fileList)

    def backDir(self):
        self.job = self.prevDirs.pop()
        self.createFileList(self.fileList)

    def setDirLabel(self):
        dirlabel = self.ui.findChild(QtWidgets.QLabel, 'currDir')
        dirlabel.setText(self.job)

    def createFileList(self, fileListWidget):
        fileListWidget.clear()
        # add directories?
        for file in os.listdir(self.job):
            f = self.job + '/' + file
            if os.path.isdir(f):
                item = QtWidgets.QListWidgetItem('/' + file)
                item.setTextColor(QtGui.QColor(60,220,47))
                fileListWidget.addItem(item)
                # fileListWidget.addItem('/' + file)
        # add hips
        for file in os.listdir(self.job):
            if file.endswith('.hip'):
                fileListWidget.addItem(file)
        self.setDirLabel()

    # Version increment method, copied directly from the aelib shelf tool
    def hipIncrementVersion(self):
        # SETTINGS ==================
        setToFirstFrame = True  # Sets playback frame of saved file to first frame (does not affect open file)
        setToManualUpdate = False  # Sets update mode of saved file to manual (does not affect open file)
        autoversion = True  # If no versioning exists, create a new version
        autoversionzfill = 3  # digit padding for autoversioning
        debug = 0  # print some items to console
        # ===========================

        orighip = hou.hipFile.name()
        hipname = hou.hipFile.basename()
        # hipfile = hipname.split(".")[0]
        # version which works for filenames with periods
        hipfile = os.path.splitext(hipname)[0]

        # check current filename for version prefix and split accordingly
        # Uses regex so a filename like myfile_verycool_v001.hip will get picked up correctly (not match the first _v)
        versionSections = ""
        versionType = ""
        if len(re.findall('_v(?=\d+)', hipfile)) > 0:
            versionSections = re.split('_v(?=\d+)', hipfile, 1)
            versionType = "_v"
        elif len(re.findall('_V(?=\d+)', hipfile)) > 0:
            versionSections = re.split('_V(?=\d+)', hipfile, 1)
            versionType = "_V"

            # if no version prefix found, create it
        if versionSections == "":
            if (autoversion):
                versionSections = [hipfile, "0" * autoversionzfill]
                versionType = "_v"
                orighip = orighip.replace(hipfile, hipfile + versionType + "0" * autoversionzfill)
                print "No version found in hip name - Autoversioning"
            else:
                print "No version found in hip name - Exiting"
                return 1

        # regex - match numbers after version splitter. Match until non-numeric value is hit.
        match = re.match('\d+', versionSections[1])
        if match:
            versionNumber = match.group(0)
        else:
            print "Problem encountered matching version number - Exiting"
            return 1

        # Create new filename
        oldVersion = versionType + versionNumber
        if debug:
            print "Old version: " + oldVersion
        newVersion = versionType + str(int(versionNumber) + 1).zfill(len(versionNumber))
        newhip = orighip.replace(oldVersion, newVersion)
        if debug:
            print "New file: " + newhip

        # Save the file
        confirm = 0
        if os.path.isfile(newhip):
            text = "Overwrite existing hip file?"
            confirm = hou.ui.displayMessage(text, buttons=("Yes", "No"), severity=hou.severityType.Message,
                                            title="New Hip")
        if confirm == 0:
            # update mode and frame settings
            updateMode = hou.updateModeSetting()
            frame = hou.frame()
            if (setToManualUpdate):
                hou.setUpdateMode(hou.updateMode.Manual)
            if (setToFirstFrame):
                # hou.setFrame(1)
                hou.setFrame(hou.playbar.playbackRange()[0])

            hou.hipFile.save(newhip)

            # reset update mode and frame
            hou.setUpdateMode(updateMode)
            hou.setFrame(frame)