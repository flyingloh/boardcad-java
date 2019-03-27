import boardcad.gui.jdk.BoardCAD
import time
from javax.swing import *
from java.io import *
from array import *
from cadcore import *
from java.awt.geom import *
	# Run cmd: execfile('\\\\mackdaddy\\GrabIt Downloads\\Surfboards\\BoardCAD\\BC2WS_Export_1.py')

	# ================================================================================
	#     SCRIPT NAME: BC2WS_Export_2.py
	#          AUTHOR: Peter Weatherhead
	#         CREATED: 2015-01-31
	#    LAST UPDATED: 2016-10-08
	#         PURPOSE: This script interrogates a BoardCAD model and generates the 
	#				   data necessary for the WaveShapes process.
	# REQUIRED INPUTS: For the script to execute properly the following preconditions
	#                  need to be met:
	#                     - The board should be loaded in BoardCAD
	#					  - Board should not be repositioned for CAM / g-code operation
	#						(i.e. the tail should be at X = 0, the lowest part of the 
	#						bottom should be Y = 0).
	#					  - The cross sections should use default control point numbers
	#					    this ensures the 2nd control point is always the tucked rail
	#						and so on.  Addition of control points to the section will 
	#						likely cause unreliable results.
	#         OUTPUTS: The script generates a CSV file which is specified by the user
	#                  which includes the data required by the WaveShapes process.
	#				   All data is automatically exported, however the Rail and Deck 
	#				   Factors have no direct correlation. Instead a number of guide
	#				   points are exported and these factors need to be trimmed by 
	#				   Graham manually to match the guide points.
	#
	#				   All outputted values are in millimetres.
	#				   All BoardCAD values are in centimetres.
	#
	#				   REV 2: Output file location hard coded to C:\BC_WS_Output.csv
	#
	# 	   HOW TO USE:  TBC
	#				   1. Install BoardCAD 3.0 or later
	#				   2. Place the script some easily accessed directory directory typically:
	#				   		C:\BC2WS_Export_1.py
	#				   3. Open the board for exporting
	#				   4. Currently (04/02/2015) BoardCAD RunScript commands do not work
	#					  From the GUI - it is necessary to run the script from the Jython
	#					  Console located at the bottom of the window.  Paste the following
	#					  command into the window - Note the double back slashes are 
	#					  necessary.
	# 							execfile('C:\\BC2WS_Export_1.py')
	# ================================================================================

def distToLine(p1, p2, p3):
	# ================================================================================
	#   FUNCTION NAME: distToLine
	#          AUTHOR: Peter Weatherhead
	#         CREATED: 2015-02-01
	#    LAST UPDATED: 2015-02-01
	#         PURPOSE: This function returns the distance between a point and a line
	#				   defined by 2 points.  It is used to determine concave on section 
	#				   bottom curves.
	# REQUIRED INPUTS: All points are of type java.awt.geom.Point2D.Double
	#                    p1,p2 - The end points of the line
	#					 p3 - The point to which distance is to be calculated
	#         OUTPUTS: Distance between p3 and the line defined by p1 and p2.
	# ================================================================================
	xDelta = p2.getX() - p1.getX();
	yDelta = p2.getY() - p1.getY();

	if ((xDelta == 0) and (yDelta == 0)):
	    print('Cant have zero length line')
	
	u = ((p3.getX() - p1.getX()) * xDelta + (p3.getY() - p1.getY()) * yDelta) / (xDelta * xDelta + yDelta * yDelta);

	if (u < 0):
	    closestPoint = p1
	elif (u > 1):
	    closestPoint = p2
	else:
	    closestPoint = Point2D.Double(p1.getX() + u * xDelta, p1.getY() + u * yDelta);
	
	return closestPoint.distance(p3);


