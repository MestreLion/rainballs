#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# rainballs - A Rain of Balls
#
#    Copyright (C) 2013 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
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
# - Change integration method from Euler to Verlet
# - Change coordinate system from PC to Euclidian
# - Create a scale factor to map pixels to abstract meters

import sys
import pygame
import math


# General options
BENCHMARK = False
FULLSCREEN = False
DEBUG = True
AUTOPLAY = True
TRACE = False


# Colors
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)


# Render stuff
SCREEN_SIZE = (1600, 900)     # Fullscreen ignores this and always use desktop resolution
FPS = 0 if BENCHMARK else 60  # 0 for unbounded


# Physics stuff - Units in pixels/second
GRAVITY = (0, 2000)                  # A vector, like everything else
DAMPING = (1, 0.8)                   # Velocity restitution coefficient of collisions on boundaries
FRICTION = 0.3                       # Kinetic coefficient of friction
TIMESTEP = 1.0/(FPS or 60)           # dt of physics simulation
EPSILON_V = max(GRAVITY)*TIMESTEP/2  # Velocity resolution threshold
#EPSILON_S = 0.1
#SCALE = 100  # How many pixels is a "meter"


# Ball initial values
radius = 50
pos = [20, 20]
vel = [500, 0]




class Args(object):
    def __init__(self, **kwargs):
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])




class Ball(pygame.sprite.Sprite):
    def __init__(self, color=WHITE, radius=1, pos=[0,0], velocity=[0,0]):
        super(Ball, self).__init__()

        self.radius = radius
        self.color = color
        self.velocity = velocity

        self.pos = pos

        self.image = pygame.Surface(2*[radius*2])
        pygame.draw.circle(self.image, color, 2*(radius,), radius)
        self.rect = self.image.get_rect()
        self.rect.x = int(self.pos[0])
        self.rect.y = int(self.pos[1])

        self.bounds=(SCREEN_SIZE[0] - 2*self.radius, SCREEN_SIZE[1] - 2*self.radius)

    @property
    def on_ground(self):
        return self.pos[1] == self.bounds[1]

    def update(self, elapsed):
        super(Ball, self).update()

        # For now (perhaps forever), ignore real elapsed time and used a fixed dt
        dt = elapsed  # Alternatives: TIMESTEP; 1; 1.0/FPS; 60.0/FPS; elapsed/TIMEFRAME

        def bounce():
            self.printdata()
            # Reflect velocity, dampered
            self.velocity[i] *= -DAMPING[i]
            # set to zero when low enough
            if abs(self.velocity[i]) < EPSILON_V:
                self.velocity[i] = 0

        if self.velocity == [0, 0] and self.on_ground:
            return

        for i in [0, 1]:
            # Apply gravity to velocity
            if not (self.on_ground and self.velocity[i] == 0):  # looks sooo hackish...
                self.velocity[i] += GRAVITY[i] * dt

            # Apply velocity to position
            self.pos[i] += self.velocity[i] * dt

            # Check lower boundary
            if self.pos[i] < 0:
                self.pos[i] = 0  # This could be refined... perhaps reflected? -self.pos[i]
                bounce()

            # Check upper boundary
            elif self.pos[i] > self.bounds[i]:
                self.pos[i] = self.bounds[i]  # Reflection would be self.bounds[i]-(self.pos[i]-self.bounds[i])
                bounce()

        # Apply friction if ball is sliding on ground
        if self.on_ground and self.velocity[1] == 0:
            self.velocity[0] -= math.copysign(min(abs(self.velocity[0]),
                                                  abs(GRAVITY[1] * FRICTION * dt)),
                                               self.velocity[0])  # self.velocity[0] * friction
            # Make it stop if low enough
            if abs(self.velocity[0]) < EPSILON_V:
                self.velocity[0] = 0
            self.printdata()

        self.rect.x = int(self.pos[0])
        self.rect.y = int(self.pos[1])

    def printdata(self):
        if args.debug:
            print "p=[%7.2f, %7.2f] v=[%7.2f, %7.2f]" % (self.pos[0], self.pos[1],
                                                         self.velocity[0], self.velocity[1])




def main():
    pygame.init()
    flags = 0
    if args.fullscreen:
        global SCREEN_SIZE
        flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        SCREEN_SIZE = (pygame.display.Info().current_w,
                       pygame.display.Info().current_h)
    screen = pygame.display.set_mode(SCREEN_SIZE, flags)

    background=pygame.Surface(screen.get_size())
    background=background.convert()

    ball = Ball(RED, radius, pos, vel)
    balls = pygame.sprite.Group(ball)

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
    clock.tick(FPS)

    rendertimes = []
    updatetimes = []
    fpslist = []
    framecounter = 0
    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
                    screen.blit(background, background.get_rect())
                    trace = not trace
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    play = not play
                    if args.debug and not play:
                        ball.printdata()
                elif event.key == pygame.K_SPACE:
                    ball.printdata()
                    if play:
                        play = False
                    else:
                        play = step = True
                elif event.key == pygame.K_ESCAPE:
                    done = True

        if play:
            t1 = pygame.time.get_ticks()
            balls.update(TIMESTEP)  # real: clock.get_time()/1000.0
            t2 = pygame.time.get_ticks()
            render()
            t3 = pygame.time.get_ticks()
            if args.benchmark or args.debug:
                if args.debug:
                    updatetimes.append(t2 - t1)
                    rendertimes.append(t3 - t2)
                framecounter += 1
                if framecounter == 100:
                    fpslist.append(clock.get_fps())
                    if args.debug:
                        for times in [updatetimes, rendertimes]:
                            print "times: %2d, %2d, %02d" % (
                                min(times), sum(times)/framecounter, max(times))
                        updatetimes = []
                        rendertimes = []
                    framecounter = 0
            if step:
                play = step = False

        clock.tick(FPS)
        if args.benchmark and pygame.time.get_ticks() > 5000:
            done = True

    if args.benchmark or args.debug:
        print sum(fpslist)/len(fpslist)
    pygame.quit()
    return True




if __name__ == "__main__":
    # Soon to be replaced by a proper argparse
    args = Args(fullscreen=FULLSCREEN, benchmark=BENCHMARK, debug=DEBUG)
    sys.exit(0 if main() else 1)
