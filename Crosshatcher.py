'''
This code is poorly documented but to outline the premise:
The input image is used to generate "Regions" of adjacent pixels that all
    fall within one of any number of pre-defined lightness ranges.
The program determines what density of crosshatch spacing is needed to replicate
    the same degree of "lightness" and computes a drawpath to crosshatch the region.
All drawpaths are combined into one master drawpath which is returned to the
    calling module.
'''
import turtle
import math
import PIL
from PIL import Image
from collections import deque
import pdb
import Driver

class Region:

    lightVal = None         #lightness value of region
    pixelArray = None       #Boolean array describing pixels in region relative to mins/maxs
    numPixels = None
    xMin = None
    xMax = None
    yMin = None
    yMax = None
    
    def __init__(self, val, x, y):
        self.lightVal = val
        self.pixelList = []
        self.pixelArray = []
        self.numPixels = 0
        self.xMin = x
        self.xMax = x
        self.yMin = y
        self.yMax = y

    def LValue(self, pixel):
        return pixel[1]*im.size[0] + pixel[0]

    def sortPList(self):
        self.mergesort(self.pixelList)

    def mergesort(self, inputList):
        if(len(inputList) > 1):
            mid = len(inputList)//2
            leftList = inputList[:mid]
            rightList = inputList[mid:]

            self.mergesort(leftList)
            self.mergesort(rightList)

            iterR = 0
            iterL = 0
            iterMain = 0
            while(iterR < len(rightList) and iterL < len(leftList)):       
                if(self.LValue(rightList[iterR]) < self.LValue(leftList[iterL])):
                    inputList[iterMain] = rightList[iterR]
                    iterR = iterR + 1
                    iterMain = iterMain + 1
                else:
                    inputList[iterMain] = leftList[iterL]
                    iterL = iterL + 1
                    iterMain = iterMain + 1

            while(iterR < len(rightList)):
                inputList[iterMain] = rightList[iterR]
                iterR = iterR + 1
                iterMain = iterMain + 1
                
            while(iterL < len(leftList)):
                inputList[iterMain] = leftList[iterL]
                iterL = iterL + 1
                iterMain = iterMain + 1


def findRegion(x, y, reg, visitedPixels, im, imData, thresholdList, valueList):

    regionPixels = []
    activePixelList = deque()
    activePixelList.append((x, y))
    nextPixelList = deque()
    while(len(activePixelList) > 0):
        for p in activePixelList:
            #add current pixel to main visited list and region pixel list
            visitedPixels[p[1]*im.size[0] + p[0]] = 1
            regionPixels.append((p[0],p[1]))

            #keep track of region mins and maxs
            if(p[0] < reg.xMin):
                reg.xMin = p[0]
            if(p[0] > reg.xMax):
                reg.xMax = p[0]
            if(p[1] < reg.yMin):
                reg.yMin = p[1]
            if(p[1] > reg.yMax):
                reg.yMax = p[1]

            #add neighboring pixels to active list
            #check right
            if(p[0]+1 < im.size[0] and visitedPixels[p[1]*im.size[0] + p[0] + 1] == 0 and (not (p[0]+1,p[1]) in nextPixelList) and outputColor(imData[p[0]+1, p[1]], thresholdList, valueList) == reg.lightVal):
                nextPixelList.append((p[0]+1, p[1]))
            #check down
            if(p[1]+1 < im.size[1] and visitedPixels[(p[1]+1)*im.size[0] + p[0]] == 0 and (not (p[0],p[1]+1) in nextPixelList) and outputColor(imData[p[0], p[1]+1], thresholdList, valueList) == reg.lightVal):
                nextPixelList.append((p[0], p[1]+1))
            #check left
            if(p[0]-1 > -1 and visitedPixels[p[1]*im.size[0] + p[0] - 1] == 0 and (not (p[0]-1,p[1]) in nextPixelList) and outputColor(imData[p[0]-1, p[1]], thresholdList, valueList) == reg.lightVal):
                nextPixelList.append((p[0]-1, p[1]))
            #check up
            if(p[1]-1 > -1 and visitedPixels[(p[1]-1)*im.size[0] + p[0]] == 0 and (not (p[0],p[1]-1) in nextPixelList) and outputColor(imData[p[0], p[1]-1], thresholdList, valueList) == reg.lightVal):
                nextPixelList.append((p[0], p[1]-1))
                
        activePixelList.clear()
        for i in range(0, len(nextPixelList)):
            activePixelList.append(nextPixelList.pop())
    
    #Populate boolean array defining visited pixels
    #initialize pixelArray as 0's
    for i in range(0, reg.xMax - reg.xMin + 1):
        temp = []
        for j in range(0, reg.yMax - reg.yMin + 1):
            temp.append(0)
        reg.pixelArray.append(temp)
    #flag pixels in region
    for e in regionPixels:
        reg.pixelArray[e[0] - reg.xMin][e[1] - reg.yMin] = 1
        reg.numPixels += 1

        
