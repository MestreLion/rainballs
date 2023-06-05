#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# reskanoid - Arkanoid clone using Pygame
#
#    Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>
#
# TODO:
# - Create a scale factor to map pixels to abstract meters

import sys
import pygame
import math
from random import randint, random, choice


# General options
BENCHMARK = False
FULLSCREEN = False
DEBUG = False
AUTOPLAY = False
TRACE = False
BALLS = 10


# Colors
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GRAY  = (127, 127, 127)



# Render stuff
SCREEN_SIZE = (700, 800)     # Fullscreen ignores this and always use desktop resolution
FPS = 0 if BENCHMARK else 60  # 0 for unbounded
BG_COLOR = BLUE


# Physics stuff - Units in pixels/second
GRAVITY = (0, 0)                 # A vector, like everything else
DAMPING = (1, 1)                     # Velocity restitution coefficient of collisions on boundaries
TIMESTEP = 1./(FPS or 60)            # dt of physics simulation

EPSILON_V = max(abs(GRAVITY[0]),
                abs(GRAVITY[1]))*TIMESTEP/2  # Velocity resolution threshold
#EPSILON_S = 0.1
#SCALE = 100  # How many pixels is a "meter"


# Ball initial values
radius = 15
pos = [100, 200]
vel = [400, 400]
elast = (1, 0.7)


# Some singletons
args = None
screen = None
background = None




class Args(object):
    def __init__(self, **kwargs):
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])




class Level(object):
    """ Stores information about each level, particularly block layout """
    # TODO: this could be a sprite.Group subclass

    BLOCKW = 50
    BLOCKH = 20

    def __init__(self, **kwargs):
        self.blocks = pygame.sprite.Group()
        self.stage = 1
        for row in xrange(10):
            top = 100 + row * (self.BLOCKH + 5)
            for col in xrange(10):
                left = 75 + col * (self.BLOCKW + 5)
                self.blocks.add(Block(self, rect=pygame.Rect(left, top, self.BLOCKW, self.BLOCKH)))

    def update(self):
        self.blocks.update()

    def draw(self, surface):
        self.blocks.draw(surface)




class Body(object):
    """ Superclass for bodies that require collision detection, response, etc """
    def collisionResponse(self):
        pass




class Block(pygame.sprite.Sprite, Body):
    def __init__(self, level, color=WHITE, rect=None, velocity=[], hits=1):
        super(Block, self).__init__()

        # Basic properties
        self.level = level
        self.color = color
        self.rect = pygame.Rect(rect)
        self.velocity = list(velocity) or [0, 0]
        self.hits = hits

        # Derived properties
        self.bounds = (screen.get_size()[0] - self.rect.width ,
                       screen.get_size()[1] - self.rect.height)

        # Pygame sprite requirements
        self.image = pygame.Surface(self.rect.size)
        self.image.fill(self.color)


    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.level.blocks.remove(self)




class Ball(pygame.sprite.Sprite, Body):
    def __init__(self, level, color=WHITE, radius=10, position=[], velocity=[], density=1,
                 elasticity=(1,1)):
        super(Ball, self).__init__()

        # Basic properties
        self.level = level
        self.color = color
        self.radius = radius
        self.position = list(position) or [0, 0]
        self.velocity = list(velocity) or [0, 0]
        self.density = density
        self.elasticity = elasticity

        # Derived properties
        self.area = self.radius * math.pi**2
        self.mass = self.area * self.density
        self.bounds = (screen.get_size()[0] - self.radius,
                       screen.get_size()[1] - self.radius)

        # Pygame sprite requirements
        self.image = pygame.Surface(2*[self.radius*2])
        self.rect = self.image.get_rect()
        self._update_rect()
        self.image.fill(BG_COLOR)
        self.image.set_colorkey(BG_COLOR)
        pygame.draw.circle(self.image, self.color, 2*(self.radius,), self.radius)


    @property
    def on_ground(self):
        return self.position[1] == self.radius


    def _update_rect(self):
        self.rect.center = (int(self.position[0]),
                            int(screen.get_size()[1] - self.position[1]))

    def _update_position(self):
        self.position = [self.rect.center[0],
                         screen.get_size()[1] - self.rect.center[1]]


    def update(self, elapsed=None):
        super(Ball, self).update()

        if elapsed is None:
            elapsed = TIMESTEP

        # dt should be constant and small, 1./60 is perfect. But I shall not enforce this here
        dt = elapsed  # Alternatives: TIMESTEP; 1./FPS; 1./60

        if self.velocity == [0, 0] and self.on_ground:
            return

        for i in [0, 1]:
            # Apply velocity to position
            self.position[i] += self.velocity[i] * dt

            # Check lower boundary
            if self.position[i] < self.radius:
                self.position[i] = self.radius
                self.velocity[i] = -self.velocity[i]

            # Check upper boundary
            elif self.position[i] > self.bounds[i]:
                self.position[i] = self.bounds[i]
                self.velocity[i] = -self.velocity[i]

        self._update_rect()


    def collisionResponse(self, block):
        """ Basic response: move away from it :) """
        # Calculate intrusion depth
        intrusion = self.rect.clip(block)

        # Intrusion time for each axis
        tx = abs(intrusion.width  / self.velocity[0])
        ty = abs(intrusion.height / self.velocity[1])

        # Which one happened first?
        if tx > ty:
            # Adjust position to either left or right of block
            if self.velocity[0] > 0:
                self.rect.right = block.rect.left
            else:
                self.rect.left = block.rect.right
            # Reflect velocity horizontally
            self.velocity[0] *= -1

        else:
            # Adjust position to either left or right of block
            if self.velocity[1] > 0:
                self.rect.top = block.rect.bottom
            else:
                self.rect.bottom = block.rect.top
            # Reflect velocity vertically
            self.velocity[1] *= -1

        self._update_position()


    def printdata(self, comment):
        if args.debug:
            print "p=[%7.2f, %7.2f] v=[%7.2f, %7.2f] %s" % (
                self.position[0], self.position[1],
                self.velocity[0], self.velocity[1],
                comment)



