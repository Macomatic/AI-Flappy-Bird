# Flappy Bird with Normal Gameplay and AI with NEAT algorithm

# Import all necessary libraries 
import pygame 
import neat
import time
import os
import random
pygame.font.init()

# Constants
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800
GEN = -1

# Loading bird images at x2 size and saving them in array
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("images","bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("images","bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("images","bird3.png")))] 
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images","pipe.png")))
GROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images","ground.png")))
BG_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("images","bg.png")))

# Fonts
ARIAL_FONT = pygame.font.SysFont('agencyfb', 40)


# Creating a new object for birds;
class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25 # Bird tilt when moving up and down
    ROTATION_VELOCITY = 20 # Rotation of bird
    ANIMATION_TIME = 5 # Bird flapping animation time

    def __init__(self,x,y):
        self.x = x # X pos of bird
        self.y = y # X pos of bird
        self.tilt = 0 # Image tilt value to be drawn on screen; 0  represents flat
        self.tick_count = 0 # Used for physics of bird
        self.velocity = 0 # Speed of bird
        self.height = self.y # Used in moving/tilting bird
        self.img_count = 0 # Tracks current image of bird flapping animation
        self.img = self.IMAGES[0]

    def jump(self): # Handles bird vertical movement
        self.velocity = -10.5 # Negative since top left corner of pygame is 0,0; negative means moving up
        self.tick_count = 0 # Resets tick count to 0
        self.height = self.y
    
    def move(self): # Handles bird horizontal movement
        self.tick_count += 1 # Keeps track of the number of times the bird moved; represents time
        displacement = self.velocity*self.tick_count + 1.5*self.tick_count**2 # Kinematics equation for displacement; displacement = vdt + 1/2(a)dt^2 with a custom acceleration
        
        if displacement >= 16: # Sets a terminal velocity
            displacement = 16

        if displacement < 0:
            displacement -= 2
        
        self.y += displacement # Updates bird pos based on displacement

        if displacement < 0 or self.y < self.height + 50: # Handles bird tilt
            if self.tilt < self.MAX_ROTATION: # Using max rot so when going up, it is not completely vertical which mimics projectile motion
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -90: # Creates nosedive effect when bird starts falling
                self.tilt -= self.ROTATION_VELOCITY

    def draw(self, window): # Draw function that would run in main game loop
        self.img_count += 1 # Tracking times a certain image of the bird is shown

        # Follow conditionals deal with bird animation
        if self.img_count < self.ANIMATION_TIME: # When the amount of times an image is drawn passes the animation time, it creates a new image
            self.img = self.IMAGES[0]
        elif self.img_count < self.ANIMATION_TIME*2: # Doubles the required time which means the second image
            self.img = self.IMAGES[1]
        elif self.img_count < self.ANIMATION_TIME*3: # Third image
            self.img = self.IMAGES[2]
        elif self.img_count < self.ANIMATION_TIME*4: # Second image
            self.img = self.IMAGES[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1: # First image
            self.img = self.IMAGES[0]
            self.img_count = 0 # Resets count to 0; resetting loop

        if self.tilt <= -80:
            self.img = self.IMAGES[1] # When nosediving, it doesn't make sense for flapping animation. This ensures that it's just a nosedive
            self.img_count = self.ANIMATION_TIME*2 # When jumping up, doesn't skip a frame but the most appropriate image

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rectangle = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x,self.y)).center)
        window.blit(rotated_image, new_rectangle.topleft)

    def get_mask(self): # Handles collision detection
        return pygame.mask.from_surface(self.img)


