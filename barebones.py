#!/usr/bin/python

import pygame

position = [100, 200]
velocity = [7, 17]
radius = 50
color = (0, 255, 0)  # green


pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((800, 600))
background = pygame.Surface(screen.get_size())
screen.blit(background, (0,0))

ball = pygame.Surface(2*[radius*2])
pygame.draw.circle(ball, color, 2*(radius,), radius)
bounds = (screen.get_size()[0] - 2 * radius,
          screen.get_size()[1] - 2 * radius)
rect = ball.get_rect()
rect.x = position[0]
rect.y = position[1]

done = False
while not done:
    for event in pygame.event.get():
        if event.type in [pygame.QUIT, pygame.KEYDOWN]:
            done = True

    for i in [0, 1]:
        position[i] += velocity[i]
        if position[i] < 0 or position[i] > bounds[i]:
            velocity[i] *= -1

    screen.blit(background, rect)
    rect.x = position[0]
    rect.y = position[1]
    screen.blit(ball, rect)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
