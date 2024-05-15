from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3, Point3, CollisionTraverser, CollisionNode, CollisionHandlerPusher, CollisionBox, CollisionPlane, Plane, BitMask32, NodePath, CardMaker, LPoint3, AmbientLight, DirectionalLight, Texture, PNMImage, PerspectiveLens
from direct.task.Task import Task
import math

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable the default camera controller
        self.disableMouse()

        # Set window properties to center the mouse
        props = WindowProperties()
        props.setFullscreen(True)
        props.setCursorHidden(False)  # Ensure cursor is visible
        props.setMouseMode(WindowProperties.M_relative)  # Set the mouse mode to relative
        self.win.requestProperties(props)

        # Create a simple surface (ground) using CardMaker
        cm = CardMaker('ground')
        cm.setFrame(-100, 100, -100, 100)  # set the size of the ground plane
        self.ground = NodePath(cm.generate())
        self.ground.reparentTo(self.render)
        self.ground.setPos(0, 0, 0)
        self.ground.setHpr(0, -90, 0)  # rotate the ground to lie flat

        # Create the main character (a cube)
        self.cube = self.loader.loadModel("models/box")
        self.cube.reparentTo(self.render)
        self.cube.setScale(1, 1, 1)
        self.cube.setPos(0, 0, 15)

        # Try to load the red texture
        try:
            red_texture = self.loader.loadTexture("textures/red.png")
            if not red_texture:
                raise IOError("Could not load texture: textures/red.png")
        except IOError:
            # Fallback: create a solid red texture programmatically
            red_texture = self.createSolidColorTexture(1, 0, 0)  # RGB values for red

        self.cube.setTexture(red_texture, 1)

        # Add lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((0.2, 0.2, 0.2, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)

        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(1, 1, -1))
        directionalLight.setColor((0.8, 0.8, 0.8, 1))
        directionalLightNP = self.render.attachNewNode(directionalLight)
        self.render.setLight(directionalLightNP)

        # Camera setup
        self.camera.setPos(0, -20, 10)
        self.camera.lookAt(self.cube)

        # Collision setup
        self.cTrav = CollisionTraverser()
        self.pusher = CollisionHandlerPusher()

        self.cubeCollisionNode = CollisionNode('cube')
        self.cubeCollisionNode.addSolid(CollisionBox((0, 0, 0), 0.5, 0.5, 0.5))
        self.cubeCollisionNP = self.cube.attachNewNode(self.cubeCollisionNode)
        self.cubeCollisionNP.show()

        self.pusher.addCollider(self.cubeCollisionNP, self.cube)
        self.cTrav.addCollider(self.cubeCollisionNP, self.pusher)

        # Ground collision setup
        groundCollisionNode = CollisionNode('ground')
        groundCollisionNode.addSolid(CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0))))
        groundCollisionNP = self.ground.attachNewNode(groundCollisionNode)
        groundCollisionNP.show()

        self.pusher.addCollider(groundCollisionNP, self.ground)
        self.cTrav.addCollider(groundCollisionNP, self.pusher)

        # Key controls
        self.accept("escape", self.exitGame)
        self.accept("a", self.setKey, ["left", True])
        self.accept("a-up", self.setKey, ["left", False])
        self.accept("d", self.setKey, ["right", True])
        self.accept("d-up", self.setKey, ["right", False])
        self.accept("w", self.setKey, ["forward", True])
        self.accept("w-up", self.setKey, ["forward", False])
        self.accept("s", self.setKey, ["backward", True])
        self.accept("s-up", self.setKey, ["backward", False])
        self.accept("space", self.setKey, ["jump", True])
        self.accept("space-up", self.setKey, ["jump", False])
        self.accept("mouse1", self.dash)

        self.keyMap = {
            "left": False,
            "right": False,
            "forward": False,
            "backward": False,
            "jump": False,
        }

        self.cubeVelocity = Vec3(0, 0, 0)
        self.gravity = Vec3(0, 0, -9.8)
        self.jumpImpulse = Vec3(0, 0, 10)
        self.isJumping = False
        self.dashSpeed = 2  # Speed multiplier for dash

        # Update task
        self.taskMgr.add(self.update, "update")

        # Camera follow task
        self.taskMgr.add(self.cameraFollow, "cameraFollow")

        # Mouse controls
        self.mouseControlActive = True
        self.taskMgr.add(self.mouseControl, "mouseControl")

    def createSolidColorTexture(self, r, g, b):
        """Creates a solid color texture."""
        img = PNMImage(1, 1)
        img.setXel(0, 0, r, g, b)
        texture = Texture()
        texture.load(img)
        return texture

    def setKey(self, key, value):
        self.keyMap[key] = value

    def dash(self):
        # Define the dash distance multiplier
        dash_distance_multiplier = 50

        # Calculate the movement distance for the dash
        move_distance = dash_distance_multiplier * 15 * globalClock.getDt()

        # Determine the direction of the dash based on the currently pressed keys
        if self.keyMap["forward"]:
            self.cube.setY(self.cube, move_distance)
        # elif self.keyMap["backward"]:
        #     self.cube.setY(self.cube, -move_distance)
        elif self.keyMap["left"]:
            self.cube.setY(self.cube, move_distance)
        elif self.keyMap["right"]:
            self.cube.setY(self.cube, move_distance)

    def cameraFollow(self, task):
        # Calculate the offset from the cube's position
        offset = Vec3(0, -10, 2)  # Adjust this offset as needed

        # Rotate the offset vector by the cube's heading and pitch
        heading = self.cube.getH() * (math.pi / 180.0)
        # pitch = self.cube.getP() * (math.pi / 180.0)
        rotatedOffset = Vec3(offset.getX() * math.cos(heading) - offset.getY() * math.sin(heading),
                             offset.getX() * math.sin(heading) + offset.getY() * math.cos(heading),
                             offset.getZ())

        # Set the camera position to follow the cube
        cameraPos = self.cube.getPos() + rotatedOffset + Vec3(0, 0, 1)
        self.camera.setPos(cameraPos)

        # Calculate the target position (center of the screen)
        targetPos = self.cube.getPos() + Vec3(0, 0, 1)

        # Look at the target position
        self.camera.lookAt(targetPos)

        return Task.cont

    def update(self, task):
        dt = globalClock.getDt()

        # Handle gravity
        if self.cube.getZ() > 0.5:
            self.cubeVelocity += self.gravity * dt
        else:
            self.cubeVelocity.setZ(0)
            self.isJumping = False

        # Handle movement
        moveSpeed = 15

        if self.isJumping:
            moveSpeed = 7  # Lower move speed while jumping

        if self.keyMap["forward"]:
            self.cube.setY(self.cube, moveSpeed * dt)
        if self.keyMap["backward"]:
            self.cube.setY(self.cube, -moveSpeed * dt)
        if self.keyMap["left"]:
            self.cube.setX(self.cube, -moveSpeed * dt)
        if self.keyMap["right"]:
            self.cube.setX(self.cube, moveSpeed * dt)
        if self.keyMap["jump"] and not self.isJumping:
            self.cubeVelocity += self.jumpImpulse
            self.isJumping = True

        self.cube.setPos(self.cube.getPos() + self.cubeVelocity * dt)

        # Update the camera to follow the cube
        self.camera.lookAt(self.cube)

        return Task.cont

    def mouseControl(self, task):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            sensitivity = 500  # Adjust this value to increase/decrease sensitivity
            self.cube.setH(
                self.cube.getH() - mpos.getX() * sensitivity * globalClock.getDt())  # Rotate the cube based on mouse X position
            self.win.movePointer(0, self.win.getProperties().getXSize() // 2,
                                 self.win.getProperties().getYSize() // 2)  # Re-center the mouse cursor
        return Task.cont

    def exitGame(self):
        self.userExit()

app = MyApp()
app.run()