class Paddle(pygame.sprite.Sprite, Body):

    BLOCKW = 100
    BLOCKH = 20
    MARGIN = 20
    SPEED = 500

    def __init__(self, level, color=WHITE, rect=None, velocity=0):
        super(Paddle, self).__init__()

        # Basic properties
        self.level = level
        self.color = color
        self.rect = pygame.Rect((screen.get_size()[0] - self.BLOCKW)/2,
                                screen.get_size()[1] - self.BLOCKH - self.MARGIN,
                                self.BLOCKW,
                                self.BLOCKH)
        self.velocity = velocity
        self.bounds = pygame.Rect(0, self.rect.top, screen.get_size()[0], self.BLOCKH)

        # Pygame sprite requirements
        self.image = pygame.Surface(self.rect.size)
        self.image.fill(self.color)


    def update(self, dt=None):
        """ Move the paddle. """
        if dt is None:
            dt = TIMESTEP
        self.rect.x += self.velocity * dt
        self.rect.clamp_ip(self.bounds)

    # Player-controlled movement:
    def go_left(self):
        """ Called when the user hits the left arrow. """
        self.velocity = -self.SPEED

    def go_right(self):
        """ Called when the user hits the right arrow. """
        self.velocity = self.SPEED

    def stop(self):
        """ Called when the user lets off the keyboard. """
        self.velocity = 0




def main(argv=None):
    """ Main Program """
    global screen, background, balls, args

    # Soon to be replaced by a proper argparse
    args = Args(fullscreen=FULLSCREEN, benchmark=BENCHMARK, debug=DEBUG)

    pygame.init()

    # Set caption and icon
    caption = "Reskanoid"
    pygame.display.set_caption(caption)
    if sys.platform.startswith("linux"):
        try:
            icon = pygame.image.load("/usr/share/pyshared/pygame/pygame_icon.tiff")
            pygame.display.set_icon(icon)
        except pygame.error as e:
            print e

    # Set the screen
    flags = 0
    size = SCREEN_SIZE
    if args.fullscreen:
        flags |= pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        size = (0, 0)  # current desktop resolution
        pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode(size, flags)

    # Set the background
    background = pygame.Surface(screen.get_size())
    background.fill(BG_COLOR)
    screen.blit(background, (0,0))

    # Create the level
    level = Level()

    # Create the ball
    ball = Ball(level, RED, radius, pos, velocity=vel)

    # Create the player paddle
    paddle = Paddle(level)

    # All sprites
    sprites = pygame.sprite.Group(ball, paddle)

    # -------- Main Game Loop -----------
    play = AUTOPLAY
    step = False

    def render():
        screen.fill(BG_COLOR)
        #sprites.clear(screen, background)
        level.draw(screen)
        sprites.draw(screen)
        pygame.display.update()

    render()
    clock = pygame.time.Clock()

    frames = 0
    done = False
    while not done:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                done = True

            if event.type == pygame.KEYDOWN:
                if   event.key == pygame.K_LEFT:
                    paddle.go_left()
                elif event.key == pygame.K_RIGHT:
                    paddle.go_right()

            if event.type == pygame.KEYUP:
                if   event.key == pygame.K_LEFT and paddle.velocity < 0:
                    paddle.stop()
                elif event.key == pygame.K_RIGHT and paddle.velocity > 0:
                    paddle.stop()

                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    play = not play
                    if not play:
                        ball.printdata("Paused")
                elif event.key == pygame.K_SPACE:
                    if play:
                        play = False
                        ball.printdata("Paused")
                    else:
                        play = step = True
                elif event.key == pygame.K_ESCAPE:
                    done = True

        if play:
            sprites.update()
            level.update()

            ####### Collision detection

            # Ball against blocks
            while True:
                block = pygame.sprite.spritecollideany(ball, level.blocks)
                if not block:
                    break
                ball.collisionResponse(block)
                block.hit()

            # Ball against paddle
            if ball.rect.colliderect(paddle):
                ball.collisionResponse(paddle)

            render()

            if step:
                play = step = False
                ball.printdata("Frame")

        if not args.fullscreen:
            frames += 1
            if frames == FPS:
                pygame.display.set_caption("%s - FPS: %.2f" % (caption, clock.get_fps()))
                frames = 0

        elapsed = clock.tick(FPS)

    pygame.quit()
    return True




if __name__ == "__main__":
    sys.exit(0 if main(sys.argv) else 1)
