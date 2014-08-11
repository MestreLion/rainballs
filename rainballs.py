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
# - Fix integrator / floor bouncing when damping is zero and gravity is active
# - Mouseover/right click for ball properties
# - Mouseclick and drag to move balls
# - Avoid low-contrast colors against background
# - Instructions (SHIFT to show/dismiss)
# - Use mass in collision formula

import sys
import pygame
import math
from random import randint


# General options
BENCHMARK = False
FULLSCREEN = False
DEBUG = False
AUTOPLAY = True
TRACE = False
BALLS = 15


# Colors
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)


# Render stuff
SCREEN_SIZE = (1600, 900)     # Fullscreen ignores this and always use desktop resolution
FPS = 60  # 0 for unbounded
BG_COLOR = WHITE


# Physics stuff - Units in pixels/second
GRAVITY = (0, 0)   # A vector, like everything else
DAMPING = (1, 1)   # Velocity restitution coefficient of collisions on boundaries
FRICTION = 0       # Kinetic coefficient of friction
TIMESTEP = 1./FPS  # dt of physics simulation. Later to be FPS-independent

EPSILON_V = max(abs(GRAVITY[0]),
                abs(GRAVITY[1]))*TIMESTEP/2  # Velocity resolution threshold


# Balls maximum values
radius = 120
vel = [400, 400]
elast = 1


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
                 elasticity=1):
        super(Ball, self).__init__()

        # Basic properties
        self.color = color
        self.radius = radius
        self.position = list(position) or [0, 0]
        self.velocity = list(velocity) or [0, 0]
        self.density = density
        self.elasticity = elasticity

        # Derived properties
        self.area = math.pi * self.radius**2
        self.mass = self.area * self.density
        self.bounds = (screen.get_size()[0] - self.radius,
                       screen.get_size()[1] - self.radius)
        self.wallp = [0, 0]  # net momentum "absorbed" by the "infinite-mass" walls. What a dirty hack :P

        # Pygame sprite requirements
        self.image = pygame.Surface(2*[self.radius*2])
        self.rect = self.image.get_rect()
        self._update_rect()
        self.image.fill(BG_COLOR)
        self.image.set_colorkey(BG_COLOR)
        pygame.draw.circle(self.image, self.color, 2*(self.radius,), self.radius)

    @property
    def momentum(self):
        return (self.velocity[0] * self.mass,
                self.velocity[1] * self.mass)

    @property
    def knectic(self):
        """ Knectic energy: Ek = m|v|²/2 """
        return self.mass * (self.velocity[0]**2 +
                            self.velocity[1]**2) / 2.

    @property
    def potential(self):
        """ Potential (gravitational) energy: Eu = mh|g| """
        # Disregard horizontal gravity for now.
        # Accurate result would be m * sqrt((gx*hx)²+(gy*hy)²)
        return self.mass * abs(GRAVITY[1]) * (self.position[1] - self.radius)

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
            # Save the momentum that will be absorbed by the wall
            self.wallp[i] += self.mass * 2 * self.velocity[i]

            # Reflect velocity, dampered
            self.velocity[i] *= -1 * DAMPING[i]

            # set to zero when low enough
            if abs(self.velocity[i]) < EPSILON_V:
                self.velocity[i] = 0

        if self.velocity == [0, 0] and self.on_ground:
            return

        for i in [0, 1]:
            # Apply gravity to velocity
            if not (self.on_ground and self.velocity[i] == 0):
                self.velocity[i] += GRAVITY[i] * dt

            # Apply velocity to position, Implicit Euler method
            self.position[i] += self.velocity[i] * dt

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
        # Do nothing on self "collisions" or when center coincide
        if other is self or self.position == other.position:
            return

        # Calculate the distance vector and its magnitude squared
        ds = [other.position[0] - self.position[0],
              other.position[1] - self.position[1]]
        mag2 = ds[0]**2 + ds[1]**2

        # Check for false positives from rect collision detection
        # by testing if distance^2 >= (sum of radii)^2
        radsum = self.radius + other.radius
        if mag2 >= radsum**2:
            self.printdata("False Positive")
            return

        # Calculate the distance vector magnitude (= the distance between the balls)
        # Also calculate the overlap width (= distance - sum of radii)
        dvmag = math.sqrt(mag2)
        overlap = abs(dvmag - radsum)

        if args.debug:
            print "collide! %r %r at [%.2f, %.2f], %.2f overlap" % (
                self.color, other.color, self.position[0], self.position[0], overlap)

        def sum(v1, v2):
            return [v1[0]+v2[0], v1[1]+v2[1]]

        def sub(v1, v2):
            return [v1[0]-v2[0], v1[1]-v2[1]]

        def mult(v, n):
            return [v[0]*n, v[1]*n]

        def dot(v1, v2):
            return v1[0]*v2[0] + v1[1]*v2[1]

        # Some constants
        CR = min(self.elasticity, other.elasticity)
        invmass = 1. / (self.mass + other.mass)

        # Calculate the normal, the unit vector from centers to collision point
        # It always points in direction from self towards other
        normal = [ds[0]/dvmag, ds[1]/dvmag]

        # Rotate the normal 90º to find the tangent vector
        tangent = [-normal[1], normal[0]]

        # Project the velocities along the normal and tangent
        uan = mult(normal,  dot(self.velocity,  normal))
        uat = mult(tangent, dot(self.velocity,  tangent))
        ubn = mult(normal,  dot(other.velocity, normal))
        ubt = mult(tangent, dot(other.velocity, tangent))

        # Apply momentum conservation for inelastic collision along the normal components
        # See https://en.wikipedia.org/wiki/Coefficient_of_restitution#Equation
        dvn = sub(ubn, uan)
        pn = sum(mult(uan, self.mass), mult(ubn, other.mass))
        van = mult(sum(pn, mult(dvn, other.mass * CR)), invmass)
        vbn = mult(sub(pn, mult(dvn, self.mass  * CR)), invmass)

        # Update the velocities, adding normal and tangent components
        self.velocity  = sum(van, uat)
        other.velocity = sum(vbn, ubt)

        # Move circles away at normal direction
        # Each ball is displaced a fraction of offset inversely proportional to its mass
        self.position[0]  -= normal[0] * overlap * other.mass * invmass
        self.position[1]  -= normal[1] * overlap * other.mass * invmass
        other.position[0] += normal[0] * overlap * self.mass  * invmass
        other.position[1] += normal[1] * overlap * self.mass  * invmass

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
    global screen, background, balls, args, FPS

    # Soon to be replaced by a proper argparse
    args = Args(fullscreen="--fullscreen" in argv or FULLSCREEN,
                benchmark="--benchmark" in argv or BENCHMARK,
                debug="--debug" in argv or DEBUG)
    if args.benchmark:
        FPS = 0

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
    for _ in xrange(BALLS):
        balls.add(Ball(color=(randint(0,255), randint(0,255), randint(0,255)),
                       radius=randint(10, radius), elasticity=elast,
                       position=[randint(100, screen.get_size()[0]-radius),
                                 randint(100, screen.get_size()[1]-radius)],
                       velocity=[randint(-vel[0], vel[0]), randint(-vel[0], vel[1])],
                       ))

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
    frames = 0  # not absolute! Gets reset at intervals
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
            balllist = list(balls)
            for i, ball in enumerate(balllist[:-1]):
                for other in pygame.sprite.spritecollide(ball, balllist[i+1:], False):
                    ball.collide(other)

            # Draw
            t2 = pygame.time.get_ticks()
            render()
            t3 = pygame.time.get_ticks()
            frames += 1

            if args.benchmark:
                updatetimes.append(t2 - t1)
                rendertimes.append(t3 - t2)
                if frames % 15 == 0:
                    fpslist.append(clock.get_fps())
                if pygame.time.get_ticks() > 10000:
                    done = True

            if frames == (FPS or 100):
                frames = 0

                # Calculate kinetic energy and linear momentum
                # P must be always constant, also E if damping is 1
                P = [0, 0]
                E = 0
                for ball in balls:
                    P[0] += ball.momentum[0] + ball.wallp[0]
                    P[1] += ball.momentum[1] + ball.wallp[1]
                    E += ball.knectic + ball.potential

                if not args.fullscreen:
                    pygame.display.set_caption(
                        "%s - FPS: %.1f - Energy: %.1f, Momentum: [%.1f, %.1f]" % (
                        caption,clock.get_fps(), E, P[0], P[1]))

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
