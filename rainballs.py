#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# rainballs - A Rain of Balls
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
# - Fix the damn collision response to avoid infinite bumping!
# - Do so without breaking fully elastical bounces!

import sys
import pygame
import math
from random import randint, random, choice


# General options
BENCHMARK = False
FULLSCREEN = False
DEBUG = True
AUTOPLAY = True
TRACE = False
BALLS = 2


# Colors
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)


# Render stuff
SCREEN_SIZE = (600, 600)     # Fullscreen ignores this and always use desktop resolution
FPS = 0 if BENCHMARK else 60  # 0 for unbounded
BG_COLOR = BLUE


# Physics stuff - Units in pixels/second
GRAVITY = (0, 0)                 # A vector, like everything else
DAMPING = (1, 1)                     # Velocity restitution coefficient of collisions on boundaries
FRICTION = 0                         # Kinetic coefficient of friction
TIMESTEP = 1./(FPS or 60)            # dt of physics simulation

EPSILON_V = max(abs(GRAVITY[0]),
                abs(GRAVITY[1]))*TIMESTEP/2  # Velocity resolution threshold
#EPSILON_S = 0.1
#SCALE = 100  # How many pixels is a "meter"


# Ball initial values
radius = 100
pos = [100, 300]
vel = [300, 0]
elast = (1, 0.7)


# Some singletons
args = None
screen = None
background = None
balls = None




class Args(object):
    def __init__(self, **kwargs):
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])




class Ball(pygame.sprite.Sprite):
    def __init__(self, color=WHITE, radius=10, position=[], velocity=[], density=1,
                 elasticity=(1,1)):
        super(Ball, self).__init__()

        # Basic properties
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


    def update(self, elapsed=None):
        super(Ball, self).update()

        if elapsed is None:
            elapsed = TIMESTEP

        # dt should be constant and small, 1./60 is perfect. But I shall not enforce this here
        dt = elapsed  # Alternatives: TIMESTEP; 1./FPS; 1./60

        def bounce():
            # Reflect velocity prior to collision, dampered
            self.velocity[i] = -(v+self.velocity[i])/2 * min(self.elasticity[i], DAMPING[i])
            # set to zero when low enough
            if abs(self.velocity[i]) < EPSILON_V:
                self.velocity[i] = 0

        if self.velocity == [0, 0] and self.on_ground:
            return

        for i in [0, 1]:
            # Save current values before any change
            p, v = self.position[i], self.velocity[i]

            # Apply gravity to velocity
            if not (self.on_ground and self.velocity[i] == 0):  # looks sooo hackish...
                self.velocity[i] += GRAVITY[i] * dt

            # Apply velocity to position, Velocity Verlet method
            self.position[i] += v * dt + GRAVITY[i] * dt**2 / 2.

            # Check lower boundary
            if self.position[i] < self.radius:
                self.position[i] = self.radius  # This could be refined... perhaps reflected? -self.position[i]
                bounce()

            # Check upper boundary
            elif self.position[i] > self.bounds[i]:
                self.position[i] = self.bounds[i]  # Reflection would be self.bounds[i]-(self.position[i]-self.bounds[i])
                bounce()

        # Apply friction if ball is sliding on ground
        if self.on_ground and self.velocity[1] == 0:
            self.velocity[0] -= math.copysign(min(abs(self.velocity[0]),
                                                  abs(GRAVITY[1] * FRICTION * dt)),
                                               self.velocity[0])
            # Make it stop if low enough
            if abs(self.velocity[0]) < EPSILON_V:
                self.velocity[0] = 0

        self._update_rect()


    def collide(self, other):
        print "collide! %r %r at %s" % (self.color, other.color, self.position)
        offset = 1 * math.copysign(1, self.velocity[0])
        self.position[0]  -= offset
        other.position[0] += offset
        self.velocity[0]  *= -1
        other.velocity[0] *= -1
        self._update_rect()
        other._update_rect()


    def printdata(self, comment):
        if args.debug:
            print "id=%s p=[%7.2f, %7.2f] v=[%7.2f, %7.2f] %s" % (
                self.color,
                self.position[0], self.position[1],
                self.velocity[0], self.velocity[1],
                comment)




