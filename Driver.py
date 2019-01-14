import pigpio as pig
#import pynput
#from pynput.keyboard import Key, Listener
import matplotlib.pyplot as plt
import time
import math
#import pdb

pi = pig.pi()

motorX = [27, 22]                        #[Step pin, Dir pin]
motorY = [4, 17]

pi.set_mode(motorX[0], pig.OUTPUT)      # X Motor Step
pi.set_mode(motorX[1], pig.OUTPUT)      # X Motor Dir

pi.set_mode(motorY[0], pig.OUTPUT)      # Y Motor Step
pi.set_mode(motorY[1], pig.OUTPUT)      # Y Motor Dir

pi.set_mode(5, pig.OUTPUT)              #Enable

STEPS_PER_MM = 12.5125  #12.468 
STEPS_PER_IN = 317.8175
PENWIDTH = 15

stepMode = 2                            #0=Full, 1=Half, 2=Quarter, 3=Eight, 4=Sixteenth
currStepX = 0
currStepY = 0
spsMain = 3000
accelStart = 1600
accelDist = 500
spsCurr = 0
spsCurrX = 0
spsCurrY = 0
#Uncomment this block to use key commands (debugging mostly)
#Required uncommenting import statements at top as well
''' 
def on_press(key):
    if(key.char == 'c'):
        print(currStepX)
        print(currStepY)
    if(key.char == 'x'):
        pi.write(5, 1)      #enable off
        pi.stop()
    if(key.char == 'e'):
        pi.write(5, 1)      #pulse enable
        time.sleep(0.1)
        pi.write(5, 0)

def on_release(key):
    if(key == Key.esc):
        return False

lis = Listener(on_press=on_press, on_release=on_release)
lis.start()
'''
def getPos():
    return (currStepX, currStepY)

def setPos(x, y):
    currStepX = x
    currStepY = y

def setSpeed(sps):
    spsMain = sps

def setAccelStart(sps):
    accelStart = sps

def setAccelDist(dist):
    accelDist = dist

def setStepMode(mode):
    #Set step-based variables down to their base values
    spsMain = spsMain / 2**stepMode
    accelStart = accelStart / 2**stepMode
    accelDist = accelDist / 2**stepMode

    #Set new stepMode and recalculate dependent variables
    stepMode = mode
    spsMain = spsMain * 2**stepMode
    accelStart = accelStart * 2**stepMode
    accelDist = accelDist * 2**stepMode
    

def Step(m, direct):
    pi.write(m[1], direct)
    pi.write(m[0], 1)
    pi.write(m[0], 0)


def calcDelay(sps):
    if(sps != 0):
        return 1/sps
    else:
        return 999999999999


