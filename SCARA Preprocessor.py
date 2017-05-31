

#Written by Andrew Wingate/ Evezor Inc.  Based on simpso_segmentize.py by Nicholas Seward/ConceptFORGE


#This program translates, rotates and transforms gcode files from cartesian space to scara space

#ALL LENGTHS IN mm

#EXPERIMANTAL. THIS CODE NEEDS IMPROVEMENT


import math
import sys


RIGHT_HANDED = False   #Mark true for right handed, false for left handed
fileInput = "DICKBUTT_0008"  #argument expects .gcode files
fileOutput = fileInput+"_out"
START_GCODE = ';G92 X-141.6 Y147.5 Z25\n'
END_GCODE = 'G1 X-45 Y135 F1200\nM84\n\n'
##############################
#DEFINE CONSTANTS
MAX_LENGTH = .5   #length of segmentized lines in millimeters

SKEW_D = 180 #HOW MUCH TO ROTATE OUTGOING GCODE
SKEW = math.radians(SKEW_D)


TRANSLATE = [246.9,318] #HOW FAR TO TRANSLATE OUTGOING GCODE FROM [0,0] 

FIRST_PARSE = False


L1=float(200) #LENGTH OF THETA LINK
L2=float(219) #LENGTH OF PHI LINK

L12=L1**2
L22=L2**2


RAPID_FEEDRATE = '1200'

prevWorkingPos = [15, 18, 0, 0, 1234] 
workingPos = [None,None,None,0,None]     
currentPos = [None,None,None,0,None]
startPos = [None,None,None,0,None]
prevScara = [None,None,None,0,None]
################################

fIn = fileInput+".gcode"
fOut = fileOutput+".gcode"

f = open(fIn,'r')
fo = open(fOut,'w')






#### Transform from cartesian system to scara space
def transform(point, rapid):
    scaraSegs=[None, None, None, None, None]
    R = math.hypot(point[0],point[1])
    gamma = math.atan2(point[1],point[0])
    beta = math.acos((R**2-L12-L22)/(-2*L1*L2))
    psi = math.pi-beta
    alpha = math.asin((L2*math.sin(psi))/R)

    if RIGHT_HANDED == True:  #Right Handed Operation
        scaraSegs[0]=math.degrees(gamma-alpha)
        scaraSegs[1]=math.degrees(psi)
    else:  #Left Handed Operation
        scaraSegs[0]=math.degrees(gamma+alpha)
        scaraSegs[1]=math.degrees(beta-math.pi)
    
    scaraSegs[2]=point[2]
    scaraSegs[3]=point[3]
    scaraSegs[4]=point[4]
    if FIRST_PARSE == False:
        print('scara first parse')
        global prevScara
        prevScara = scaraSegs
        finishingTouches(scaraSegs, rapid)
    else:
        l=distance(prevScara, scaraSegs)
        scaraSegs[4]=l/scaraSegs[4]
        finishingTouches(scaraSegs, rapid)
        prevScara=scaraSegs
    return
    
    

#### find new points from segmentation
def interpolate(start, end, i, n):
    midSegs=[None, None,None,None,None]
    for j in range(4):
        midSegs[j]=(i*end[j]+(n-i)*start[j])/n
        midSegs[4]=currentPos[4]
    return midSegs
    

#### Segmentize lines into pieces  
def segmentize(start, end, rapid):
    l=distance(start, end)
    if l<= MAX_LENGTH:
        end[4]=(1/currentPos[4])*l
        transform(end, rapid)
        return
    else:
        n=int(math.ceil(l/MAX_LENGTH))
        end[4]=(1/currentPos[4])*l/n
        for i in range(1, n+1):
            transform(interpolate(start, end, i, n),rapid)
    return 
    

#### Find distance of line segment 
def distance(start, end):
    return math.sqrt((end[0]-start[0])**2+(end[1]-start[1])**2+(end[2]-start[2])**2)



#### Put List back into gcode format
def finishingTouches(gCoder, rapid):
    if rapid == 0:
        fo.write('G0 ')
    else:
       fo.write('G1 ') 
    fo.write('X')
    fo.write(str("%.3f" % gCoder[0]))
    fo.write(' Y')
    fo.write(str("%.3f" % gCoder[1]))
    if gCoder[2] == prevScara[2]:
        pass
    else:
        fo.write(' Z')
        fo.write(str("%.3f" % gCoder[2]))
    if gCoder[3] == prevScara[3]:
        pass
    else:
        fo.write(' E')
        fo.write(str("%.2f" % gCoder[3]))
    
    fo.write(' F')
    if rapid == 0:
        fo.write(RAPID_FEEDRATE)
    else:
        fo.write(str(int(gCoder[4])))
    fo.write('\n')
    return




