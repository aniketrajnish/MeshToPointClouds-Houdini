import random
from PySide2 import QtWidgets, QtGui, QtCore   

class PointCloud:
    '''
    This class creates point clouds around any mesh file in Houdini.
    '''
    def __init__(self):
        '''
        Initialize the class variables to None.
        '''
        self.selectedGeo = None
        self.lastGeoNode = None
        self.materialNode = None
        self.attribFromMap = None
        self.scatterNode = None
        self.copyNode = None
        self.texturePath = None
        self.numPts = None
        self.modelPath = None
    
    @staticmethod
    def extractChild(parent, childType):
        '''
        Function to extract the child node of a given type from a parent node.
        '''
        listOfChildrens = parent.children()
        for node in listOfChildrens:
            if node.type().name() == childType:
                return node                   
    
    def selectGeoContainer(self):
        '''
        Function to prompt user to select the geometry container node and assign it as the selected geometry.
        '''        
        self.modelPath = hou.ui.selectNode(title='Select Geometry Container node', node_type_filter=hou.nodeTypeFilter.Sop)
        if not self.modelPath:
            raise Exception('Select a geometry node first')

        self.selectedGeo = hou.node(self.modelPath)
        self.lastGeoNode = self.selectedGeo.children()[-1] # generally the last node of the selected geometry node has the mesh information

    def getUVandColor(self):
        '''
        Create attribfrommap node to get UV and color information from the mesh later.
        '''
        self.attribFromMap = self.selectedGeo.createNode('attribfrommap', 'AFM')
        self.attribFromMap.setInput(0, self.lastGeoNode)

    def scatterPoints(self):
        '''
        Create scatter node to scatter points on the mesh around which the point clouds will be created.
        The number of points to be scattered is taken from the user.
        '''
        self.scatterNode = self.selectedGeo.createNode('scatter', 'SP')
        self.scatterNode.setInput(0, self.attribFromMap)

        numInpDialog = NumberInputDialog()
        if numInpDialog.exec_():
            self.numPts = numInpDialog.numVal()
        else:
            raise Exception('Choose the number of point clouds:')

        self.scatterNode.parm('npts').set(self.numPts)
        self.scatterNode.parm('emergencylimit').set(self.numPts + 1) # to avoid emergency limit error

    def applyTexture(self):
        '''
        Apply texture to the mesh and transfer the color information using UV information from attribfrommap node.
        The automatic texture search is works in most of the houdini example geometry.
        '''
        self.matNode = self.extractChild(self.lastGeoNode, 'matnet')
        if not self.matNode:
            raise Exception('material node not found.')   

        texDialog = TextureDialog(matNode=self.matNode)
        result = texDialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            self.texturePath = texDialog.selectedTexturePath
            if self.texturePath:
                self.attribFromMap.parm('filename').set(self.texturePath)
                self.attribFromMap.parm('export_attribute').set('Cd')
            else:
                raise Exception('Texture path not provided.')

        self.attribFromMap.parm('filename').set(self.texturePath)
        self.attribFromMap.parm('export_attribute').set('Cd')

    def createPointClouds(self):
        '''
        Function to create point clouds around the mesh and display it.
        Transfrer the color information from the mesh's texture to the point clouds.
        '''
        addNode = self.selectedGeo.createNode('add', 'ptNode')
        addNode.parm('points').set(1)

        self.copyNode = self.selectedGeo.createNode('copytopoints', 'CTP')
        self.copyNode.setInput(0, addNode)
        self.copyNode.setInput(1, self.scatterNode)  

        attribTransfer = self.selectedGeo.createNode('attribtransfer', 'AT')
        attribTransfer.setInput(0, self.copyNode)  
        attribTransfer.setInput(1, self.scatterNode)  
        attribTransfer.parm('pointattriblist').set('Cd') 

        attribTransfer.setDisplayFlag(True)

class TextureDialog(QtWidgets.QDialog):
    '''
    Qt dialog to select the texture for the mesh, either manually or automatically.
    Automatic texture search works in most of the houdini example geometry.
    '''
    def __init__(self, parent=None, matNode=None):
        '''
        Initialize the class variables and call the initUI function.
        '''
        super(TextureDialog, self).__init__(parent)
        self.setWindowTitle('Texture Options')
        self.selectedTexturePath = None
        self.matNode = matNode 
        self.initUI()

    def initUI(self):
        '''
        Function to create the UI for the dialog.
        It contains two buttons, one to load  texture manually, other to search texture automatically.
        Vertical box layout is used to arrange the buttons.
        '''
        vbox = QtWidgets.QVBoxLayout(self)

        self.manualBtn = QtWidgets.QPushButton('Load Texture Manually', self)
        self.manualBtn.clicked.connect(self.loadTexManually)
        vbox.addWidget(self.manualBtn)

        self.autoBtn = QtWidgets.QPushButton('Search Texture Automatically', self)
        self.autoBtn.clicked.connect(self.loadTexAuto)
        vbox.addWidget(self.autoBtn)

        self.setLayout(vbox)

    def loadTexManually(self):
        '''
        Opens a file dialog to select the texture file manually.
        '''
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Texture File', '', 'Image Files (*.png *.jpg *.bmp *.tga)')
        if fileName:
            self.selectedTexturePath = fileName 
            self.accept()

    def loadTexAuto(self):        
        '''
        Tries to look for the basecolor texture parameter in the material node and retrieves the texture path from it.
        '''
        if not self.matNode:
            QtWidgets.QMessageBox.warning(self, 'Error', 'Material node not provided.')
            return
                
        baseTex = self.matNode.children()[0].parm('basecolor_texture')
        if not baseTex:
            errDialog = QtWidgets.QMessageBox.warning(self, 'Texture Not Found', 'Basecolor texture parameter not found. Locate manually.')
            self.loadTexManually()
            return

        texPath = baseTex.eval()
        if texPath:
            self.selectedTexturePath = texPath
            self.accept()
        else:
            errDialog = QtWidgets.QMessageBox.warning(self, 'Texture Not Found', 'Texture not found. Locate manually.')
            self.loadTexManually()