# Creating a new object for the pipes
class Pipe:
    PIPE_GAP = 200 # Gap between ceiling and ground pipe
    PIPE_VELOCITY = 5 # Bird doesn't move, pipes move; this is the pipe speed

    def __init__(self,x):
        self.x = x
        self.height = 0
        self.top = 0 # Top pipe height coord, random generated
        self.bottom = 0 # Bottom pipe height coord, random generates
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE,False,True) # Upside down pipe
        self.PIPE_BOTTOM = PIPE_IMAGE
        self.passed = False # Determines if the bird successfully passed through the pipe
        self.set_height()

    def set_height(self):
        self.height = random.randrange(40,450)
        self.top = self.height - self.PIPE_TOP.get_height() # Ensures that the gap fluctuates by drawing the long pipe image at a negative coord
        self.bottom = self.height + self.PIPE_GAP

    def move(self):
        self.x -= self.PIPE_VELOCITY # Moves the pipe left at a constant speed

    def draw(self, window): # Draws pipe
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, window): # Deals with bird-pipe collision
        bird_mask = bird.get_mask() # Gets bird mask

        topPipe_mask = pygame.mask.from_surface(self.PIPE_TOP) # Gets top pipe mask
        topPipe_offset = (self.x-bird.x, self.top-round(bird.y)) # Gets offset distance between bird and top pipe
        top_collision = bird_mask.overlap(topPipe_mask, topPipe_offset) # Determines if there is a pixel-perfect collision

        bottomPipe_mask = pygame.mask.from_surface(self.PIPE_BOTTOM) # Gets bottom pipe mask
        bottomPipe_offset = (self.x - bird.x, self.bottom - round(bird.y)) # Gets offset distance between bird and bottom pipe
        bottom_collision = bird_mask.overlap(bottomPipe_mask, bottomPipe_offset) # Determines if there is a pixel-perfect collision

        if bottom_collision or top_collision: # If the bird collides with either the top pipe or bottom pipe
            return True # Boolean returned for use in main loop
        return False

# Used for motion of the motionless ground image
class Ground: # Works by having 2 ground images moving left at the same speed, when one is completely off the screen, it moves to the right of the previous image therefore simulating movement
    VELOCITY = 5 # has to be the same as the pipe
    WIDTH = GROUND_IMAGE.get_width()
    IMAGE = GROUND_IMAGE

    def __init__(self,y):
        self.y = y
        self.x1 = 0 # Used for first image
        self.x2 = self.WIDTH # Used for second image, puts it right after first image

    def move(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0: # Checks if first image is off the screen
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0: # Checks if second image is off the screen
            self.x2 = self.x1 + self.WIDTH

    def draw(self,window):
        window.blit(self.IMAGE, (self.x1,self.y))
        window.blit(self.IMAGE, (self.x2,self.y))
        
        
def draw_window(window, birds, pipes, ground, score, gen, alive): # Draws background window and bird based on values
    window.blit(BG_IMAGE,(0,0))
    score_text = ARIAL_FONT.render("Score: " + str(score), 1, (255,255,255))
    window.blit(score_text, (WINDOW_WIDTH - score_text.get_width() - 10, 10))
    gen_text = ARIAL_FONT.render("Gen: " + str(gen), 1, (255,255,255))
    window.blit(gen_text, (10, 10))
    alive_text = ARIAL_FONT.render("Alive: " + str(alive), 1, (255,255,255))
    window.blit(alive_text, (10,60))

    for pipe in pipes:
        pipe.draw(window)

    ground.draw(window)

    for bird in birds:
        bird.draw(window)

    pygame.display.update()


def main(genomes, config): # Game loop
    global GEN
    GEN += 1
    birds = []
    nets = []
    ge = []

    for _, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome,config)
        nets.append(net)
        birds.append(Bird(230,350))
        genome.fitness = 0
        ge.append(genome)

    ground = Ground(730)
    pipes = [Pipe(700)]
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock() # Creating a clock to set framerate to be constant
    score = 0 # Tracks score i.e pipes passed
    gen = 0
    alive = True # Used for game loop 
    
    while alive and len(birds) > 0:
        clock.tick(30)
        for event in pygame.event.get(): # Checks for any input from user
            if event.type == pygame.QUIT:
                alive = False
                pygame.quit()
                quit()
        
        pipe_index = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_index = 1

        for bird in birds:
            ge[birds.index(bird)].fitness += 0.1 # Give some fitness for moving
            bird.move()
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom)))

            if output[0] > 0.5:
                bird.jump()

        ground.move()
        add_pipe = False
        removed_pipes = []
        for pipe in pipes:
            pipe.move()
            for bird in birds:
                if pipe.collide(bird, window):
                    ge[birds.index(bird)].fitness -= 1 # Discourages birds from hitting pipes and only favouriting making it far
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0: # If pipe is on screen, spawn another one
                removed_pipes.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            

        if add_pipe: # True when the bird passes a pipe
            score += 1
            for genome in ge:
                genome.fitness += 5

            pipes.append(Pipe(600))

        for pipe in removed_pipes: # Removes pipes that are passed
            pipes.remove(pipe)

        for bird in birds:
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(window, birds, pipes, ground, score, GEN, len(birds))

def run(config_path): # Used for NEAT algorithm
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())
    winner = population.run(main,20)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)