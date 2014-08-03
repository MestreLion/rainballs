#!/usr/bin/python

import pygame

position = [100, 200]
velocity = [7, 17]
radius = 50
color = (0, 255, 0)  # green


class Ball(pygame.sprite.Sprite):
    def __init__(self, position=[], velocity=[], radius=10, color=(255, 255, 255)):
        super(Ball, self).__init__()

        self.position = position[:] or [0, 0]
        self.velocity = velocity[:] or [0, 0]
        self.bounds = (screen.get_size()[0] - 2 * radius,
                       screen.get_size()[1] - 2 * radius)

        self.image = pygame.Surface(2*[radius*2])
        self.rect = self.image.get_rect()
        self.rect.x = int(self.position[0])
        self.rect.y = int(self.position[1])
        pygame.draw.circle(self.image, color, 2*(radius,), radius)

    def update(self):
        super(Ball, self).update()

        for i in [0, 1]:
            self.position[i] += self.velocity[i]

            if self.position[i] < 0 or self.position[i] > self.bounds[i]:
                self.velocity[i] *= -1

        self.rect.x = int(self.position[0])
        self.rect.y = int(self.position[1])


pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((800, 600))
background = pygame.Surface(screen.get_size())
screen.blit(background, (0,0))

ball = Ball(position, velocity, radius, color)
balls = pygame.sprite.Group(ball)


done = False
while not done:
    for event in pygame.event.get():
        if event.type in [pygame.QUIT, pygame.KEYDOWN]:
            done = True

    balls.update()
    balls.clear(screen, background)
    balls.draw(screen)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
