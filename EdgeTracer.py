import turtle
import PIL
from PIL import Image
from PIL import ImageDraw
import math
import numpy as np
import pdb

class Pixel:
    L = None
    angle = None
    hasBeenDrawn = None

    def __init__(self, lIn, angleIn):
        self.L = lIn
        self.angle = angleIn
        self.hasBeenDrawn = False

def preBlur(radius):
    tempData = im.load()
    for y in range(0, ySize):
        for x in range(0, xSize):
            L = 0
            for kernY in range(y-radius, y+radius+1):
                for kernX in range(x-radius, x+radius+1):
                    #Corner cases
                    if(kernX < 0 and kernY < 0):
                        L = L + tempData[0,0]
                    elif(kernX >= xSize and kernY < 0):
                        L = L + tempData[xSize-1,0]
                    elif(kernX < 0 and kernY >= ySize):
                        L = L + tempData[0,ySize-1]
                    elif(kernX >= xSize and kernY >= ySize):
                        L = L + tempData[xSize-1,ySize-1]
                    #Edge cases
                    elif(kernX < 0):
                        L = L + tempData[0,kernY]
                    elif(kernX >= xSize):
                        L = L + tempData[xSize-1,kernY]
                    elif(kernY < 0):
                        L = L + tempData[kernX,0]
                    elif(kernY >= ySize):
                        L = L + tempData[kernX,ySize-1]
                    #Normal case
                    else:
                        L = L + tempData[kernX,kernY]
            L = L/(2*radius+1)**2
            imData[x,y] = (round(L))


def sobel(pixelArray, outputImage, im, edgeThreshold):
    '''Finds edges in image based using Sobel convolution
        
        Args:
            pixelArray (ndarray):   2D array of Pixel objects to be defined by
            the Sobel function.
            outputImage (Image):    Image used to visually display output of the 
            Sobel function.
    '''

    tempData = im.load()
    xSize = im.size[0]
    ySize = im.size[1]
    draw = ImageDraw.Draw(outputImage, 'L')
    sobX = [[-1, -2, -1],
            [ 0,  0,  0],
    		[ 1,  2,  1]]

    sobY = [[-1,  0,  1],
    		[-2,  0,  2],
    		[-1,  0,  1]]

    for y in range(0, ySize):		#These move the kernel through the image
        for x in range(0, xSize):
            xGrad = 0				#X and Y gradient intensity at pixel [x,y]
            yGrad = 0
            for kernY in range(0, 3):		#These iterate through the kernel
                for kernX in range(0, 3):
                    pixX = x + kernX - 1
                    pixY = y + kernY - 1
                    #Corner cases
                    if(pixX < 0 and pixY < 0):
                        xGrad += tempData[0, 0] * sobX[kernX][kernY]
                        yGrad += tempData[0, 0] * sobY[kernX][kernY]
                    elif(pixX >= xSize and pixY < 0):
                        xGrad += tempData[xSize-1, 0] * sobX[kernX][kernY]
                        yGrad += tempData[xSize-1, 0] * sobY[kernX][kernY]
                    elif(pixX < 0 and pixY >= ySize):
                        xGrad += tempData[0, ySize-1] * sobX[kernX][kernY]
                        yGrad += tempData[0, ySize-1] * sobY[kernX][kernY]
                    elif(pixX >= xSize and pixY >= ySize):
                        xGrad += tempData[xSize-1, ySize-1] * sobX[kernX][kernY]
                        yGrad += tempData[xSize-1, ySize-1] * sobY[kernX][kernY]
                    #Edge cases
                    elif(pixX < 0):
                        xGrad += tempData[0, pixY] * sobX[kernX][kernY]
                        yGrad += tempData[0, pixY] * sobY[kernX][kernY]
                    elif(pixX >= xSize):
                        xGrad += tempData[xSize-1, pixY] * sobX[kernX][kernY]
                        yGrad += tempData[xSize-1, pixY] * sobY[kernX][kernY]
                    elif(pixY < 0):
                        xGrad += tempData[pixX, 0] * sobX[kernX][kernY]
                        yGrad += tempData[pixX, 0] * sobY[kernX][kernY]
                    elif(pixY >= ySize):
                        xGrad += tempData[pixX, ySize-1] * sobX[kernX][kernY]
                        yGrad += tempData[pixX, ySize-1] * sobY[kernX][kernY]
                    #Normal case
                    else:
                        xGrad += tempData[pixX, pixY] * sobX[kernX][kernY]
                        yGrad += tempData[pixX, pixY] * sobY[kernX][kernY]
                   
            rawGradient = (xGrad**2 + yGrad**2)**0.5 * 0.25  #Scale back down to 0 <= x <= 255
            if(rawGradient >= edgeThreshold):
                draw.point([x, y], round(rawGradient))
            if(xGrad == 0):
                pixelArray[x,y] = Pixel(rawGradient, None)
            else:
                pixelArray[x,y] = Pixel(rawGradient, math.atan2(yGrad, xGrad))