def BC2WS_Export():
	# ================================================================================
	#   FUNCTION NAME: BC2WS_Export
	#          AUTHOR: Peter Weatherhead
	#         CREATED: 2015-01-31
	#    LAST UPDATED: 2015-02-04
	#         PURPOSE: This script performs the above mentioned tasks.
	# REQUIRED INPUTS: See Above. 
	#         OUTPUTS: See Above. 
	# ================================================================================
	
	# Set Up Data and Variables
	# ================================================================================
	# Wave Shape section position as % of board straight length
	# Data is to be arranged Nose to Tail to permit easy cut and pasting of data into 
	# the WS Excel table format.
	# Output table currently matches the WS measurement template.
	SecPosPCs = array('f',[0.9999, 0.92,0.78, 0.60,0.32,0,-0.32,-0.60,-0.78,-0.92,-0.9999])
	DeckGuidePCs = array('f',[0.80, 0.60,0.30])
	BoardLength = 0
	HalfLength = 0
	HalfSectWidth = 0
	SectPositions = []
	SectWidths = []
	Thicknesses = []
	Vees = []
	Concaves = []
	ConcaveFactors = []
	EdgeTangentHeights = []
	BottomLines = []
	OutputFile = 'C:\\Temp\\BC_WS_Output.csv'
	
	# Creates a 3 x 11 Matrix
	DeckGuideXs = [[0 for y in xrange(len(SecPosPCs))] for x in xrange(len(DeckGuidePCs))]
	DeckGuideYs = [[0 for y in xrange(len(SecPosPCs))] for x in xrange(len(DeckGuidePCs))]

	# Get Board Object and Length
	# ================================================================================
	brd = boardcad.gui.jdk.BoardCAD.getInstance().getCurrentBrd()
	BoardLength = brd.getLength()*10
	HalfLength = BoardLength/2	
	
	# Get interpolated cross sections at each of the WS positions and record required
	# parameters
	# ================================================================================
	i = 0
	for SecPosPC in SecPosPCs:
		SectPositions.append(HalfLength*SecPosPC)
		SectWidths.append(((brd.getWidthAt((HalfLength+HalfLength*SecPosPC)/10))*10))
		HalfSectWidth = (((brd.getWidthAt((HalfLength+HalfLength*SecPosPC)/10))*10/2))
		BottomLines.append(((brd.getBottomAt((HalfLength+HalfLength*SecPosPC)/10,0))*10))
		Thicknesses.append(((brd.getThicknessAtPos((HalfLength+HalfLength*SecPosPC)/10))*10))
		
		# Measure Vee by comparing control point position
		# ============================================================================
		TempXSect = brd.getInterpolatedCrossSection((HalfLength+HalfLength*SecPosPC)/10)
		TempBSpline = TempXSect.getBezierSpline() 
		# Note this requires the tucked rail control points to be the 2nd point per default
		# cross section.
		TempStartCP = TempBSpline.getControlPoint(0) 
		TempEndCP = TempBSpline.getControlPoint(1)
		TempSP = TempStartCP.getEndPoint()
		TempEP = TempEndCP.getEndPoint()
		Vees.append((TempEP.y*10))
		
		# Measure Concave by finding the peak distance between the interpolated cross 
		# section bottom curve, and the line between the control point centre of the 
		# board and the control point at the tuck point. 
		# Note - this would not work for a convex bottom shape - the concave sign would 
		# be incorrect.
		# ============================================================================
		# Note this requires the edge tangent control point to be the 3rd point per default
		# cross section
		TempRailCP = TempBSpline.getControlPoint(2)
		TempRP = TempRailCP.getEndPoint()
		TempBotCurve = TempBSpline.getCurve(0) 
		TempBotCurveLen = TempBotCurve.getLength(0,1)
		# Evaluate bottom curve in 100 segments - this will potentially result ~2.5mm 
		# resolution.
		maxCC = 0
		maxCCXPos = 0
		for k in xrange(1,100):
			TempPt = TempBotCurve.getValue(k*0.01)
			CCDist = distToLine(TempSP, TempEP, TempPt)
			if (CCDist > maxCC):
				maxCC = CCDist
				maxCCXPos = TempPt.x
		Concaves.append((maxCC*10))
		ConcaveFactors.append((((TempBotCurve.getTForX(maxCCXPos))/(TempBotCurve.getLength(0,1)))*10))
		EdgeTangentHeights.append(((TempRP.y - TempEP.y)*10))
		
		# Get Deck / Rail Guide Points
		# At predefined percentages of half width.
		# ============================================================================
		TempRailTopCurve = TempBSpline.getCurve(2) 
		TempDeckCurve = TempBSpline.getCurve(3)
		TempDeckMidCP = TempBSpline.getControlPoint(3) 
		TempDMP = TempDeckMidCP.getEndPoint()
		
		j = 0
		for xPC in DeckGuidePCs:
			tempX = HalfSectWidth * xPC / 10
			DeckGuideXs[j][i] = HalfSectWidth * xPC
			if (tempX >= TempDMP.x):
				tempY = TempRailTopCurve.getYValue(TempRailTopCurve.getTForX(tempX))
			else:
				tempY = TempDeckCurve.getYValue(TempDeckCurve.getTForX(tempX))
			
			DeckGuideYs[j][i] = (((brd.getThicknessAtPos((HalfLength+HalfLength*SecPosPC)/10)) - tempY)*10)	
			j = j + 1
		
		i = i + 1
	# print (DeckGuideXs)
	# print (DeckGuideYs)

	# Prompt for output file name
	# Comment block below to remove hard coded file name
	# ================================================================================	

	# fc = JFileChooser()
	# fc.setCurrentDirectory(File(boardcad.gui.jdk.BoardCAD.getInstance().defaultDirectory))
	# returnVal = fc.showSaveDialog(boardcad.gui.jdk.BoardCAD.getInstance().getFrame())
	# if (returnVal != JFileChooser.APPROVE_OPTION):
		# return
	# mfile = fc.getSelectedFile()
	# filename = mfile.getPath()
	# if(filename == None):
		# return
	
	# Hardcode file name if less annoying - will overwrite previous file
	# Comment block above to remove prompt
	# ================================================================================
	filename = OutputFile
	
	
	# Open File for Writing
	# ================================================================================
	f=open(filename, 'w')
	f.write('Data for Graeme Smith @ Wave Shapes Machine - Gosford\n')
	f.write('_______________________________________________________\n')
	
	f.write('Date: ')
	f.write(time.strftime("%d/%m/%Y"))
	f.write('\n')
	
	f.write('Make: ')
	f.write(brd.getDesigner())
	f.write('\n')
	
	f.write('Board: ')
	f.write(brd.getModel())
	f.write('\n')
		
	f.write('Length: %.1f mm\n' % BoardLength)
	f.write('Width: %.1f mm\n' % (brd.getMaxWidth()*10))
	f.write('Thickness: %.1f mm\n' % (brd.getMaxThickness()*10))
	f.write('_______________________________________________________\n')
	
	f.write('Section Position')
	for SecPos in SectPositions:
		f.write(',%.1f' % SecPos)
	f.write('\n')
	
	f.write('Widths')
	for SW in SectWidths:
		f.write(',%.1f' % SW)
	f.write('\n')

	f.write('Thickness')
	for Thick in Thicknesses:
		f.write(',%.1f' % Thick)
	f.write('\n')	

	f.write('Vee')
	for V in Vees:
		f.write(',%.1f' % V)
	f.write('\n')
	
	f.write('Concave')
	for CC in Concaves:
		f.write(',%.1f' % CC)
	f.write('\n')
	
	f.write('Edge Height')
	for ETH in EdgeTangentHeights:
		f.write(',%.1f' % ETH)
	f.write('\n')
	
	f.write('Bottom Line')
	for BL in BottomLines:
		f.write(',%.1f' % BL)
	f.write('\n')
	
	f.write('_______________________________________________________\n')
	f.write('Deck / Rail Guide Points\n')
	j = 0
	for xPC in DeckGuidePCs:
		i = 0
		f.write('X%i' % (j+1))
		for SecPos in SectPositions:
			f.write(',%.1f' % (DeckGuideXs[j][i]))
			i = i + 1
		f.write('\n')
		i = 0
		f.write('Y%i' % (j+1))
		for SecPos in SectPositions:
			f.write(',%.1f' % (DeckGuideYs[j][i]))
			i = i + 1
		f.write('\n')
		j = j + 1
	
	f.write('_______________________________________________________\n')
	f.flush
	f.close
	print(filename)

BC2WS_Export()
