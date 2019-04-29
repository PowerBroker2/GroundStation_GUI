import pygame
from time import sleep


pygame.init()

# Loop until the user clicks the close button.
done = False

# Initialize the joysticks
pygame.joystick.init()
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    # Get count of joysticks
    joystick_count = pygame.joystick.get_count()
    # For each joystick:
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()

        # Get the name from the OS for the controller/joystick
        name = joystick.get_name()
        if name == "T.16000M":
            axes = joystick.get_numaxes()
            print("Number of axes: {}".format(axes))

            for i in range(axes):
                axis = joystick.get_axis(i)
                print("Axis {} value: {:>6.3f}".format(i, axis))

            buttons = joystick.get_numbuttons()

            for i in range(buttons):
                button = joystick.get_button(i)
                print("Button {:>2} value: {}".format(i, button))

    sleep(1)

pygame.quit()