def outputColor(pixel, thresholdList, valueList):
    ## Outputs percieved lighness of a pixel (0=black, 255=white)
    lum = pixel[0]*0.299 + pixel[1]*0.587 + pixel[2]*0.114
    for i in range(0, len(thresholdList)):
        if lum <= thresholdList[i]:
            return valueList[i]


def computeLineSpacing(lightnessVal, lineThickness, mode, xSize, ySize):
    ## Outputs a crosshatch spacing to replicate a particular lightness value
    if(lightnessVal == 255):
        return xSize + ySize
    percentBlk = (255-lightnessVal)/255
    if(mode <= 1): #Line shading
        spacing = lineThickness + (1-percentBlk)/percentBlk
        return spacing
    if(mode == 2): #Crosshatch shading
        spacing = lineThickness + ((-1*(lineThickness)**2 * (percentBlk - 1))**(1/2) + lineThickness*-1*percentBlk + lineThickness) / percentBlk
        return spacing


def preBlur(radius):
    tempData = im.load()
    for y in range(0, ySize):
        for x in range(0, xSize):
            r = 0
            g = 0
            b = 0
            for kernY in range(y-radius, y+radius+1):
                for kernX in range(x-radius, x+radius+1):
                    #Corner cases
                    if(kernX < 0 and kernY < 0):
                        r = r + tempData[0,0][0]
                        g = g + tempData[0,0][1]
                        b = b + tempData[0,0][2]
                    elif(kernX >= xSize and kernY < 0):
                        r = r + tempData[xSize-1,0][0]
                        g = g + tempData[xSize-1,0][1]
                        b = b + tempData[xSize-1,0][2]
                    elif(kernX < 0 and kernY >= ySize):
                        r = r + tempData[0,ySize-1][0]
                        g = g + tempData[0,ySize-1][1]
                        b = b + tempData[0,ySize-1][2]
                    elif(kernX >= xSize and kernY >= ySize):
                        r = r + tempData[xSize-1,ySize-1][0]
                        g = g + tempData[xSize-1,ySize-1][1]
                        b = b + tempData[xSize-1,ySize-1][2]
                    #Edge cases
                    elif(kernX < 0):
                        r = r + tempData[0,kernY][0]
                        g = g + tempData[0,kernY][1]
                        b = b + tempData[0,kernY][2]
                    elif(kernX >= xSize):
                        r = r + tempData[xSize-1,kernY][0]
                        g = g + tempData[xSize-1,kernY][1]
                        b = b + tempData[xSize-1,kernY][2]
                    elif(kernY < 0):
                        r = r + tempData[kernX,0][0]
                        g = g + tempData[kernX,0][1]
                        b = b + tempData[kernX,0][2]
                    elif(kernY >= ySize):
                        r = r + tempData[kernX,ySize-1][0]
                        g = g + tempData[kernX,ySize-1][1]
                        b = b + tempData[kernX,ySize-1][2]
                    #Normal case
                    else:
                        r = r + tempData[kernX,kernY][0]
                        g = g + tempData[kernX,kernY][1]
                        b = b + tempData[kernX,kernY][2]
            r = r/(2*radius+1)**2
            g = g/(2*radius+1)**2
            b = b/(2*radius+1)**2
            imData[x,y] = (round(r), round(g), round(b), 255)


def resize(image, width):
    if(width == image.size[0]):
        return image
    oldX = image.size[0]
    oldY = image.size[1]
    oldRatio = oldX / oldY
    newY = math.floor(width / oldRatio)
    return image.resize((width, newY), PIL.Image.BICUBIC)