class LogSlider(QtWidgets.QSlider):
    '''
    Qslider override class to create a logarithmic slider.
    The slider values are converted to logarithmic values and displayed as 10^x.
    '''
    def __init__(self, *args, **kwargs):
        super(LogSlider, self).__init__(*args, **kwargs)
        self.setFixedHeight(75)

    def paintEvent(self, event):
        '''
        Override the paintEvent function to draw custom tick marks and labels.
        '''
        super(LogSlider, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        for i in range(6): # tick marks and labels for 10^3 to 10^8 (i+3)
            color = QtGui.QColor('green') if i < 4 else QtGui.QColor('red')
            painter.setPen(color)

            x, y = self.calcPos(i)

            if i > 0:
                painter.drawLine(x, y - 15, x, y + 15)  

            labelText = f'10^{i+3}'
            self.drawLabel(painter, labelText, x, y)

    def calcPos(self, i):
        '''
        Function to calculate the position of the tick marks and labels on the slider.
        '''
        x = self.width() * (i / 5.0)  # divide whole by 5.0 to get 5 tick marks
        y = self.height() / 2  # center vertically
        return x, y

    def drawLabel(self, painter, text, x, y):
        '''
        Function to draw the labels on the slider.
        '''
        w = painter.fontMetrics().width(text)
        h = painter.fontMetrics().height()
        textX = x + w 
        textY = y + h
        painter.drawText(textX, textY, text)

class NumberInputDialog(QtWidgets.QDialog):
    '''
    Qt dialog to select number of point clouds.
    '''
    MIN_VAL = 1000 # Constants to look cool
    MAX_VAL = 100000000

    def __init__(self, parent=None):
        '''
        Initialize the class variables and call the initUI function.
        '''
        super(NumberInputDialog, self).__init__(parent)
        self.setWindowTitle('Select Number of Point Clouds') 
        self.initUI()

    def initUI(self):
        '''
        Function to create the UI for the dialog.
        It contains a slider to select the number of point clouds and two buttons to accept or reject the value.
        The value is displayed as 10^x where x is the slider value. It ranges from 10^3 to 10^8.
        Vertical box layout is used to arrange the buttons.
        '''
        vbox = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel('Select number of point clouds (between 1000 and 100,000,000):', self)
        vbox.addWidget(self.label)

        self.slider = LogSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(300)  # 10^0
        self.slider.setMaximum(800)  # 10^8
        self.slider.setValue(600)  # default - 10^6
        self.slider.valueChanged.connect(self.logVal)
        vbox.addWidget(self.slider)       

        self.valLabel = QtWidgets.QLabel('1000000', self)
        vbox.addWidget(self.valLabel)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        vbox.addWidget(buttons)

    def logVal(self, value):
        '''
        Function to convert the slider value to logarithmic value and update the label.
        Looks for valueChange signal from the slider.
        '''
        logVal = self.calcLogVal(value)        
        if self.isValidVal(logVal):
            self.updateLabel(int(logVal))
        else:
            self.edgeCaseCheck()

    def updateLabel(self, value):
        '''
        Function to update the label with the current slider value.
        '''
        if self.isValidVal(value):
            self.valLabel.setText(str(value))
        else:
            self.edgeCaseCheck()

    def numVal(self):
        '''
        Return number of point clouds if the value is valid.
        '''
        sliderVal = self.slider.value()
        value = int(self.calcLogVal(sliderVal))
        if self.isValidVal(value):
            return value
        else:
            self.edgeCaseCheck()
            return None  # Return None if the value is not valid

    def isValidVal(self, value):
        '''
        Function to check if the value is in the valid range.
        '''
        return self.MIN_VAL <= value <= self.MAX_VAL

    def edgeCaseCheck(self):
        '''
        Function to display error message if the value is not in the valid range.
        '''
        errMsg = f'Value must be between {self.MIN_VAL} and {self.MAX_VAL}.'
        QtWidgets.QMessageBox.warning(self, 'Invalid Value', errMsg)

    @staticmethod
    def calcLogVal(value):
        '''
        Function for linear to logarithmic conversion.
        '''
        return 10 ** (value / 100)  # Convert linear slider value to logarithmic value

def main():
    '''
    Main function to call the PointCloud class functions and create point clouds around the mesh chosen by the user.
    '''
    pc = PointCloud()
    pc.selectGeoContainer()
    pc.getUVandColor()
    pc.scatterPoints()
    pc.applyTexture()
    pc.createPointClouds()

main()