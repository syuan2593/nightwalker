import os, sys
import pygame
import random
import copy
from pygame.locals import *
import math
import string

sys.setrecursionlimit(99999999)

#from https://www.pygame.org/docs/tut/ChimpLineByLine.html
def loadImage(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

#####################################
#Drawn objects
#####################################

class Player(pygame.sprite.Sprite):
    def __init__(self, game, hp = 6, killCount = 0):
        super().__init__()
        hit = (pygame.image.load('data\\playerHit.png')).convert()
        hit.set_colorkey((0,0,0))
        self.hitSprite = pygame.transform.scale(hit, (42,76))
        idle0 = (pygame.image.load('data\\playerIdle1.png')).convert()
        idle1 = (pygame.image.load('data\\playerIdle2.png')).convert()
        idle0.set_colorkey((0,0,0))
        idle1.set_colorkey((0,0,0))
        self.idleSprites = [pygame.transform.scale(idle0, (42,76)),
                            pygame.transform.scale(idle1, (42,78))]
        walk0 = (pygame.image.load('data\\playerWalk1.png')).convert()
        walk1 = (pygame.image.load('data\\playerWalk2.png')).convert()
        walk0.set_colorkey((0,0,0))
        walk1.set_colorkey((0,0,0))
        self.walkSprites = [pygame.transform.scale(walk0, (42,78)),
                            pygame.transform.scale(walk1, (42,78))]
        self.image = self.idleSprites[0]
        
        self.rect = self.image.get_rect(center = (game.width//2, game.height//2))
        self.hp = hp
        self.maxHP = 6
        self.speed = 12
        self.lastFaced = 1
        self.flipped = False
        self.hitTimer = -1
        self.killCount = killCount
        self.blockSprites = pygame.sprite.Group()
    #update method moved to the camera object
    def spriteUpdate(self, moveVector, game):
        if self.hitTimer >= 0: self.image = self.hitSprite
        elif moveVector == [0,0]:
            self.image = self.idleSprites[((game.spriteChangeCounter//8)%(len(self.idleSprites)))]
        else:
            self.image = self.walkSprites[((game.spriteChangeCounter//5)%(len(self.walkSprites)))]
        if self.flipped:
            self.image = pygame.transform.flip(self.image, True, False)
    def shoot(self, game, clickPos, currMap, camera):
        game.gunSound.play()
        dx, dy = (clickPos[0]-game.width//2), (clickPos[1]-game.height//2)
        vectLen = (dx**2+dy**2)**.5
        dx, dy = dx/vectLen, dy/vectLen
        bullet = Bullet(game, dx, dy, self.rect.center, camera, True)
        currMap.myBulletSprites.add(bullet)
    def block(self, game, clickPos, camera):
        dx, dy = (clickPos[0]-game.width//2), (clickPos[1]-game.height//2)
        vectLen = (dx**2+dy**2)**.5
        dx, dy = dx/vectLen, dy/vectLen
        self.blockSprite = Block(game, dx, dy, camera)
        self.blockSprites.add(self.blockSprite)

class Block(pygame.sprite.Sprite):
    def __init__(self, game, dx, dy, camera):
        super().__init__()
        image = (pygame.image.load('data\\blockSprite.png')).convert()
        if dx == 0:
            dx = .001
        self.angle = (math.atan(-dy/dx)*180/3.1415)
        if dx < 0: self.image = pygame.transform.rotozoom(image, self.angle + 180, 0.375)
        else: self.image = pygame.transform.rotozoom(image, self.angle, 0.375)
        self.image.set_colorkey((0,0,0))
        self.rect = self.image.get_rect(center = (game.width//2 + dx*45, game.height//2 + dy*45))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, dx, dy, pos, camera, friendly):
        super().__init__()
        image = (pygame.image.load('data\\bullet.png')).convert()
        image.set_colorkey((0,0,0))
        self.image = pygame.transform.scale(image, (30,30))
        self.rect = self.image.get_rect(center = pos)
        self.pos = ((pos[0] + camera.xOffset),
                    (pos[1] + camera.yOffset))
        self.friendly = friendly
        self.speed = 21
        self.dirX = dx
        self.dirY = dy
    def update(self, currMap, camera, player):
        self.rect.center = ((self.pos[0] - camera.xOffset + int(self.dirX*self.speed)),
                            (self.pos[1] - camera.yOffset + int(self.dirY*self.speed)))
        self.pos = ((self.pos[0] + int(self.dirX*self.speed)),
                    (self.pos[1] + int(self.dirY*self.speed)))

        #checking collisions with enemies: moved to the event loop and overhauled for optimization

#First enemy: 
class GunGrunt(pygame.sprite.Sprite):
    def __init__(self, pos, game, camera, hp = 4):
        super().__init__()
        idle = (pygame.image.load('data\\gruntIdle.png')).convert()
        hit = (pygame.image.load('data\\gruntHit.png')).convert()
        idle.set_colorkey((0,0,0))
        hit.set_colorkey((0,0,0))
        self.type = 'grunt'
        self.hitSprite = pygame.transform.scale(hit, (54,74))
        self.idleSprite = pygame.transform.scale(idle, (54,74))
        walk0 = (pygame.image.load('data\\gruntWalk1.png')).convert()
        walk1 = (pygame.image.load('data\\gruntWalk2.png')).convert()
        walk0.set_colorkey((0,0,0))
        walk1.set_colorkey((0,0,0))
        self.walkSprites = [pygame.transform.scale(walk0, (54,80)),
                            pygame.transform.scale(walk1, (54,80))]
        dead = (pygame.image.load('data\\dead.png')).convert()
        dead.set_colorkey((0,0,0))
        self.deadSprite = pygame.transform.scale(dead, (85,26))
        self.image = self.idleSprite
        self.rect = self.image.get_rect(topleft = ((pos[0]+game.width//2),
                                                   (pos[1]+game.height//2)))
        self.pos = self.rect.topleft
        self.hp = hp
        self.dirX = 0
        self.dirY = 0
        self.peeking = False
        self.speed = 8
        self.lastX = 0
        self.lastY = 0
        self.updateFrequency = 15
        self.timeDelay = random.randint(0,self.updateFrequency)
        self.hitTimer = -1
        self.active = False
        self.hitWallRecently = False
        self.dead = False
        self.revived = False

    def passiveUpdate(self, camera):
        if self.dead: self.image = self.deadSprite
        elif self.hitTimer >= 0:
            self.image = self.hitSprite
        else:
            self.image = self.idleSprite
        self.rect.topleft = (int(self.pos[0] - camera.xOffset),
                             int(self.pos[1] - camera.yOffset))

    def update(self, camera, game, currMap):
        if self.dead: self.image = self.deadSprite
        elif self.hitTimer >= 0:
            self.image = self.hitSprite
        else:
            self.image = self.idleSprite
        if self.dirY == 2:
            self.shoot(game, currMap, camera)
            self.dirY = [-1,0,0,0,1][random.randint(0,4)]
        oldPos = self.rect
        if abs(self.dirX) == abs(self.dirY) == 1:
            self.dirX, self.dirY = .7*self.dirX, .7*self.dirY
        self.rect.topleft = (int(self.pos[0] - camera.xOffset + (self.dirX*self.speed)),
                             int(self.pos[1] - camera.yOffset + (self.dirY*self.speed)))
        if pygame.sprite.spritecollideany(self, currMap.wallSprites):
            self.rect = oldPos

            if self.hitWallRecently:
                if self.dirX == 0:
                    self.dirX = [1,-1][random.randint(0,1)]
                else:
                    self.dirX = 0
                if self.dirX != 0:
                    self.dirY = 0
                else:
                    self.dirY = [1,-1][random.randint(0,1)]

            self.dirX = -self.dirX
            self.dirY = -self.dirY
            self.hitWallRecently = True
            return
        self.pos = ((self.pos[0] + self.dirX*self.speed),
                    (self.pos[1] + self.dirY*self.speed))

    def shoot(self, game, currMap, camera):
        game.gunSound.play()
        x, y = self.rect.center
        dx, dy = (game.width//2-x), (game.height//2-y)
        vectLen = (dx**2+dy**2)**.5
        dx, dy = dx/vectLen, dy/vectLen
        bullet = Bullet(game, dx, dy, (x, y), camera, False)
        currMap.bulletSprites.add(bullet)

    def peek(self, game, camera, currMap):
        if self.lastX == self.lastY == 0:
            self.getAction()
            return
        self.dirX = -(self.lastX)
        self.dirY = -(self.lastY)
        self.peeking = False

    def die(self, currMap, player, camera, game):
        self.image = self.deadSprite
        self.kill()
        self.dead = True
        currMap.deadEnemies.add(self)
        if not self.revived: player.killCount += 1
        if (random.randint(0,8+int(12*player.hp/player.maxHP)) and player.hp != player.maxHP):
            healthPack = HealthPack((self.rect.center[0]+camera.xOffset-game.width//2, self.rect.center[1]+camera.yOffset-game.height//2))
            currMap.healthSprites.add(healthPack)

    def getAction(self):
        dirList = [-1, 0, 0, 0, 1, 2, 2, 2, 2]
        self.dirX = dirList[random.randint(0,4)]
        self.dirY = dirList[random.randint(0,8)]

class Necro(pygame.sprite.Sprite):
    def __init__(self, pos, game, camera, hp = 3):
        super().__init__()
        idle = (pygame.image.load('data\\necroIdle.png')).convert()
        hit = (pygame.image.load('data\\necroHit.png')).convert()
        idle.set_colorkey((0,0,0))
        hit.set_colorkey((0,0,0))
        self.type = 'necro'
        self.hitSprite = pygame.transform.scale(hit, (44,52))
        self.idleSprite = pygame.transform.scale(idle, (44,52))
        dead = (pygame.image.load('data\\dead.png')).convert()
        dead.set_colorkey((0,0,0))
        self.deadSprite = pygame.transform.scale(dead, (85,26))
        self.image = self.idleSprite
        self.rect = self.image.get_rect(topleft = ((pos[0]+game.width//2),
                                                   (pos[1]+game.height//2)))
        self.pos = self.rect.topleft
        self.hp = hp
        self.dirX = 0
        self.dirY = 0
        self.speed = 4
        self.lastX = 0
        self.lastY = 0
        self.updateFrequency = 60
        self.timeDelay = random.randint(0,self.updateFrequency)
        self.hitTimer = -1
        self.active = False
        self.hitWallRecently = False
        self.reviveCircleTimer = 0
        self.dead = False
        self.revived = False

    def passiveUpdate(self, camera):
        if self.dead: self.image = self.deadSprite
        elif self.hitTimer >= 0:
            self.image = self.hitSprite
        else:
            self.image = self.idleSprite
        self.rect.topleft = (int(self.pos[0] - camera.xOffset),
                             int(self.pos[1] - camera.yOffset))

    def update(self, camera, game, currMap):
        if self.dead: self.image = self.deadSprite
        elif self.hitTimer >= 0:
            self.image = self.hitSprite
        else:
            self.image = self.idleSprite
        if self.dirY == 2:
            self.revive(currMap, game)
            self.dirY = [-1,0,1][random.randint(0,2)]
        oldPos = self.rect
        if abs(self.dirX) == abs(self.dirY) == 1:
            self.dirX, self.dirY = .7*self.dirX, .7*self.dirY
        self.rect.topleft = (int(self.pos[0] - camera.xOffset + self.dirX*self.speed),
                             int(self.pos[1] - camera.yOffset + self.dirY*self.speed))
        if pygame.sprite.spritecollideany(self, currMap.wallSprites):
            self.rect = oldPos
            if self.hitWallRecently:
                if self.dirX == 0:
                    self.dirX = [1,-1][random.randint(0,1)]
                else:
                    self.dirX = 0
                if self.dirX != 0:
                    self.dirY = 0
                else:
                    self.dirY = [1,-1][random.randint(0,1)]
            else:
                self.dirX = -self.dirX
                self.dirY = -self.dirY
            self.hitWallRecently = True
            return
        self.pos = ((self.pos[0] + self.dirX*self.speed),
                    (self.pos[1] + self.dirY*self.speed))

    def die(self, currMap, player, camera, game):
        self.kill()
        self.image = self.deadSprite
        self.dead = True
        currMap.deadEnemies.add(self)
        if not self.revived: player.killCount += 1
        if (random.randint(0,8+int(12*player.hp/player.maxHP)) and player.hp != player.maxHP):
            healthPack = HealthPack((self.rect.center[0]+camera.xOffset-game.width//2, self.rect.center[1]+camera.yOffset-game.height//2))
            currMap.healthSprites.add(healthPack)
    
    def revive(self, currMap, game):
        game.reviveSound.play()
        self.reviveCircleTimer = 5
        for enemy in currMap.deadEnemies:
            if ((enemy.rect.left > 0) and (enemy.rect.top > 0) and
                (enemy.rect.right < game.width) and (enemy.rect.bottom < game.height)):
                enemy.kill()
                enemy.hp = 3
                enemy.image = enemy.idleSprite
                currMap.enemySprites.add(enemy)
                if enemy.type == 'sword':
                    currMap.swordSprites.add(enemy)
                enemy.dead = False
                enemy.revived = True

    def getAction(self):
        dirList = [-1, 0, 0, 0, 1, 2, 2]
        self.dirX = dirList[random.randint(0,4)]
        self.dirY = dirList[random.randint(0,6)]

class MeleeGrunt(pygame.sprite.Sprite):
    def __init__(self, pos, game, camera, hp = 2):
        super().__init__()
        idle = (pygame.image.load('data\\swordIdle.png')).convert()
        hit = (pygame.image.load('data\\swordHit.png')).convert()
        charge = (pygame.image.load('data\\swordCharge.png')).convert()
        idle.set_colorkey((0,0,0))
        hit.set_colorkey((0,0,0))
        charge.set_colorkey((0,0,0))
        self.type = 'sword'
        self.chargeSprite = pygame.transform.scale(charge, (72,80))
        self.hitSprite = pygame.transform.scale(hit, (72,80))
        self.idleSprite = pygame.transform.scale(idle, (42,80))
        dead = (pygame.image.load('data\\dead.png')).convert()
        dead.set_colorkey((0,0,0))
        self.deadSprite = pygame.transform.scale(dead, (85,26))
        self.image = self.idleSprite
        self.rect = self.image.get_rect(topleft = ((pos[0]+game.width//2),
                                                   (pos[1]+game.height//2)))
        self.pos = self.rect.topleft
        self.hp = hp
        self.dirX = 0
        self.dirY = 0
        self.peeking = False
        self.speed = 10
        self.chargeSpeed = 18
        self.lastX = 0
        self.lastY = 0
        self.updateFrequency = 15
        self.timeDelay = random.randint(0,self.updateFrequency)
        self.hitTimer = -1
        self.active = False
        self.hitWallRecently = False
        self.dead = False
        self.charging = False
        self.revived = False

    def passiveUpdate(self, camera):
        if self.dead: self.image = self.deadSprite
        elif self.hitTimer >= 0:
            self.image = self.hitSprite
        self.rect.topleft = (int(self.pos[0] - camera.xOffset),
                             int(self.pos[1] - camera.yOffset))

    def update(self, camera, game, currMap):
        oldPos = self.rect
        if not self.charging:
            self.updateFrequency = 15
            self.speed = 10
            if self.dead: self.image = self.deadSprite

            elif self.hitTimer >= 0:
                self.image = self.hitSprite
            else:
                self.image = self.idleSprite

            if abs(self.dirX) == abs(self.dirY) == 1:
                self.dirX, self.dirY = .7*self.dirX, .7*self.dirY
            self.rect.topleft = (int(self.pos[0] - camera.xOffset + (self.dirX*self.speed)),
                                int(self.pos[1] - camera.yOffset + (self.dirY*self.speed)))
            if pygame.sprite.spritecollideany(self, currMap.wallSprites):
                self.rect = oldPos

                if self.hitWallRecently:
                    if self.dirX == 0:
                        self.dirX = [1,-1][random.randint(0,1)]
                    else:
                        self.dirX = 0
                    if self.dirX != 0:
                        self.dirY = 0
                    else:
                        self.dirY = [1,-1][random.randint(0,1)]

                self.dirX = -self.dirX
                self.dirY = -self.dirY
                self.hitWallRecently = True
                return
            self.pos = ((self.pos[0] + self.dirX*self.speed),
                        (self.pos[1] + self.dirY*self.speed))
        else:
            self.image = self.chargeSprite
            self.speed = self.chargeSpeed

            x, y = self.rect.center
            dx, dy = (game.width//2-x), (game.height//2-y)
            vectLen = (dx**2+dy**2)**.5
            if vectLen == 0: vectLen = .01
            dx, dy = dx/vectLen, dy/vectLen
            self.dirX = self.chargeX = dx
            self.dirY = self.chargeY = dy

            self.rect.topleft = (int(self.pos[0] - camera.xOffset),
                                int(self.pos[1] - camera.yOffset + (self.dirY*self.speed)))
            if pygame.sprite.spritecollideany(self, currMap.wallSprites):
                self.rect = oldPos
                self.dirY = 0
            else:
                oldPos = self.rect
                self.dirY = self.chargeY

            self.rect.topleft = (int(self.pos[0] - camera.xOffset + (self.dirX*self.speed)),
                                int(self.pos[1] - camera.yOffset + (self.dirY*self.speed)))
            if pygame.sprite.spritecollideany(self, currMap.wallSprites):
                self.rect = oldPos
                self.dirX = 0
            else:
                self.dirX = self.chargeX
            self.pos = ((self.pos[0] + self.dirX*self.speed),
                        (self.pos[1] + self.dirY*self.speed))

    def charge(self, game, currMap, camera):
        x, y = self.rect.center
        dx, dy = (game.width//2-x), (game.height//2-y)
        vectLen = (dx**2+dy**2)**.5
        dx, dy = dx/vectLen, dy/vectLen
        self.dirX = self.chargeX = dx
        self.dirY = self.chargeY = dy
        self.charging = True
        self.updateFrequency = 100

    def die(self, currMap, player, camera, game):
        self.image = self.deadSprite
        self.kill()
        self.dead = True
        currMap.deadEnemies.add(self)
        if not self.revived: player.killCount += 1
        if (random.randint(0,8+int(12*player.hp/player.maxHP)) and player.hp != player.maxHP):
            healthPack = HealthPack((self.rect.center[0]+camera.xOffset-game.width//2, self.rect.center[1]+camera.yOffset-game.height//2))
            currMap.healthSprites.add(healthPack)

    def getAction(self):
        dirList = [-1, 0, 0, 1]
        self.dirX = dirList[random.randint(0,3)]
        self.dirY = dirList[random.randint(0,3)]

class HealthPack(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        image = (pygame.image.load('data\\healthSprite.png')).convert()
        self.image = pygame.transform.scale(image, (20,20))
        self.rect = self.image.get_rect(topleft = (pos[0],pos[1]))
        self.x = pos[0]
        self.y = pos[1]
        self.timer = 300
    def update(self, camera, game, player):
        self.rect = self.image.get_rect(topleft = (self.x-camera.xOffset+game.width//2, self.y-camera.yOffset+game.height//2))
        self.timer -= 1
        self.image.set_alpha(255*((self.timer)/300))
        if self.timer < 0: self.kill()

def covered(enemy, player, currMap, game, camera):
    if ((enemy.rect.left < 0) or (enemy.rect.top < 0) or
        (enemy.rect.right > game.width) or (enemy.rect.bottom > game.height)):
        return True
    playerPos = player.rect.center
    enemyPos = enemy.rect.center
    xDiff = enemyPos[0]-playerPos[0]
    yDiff = enemyPos[1]-playerPos[1]
    dispVect = [xDiff, yDiff]
    length = ((((xDiff**2)+(yDiff**2))**.5)/game.cellSize)
    if length <= 1: return False
    dispVector = [elem/length for elem in dispVect]
    playerLoc = [(camera.xOffset), (camera.yOffset)]
    for i in range(1, int(length)):
        tempVect = [i*elem for elem in dispVector]
        checkLoc = [int(playerLoc[j] + tempVect[j]) for j in range(2)]
        if tuple(currMap.image.get_at(tuple(checkLoc))) != (currMap.floorColor + (255,)):
            return True
    return False

#####################################
#sidescrolling
#####################################

class Camera(object):
    def __init__(self, game, wallList):
        y,x = getSpawn(game, wallList)
        self.xOffset = int((x+.5)*game.cellSize)
        self.yOffset = int((y+.5)*game.cellSize)

    def update(self, player, currMap, moveVector, game):
        moveVector = [round(player.speed * d) for d in moveVector]
        oldXOffset, oldYOffset = self.xOffset, self.yOffset
        newXOffset = self.xOffset + moveVector[0]
        newYOffset = self.yOffset + moveVector[1]
        self.xOffset = newXOffset
        #X wall collision here
        oldWallSprites = currMap.wallSprites.copy()
        currMap.wallSprites.update(self, game)
        if pygame.sprite.spritecollideany(player, currMap.wallSprites):
            self.xOffset = oldXOffset
            currMap.wallSprites = oldWallSprites

        #y wall collision here
        self.yOffset = newYOffset
        oldWallSprites = currMap.wallSprites.copy()
        currMap.wallSprites.update(self, game)
        if pygame.sprite.spritecollideany(player, currMap.wallSprites):
            self.yOffset = oldYOffset
            currMap.wallSprites = oldWallSprites
        
        currMap.exit.update(self, game, player)
        for enemy in currMap.enemySprites:
            if not enemy.active: enemy.passiveUpdate(self)
        for deadEnemy in currMap.deadEnemies:
            deadEnemy.passiveUpdate(self)
        return pygame.sprite.collide_rect(player, currMap.exit)
    
#####################################
#generates a pseudo-random number from a seed
#####################################

def generateFromSeed(game):
    while True:
        random.seed(game.seed)
        a = random.getrandbits(10)
        game.seed = a
        yield a

def getRandRange(game, range):
    temp = next(generateFromSeed(game))
    game.seed = temp
    return temp%range

#######################################
#generates maps
#######################################

def getCenterBiasedDir(game, dirList, walkerPosX, walkerPosY, size):
    mod = 0
    if walkerPosX < size//2: dirList += [(1,0)]
    elif walkerPosX > size//2 : dirList += [(-1,0)]
    else: mod -= 1
    if walkerPosY < size//2: dirList += [(0,1)]
    elif walkerPosY > size//2: dirList += [(0,-1)]
    else: mod -= 1
    return dirList[getRandRange(game,(len(dirList)+mod))]

#algorithm inspired by http://pcg.wikidot.com/pcg-algorithm:drunkard-walk#:~:text=
#code is original
def drunkardWalk(game, size, maxSteps, maxFloors):
    rows = cols = size
    wallList = [[False]*cols for i in range(rows)]
    walkerPosX = walkerPosY = size//2
    enemyCount = 0
    spawnChance = max(int((((20**3)//(max(1,(int(game.level*.75))))))**.33), 2)
    for step in range(maxFloors):
        dirList = [(0,1),(1,0), (-1,0),(0,-1)]*2
        direc = getCenterBiasedDir(game, dirList, walkerPosX, walkerPosY, size)
        steps = (getRandRange(game,(maxSteps-1))+1)
        for i in range(steps):
            if random.randint(0,spawnChance) == 2:
                wallList[walkerPosX][walkerPosY] = 'G'
                enemyCount += 1
            elif random.randint(0,7*spawnChance) == 0:
                wallList[walkerPosX][walkerPosY] = 'N'
                enemyCount += 1
            elif random.randint(0, int(1.5*spawnChance)) == 0:
                wallList[walkerPosX][walkerPosY] = 'S'
                enemyCount += 1
            else:
                wallList[walkerPosX][walkerPosY] = True
            walkerPosX += direc[0]
            walkerPosY += direc[1]

            #turns around when it hits a wall
            if (walkerPosX >= cols or walkerPosX < 0 or
                walkerPosY >= rows or walkerPosY < 0):
                walkerPosX -= 4*direc[0]
                walkerPosY -= 4*direc[1]
                direc = (-direc[0],-direc[1])
    if enemyCount < (game.level + 1.4) * 5:
        return drunkardWalk(game, size, maxSteps, maxFloors)
    return wallList

def getSpawn(game, wallList):
    rows,cols = len(wallList), len(wallList[0])
    counter = 0
    for row in range(rows):
        for col in range(cols):
            if wallList[row][col]:
                if counter >= game.spawnOffset:
                    return (row,col)
                counter += 1

def getExit(game, wallList):
    rows, cols = len(wallList), len(wallList[1])
    for row in range(rows-1,0,-1):
        for col in range(cols-1,0,-1):
            if wallList[row][col]:
                return (row, col)

def cutWallList(wallList):
    size = len(wallList)
    for row in range(size-1):
        if (True in wallList[row]):
            wallList = wallList[row:]
            break
    size = len(wallList)
    for row in range(size):
        if ((True in wallList[-(row + 1)]) and (row != 0)):
            wallList = wallList[:-(row)]
            break
    rows, cols= len(wallList), len(wallList[0])
    Break = False
    for col in range(cols):
        for row in range(rows):
            if wallList[row][col]:
                for row in wallList:
                    row = row[col:]
                Break = True
                break
        if Break: break
    cols = len(wallList[0])
    Break = False
    for col in range(cols):
        for row in range(rows):
            if ((wallList[row][-(col+1)]) and (col != 0)):
                for row in wallList:
                    row = [False] + row[:-col] + [False]
                Break = True
                break
        if Break: break
    rows, cols= len(wallList), len(wallList[0])
    wallList.append([False]*cols)
    wallList.insert(0, [False]*cols)
    return wallList

#ABOVE FOR MAP TYPE 1, BELOW FOR MAP TYPE 2

def getRoomGrid(game):
    rows = cols = game.level + 1
    edgeSquares = 4*rows - 4
    entrance = getRandRange(game, edgeSquares)
    if entrance < cols: entranceCoords = (0,entrance)
    elif entrance >= edgeSquares-cols:
        entranceCoords = (rows-1, (entrance-cols)-(2*(rows-2)))
    else:
        entranceCoords = ((((entrance-cols)//2)+1), [0, rows-1][(entrance-cols)%2])
    exitCoords = (0,0)
    if entranceCoords[0] < rows//2: exitCoords = (rows-1, exitCoords[1])
    if entranceCoords[1] < cols//2: exitCoords = (exitCoords[0], cols-1)
    return entranceCoords, exitCoords, rows

def getRoute(entranceCoords, exitCoords, game, rows, cols):
    roomGrid = [[False]*cols for row in range(rows)]
    walkerPosX = entranceCoords[1]
    walkerPosY = entranceCoords[0]
    dirList = [(0,1),(1,0), (-1,0),(0,-1)]
    travelList = []
    depth = 0
    while True:
        depth +=1
        direc = dirList[getRandRange(game,4)]
        roomGrid[walkerPosY][walkerPosX] = True
        coords = (walkerPosY, walkerPosX)
        travelList.append(coords)
        if coords == exitCoords: break
        walkerPosX += direc[1]
        walkerPosY += direc[0]
        if (walkerPosX >= cols or walkerPosX < 0 or
            walkerPosY >= rows or walkerPosY < 0):
            walkerPosX -= 2*direc[1]
            walkerPosY -= 2*direc[0]
        elif depth == rows**5:
            exitCoords = coords
            break
    return roomGrid, travelList, exitCoords

def drawHallways(travelList, wallList, roomWidth, roomHeight):
    rows, cols = len(wallList), len(wallList[1])
    for room in range(len(travelList)-1):
        init = travelList[room]
        dest = travelList[room+1]
        initY = (init[0]*(roomHeight+2) + roomHeight//2)
        initX = (init[1]*(roomWidth+2) + roomWidth//2)
        destY = (dest[0]*(roomHeight+2) + roomHeight//2)
        destX = (dest[1]*(roomWidth+2) + roomWidth//2)
        #horizontal path
        if (initY == destY):
            for tile in range(roomWidth):
                #headed right
                if initX < destX:
                    wallList[initY][initX+tile] = True
                #headed left
                else:
                    wallList[initY][initX-tile] = True
        #vertical path
        elif (initX == destX):
            for tile in range(roomWidth):
                #headed down
                if initY < destY:
                    wallList[initY+tile][initX] = True
                #headed up
                else:
                    wallList[initY-tile][initX] = True

def decorateRoom(room, roomWidth, roomHeight, game, isExit):
    topRowOutcroppings = []
    #some basic outcroppings
    for col in range(roomWidth):
        if getRandRange(game, 3) == 0:
            room[0][col] = False
            topRowOutcroppings += [col]
    #extending outcroppings
    if getRandRange(game,2) == 0 or isExit:
        for outcropping in topRowOutcroppings:
            if getRandRange(game, 2) == 0:
                room[1][outcropping] = False
                if getRandRange(game, 2) == 0:
                    room[2][outcropping] = False
                    room[3][outcropping] = False
    #or create an island
    else:
        walkerYPos = roomHeight//2
        walkerXPos = roomWidth//2
        direcList = [(0,1),(1,0), (-1,0),(0,-1)]
        for i in range(25):
            room[walkerYPos][walkerXPos] = False
            direc = direcList[getRandRange(game, 4)]
            walkerXPos += direc[0]
            walkerYPos += direc[1]
            if ((walkerXPos < roomWidth//3) or (walkerXPos > 2*roomWidth//3) or 
               (walkerYPos < roomHeight//3) or (walkerYPos > 2*roomHeight//3)):
               walkerXPos -= 2*direc[0]
               walkerYPos -= 2*direc[1]
    #now place enemies:
    spawnChance = max(int(((35**3//(max(1,(int(game.level*.75))))))**.33), 2)
    rows, cols = len(room), len(room[1])
    for row in range(rows):
        for col in range(cols):
            if room[row][col] and random.randint(0,spawnChance) == 1: #0,20
                room[row][col] = 'G'
            if room[row][col] and random.randint(0,spawnChance*4) == 1: #0,80
                room[row][col] = 'N'
            if room[row][col] and random.randint(0,spawnChance*2) == 1: #0,80
                room[row][col] = 'S'
    #now place the exit:
    if isExit:
        drows = [-1, 0, 1]
        dcols = [-1, 0, 1]
        for drow in drows:
            for dcol in dcols:
                if (drow != 0 or dcol != 0) and random.randint(0,1):
                    room[roomHeight//2 + drow][roomWidth//2 + dcol] = 'G'
        room[roomHeight//2][roomWidth//2] = 'X'
    game.seed *= 37

def addRoom(row, col, room, wallList, roomWidth, roomHeight):
    horWall = [False]*(roomWidth+2)
    for cellRow in room:
        cellRow.insert(0, False)
        cellRow.append(False)
    room.insert(0, horWall)
    room.append(horWall)
    if col == 0:
        wallList.extend(room)
    else:
        for i in range(len(room)):
            (wallList[-(i+1)]).extend(room[-(i+1)])

def generateMap2(game):
    entranceCoords, exitCoords, rows = getRoomGrid(game)
    #we now have coordinates for an entrance and exit
    #now we need to get a route from entrance to exit
    roomGrid, travelList, exitCoords = getRoute(entranceCoords, exitCoords, game, rows, rows)
    #we now have a grid mapping out a complete route from entrance to exit
    #now we need to flesh out each room
    rows = len(roomGrid)
    roomWidth = 14
    roomHeight = 7
    wallList = []
    for row in range(rows):
        #wallList += [[False]*((roomWidth+2)*rows)]
        for col in range(rows):
            isExit = False
            if exitCoords == (row, col):
                isExit = True
            if roomGrid[row][col]:
                room = [[True]*roomWidth for row in range(roomHeight)]
                decorateRoom(room, roomWidth, roomHeight, game, isExit)
            else: room = [[False]*roomWidth for row in range(roomHeight)]
            addRoom(row, col, room, wallList, roomWidth, roomHeight)
    #we have a grid of decorated rooms
    #we now need to add hallways along the travel list
    drawHallways(travelList, wallList, roomWidth, roomHeight)
    #done
    return wallList


##########################################
#saved/initialized values
##########################################

class Wall(pygame.sprite.Sprite):
    def __init__(self, pos, game):
        super().__init__()
        image = (pygame.image.load('data\\wallSprite3.png')).convert()
        self.image = pygame.transform.scale(image, (game.cellSize+1,game.cellSize+1))
        self.rect = self.image.get_rect(topleft = (pos[0],pos[1]))
        self.x = pos[0]
        self.y = pos[1]
    def update(self, camera, game):
        self.rect = self.image.get_rect(topleft = (self.x-camera.xOffset+game.width//2, self.y-camera.yOffset+game.height//2))
                    
class Game(object):
    def __init__(self):
        self.activeGame = False
        self.seed = 4244174 #random.randint(0,9999999) #8839645 #3977117 #872153 #7436243
        self.initialSeed = self.seed
        self.spriteChangeCounter = 0
        self.spawnOffset = 3
        self.level = 0
        self.levelSize = 60
        self.cellSize = 100
        self.mapCounter = 0
        #all music by Mewmore, used with permission
        self.menuSong = 'data\\Nimbasa City (Remix).mp3'
        song1 = 'data\\Team Rocket Hideout (GSC Remix).mp3'
        song2 = 'data\\Battle! Vs Gym Leader (XY Remix).mp3'
        song3 = 'data\\Drought (Remix).mp3'
        song4 = 'data\\Indigo Plateau (Remix).mp3'
        self.songList = [song1, song2, song3, song4]
        self.volume = 0.5
        self.gunSound = pygame.mixer.Sound('data\\gunfire.wav')
        self.reviveSound = pygame.mixer.Sound('data\\revive.wav')

    def getLevelParameters(self):
        self.stepsPerWalkList = [4,5,6,7]
        maxWalks = self.level*20 + 200
        maxStepsPerWalk = self.stepsPerWalkList[getRandRange(self, len(self.stepsPerWalkList))]
        return maxStepsPerWalk, maxWalks

    def getWallList(self):
        if self.mapCounter%2 == 0:
            maxStepsPerWalk, maxWalks = self.getLevelParameters()
            wallList = drunkardWalk(self,self.levelSize, maxStepsPerWalk, maxWalks)
            wallList = cutWallList(wallList)
            exitCoords = getExit(self, wallList)
            wallList[exitCoords[0]][exitCoords[1]] = 'X'
        else:
            wallList = generateMap2(self)
            wallList = cutWallList(wallList)
        return wallList

class Map(object):
    def __init__(self, game):
        self.wallList = game.getWallList()
        self.cols = len(self.wallList[2])
        self.rows = len(self.wallList)
        self.width = self.cols * game.cellSize
        self.height = self.rows * game.cellSize
        self.image = pygame.Surface((self.width, self.height))
        self.floorColor = (40,30,30)
        self.image.fill(self.floorColor)
        self.healthSprites = pygame.sprite.Group()

    def placeWalls(self, game, camera):
        self.wallSprites = pygame.sprite.Group()
        self.enemySprites = pygame.sprite.Group()
        self.deadEnemies = pygame.sprite.Group()
        self.swordSprites = pygame.sprite.Group()
        for row in range(self.rows):
            for col in range(self.cols):
                #loop thru the wallList
                cell = self.wallList[row][col]
                #placing walls
                if cell == False :
                    wallPos = (col*game.cellSize, row*game.cellSize)
                    wall = Wall(wallPos, game)
                    self.wallSprites.add(wall)
                    self.image.blit(wall.image, wall.rect)
                #placing grunts
                elif cell == 'G':
                    gruntPos = (col*game.cellSize, row*game.cellSize)
                    gunGrunt = GunGrunt(gruntPos, game, camera)
                    self.enemySprites.add(gunGrunt)
                elif cell == 'N':
                    necroPos = (col*game.cellSize, row*game.cellSize)
                    necro = Necro(necroPos, game, camera)
                    self.enemySprites.add(necro)
                elif cell == 'S':
                    swordPos = (col*game.cellSize, row*game.cellSize)
                    sword = MeleeGrunt(swordPos, game, camera)
                    self.enemySprites.add(sword)
                    self.swordSprites.add(sword)
                if cell == 'X':
                    exitPos = (col*game.cellSize, row*game.cellSize)
                    self.exit = Exit(exitPos, game, camera)
                    self.image.blit(self.exit.image, self.exit.rect)

class Exit(pygame.sprite.Sprite):
    def __init__(self, pos, game, camera):
        super().__init__()
        image = (pygame.image.load('data\\exitSprite.png')).convert()
        self.image = pygame.transform.scale(image, (game.cellSize+1,game.cellSize+1))
        self.rect = self.image.get_rect(topleft = (pos[0],pos[1]))
        self.x = pos[0]
        self.y = pos[1]
    def update(self, camera, game, player):
        self.rect = self.image.get_rect(topleft = (self.x-camera.xOffset+game.width//2, self.y-camera.yOffset+game.height//2))


##########################################
#Controller Helper functions
##########################################

def getMoveDir(keyList):
    moveVector = [0,0]
    if keyList[K_a]:
        moveVector[0] -= 1
    if keyList[K_d]:
        moveVector[0] += 1
    if keyList[K_w]:
        moveVector[1] -= 1
    if keyList[K_s]:
        moveVector[1] += 1
    return moveVector

#from http://www.cs.cmu.edu/~112/notes/notes-strings.html#basicFileIO
def readFile(path):
    with open(path, "rt") as f:
        return f.read()

#from the 15-112 piazza and http://www.cs.cmu.edu/~112/notes/notes-strings.html#basicFileIO
def writeFile(path, contents):
    with open(path, "a+") as f:
        f.write(contents)

def saveScore(playerName, killCount):
    contents = f'{killCount},{playerName}\n'
    writeFile('data\\leaderboard.txt', contents)

#from http://www.cs.cmu.edu/~112/notes/notes-recursion-part1.html#mergesort 
#slightly altered
def merge(A, B):
    C = [ ]
    i = j = 0
    while ((i < len(A)) or (j < len(B))):
        if ((j == len(B)) or ((i < len(A)) and (A[i][0] >= B[j][0]))):
            C.append(A[i])
            i += 1
        else:
            C.append(B[j])
            j += 1
    return C

#from http://www.cs.cmu.edu/~112/notes/notes-recursion-part1.html#mergesort 
def mergeSort(L):
    if (len(L) < 2):
        return L
    else:
        mid = len(L)//2
        left = mergeSort(L[:mid])
        right = mergeSort(L[mid:])
        return merge(left, right)
##########################################
##########################################
##########################################

def viewLeaderboard(game, clock):
    contents = readFile('data\\leaderboard.txt')
    playerList = []
    for player in contents.splitlines():
        L = player.split(',')
        score = int(L[0])
        name = L[1]
        playerTuple = (score, name)
        playerList.append(playerTuple)
    sortedPlayerList = (mergeSort(playerList))

    titleFont = pygame.font.SysFont(None, 80)
    playerFont = pygame.font.SysFont(None, 40)

    background = pygame.surface.Surface((game.width, game.height))
    background.fill((20,20,20))
    background.convert()
    game.screen.blit(background, (0,0))

    scoreText = (titleFont.render("Score", True, (250,250,250), (0,0,0))).convert()
    scoreText.set_colorkey((0,0,0))
    scoreCenter = (2*game.width//3, 100)
    scoreButton = scoreText.get_rect(center = scoreCenter)

    nameText = (titleFont.render("Player Name", True, (250,250,250), (0,0,0))).convert()
    nameText.set_colorkey((0,0,0))
    nameCenter = (game.width//3, 100)
    nameButton = nameText.get_rect(center = nameCenter)

    backText = (titleFont.render('Back', True, (250,250,250), (0,0,0))).convert()
    backText.set_colorkey((0,0,0))
    backCenter = (game.width//2, 50)
    backButton = backText.get_rect(center = backCenter)

    game.screen.blit(scoreText, scoreButton)
    game.screen.blit(backText, backButton)
    game.screen.blit(nameText, nameButton)

    for i in range(min(20, len(sortedPlayerList))):
        indexTopLeft = (game.width//5, 170+i*50)
        indexText = (playerFont.render(f'{i+1}', True, (250,250,250), (0,0,0))).convert()
        game.screen.blit(indexText, indexTopLeft)

        nameCenter = (game.width//3, 170+i*50)
        nameText = sortedPlayerList[i][1]
        nameText = (playerFont.render(nameText, True, (250,250,250), (0,0,0))).convert()
        game.screen.blit(nameText, nameCenter)

        scoreCenter = (2*game.width//3, 170+i*50)
        scoreText = str(sortedPlayerList[i][0])
        scoreText = (playerFont.render(scoreText, True, (250,250,250), (0,0,0))).convert()
        game.screen.blit(scoreText, scoreCenter)
    
    pygame.display.flip()

    while True:
        time = clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                clickPos = event.pos
                if backButton.collidepoint(clickPos):
                    return

def boot():
    pygame.init()
    pygame.mixer.init()
    game = Game()
    inMenu = True
    clock = pygame.time.Clock()
    game.screen = pygame.display.set_mode((1920,1080))
    game.height = game.screen.get_height()
    game.width = game.screen.get_width()
    path = 'D:\\School\\College\\S2\\112\\TP\\data\\menuBG.jpg'
    #source: https://wallpapercave.com/dark-wallpaper-full-hd
    image, rect = loadImage(path,-1)
    background = image.convert()
    dispReset = pygame.surface.Surface((game.width, game.height))
    dispReset.fill((0,0,0))
    pygame.display.set_caption('Radioactive Chair')
    pygame.mouse.set_visible(1)
    menuFont = pygame.font.SysFont(None, 120)
    titleFont = pygame.font.Font(None, 200)

    #boot menu visuals
    playText = (menuFont.render('Play', True, (250,250,250), (0,0,0))).convert()
    playText.set_colorkey((0,0,0))
    playTopLeft = (((game.width-playText.get_width())//2),game.height//2)
    playButton = playText.get_rect(topleft = playTopLeft)

    settingsText = (menuFont.render('Settings', True, (250,250,250), (0,0,0))).convert()
    settingsText.set_colorkey((0,0,0))
    settingsTopLeft = ((game.width-settingsText.get_width())//2, 5*game.height//8)
    settingsButton = settingsText.get_rect(topleft = settingsTopLeft)

    boardText = (menuFont.render('Leaderboard', True, (250,250,250), (0,0,0))).convert()
    boardText.set_colorkey((0,0,0))
    boardTopLeft = ((game.width-boardText.get_width())//2, 3*game.height//4)
    boardButton = boardText.get_rect(topleft = boardTopLeft)

    exitText = (menuFont.render('Quit', True, (250,250,250), (0,0,0))).convert()
    exitText.set_colorkey((0,0,0))
    exitTopLeft = ((game.width-exitText.get_width())//2, 7*game.height//8)
    exitButton = exitText.get_rect(topleft = exitTopLeft)

    titleText = (titleFont.render('Nightwalker', True, (250,250,250), (0,0,0))).convert()
    titleText.set_colorkey((0,0,0))
    titleTopLeft = ((game.width-titleText.get_width())//2, game.height//4)

    game.screen.blit(dispReset, (0, 0))
    game.screen.blit(background, (0, 0))
    game.screen.blit(playText, playTopLeft)
    game.screen.blit(settingsText, settingsTopLeft)
    game.screen.blit(exitText, exitTopLeft)
    game.screen.blit(boardText, boardTopLeft)
    game.screen.blit(titleText, titleTopLeft)
    pygame.display.flip()
    pygame.event.set_allowed([MOUSEBUTTONDOWN, QUIT])
    
    pygame.mixer.music.load(game.menuSong)
    pygame.mixer.music.play(-1)
    while inMenu:
        time = clock.tick(15)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                clickPos = event.pos
                if exitButton.collidepoint(clickPos):
                    pygame.quit()
                    sys.exit()
                elif settingsButton.collidepoint(clickPos):
                    game.seed = adjustSettings(clock, game)
                elif boardButton.collidepoint(clickPos):
                    viewLeaderboard(game, clock)
                elif playButton.collidepoint(clickPos):
                    inMenu = False
        game.screen.blit(dispReset, (0, 0))
        game.screen.blit(background, (0, 0))
        game.screen.blit(playText, playTopLeft)
        game.screen.blit(settingsText, settingsTopLeft)
        game.screen.blit(boardText, boardTopLeft)
        game.screen.blit(exitText, exitTopLeft)
        game.screen.blit(titleText, titleTopLeft)
        pygame.display.flip()
    playGame(game)

def adjustSettings(clock, game):
    titleFont = pygame.font.SysFont(None, 120)
    menuFont = pygame.font.SysFont(None, 60)

    background = pygame.surface.Surface((game.width, game.height))
    background.fill((20,20,20))
    background.convert()

    settingsText = (titleFont.render("Settings", True, (250,250,250), (0,0,0))).convert()
    settingsText.set_colorkey((0,0,0))
    settingsCenter = (game.width//2, game.height//4)
    settingsButton = settingsText.get_rect(center = settingsCenter)

    backText = (menuFont.render('Back', True, (250,250,250), (0,0,0))).convert()
    backText.set_colorkey((0,0,0))
    backCenter = (game.width//2, 7*game.height//8)
    backButton = backText.get_rect(center = backCenter)

    seedText = (menuFont.render('Enter Seed', True, (250,250,250), (0,0,0))).convert()
    seedText.set_colorkey((0,0,0))
    seedTextCenter = (game.width//2, 3*game.height//8 - 20)
    seedTextRect = seedText.get_rect(center = seedTextCenter)

    seedButton = pygame.rect.Rect(game.width//2-400, 3*game.height//8+20, 800, 75)
    gameSeedText = (menuFont.render(str(game.seed), True, (0,0,0), (250,250,250))).convert()
    gameSeedText.set_colorkey((250,250,250))

    volumeText = (menuFont.render('Volume', True, (250,250,250), (0,0,0))).convert()
    volumeText.set_colorkey((0,0,0))
    volumeCenter = (game.width//2, game.height//2)
    volumeRect = volumeText.get_rect(center = volumeCenter)

    game.screen.blit(background, (0,0))
    game.screen.blit(settingsText, settingsButton)
    game.screen.blit(backText, backButton)
    game.screen.blit(seedText, seedTextRect)
    pygame.draw.rect(game.screen, (250,250,250), seedButton) #text box for seed entry
    game.screen.blit(gameSeedText, seedButton) #seed here
    game.screen.blit(volumeText, volumeRect)

    pygame.draw.line(game.screen, (250,250,250), (game.width//4,
                    game.height//2+40), (3*game.width//4,
                    game.height//2+40), 7) #volume slider line
    volumeSlider = pygame.rect.Rect(int((game.volume*game.width//2) + game.width//4 - 10), game.height + 20, 20, 40)
    pygame.draw.rect(game.screen, (250,250,250), volumeSlider)

    pygame.display.flip()
    seedInput = False
    adjustingVolume = False

    while True:
        time = clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                clickPos = event.pos
                if seedButton.collidepoint(clickPos):
                    game.seed = ''
                    seedInput = True
                else: seedInput = False

                if backButton.collidepoint(clickPos):
                    if not isinstance(game.seed, int): game.seed = game.initialSeed
                    return game.seed
                elif volumeSlider.collidepoint(clickPos):
                    x, y = pygame.mouse.get_rel()
                    adjustingVolume = True

            if event.type == MOUSEBUTTONUP and event.button == 1:
                adjustingVolume = False

            if event.type == pygame.KEYDOWN and seedInput and len(str(game.seed)) < 9:
                if event.key == pygame.K_BACKSPACE:
                    game.seed //= 10
                elif event.key == pygame.K_RETURN:
                    seedInput = False
                elif (event.unicode).isdigit():
                    if game.seed == '': game.seed = 0
                    game.seed = (int(game.seed) * 10) + int(event.unicode)

        if adjustingVolume:
            x, y = pygame.mouse.get_rel()
            volDiff = x/(game.width//2)
            game.volume += volDiff

        gameSeedText = (menuFont.render(str(game.seed), True, (0,0,0), (250,250,250))).convert()
        game.screen.blit(background, (0,0))
        game.screen.blit(settingsText, settingsButton)
        game.screen.blit(backText, backButton)
        game.screen.blit(seedText, seedTextRect)
        pygame.draw.rect(game.screen, (250,250,250), seedButton)
        game.screen.blit(gameSeedText, seedButton)
        game.screen.blit(volumeText, volumeRect)
        pygame.draw.line(game.screen, (250,250,250), (game.width//4,
                game.height//2+40), (3*game.width//4,
                game.height//2+40), 7) #volume slider line
        sliderXPos = int((game.volume*game.width//2) + game.width//4 - 10)
        if sliderXPos > 3*game.width//4: sliderXPos = 3*game.width//4
        elif sliderXPos < game.width//4: sliderXPos = game.width//4
        volumeSlider = pygame.rect.Rect(sliderXPos, int(game.height//2 + 20), 20, 40)
        pygame.draw.rect(game.screen, (250,250,250), volumeSlider)
        pygame.mixer.music.set_volume(game.volume)
        pygame.display.flip()

def incrementLevel(game, player):
    game.seed *= 37
    game.mapCounter += 1
    game.level += 1
    player = Player(game, player.hp, player.killCount)
    allSprites = pygame.sprite.Group((player))
    background = pygame.Surface((game.width, game.height))
    background.fill((0,0,0))
    game.screen.blit(background, (0,0))
    pygame.display.flip()

    currMap = Map(game)
    camera = Camera(game, currMap.wallList)
    currMap.bulletSprites = pygame.sprite.Group()
    currMap.myBulletSprites = pygame.sprite.Group()
    currMap.placeWalls(game, camera)
    currMap.wallSprites.update(camera, game)
    currMap.enemySprites.update(camera, game, currMap)

    game.screen.blit(background, (0,0))
    game.screen.blit(currMap.image, (-(camera.xOffset-game.width//2),-(camera.yOffset-game.height//2)))
    (currMap.enemySprites).draw(game.screen)
    allSprites.draw(game.screen)
    pygame.display.flip()

    shotLag = False
    levelFinished = False
    pygame.mixer.music.load(game.songList[(game.level%len(game.songList))])
    pygame.mixer.music.play(-1, 0)
    return allSprites, player, game, currMap, camera, game, shotLag, levelFinished

def playGame(game):
    clock = pygame.time.Clock()

    player = Player(game)
    allSprites = pygame.sprite.Group((player))
    background = pygame.Surface((game.width, game.height))
    background.fill((0,0,0))
    game.screen.blit(background, (0,0))
    pygame.display.flip()

    #initialize the level map: move this into a separate helper function once multiple levels are implemented
    currMap = Map(game)
    camera = Camera(game, currMap.wallList)
    currMap.bulletSprites = pygame.sprite.Group()
    currMap.myBulletSprites = pygame.sprite.Group()
    currMap.placeWalls(game, camera)
    currMap.wallSprites.update(camera, game)
    currMap.enemySprites.update(camera, game, currMap)

    spriteChange = pygame.USEREVENT
    pygame.time.set_timer(spriteChange, 100)

    #before we enter the game loop: blit everything so that it looks cleaner
    game.screen.blit(background, (0,0))
    game.screen.blit(currMap.image, (-(camera.xOffset-game.width//2),-(camera.yOffset-game.height//2)))
    (currMap.enemySprites).draw(game.screen)
    allSprites.draw(game.screen)
    pygame.display.flip()

    healthFont = pygame.font.SysFont(None, 40)

    shotLag = False
    blockLag = False
    blocking = False
    levelFinished = False

    pygame.event.set_blocked(pygame.MOUSEMOTION)

    pygame.mixer.music.load(game.songList[(game.level%len(game.songList))])
    pygame.mixer.music.set_volume(game.volume)
    pygame.mixer.music.play(-1)

    healthBar = pygame.rect.Rect(50, 50, 160, 40)
    healthRect = pygame.rect.Rect(55,55, int(150*player.hp/player.maxHP), 30)
    healthText = (healthFont.render(f'{player.hp}/{player.maxHP}', True, (250,250,250), (0,0,0))).convert()
    healthText.set_colorkey((0,0,0))
    healthWidth = healthText.get_width()

    #game loop
    while True:
        time = clock.tick(30)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1 and shotLag == False:
                    player.shoot(game, event.pos, currMap, camera)
                    shotLag = True
                elif event.button == 3 and blockLag == False and game.level > 3:
                    player.block(game, event.pos, camera)
                    blockLag = True
                    blocking = True

            if event.type == 24:
                game.spriteChangeCounter += 1
                player.spriteUpdate(moveVector, game)
                if game.spriteChangeCounter%3 == 0:
                    shotLag = False
                    
                if game.spriteChangeCounter%10 == 0:
                    if blocking == True: player.blockSprite.kill()
                    blocking = False
                    blockLag = False

            
            #deals with updating enemies
                for enemy in currMap.enemySprites:
                    enemy.hitTimer -= 1
                    if enemy.type == 'necro': enemy.reviveCircleTimer -= 1
                    if ((enemy.rect.left > 0) and (enemy.rect.top > 0) and
                        (enemy.rect.right < game.width) and
                        (enemy.rect.bottom < game.height)):
                            if ((game.spriteChangeCounter+enemy.timeDelay)%(enemy.updateFrequency) == 1):

                                enemy.hitWallRecently = False

                                if enemy.type == 'grunt': 
                                    enemy.shoot(game, currMap, camera)

                                    if covered(enemy, player, currMap, game, camera) or enemy.peeking:
                                        enemy.peek(game, camera, currMap)
                                        enemy.peeking = True
                                    else:
                                        enemy.lastX = enemy.dirX
                                        enemy.lastY = enemy.dirY
                                        enemy.getAction()

                                elif enemy.type == 'necro':
                                    if covered(enemy, player, currMap, game, camera):
                                        enemy.dirX = enemy.dirY = 0
                                    else: enemy.getAction()

                                elif enemy.type == 'sword':
                                    if covered(enemy, player, currMap, game, camera):
                                        enemy.charging = False
                                        enemy.getAction()
                                    else:
                                        enemy.charge(game, currMap, camera)

                            enemy.active = True
                    else:
                        enemy.active = False
                #resets shooting
                if game.spriteChangeCounter%100 == 1 and levelFinished:
                    (allSprites, player, game, currMap, camera, game, shotLag, levelFinished) = incrementLevel(game, player)

        #movement
        keyList = pygame.key.get_pressed()
        if keyList[K_ESCAPE]:
            pygame.quit()
            sys.exit()
        moveVector = getMoveDir(keyList)

        #shooting
        
        #deals with movement
        if moveVector != [0,0] and levelFinished == False:
            if (abs(moveVector[0]) == abs(moveVector[1])):
                if camera.update(player, currMap, [.7*mag for mag in moveVector], game):
                    levelFinished = True
                    if game.level == 3:
                        if victoryScreen(clock, game):
                            restart = True
                            break
                        else: incrementLevel(game, player)
            else:
                if camera.update(player, currMap, moveVector, game):
                    levelFinished = True
                    if game.level == 3:
                        if victoryScreen(clock, game):
                            restart = True
                            break
                        else: incrementLevel(game, player)
        #deals with flipping the character
            if (moveVector[0] != player.lastFaced and moveVector[0] != 0):
                player.flipped = not player.flipped
                player.lastFaced = moveVector[0]

        #updates bullets
        currMap.bulletSprites.update(currMap, camera, player)
        currMap.myBulletSprites.update(currMap, camera, player)

        #deals with idle/walking animations
        

        player.hitTimer -= 1
        for enemy in currMap.enemySprites:
            if enemy.active:
                enemy.update(camera, game, currMap)

        #deals with bullet collisions
        ratioBulletCollide = pygame.sprite.collide_rect_ratio(.85)
        hitEnemies = pygame.sprite.groupcollide(currMap.enemySprites, currMap.myBulletSprites, False, True, collided=ratioBulletCollide)
        for enemy in hitEnemies:
            enemy.hp -= 1
            enemy.hitTimer = 3
            if enemy.hp == 0:
                enemy.die(currMap, player, camera, game)
        pygame.sprite.groupcollide(currMap.wallSprites, currMap.myBulletSprites, False, True)
        pygame.sprite.groupcollide(player.blockSprites, currMap.bulletSprites, False, True)
        pygame.sprite.groupcollide(currMap.wallSprites, currMap.bulletSprites, False, True)
        healthCollideList = pygame.sprite.spritecollide(player, currMap.healthSprites, True)
        collideList = pygame.sprite.spritecollide(player, currMap.bulletSprites, True, collided=ratioBulletCollide)
        swordCollideList = pygame.sprite.spritecollide(player, currMap.swordSprites, False, collided=ratioBulletCollide)
        if ((collideList != [] or swordCollideList != []) and player.hitTimer < -10):
            player.hp -= (len(collideList) + 2*len(swordCollideList))
            player.hitTimer = 4
            healthRect = pygame.rect.Rect(50,50, int(150*player.hp/player.maxHP), 40)
            healthText = (healthFont.render(f'{player.hp}/{player.maxHP}', True, (250,250,250), (0,0,0))).convert()
            if player.hp <= 0:
                levelFinished = True
                restart = loseScreen(clock, game, player)
                if restart: break
        if (len(healthCollideList) != 0) and player.hp < player.maxHP:
            player.hp += len(healthCollideList)
            healthRect = pygame.rect.Rect(55,55, int(150*player.hp/player.maxHP), 30)
            healthText = (healthFont.render(f'{player.hp}/{player.maxHP}', True, (250,250,250), (0,0,0))).convert()
        currMap.healthSprites.update(camera, game, player)

        game.screen.blit(background, (0,0))
        game.screen.blit(currMap.image, (-(camera.xOffset-game.width//2),-(camera.yOffset-game.height//2)))
        currMap.bulletSprites.draw(game.screen)
        currMap.myBulletSprites.draw(game.screen)
        currMap.deadEnemies.draw(game.screen)
        (currMap.enemySprites).draw(game.screen)
        player.blockSprites.draw(game.screen)
        allSprites.draw(game.screen)

        currMap.healthSprites.draw(game.screen)
        pygame.draw.rect(game.screen, (250,250,250), healthBar)
        pygame.draw.rect(game.screen, (250,0,0), healthRect)
        healthText.set_colorkey((0,0,0))
        game.screen.blit(healthText, (healthRect.centerx-healthWidth//2, healthRect.top+5))
        pygame.display.flip()

    if restart:
        boot()

def victoryScreen(clock, game):
    victoryFont = pygame.font.SysFont(None, 120)
    menuFont = pygame.font.SysFont(None, 80)
    blockFont = pygame.font.SysFont(None, 50)
    background = pygame.surface.Surface((game.width, game.height))
    background.fill((20,20,20))
    background.convert()
    lossText = (victoryFont.render("You've Made It", True, (250,250,250), (0,0,0))).convert()
    lossText.set_colorkey((0,0,0))
    lossCenter = (game.width//2, game.height//3)
    lossButton = lossText.get_rect(center = lossCenter)
    quitText = (menuFont.render('Quit', True, (250,250,250), (0,0,0))).convert()
    quitText.set_colorkey((0,0,0))
    quitCenter = (2*game.width//3, game.height//2)
    quitButton = quitText.get_rect(center = quitCenter)
    menuText = (menuFont.render('Menu', True, (250,250,250), (0,0,0))).convert()
    menuText.set_colorkey((0,0,0))
    menuCenter = (game.width//3, game.height//2)
    menuButton = menuText.get_rect(center = menuCenter)
    continueText = (menuFont.render('Continue', True, (250,250,250), (0,0,0))).convert()
    continueText.set_colorkey((0,0,0))
    continueCenter = (game.width//2, 3*game.height//4)
    continueButton = menuText.get_rect(center = continueCenter)
    blockText = (menuFont.render('It only gets harder from here... Right-click to block bullets', True, (250,250,250), (0,0,0))).convert()
    blockCenter = (game.width//2, 7*game.height//8)
    blockButton = blockText.get_rect(center = blockCenter)
    game.screen.blit(background, (0,0))
    game.screen.blit(lossText, lossButton)
    game.screen.blit(quitText, quitButton)
    game.screen.blit(menuText, menuButton)
    game.screen.blit(blockText, blockButton)
    game.screen.blit(continueText, continueButton)
    pygame.display.flip()

    while True:
        time = clock.tick(15)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                clickPos = event.pos
                if quitButton.collidepoint(clickPos):
                    pygame.quit()
                    sys.exit()
                elif menuButton.collidepoint(clickPos):
                    return True
                elif continueButton.collidepoint(clickPos):
                    return False

def loseScreen(clock, game, player):
    menuFont = pygame.font.SysFont(None, 120)
    killsFont = pygame.font.SysFont(None, 60)
    background = pygame.surface.Surface((game.width, game.height))
    background.fill((20,20,20))
    background.convert()
    lossText = (menuFont.render('You Died!', True, (250,250,250), (0,0,0))).convert()
    lossText.set_colorkey((0,0,0))
    lossCenter = (game.width//2, game.height//4)
    lossButton = lossText.get_rect(center = lossCenter)

    killsText = (killsFont.render(f'You took {player.killCount} enemies with you', True, (250,250,250), (0,0,0))).convert()
    killsText.set_colorkey((0,0,0))
    killsCenter = (game.width//2, game.height//2)
    killsButton = killsText.get_rect(center = killsCenter)

    seedText = (killsFont.render('Enter Your Name Here', True, (250,250,250), (0,0,0))).convert()
    seedText.set_colorkey((0,0,0))
    seedTextCenter = (game.width//2, 5*game.height//8 + 20)
    seedTextRect = seedText.get_rect(center = seedTextCenter)
    playerName = ''

    seedButton = pygame.rect.Rect(game.width//2-400, 5*game.height//8+60, 800, 75)
    gameSeedText = (killsFont.render(playerName, True, (0,0,0), (250,250,250))).convert()
    gameSeedText.set_colorkey((250,250,250))

    quitText = (menuFont.render('Quit', True, (250,250,250), (0,0,0))).convert()
    quitText.set_colorkey((0,0,0))
    quitCenter = (3*game.width//4, 7*game.height//8)
    quitButton = quitText.get_rect(center = quitCenter)
    menuText = (menuFont.render('Menu', True, (250,250,250), (0,0,0))).convert()
    menuText.set_colorkey((0,0,0))
    menuCenter = (game.width//4, 7*game.height//8)
    menuButton = menuText.get_rect(center = menuCenter)


    game.screen.blit(background, (0,0))
    game.screen.blit(lossText, lossButton)
    game.screen.blit(quitText, quitButton)
    game.screen.blit(menuText, menuButton)
    game.screen.blit(killsText, killsButton)

    game.screen.blit(seedText, seedTextRect)
    pygame.draw.rect(game.screen, (250,250,250), seedButton)
    game.screen.blit(gameSeedText, seedButton)

    pygame.display.flip()

    nameInput = False
    while True:
        time = clock.tick(15)
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                clickPos = event.pos

                if seedButton.collidepoint(clickPos):
                    playerName = ''
                    nameInput = True
                else: nameInput = False

                if quitButton.collidepoint(clickPos):
                    pygame.quit()
                    sys.exit()
                elif menuButton.collidepoint(clickPos):
                    return True
            if event.type == pygame.KEYDOWN and nameInput:
                if event.key == pygame.K_BACKSPACE:
                    playerName = playerName[:-1]
                if len(playerName) < 4:
                    if event.key == pygame.K_RETURN:
                        nameInput = False
                        saveScore(playerName, player.killCount)
                        return True
                    elif (event.unicode).isalnum():
                        playerName += event.unicode

        gameSeedText = (killsFont.render(playerName, True, (0,0,0), (250,250,250))).convert()
        game.screen.blit(background, (0,0))
        game.screen.blit(lossText, lossButton)
        game.screen.blit(quitText, quitButton)
        game.screen.blit(menuText, menuButton)
        game.screen.blit(killsText, killsButton)

        game.screen.blit(seedText, seedTextRect)
        pygame.draw.rect(game.screen, (250,250,250), seedButton)
        game.screen.blit(gameSeedText, seedButton)
        pygame.display.flip()

boot()