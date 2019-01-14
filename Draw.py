import math
import turtle
#import Driver
import Crosshatcher
import EdgeTracer

def draw(drawPath, mode, lineWidth):
    '''Renders an image from a drawpath using turtle or cnc machine
        Args:
            drawPath (list):  List of 3-tuples (x, y, pen)
            mode:             0=turtle, 1=cnc
        Returns:
            None
    '''

    pathLength = 0
    drawLength = 0
    penUpLength = 0
    isPenUp = True
    lastX = 0
    lastY = 0
    
    if(mode == 0):
        print("Drawing image using Turtle")
        #Initialize turtle t
        t = turtle
        t.width(lineWidth)
        t.speed(0)
        t.ht()
        t.delay(0)
        t.tracer(10, 0)
        t.penup()
        
        pathLengthT = 0
        drawLengthT = 0
        penUpLengthT = 0
        isPenUp = True

        # Main Draw Loop
        for p in drawPath:
            drawLength = drawLength + ((p[0]-t.xcor())**2 + (-p[1]-t.ycor())**2)**0.5
            if(isPenUp):
                penUpLength = penUpLength + ((p[0]-t.xcor())**2 + (-p[1]-t.ycor())**2)**0.5
            if(p[2] == 0):
                #t.dot(2)
                t.penup()
                isPenUp = True
            else:
                t.pendown()
                isPenUp = False
            t.goto(p[0] - 200, -p[1] + 200)
            
        t.update()
        
    else:
        print("Drawing image using CNC")
        #Initalize CNC driver d
        import Driver
        d = Driver
        d.enableOn()
        d.penUp()

        pathLength = 0
        drawLength = pathLength
        isPenDown = True

        #Main Draw Loop
        for p in drawPath:
            moveDist = ((p[0] - lastX)**2 + (p[1] - lastY)**2)**0.5 / d.STEPS_PER_MM
            if(p[2] == 0 and isPenDown):
                d.penUp()
                isPenDown = False
                penUpLength += moveDist
            elif(p[2] == 1 and not(isPenDown)):
                d.penDown()
                isPenDown = True
                drawLength += moveDist
            d.goto(p[0]*12, p[1]*12)
            pathLength += moveDist
            lastX = p[0]
            lastY = p[1]
            
        d.stop()


    print("Image Complete!")
    print(len(drawPath), "Drawpath elements")
    print("Total toolpath distance:", pathLength) 
    print("Draw distance:", drawLength)
    print("PenUp distance:", penUpLength)


##### MAIN #####
imageString = "bob.jpg"    #Image filename to draw
lineWidth = 1                   #Width of pen line
computeMode = 1                 #0=Crosshatch, 1=EdgeTrace
outputMode = 1                  #0=Turtle, 1=CNC

#Calculate Drawpath
if(computeMode == 0):
    path = Crosshatcher.findDrawPath(imageString, 2, 10)
elif(computeMode == 1):
    path = EdgeTracer.findDrawPath(imageString, 40)
else:
    print("Invalid compute mode!")

#Draw 
draw(path, outputMode, lineWidth)