#### Move points from 0,0 to translate space and rotate by skew angle
def translate(toTranslate, *args):
    hyp = math.hypot(toTranslate[0], toTranslate[1])
    hypAngle = math.atan2(toTranslate[1],toTranslate[0])
    newHypAngle = hypAngle+SKEW
    
    for i in range(len(TRANSLATE)):
        
        if i < 1:
            toTranslate[i]= math.cos(newHypAngle)*hyp
        elif i < 2:
            toTranslate[i]= math.sin(newHypAngle)*hyp
        else:
            pass
        toTranslate[i]= toTranslate[i]+TRANSLATE[i]
        
    return toTranslate




#### Parse gcode line and put variables into a list
def parse(toParse = [], *args):    
    parsed = [None,None,None,None,None]
    del toParse[0]
    for i in range(len(toParse)):
        parsing = toParse[i]
        if parsing[0] == 'X':
            string = parsing.replace('X','')
            try:
                parsed[0] = float(string)
            except:
                print ('error converting x to float')
                pass
        elif parsing[0] == 'Y':
            string = parsing.replace('Y','')
            try:
                parsed[1] = float(string)
            except:
                print ('error converting y to float')
                pass
        elif parsing[0] == 'Z':
            string = parsing.replace('Z','')
            try:
                parsed[2] = float(string)
            except:
                print ('error converting Z to float')
                pass
        elif parsing[0] == 'E':
            string = parsing.replace('E','')
            try:
                parsed[3] = float(string)
            except:
                print ('error converting E to float')                
                pass
        elif parsing[0] == 'F':
            string = parsing.replace('F','')
            try:
                parsed[4] = float(string)
            except:
                print ('error converting F to float')
                print (parsing)
                pass        
        else:
            pass
    return parsed





#Handle incoming gcode, send to parser and transform
########################################################


#GCODE BEGIN TEXT
fo.write(';This file had been transformed by SCARA Preprocessor with \n;Translate:['+str(TRANSLATE[0])+','+str(TRANSLATE[1])+ '] and Rotation of: '+str(SKEW_D)+' as variables\n;Transform Start\n')
fo.write('Start GCODE\n')
fo.write(START_GCODE + '\n')

for line in f:
    
    if line[0]==';' or line[0]=='\n':  #deal with pure comment lines
        line = line.strip()

    else:
        line = line.strip()
        Gline = line.split(';')[0].split() #split line into list and remove comments
        Gline = line.split('(P')[0].split()
        
        
        if Gline[0] == 'G1' or Gline[0] == 'G01' or Gline[0] == 'G0' or Gline[0] == 'G00':
            
            if Gline[0] == 'G0' or Gline[0] == 'G00':
                rapid = 0
            else:
                rapid = 1


            workingPos = parse(Gline) #parse line for gcode values            
                       

            for i in range(5):  ## fill out the list 
                if workingPos[i] is None:
                    workingPos[i]=prevWorkingPos[i]
                else:
                    pass


            if workingPos[0] == prevWorkingPos[0] and workingPos[1] == prevWorkingPos[1] and workingPos[2] == prevWorkingPos[2]:  ## if it's a 0 motion move just pass
                fo.write('G1 E')
                fo.write(str(workingPos[3]))
                fo.write(' F')
                fo.write(str(workingPos[4]))
                fo.write(' ;this should be retracts\n')
                pass
                
            

            else:
                
                prevWorkingPos = list(workingPos)  #copy list for reference with next Gline
                currentPos = translate(workingPos)     #translate points in cartesian space to defined workpiece/bed position       
                workingPos = [None,None,None,None,None]
                               
                if FIRST_PARSE is False:
                    transform(currentPos, rapid)
                    fo.write(";GCODE PARSE BEGINNING\n")
                    FIRST_PARSE = True
                    startPos=currentPos

                elif rapid == 0:         ###deal with rapid moves
                    transform(currentPos, rapid)
                    startPos=currentPos
                    
                else:
                    segmentize(startPos,currentPos, rapid)                
                    startPos=currentPos                
           

        elif Gline[0] == 'G92':
            prevWorkingPos[3] = 0
            currentPos[3] = 0
            for i in range(len(Gline)): #pass everything else straight to output file
                fo.write(Gline[i])
                fo.write(' ')
            fo.write(" ;reset e\n")  #need to finish writing for other axis
            

        else:
            for i in range(len(Gline)): #pass everything else straight to output file
                fo.write(Gline[i])
                fo.write(' ')
            fo.write(" ;straight output\n")
fo.write(END_GCODE)   #SOME END GCODE           
f.close()
fo.close()
print('done')
