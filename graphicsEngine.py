import numpy as np
import math
import pygame

#==========================
# Colors
#==========================
WHITE = (255,255,255)
GREEN = (0,255,0)
DARK_GREEN = (0,100,0)
DARK_BLUE = (0,0,100)
RED = (255,0,0)

class graphicsEngine:
    def __init__(self):
        #====================================================
        # DEBUGGING VARIABLES!                              =
        #====================================================
        self.debugRotation = 0
        self.debugTranslation = 1

        self.enableMouse = 0
        self.movingSpeed = 0.0001

        #----------------
        # Old rotations
        #----------------
        self.oldXAngle = -361
        self.oldYAngle = -361
        self.oldZAngle = -361

        #---------------------
        # Current translation
        #---------------------
        self.currentX = 0
        self.currentY = 0
        self.currentZ = 0

        #------------------
        # Old translations
        #------------------
        self.oldXTranslation = -9999
        self.oldYTranslation = -9999
        self.oldZTranslation = -9999

        #===================================
        # POINTS
        #===================================

        pygame.init()

        if self.enableMouse:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            

        #/////////////////////////////////////
        # PERSPECTIVE PROJECTION SETTINGS
        #/////////////////////////////////////
        self.width = 640
        self.heigth = 480

        self.near = 250
        self.far = 2000

        self.right = 640
        self.left = 0
        self.top = 480
        self.bottom = 0

        self.scaling = 1

        #/////////////////////////////////////
        # POINT DRAWING SETTINGS
        #/////////////////////////////////////

        self.pointRadius = 4
        self.pointThickness = 1

        #/////////////////////////////////////
        # ZOOM SETTINGS
        #/////////////////////////////////////

        self.zoomStep = 1

        #initialize the screen
        size = [640,480]
        self.screen = pygame.display.set_mode(size)

        self.screen.set_alpha(None)

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 18)

        self.running = True

        self.pointMatrix = np.matrix('100,100,0,1;100,-100,0,1;-100,100,0,1;-100,-100,0,1;\
              100,100,100,1;100,-100,100,1;-100,100,100,1;-100,-100,100,1')

        self.lineMatrix = np.matrix('0,1;1,3;3,2;0,2;\
               0,4;1,5;2,6;3,7;\
               4,5;5,7;7,6;4,6\
              ')
        self.polygons = np.matrix('0,1,2,0;\
                      1,2,3,3;\
                      4,5,6,4\
                     ')

        #=================
        # Matrices
        #=================
        self.Rx = np.zeros((4,4))
        self.Ry = np.zeros((4,4))
        self.Rz = np.zeros((4,4))
        self.T = np.zeros((4,4))
        self.projectionMatrix = np.zeros((4,4))

        #==================
        # Angles
        #==================
        self.xAngle = 0
        self.yAngle = -15.706
        self.zAngle = math.radians(180)
    
    def rotateXMatrix(self, angle):        
        #check if angle is different than before
        if angle == self.oldXAngle:
            return
        self.oldXAngle = angle
    
        self.Rx[0] = [1,0,0,0]
        self.Rx[1] = [0,math.cos(angle),-1*math.sin(angle),0]
        self.Rx[2] = [0,math.sin(angle),math.cos(angle),0]
        self.Rx[3] = [0,0,0,1]

        #if using debugging
        if self.debugRotation:
            print("\nRX: ",self.Rx, "angle: ",angle)

    def rotateYMatrix(self, angle):
        #check if angle is different than before
        if angle == self.oldYAngle:
            return
        self.oldYAngle = angle
        
        self.Ry[0] = [math.cos(angle),0,math.sin(angle),0]
        self.Ry[1] = [0,1,0,0]
        self.Ry[2] = [-1*math.sin(angle),0,math.cos(angle),0]
        self.Ry[3] = [0,0,0,1]

        #if using debugging
        if self.debugRotation:
            print("\nRY: ",self.Ry, "angle: ",angle)

    def rotateZMatrix(self, angle):
        #check if angle is different than before
        if angle == self.oldZAngle:
            return
        self.oldZAngle = angle
        
        self.Rz[0] = [math.cos(angle),-1*math.sin(angle),0,0]
        self.Rz[1] = [math.sin(angle),math.cos(angle),0,0]
        self.Rz[2] = [0,0,1,0]
        self.Rz[3] = [0,0,0,1]

        #if using debugging
        if self.debugRotation:
            print("\nRZ: ",self.Rz, "angle: ",angle)

    def updateProjectionMatrix(self):
        self.projectionMatrix[0] = [(2*self.near)/(self.right-self.left), 0, -1*(self.right + self.left)/(self.right-self.left), 0]
        self.projectionMatrix[1] = [0,(2*self.near)/(self.bottom-self.top),-1*(self.bottom+self.top)/(self.bottom-self.top),0]
        self.projectionMatrix[2] = [0,0,(self.far+self.near)/(self.far-self.near),(-2*self.far*self.near)/(self.far-self.near)]
        self.projectionMatrix[3] = [0,0,1,0]
        
    def translateMatrix(self, tx,ty,tz):
        if self.oldXTranslation == tx and self.oldYTranslation == ty and self.oldZTranslation == tz:
            return

        self.oldXTranslation = tx
        self.oldYTranslation = ty
        self.oldZTranslation = tz
        
        self.T[0] = [1,0,0,tx]
        self.T[1] = [0,1,0,ty]
        self.T[2] = [0,0,1,tz]
        self.T[3] = [0,0,0,1]

        if self.debugTranslation:
            print("\nTranslation: \n",self.T)

    def convertVectorToCoordinates(self, point):
        w = int(point[0,3])
        if w == 0:
            w = 1
            
        x = int(point[0,0])/w
        y = int(point[0,1])/w
        z = int(point[0,2])/w

        coords = np.zeros((1,3))
        coords[0] = [x,y,z]

        return x,y,z
        
    #=========================================
    #convert 3d vector to 2d plane coordinates
    #=========================================
    def projectPointToPlane(self, point):            
        x = int(point[0,0])
        y = int(point[0,1])
        z = int(point[0,2])

        #x,y,z = self.convertVectorToCoordinates(point)
        
        if z == 0:
            return(int(x) + 320,int(y) + 240)

        u = x + 640/2
        v = y + 480/2

        return (int(u),int(v))

        """
        w = int(point[0,3])
        if w == 0:
            w = 1
            
        x = int(point[0,0])/w
        y = int(point[0,1])/w
        z = int(point[0,2])/w
        
        x,y,z = self.convertVectorToCoordinates(point)

        if z == 0:
            z = 1

        x = x/z + 320
        y = y/z + 240

        return (int(x),int(y))
        """

    #========================================
    # Convert number to color
    #========================================

    def numberToColor(self, color):
        if color == 0:
            return (0,0,0)
        if color == 1:
            return WHITE
        if color == 2:
            return GREEN
        if color == 3:
            return DARK_GREEN
        if color == 4:
            return RED
        if color == 10:
            return DARK_BLUE

    #==============
    # Draw points
    #==============
    def drawPoints(self):
        for nPoint in range (0,int(self.pointMatrix.shape[0])):
            rotatedPoint = self.pointMatrix[nPoint]*self.Rx*self.Rz*self.Ry
            rotatedPoint *= self.T
            rotatedPoint *= self.projectionMatrix
            rotatedPoint *= self.scaling
            
            # Draw rotated point
            pygame.draw.circle(self.screen,WHITE,self.projectPointToPlane(rotatedPoint), self.pointRadius, self.pointThickness)

    #==============
    # Draw lines
    #==============
    def drawLines(self):
        for nLine in range(0, int(self.lineMatrix.shape[0])):
            rotatedStartPoint = self.pointMatrix[self.lineMatrix[nLine,0]]*self.Rx*self.Rz*self.Ry #rotate startpoint
            rotatedStartPoint *= self.T #translate starting point
            rotatedStartPoint *= self.projectionMatrix
            rotatedStartPoint *= self.scaling

            rotatedEndPoint = self.pointMatrix[self.lineMatrix[nLine,1]]*self.Rx*self.Rz*self.Ry #rotate endpoint
            rotatedEndPoint *= self.T #translate endpoint
            rotatedEndPoint *= self.projectionMatrix
            rotatedEndPoint *= self.scaling
            
            startPoint = self.projectPointToPlane(rotatedStartPoint) #project points from 3D space to 2D plane
            endPoint = self.projectPointToPlane(rotatedEndPoint)
            
            pygame.draw.line(self.screen,GREEN,startPoint,endPoint,1)

    #==============
    # Draw polygons
    #==============
    def drawPolygons(self):
        for nPolygons in range(0, int(self.polygons.shape[0])):
            
            point0 = self.projectPointToPlane(self.pointMatrix[self.polygons[nPolygons,0]]*self.Rx*self.Rz*self.Ry*self.T*self.projectionMatrix*self.scaling)
            point1 = self.projectPointToPlane(self.pointMatrix[self.polygons[nPolygons,1]]*self.Rx*self.Rz*self.Ry*self.T*self.projectionMatrix*self.scaling)
            point2 = self.projectPointToPlane(self.pointMatrix[self.polygons[nPolygons,2]]*self.Rx*self.Rz*self.Ry*self.T*self.projectionMatrix*self.scaling)

            color = self.polygons[nPolygons,3]
            
            pygame.draw.polygon(self.screen, self.numberToColor(color), ((point0,point1,point2)))
            
    def run(self):
        if not self.running:
            return
        
        #-------------
        # Clear screen
        #-------------
        self.screen.fill((20,20,20))

        #--------------------------------------
        # Calculate rotations and translations
        #--------------------------------------
        self.rotateXMatrix(self.xAngle)
        self.rotateYMatrix(self.yAngle)
        self.rotateZMatrix(self.zAngle)
        self.translateMatrix(self.currentX, self.currentY, self.currentZ)
        
        #------------
        # Draw
        #------------
        if self.drawOnlyPoints == 0:
            self.drawPolygons()
        self.drawPoints()
        if self.drawOnlyPoints == 0:
            self.drawLines()

        #-----------
        # UI
        #-----------
        fps = self.font.render(str(int(self.clock.get_fps())), True, pygame.Color('white'))
        self.screen.blit(fps,(5,5))
        
        #------------------------
        # Handle mouse movements
        #------------------------
        
        #get mouse relative position
        if self.enableMouse == 1:
            mouseMovement = pygame.mouse.get_pos()
            pygame.mouse.set_pos(640/2,480/2)
            
            self.yAngle += math.radians((mouseMovement[0]-640/2))*0.1
            self.xAngle -= math.radians((mouseMovement[1]-480/2))*0.1

        #------------------------
        # Display screen
        #------------------------
        pygame.display.flip()
        self.clock.tick()
        #time.sleep(0.01)

        #------------------------
        # Limit rotation angles
        #------------------------
        if(self.xAngle>math.radians(360)):
            self.xAngle = 0
        if(self.yAngle>math.radians(360)):
            self.yAngle = 0
        if(self.zAngle>math.radians(360)):
            self.zAngle = 0

        #----------------------------------
        # Check if user has pressed ESCAPE
        #----------------------------------
        getKeys = pygame.key.get_pressed()
        if getKeys[pygame.K_ESCAPE]:
            self.running = False
            pygame.quit()
            return

        #----------------------------------
        # Check if user has pressed W
        #----------------------------------
        if getKeys[pygame.K_w]:
            self.currentY += self.movingSpeed

        #----------------------------------
        # Check if user has pressed S
        #----------------------------------
        if getKeys[pygame.K_s]:
            self.currentY -= self.movingSpeed

        #----------------------------------
        # Check if user has pressed D
        #----------------------------------
        if getKeys[pygame.K_d]:
            self.currentX += self.movingSpeed

        #----------------------------------
        # Check if user has pressed A
        #----------------------------------
        if getKeys[pygame.K_a]:
            self.currentX -= self.movingSpeed

        #----------------------------------
        # Check if user has pressed N
        #----------------------------------
        if getKeys[pygame.K_n]:
            self.near -= self.zoomStep
            self.updateProjectionMatrix()
            print(self.near)

        #----------------------------------
        # Check if user has pressed M
        #----------------------------------
        if getKeys[pygame.K_m]:
            self.near += self.zoomStep
            self.updateProjectionMatrix()
            print(self.near)

        #----------------------------------
        # Handle events
        #----------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                break
            if event.type == pygame.USEREVENT:
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.zAngle += math.radians(2)
                if event.button == 5:
                    self.zAngle -= math.radians(2)