def traceEdges(pixelArray, drawThreshold, xSize, ySize):
    '''Computes edge drawpath based on output of Sobel analysis
        
        Args:
            pixelArray (ndarray):   2D array of Pixel objects.
            drawThreshold (int):    Edges with intensity less than this threshold will be ignored.

        Returns:
            drawPath (List of (x,y,pen)):   List of coordinates and pen instructions to draw image.            
    '''

    finalDrawPath = [(0,0,0)]
    drawPathList = []
    probe = [0.0, 0.0]  
    stepSize = 2.5              #Distance moved in direction specified by edge gradient
    probeOverlapDist = 0.5      #Collision size of probe when comparing to previous probe positions
    pixelsDrawn = 0
    pixelMarkRadius = 2         #Radius around probecoord path to mark pixels as drawn

    #Scan image for undrawn pixel above threshold
    for y in range(0, ySize):
        for x in range(0, xSize):
            if(pixelArray[x,y].L >= drawThreshold and pixelArray[x,y].hasBeenDrawn == False):
                prevProbeCoords = [(x,y)]        #Tuples of coords of previous probe positions
                currDrawPath = []
                
                clockPath = probeScan(False, pixelArray, x, y, prevProbeCoords, stepSize, probeOverlapDist, drawThreshold, xSize, ySize)
                antiClockPath = probeScan(True, pixelArray, x, y, prevProbeCoords, stepSize, probeOverlapDist, drawThreshold, xSize, ySize)

                #Modify first element in drawpath such that the pen is up
                i = len(clockPath)-1
                clockPath[i] = (clockPath[i][0], clockPath[i][1], 0)

                #Add elements to drawpath in decsending order from clockPath, 
                #ascending order from antiClockPath
                for i in range(len(clockPath)-1, -1, -1):
                    currDrawPath.append(clockPath[i])
                for e in antiClockPath:
                    currDrawPath.append(e)

                #Iterate through probe path and mark pixels as drawn
                for c in prevProbeCoords:
                    rpx = round(c[0])
                    rpy = round(c[1])
                    for j in range(rpy-pixelMarkRadius, rpy+pixelMarkRadius+1):
                        for i in range(rpx-pixelMarkRadius, rpx+pixelMarkRadius+1):
                            if(i >= 0 and i < xSize and j >=0 and j < ySize):   #Edge cases
                                pixelArray[i,j].hasBeenDrawn = True
                                pixelsDrawn += 1

                #Append currDrawPath as a new element in drawPathList
                drawPathList.append(currDrawPath)

    ##Sort drawPathLists by nearest neighbor
    lastCoordIndex = 0  #Index in mainDrawPath of last-added coordinates
    bestPathIndex = 0   #Index in drawPathList of closest next line
    lastCoords = (0,0)
    #This iterates the max number of times it can take to sort the dPL
    for counter in range(0, len(drawPathList)):
        bestDist = None
        #Find closest start point to last end point
        for i in range(0, len(drawPathList)):
            d = ((lastCoords[0] - drawPathList[i][0][0])**2 + (lastCoords[1] - drawPathList[i][0][1])**2)**0.5
            if(bestDist == None or d < bestDist):
                bestDist = d
                bestPathIndex = i
                lastCoords = (drawPathList[i][0][0], drawPathList[i][0][1])
        #Append closest next path to finalDrawPath
        for e in drawPathList[bestPathIndex]:
            finalDrawPath.append(e)
        #Delete added path from drawPathList
        del drawPathList[bestPathIndex]
            

    return finalDrawPath