def goto(xRaw, yRaw):
    global spsMain
    global currStepX
    global currStepY
    global accelStart
    global accelDist
    global spsCurr
    global spsCurrX
    global spsCurrY

    x = round(xRaw)
    y = round(yRaw)

    if(x == currStepX and y == currStepY):
        return
    
    accelRate = (spsMain**2-accelStart**2) / (2*accelDist)
    startX = currStepX
    startY = currStepY
    spsCurr = accelStart
    xSteps = math.fabs(x - currStepX)      #Path length for X
    ySteps = math.fabs(y - currStepY)      #Path length for Y
    if(xSteps > 0):
        pSlope = (y - currStepY)/(x - currStepX)
    else:
        pSlope = 9999999999999
    dist = (xSteps**2 + ySteps**2)**0.5
    errDist = 0
    holdX = False
    holdY = False
    maxError = 5
    
    lastStepTimeX = 0
    lastStepTimeY = 0
    
    t0 = time.time()
    MainSpeed = []
    XPos = []
    YPos = []
    XSpeed = []
    YSpeed = []
    Time = []
    Err = []
    ErrX = []
    ErrY = []
    
    
    while(currStepX != x or currStepY != y):
        currTime = time.time()-t0 
        currDist = math.fabs(((currStepX - startX)**2 + (currStepY - startY)**2)**0.5)

        #Calculate component sps and find delay
        spsCurrX = math.fabs(spsCurr * (xSteps/dist))
        spsCurrY = math.fabs(spsCurr * (ySteps/dist))
        delayX = calcDelay(spsCurrX)
        delayY = calcDelay(spsCurrY)

        #Calculate error
        errDist = math.fabs((y - startY)*currStepX - (x - startX)*currStepY + x*startY - y*startX) / dist
        nearX = (currStepX + pSlope*(pSlope*startX - startY + currStepY)) / (1 + pSlope**2)
        nearY = pSlope*(nearX-startX) + startY
        errX = currStepX - nearX
        errY = currStepY - nearY

        #Set hold flag if error is too high
        if(errDist > maxError):
            if(math.fabs(startX - currStepX) > math.fabs(startX - nearX)):
                holdX = True
            if(math.fabs(startY - currStepY) > math.fabs(startY - nearY)):
                holdY = True
        else:
            holdX = False
            holdY = False
        
        if(spsCurrX != 0 and currStepX != x and currTime > lastStepTimeX + delayX and (not holdX)):
            
            #Take step
            if(x > currStepX):
                Step(motorX, 1)
                currStepX += 1
            else:
                Step(motorX, 0)
                currStepX -= 1

            #Update timestamp     
            lastStepTimeX = currTime
            
        if(spsCurrY != 0 and currStepY != y and currTime > lastStepTimeY + delayY and (not holdY)):

            #Take step
            if(y > currStepY):
                Step(motorY, 0)
                currStepY += 1
            else:                       
                Step(motorY, 1)
                currStepY -= 1
                
            #Update timestamp    
            lastStepTimeY = currTime

        #Modify delays for accel/decel
        currDist = math.fabs(((currStepX - startX)**2 + (currStepY - startY)**2)**0.5)
        if(dist < accelDist*2):                                 
            if(currDist < dist/2):
                spsCurr = (accelStart**2 + 2*accelRate*currDist)**0.5
            else:
                spsCurr = (accelStart**2 + 2*accelRate*(dist - currDist))**0.5
        else:
            if(currDist <= accelDist):
                spsCurr = (accelStart**2 + 2*accelRate*currDist)**0.5
            if(currDist > dist - accelDist):
                spsCurr = (accelStart**2 + 2*accelRate*(dist - currDist))**0.5

        XPos.append(currStepX)
        YPos.append(-currStepY)
        MainSpeed.append(spsCurr)    
        XSpeed.append(spsCurrX)
        YSpeed.append(spsCurrY)
        Time.append(currTime)
        Err.append(errDist)
        ErrX.append(nearX)
        ErrY.append(-nearY)
            
        
    #plt.plot(Time, MainSpeed)
    #plt.plot(Time, Err)
    #plt.plot(Time, XSpeed)
    #plt.plot(Time, YSpeed)
    #plt.plot(XPos, YPos)
    #plt.plot(ErrX, ErrY)
    #plt.show()
    
def penUp():
    pi.set_servo_pulsewidth(18, 965)
    time.sleep(0.1)

def penDown():
    pi.set_servo_pulsewidth(18, 800)
    time.sleep(0.1)

def stop():
    penUp()
    goto(0,0)
    enableOff()      #disable motors
    pi.stop()
    pynput.keyboard.Listener.stop(lis)

def enableOn():
    pi.write(5, 0)

def enableOff():
    pi.write(5, 1)


'''#Diagonal shaded square
penDown()
goto(2000, 0)
goto(2000, 2000)
goto(0, 2000)
goto(0, 0)
goto(2000, 2000)
penUp()
goto(2000, 0)
penDown()
goto(0, 2000)
penUp()
for i in range(0, 10):
    xc = i*200
    goto(xc, xc)
    penDown()
    goto(xc, -xc+2000)
    penUp()
    xc += 100
    goto(xc, -xc+2000)
    penDown()
    goto(xc, xc)
    penUp()'''

'''Concentric Circles
sX = 3000
sY = 2500
goto(sX, sY)
for i in range(1, 6):
    goto(sX + i*200*math.cos(math.radians(0)), sY)
    penDown()
    for j in range(0, 361):
        goto(sX + i*200*math.cos(math.radians(j)), sY + i*200*math.sin(math.radians(j)))
    penUp()'''