def main(*argv):
    """ Main Program """
    global screen, background, balls, args

    # Soon to be replaced by a proper argparse
    args = Args(fullscreen=FULLSCREEN, benchmark=BENCHMARK, debug=DEBUG)

    pygame.init()

    # Set caption and icon
    caption = "Rain Balls"
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

    # Create the balls
    balls = pygame.sprite.Group()
    balls.add(Ball(color=RED,   radius=radius, position=pos, velocity=vel))
    balls.add(Ball(color=GREEN, radius=radius,
                   position=[500, pos[1]+150], velocity=[-vel[0],vel[1]]))
#     for _ in xrange(BALLS):
#         balls.add(Ball(color=(randint(0,255), randint(0,255), randint(0,255)),
#                        radius=randint(10, radius),
#                        position=[randint(100, screen.get_size()[0]-radius),
#                                  randint(100, screen.get_size()[0]-radius)],
#                        velocity=[randint(50, vel[0]), randint(50, vel[1])],
#                        ))

    # -------- Main Game Loop -----------
    trace = TRACE
    play = AUTOPLAY
    step = False

    def render():
        if not trace:
            balls.clear(screen, background)
        balls.draw(screen)
        pygame.display.update()

    # draw t=0
    clock = pygame.time.Clock()
    balls.update(0)
    render()
    elapsed = clock.tick(FPS)

    rendertimes = []
    updatetimes = []
    fpslist = []
    framecounter = 0
    done = False
    while not done:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
                    screen.blit(background, background.get_rect())
                    trace = not trace
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    play = not play
                    if not play:
                        balls.sprites()[0].printdata("Paused")
                if event.key == pygame.K_SPACE:
                    if play:
                        play = False
                        balls.sprites()[0].printdata("Paused")
                    else:
                        play = step = True

        if play:

            # Update
            t1 = pygame.time.get_ticks()
            balls.update()  # real dt: elapsed/1000.

            # Collision detection and resolution
            # TODO: remove ball from balls (use temp group) after processing, to avoid redundant checks
            for ball in balls:
                for other in pygame.sprite.spritecollide(ball, balls, False):
                    if other is not ball:
                        ball.collide(other)
                break

            # Draw
            t2 = pygame.time.get_ticks()
            render()
            t3 = pygame.time.get_ticks()

            if args.benchmark:
                updatetimes.append(t2 - t1)
                rendertimes.append(t3 - t2)
                if framecounter == 10:
                    fpslist.append(clock.get_fps())
                    framecounter = 0
                framecounter += 1
                if pygame.time.get_ticks() > 10000:
                    done = True
            elif not args.fullscreen:
                if framecounter == FPS:
                    pygame.display.set_caption("%s - FPS: %7.2f" % (caption,clock.get_fps()))
                    framecounter = 0
                framecounter += 1

            if step:
                play = step = False
                balls.sprites()[0].printdata("Frame")

        elapsed = clock.tick(FPS)

    if args.benchmark and fpslist :
        def printtimes(name, times, limit, lowerisbetter=False):
            fail = sum(1 for x in times if (x<limit if lowerisbetter else x>limit))
            total = len(times)
            failp = 100. * fail / total
            print ("%s: " + 6*"%3d  ") % (
                name, min(times), sum(times)/total, max(times), limit, fail, failp)
        print      "t (ms): min, avg, max, top, fail   %"
        printtimes("Update", updatetimes, TIMESTEP*1000)
        printtimes("Render", rendertimes, TIMESTEP*1000)
        printtimes("FPS   ", fpslist, 1./TIMESTEP, True)

    pygame.quit()
    return True




if __name__ == "__main__":
    sys.exit(0 if main(*sys.argv[1:]) else 1)
