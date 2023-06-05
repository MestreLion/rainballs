import pygame, sys, random

pygame.init()

## Functions and classes

## Variables

clock = pygame.time.Clock()
SCREEN = pygame.display.set_mode(pygame.display.list_modes()[-1])

radius = 50

# create the surface that will contain the circle image.
# circle will be drawn on its center, so surface width and height is 2*radius
circle = pygame.Surface((2*radius, 2*radius))

# Let's also paint the surface GREEN so you see its corners behind the circle
circle.fill((0, 255, 0))

# draw the circle on the surface instead of screen
pygame.draw.circle(circle, (255, 255, 255), (radius, radius), radius)

# Last but not the least, create a companion rect, based on surface's size
# A rect is just a tool to define width, height and position at the same time
rect = circle.get_rect()

# rect now has same width and height as the surface, but it's positioned at (0, 0)
# So let's move it to desired initial position

rect.x = 0  # instead of SCRENRECT.centerx, so it stays longer on screen
rect.y = SCREEN.get_rect().centery

# The surface (and our friend the rect) is set up and ready to be used on screen


## Main loop

running = True

while running:
    #Quit event etc
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            running= False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
                running= False

    rect.x += 1

#    SCREEN.fill((0, 0, 0))

    # and now we blit the pre-drawn circle onto the screen, using rect as coordinates
    SCREEN.blit(circle, rect)

    pygame.display.update()
    clock.tick(60)