def probeScan(isClockwise, pixelArray, startX, startY, prevProbeCoords, stepSize, probeOverlapDist, drawThreshold, xSize, ySize):
    probe = [startX,startY]
    drawPath = [(startX,startY,1)]      #PRE LOOP
    currPx = [startX,startY]            #Current pixel that is guiding drawpath

    searchRadius = 2                    #How far to look for nearest high pixel

    #This is the main while loop that runs the edge following algorithm
    while(True):

        #Move probe 1 step in current pixel's direction
        if(isClockwise):
            if(pixelArray[currPx[0],currPx[1]].angle == None):
                probe[0] = currPx[0] - stepSize
                probe[1] = currPx[1]
            else:
                probe[0] = currPx[0] + -stepSize*math.sin(pixelArray[currPx[0],currPx[1]].angle)
                probe[1] = currPx[1] + stepSize*math.cos(pixelArray[currPx[0],currPx[1]].angle)
        else:
            if(pixelArray[currPx[0],currPx[1]].angle == None):
                probe[0] = currPx[0] + stepSize
                probe[1] = currPx[1]
            else:
                probe[0] = currPx[0] + stepSize*math.sin(pixelArray[currPx[0],currPx[1]].angle)
                probe[1] = currPx[1] + -stepSize*math.cos(pixelArray[currPx[0],currPx[1]].angle)
        rpx = round(probe[0])
        rpy = round(probe[1])

        #Check if probe has moved to invalid position, break if so
        # - Probe has moved off picture
        if(not(rpx >= 0 and rpx < xSize and rpy >=0 and rpy < ySize)):
            break
        # - Probe is too close to previously drawn position
        breakFlag = False
        for c in prevProbeCoords:
            if(((c[0]-probe[0])**2 + (c[1]-probe[1])**2)**0.5 < probeOverlapDist):
                #pdb.set_trace()
                breakFlag = True
        if(breakFlag):
            break

        #Add new probe position to drawpath and prevProbeCoords
        drawPath.append((probe[0], probe[1], 1))
        prevProbeCoords.append((probe[0], probe[1]))

        
        #Search for nearest high pixel
        bestDist = None
        for j in range(rpy-searchRadius, rpy+searchRadius+1):
            for i in range(rpx-searchRadius, rpx+searchRadius+1):
                if(i >= 0 and i < xSize and j >=0 and j < ySize):   #Edge cases
                    if(pixelArray[i,j].L >= drawThreshold and pixelArray[i,j].hasBeenDrawn == False):
                        d = ((probe[0]-i)**2 + (probe[1]-j)**2)**0.5
                        if(bestDist == None or d < bestDist):
                            bestDist = d
                            currPx = [i,j]

        #If next pixel exists, restart loop with that pixel
        #Otherwise, break while loop
        if(bestDist == None):
            break

    return drawPath

def turtleDraw(drawPath):
    t = turtle
    for e in drawPath:
        if(e[2] == 0):
            t.penup()
        else:
            t.pendown()
        t.goto(round(e[0]), -round(e[1]))


def findDrawPath(imageString, edgeThreshold):
    im = Image.open(imageString)
    im = im.convert('L') #Greyscale conversion
    imData = im.load()
    xSize = im.size[0]
    ySize = im.size[1]

    print("Running Sobel analysis")
    #Create 2D List of Pixel objects
    pArray = np.empty([xSize, ySize], dtype=Pixel)

    #Creates new Image to display output of Sobel analysis
    sobelOutput = Image.new('L', (xSize, ySize))

    #preBlur(1)
    #im.show()
    sobel(pArray, sobelOutput, im, edgeThreshold)
    
    sobelOutput.show()      #****COMMENT/UNCOMMENT TO TOGGLE SOBEL OUTPUT****
    print("Computing drawpath")
    path = traceEdges(pArray, edgeThreshold, xSize, ySize)
    
    #Start drawpath with border
    finalPath = []
    finalPath.append((0,0,0))
    finalPath.append((xSize, 0, 1))
    finalPath.append((xSize, ySize, 1))
    finalPath.append((0, ySize, 1))
    finalPath.append((0, 0, 1))

    #Combine drawpaths
    for e in path:
        finalPath.append(e)
    
    print("Drawpath complete")
    return finalPath