def findDrawPath(imageName, mode, thresholds):
    im = Image.open(imageName)
    #im = resize(im, 200)
    #im.show()
    imData = im.load()
    xSize = im.size[0]
    ySize = im.size[1]
    numThresholds = thresholds                      #Number of lightness values to resolve
    blurAmount = 1                                  #Radius of pre-blur convolution kernel            
    lineWidth = 1                                   #Thickness of drawing line
    fillMode = mode                                 #Decides between line fill and crosshatching, 0=line, 1=smart line, 2=crosshatch
    minRegionSize = 5                               #Minimum number of pixels for a region, all smaller regions are discarded
    thresholdList = []                              #List of upper bounds for each threshold
    valueList = []                                  #Values of each lighness, dark to light
    visitedPixels = [0]*(im.size[0] * im.size[1])   #Single dim array representing each pixel, 0=no 1=yes
    regionList = []                                 #List of lightness regions
    drawPath = []                                   #Coordinates for drawing: (x, y, penIsDown) 0=no 1=yes




    #Init thresholdList and valueList
    for i in range(0, numThresholds):
        thresholdList.append(255/numThresholds * (i+1))
        if(i==0):
            valueList.append(0)
        elif(i==numThresholds-1):
            valueList.append(255)
        else:
            valueList.append(255/numThresholds * i + (255/numThresholds)/2)

    print("Lightness thresholds:", numThresholds)

    # Pre blur image
    print("Pre-blurring image")
    #preBlur(blurAmount)

    # Create Regions based on image input
    print("Finding regions")
    for y in range(0, im.size[1]):
        for x in range(0, im.size[0]):
            if(visitedPixels[y*im.size[0] + x] == 0):
                r = Region(outputColor(imData[x, y], thresholdList, valueList), x, y)
                findRegion(x, y, r, visitedPixels, im, imData, thresholdList, valueList)
                #disregard regions of small enough size
                if(r.numPixels >= minRegionSize):
                    regionList.append(r)

    print("Regions found:", len(regionList))

    '''
    opt = 0
    for r in regionList:
        opt = opt + (len(r.pixelList)*((255-r.lightVal)/255) + lineWidth*(len(r.pixelList)/computeLineSpacing(r.lightVal, lineWidth, fillMode)**2))
    print("Optimal drawpath:", opt)
    '''

    # Compute draw path
    # Draw path consists of 3-tuples (int x, int y, bool penDown)
    # penDown = 0 means pen is up for duration of this move, etc.
    print("Compiling drawPath")
    penDown = False
    forward = True
    for r in regionList:
        
        if(r.lightVal == 255):
            continue

        spacing = computeLineSpacing(r.lightVal, lineWidth, fillMode, xSize, ySize)
        
        #Compute horizontal lines
        if(fillMode == 0 or (fillMode == 1 and r.xMax - r.xMin > r.yMax - r.yMin) or fillMode == 2):
            yTrue = r.yMin
            y = yTrue
            while(y <= r.yMax):
                if(forward): #reverses direction of drawing for each line
                    for x in range(r.xMin, r.xMax+1):
                        if(r.pixelArray[x-r.xMin][y-r.yMin] == 1 and (not penDown)):
                            drawPath.append((x, y, 0))
                            penDown = True
                        elif(r.pixelArray[x-r.xMin][y-r.yMin] == 0 and penDown):
                            drawPath.append((x-1, y, 1))
                            penDown = False
                        #pick up pen if line is drawn to edge of region
                        if(x == r.xMax and penDown):
                            drawPath.append((x, y, 1))
                            penDown = False
                    forward = False
                else:
                    for x in range(r.xMax, r.xMin - 1, -1):
                        if(r.pixelArray[x-r.xMin][y-r.yMin] == 1 and (not penDown)):
                            drawPath.append((x, y, 0))
                            penDown = True
                        elif(r.pixelArray[x-r.xMin][y-r.yMin] == 0 and penDown):
                            drawPath.append((x+1, y, 1))
                            penDown = False
                        #pick up pen if line is drawn to edge of region
                        if(x == r.xMin and penDown):
                            drawPath.append((x, y, 1))
                            penDown = False
                    forward = True
                yTrue = yTrue + spacing
                y = round(yTrue)

        #Compute vertical lines
        if((fillMode == 1 and r.xMax - r.xMin < r.yMax - r.yMin) or (fillMode == 2 and r.lightVal != 0)):
            xTrue = r.xMin
            x = xTrue
            while(x <= r.xMax):
                if(forward): #reverses direction of drawing for each line
                    for y in range(r.yMin, r.yMax+1):
                        if(r.pixelArray[x-r.xMin][y-r.yMin] == 1 and (not penDown)):
                            drawPath.append((x, y, 0))
                            penDown = True
                        elif(r.pixelArray[x-r.xMin][y-r.yMin] == 0 and penDown):
                            drawPath.append((x, y-1, 1))
                            penDown = False
                        #pick up pen if line is drawn to edge of region
                        if(y == r.yMax and penDown):
                            drawPath.append((x, y, 1))
                            penDown = False
                    forward = False
                else:
                    for y in range(r.yMax, r.yMin - 1, -1):
                        if(r.pixelArray[x-r.xMin][y-r.yMin] == 1 and (not penDown)):
                            drawPath.append((x, y, 0))
                            penDown = True
                        elif(r.pixelArray[x-r.xMin][y-r.yMin] == 0 and penDown):
                            drawPath.append((x, y+1, 1))
                            penDown = False
                        #pick up pen if line is drawn to edge of region
                        if(y == r.yMin and penDown):
                            drawPath.append((x, y, 1))
                            penDown = False
                    forward = True
                xTrue = xTrue + spacing
                x = round(xTrue)

    #Start drawpath with border
    finalPath = []
    finalPath.append((0,0,0))
    finalPath.append((xSize, 0, 1))
    finalPath.append((xSize, ySize, 1))
    finalPath.append((0, ySize, 1))
    finalPath.append((0, 0, 1))

    #Combine drawpaths
    for e in drawPath:
        finalPath.append(e)            
    print("Drawpath complete")
    return finalPath

