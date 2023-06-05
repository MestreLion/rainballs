import pygame
import math
import euclid

RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)

SCREEN_SIZE = (600, 600)
FPS = 60
BG_COLOR = BLUE


class Ball(pygame.sprite.Sprite):
    def __init__(self, color=WHITE, radius=10, position=[], velocity=[]):
        super(Ball, self).__init__()

        self.color = color
        self.radius = radius
        self.position = list(position) or [0, 0]
        self.velocity = list(velocity) or [0, 0]
        self.bounds = (screen.get_size()[0] - self.radius,
                       screen.get_size()[1] - self.radius)

        self.image = pygame.Surface(2*[self.radius*2])
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()

        pygame.draw.circle(self.image, self.color, 2*(self.radius,), self.radius)

    def update(self, dt=1./FPS):
        super(Ball, self).update()

        for i in [0, 1]:
            self.position[i] += self.velocity[i] * dt

            if self.position[i] < self.radius:
                self.position[i] = self.radius
                self.velocity[i] *= -1

            elif self.position[i] > self.bounds[i]:
                self.position[i] = self.bounds[i]
                self.velocity[i] *= -1

        self.rect.center = self.position

    def collide_circle(self, circle):
        if circle is self:
            return True
        d2 = 0
        for i in [0, 1]:
            d2 += (self.rect.center[i] - circle.rect.center[i])**2
        if d2 < (self.radius + getattr(circle, "radius",
                                        math.sqrt(circle.rect.width**2 +
                                                  circle.rect.height**2)))**2:
            return True
        return False

    def collide(self, other):
        # Do nothing for self "collisions"
        if other is self:
            return

        # Calculate the subtraction vector and its magnitude squared
        dv = [other.position[0] - self.position[0],
              other.position[1] - self.position[1]]
        mag2 = dv[0]**2 + dv[1]**2

        # Check for false positives from rect collision detection
        # by testing if distance^2 < (sum of radii)^2
        if mag2 >= (self.radius + other.radius)**2:
            print "false positive"
            return

        # Calculate vector magnitude, which is also the distance between the balls
        # and the overlap width (= distance - sum of radii)
        radsum = self.radius + other.radius
        dvmag = math.sqrt(mag2)
        overlap = abs(dvmag - radsum)

        print "collide! %r %r at [%.2f, %.2f], %.2f overlap" % (
            self.color, other.color, self.position[0], self.position[0], overlap)

        # Calculate the normal, the unit vector from centers to collision point
        # It always points in direction from self towards other
        normal = [dv[0]/dvmag, dv[1]/dvmag]

        # Use normal to calculate new position and velocity
        for circle in [self, other]:
            # Move circles away from each other by overlap amount at normal direction
            circle.position[0] -= overlap/2 * normal[0]
            circle.position[1] -= overlap/2 * normal[1]
            circle.rect.center = circle.position

            # Adjust the velocities by rotating current velocity to the normal's direction
            # (ie, multiply normal by current velocity magnitude)
            mag = math.sqrt(circle.velocity[0]**2 + circle.velocity[1]**2)
            circle.velocity[0] = mag * -normal[0]
            circle.velocity[1] = mag * -normal[1]

            # rinse and repeat for other, using a reflected normal
            normal[0] *= -1
            normal[1] *= -1




pygame.init()

screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()

background = pygame.Surface(screen.get_size())
background.fill(BG_COLOR)
screen.blit(background, (0,0))

vel = 100
radius = 100
balls = pygame.sprite.Group()
balls.add(Ball(color=RED,   radius=radius, position=[100, 300], velocity=[ vel, 0]))
balls.add(Ball(color=GREEN, radius=radius, position=[500, 150], velocity=[-vel, 0]))

done = False
play = False
step = False
while not done:
    for event in pygame.event.get():
        if (event.type == pygame.QUIT or
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                play = not play
            if event.key == pygame.K_SPACE:
                if play:
                    play = False
                else:
                    play = step = True

    if not play:
        clock.tick(FPS)
        continue

    balls.update()
    for ball in balls:
        for other in pygame.sprite.spritecollide(ball, balls, False):
            if other is not ball:
                ball.collide(other)
        break

    if step:
        play = step = False

    balls.clear(screen, background)
    balls.draw(screen)
    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
