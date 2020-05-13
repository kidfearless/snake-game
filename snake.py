import math
import random
import pygame as pygame
import tkinter as tk
import threading
import time
from tkinter import messagebox
import copy

g_iSize = 512
g_iRows = 10
g_Window = None
g_Snake = None
g_Food = None
g_bShouldRun = True
g_iFrameCount = 0


# Vector2D object to track the position and direction of the snakes and cubes
class Vector2D(object):
#
	def __init__(self, x=0, y=0):
	#
		self.x = x
		self.y = y
	#

	def __str__(self):
	#
		return "[{}, {}]".format(self.x, self.y)
	#

	def __eq__(self, other):
	#
		return self.x == other.x and self.y == other.y
	#

	def __add__(self, right):
	#
		return Vector2D(self.x + right.x, self.y + right.y)
	#

	def __hash__(self):
	#
		return id(self)
	#

	def Clone(self):
	#
		return Vector2D(self.x, self.y)
	#
#

# Static class to represent the grid in which the players play on
class Grid():
#
	@staticmethod
	def Draw():
	#
		self = Vector2D()
		sizeBetween = g_iSize // g_iRows
		for _ in range(g_iRows):
		#
			self.x = self.x + sizeBetween
			self.y = self.y + sizeBetween
			white = (255, 255, 255)
			line = pygame.draw.line
			line(g_Window, white, (self.x, 0), (self.x, g_iSize))
			line(g_Window, white, (0, self.y,), (g_iSize, self.y,))
		#
	#
#

# Direction class for the movement of the head of the snake.
# The class contains static properties that should be viewed as const
class Direction(Vector2D):
#
	Left = {}
	Right = {}
	Up = {}
	Down = {}
	Stop = {}

	def __init__(self, x=0, y=0):
	#
		super().__init__(x, y)
	#

	def __add__(self, right):
	#
		dir = Direction(self.x + right.x, self.y + right.y)
		return dir
	#

	def __hash__(self):
	#
		return id(self)
	#

	def Clone(self):
	#
		return Direction(self.x, self.y)
	#
	
	# I don't really know how to do this better, maybe with some fancy vector math
	@staticmethod
	def Invert(direction):
	#
		if direction == Direction.Left:
		#
			return Direction.Right
		#
		if direction == Direction.Right:
		#
			return Direction.Left
		#
		if direction == Direction.Up:
		#
			return Direction.Down
		#
		if direction == Direction.Down:
		#
			return Direction.Up
		#
		return Direction.Stop
	#
#

# can't assign class properties to an instance of the class inside the class
Direction.Left = Direction(-1, 0)
Direction.Right = Direction(1, 0)
Direction.Up = Direction(0, -1)
Direction.Down = Direction(0, 1)
Direction.Stop = Direction(0, 0)

# Cube object for the cube, head, and body entities
class Cube(object):
#
	def __init__(self, isHead = False, direction = Direction.Right, position = Vector2D(), color = (255, 0, 0)):
	#
		self.Position = position
		self.Color = color
		# only the head uses the direction property
		self.Direction = direction
		self.Head = isHead
	#

	def Move(self):
	#
		self.Position = self.Position + self.Direction
	#

	def Draw(self):
	#
		global g_iRows, g_iSize, g_Window
		distance = g_iSize // g_iRows
		try:
		#
			rect = ( 
				(self.Position.x * distance) + 1, 
				(self.Position.y * distance) + 1, 
				distance - 2, 
				distance - 2
			)

			pygame.draw.rect(g_Window, self.Color, rect)

			if self.Head:
			#
				center = distance // 2
				radius = 3
				circleMiddle = ( 
					(self.Position.x * distance) + center - radius, 
					(self.Position.y * distance) + 8
				)
				circleMiddle2 = ( 
					(self.Position.x * distance) + distance - (radius * 2), 
					(self.Position.y * distance) + 8
				)
				pygame.draw.circle(g_Window, (0, 0, 0), circleMiddle, radius)
				pygame.draw.circle(g_Window, (0, 0, 0), circleMiddle2, radius)
			#
		except:
		#
			pass
		#
	#

	def Clone(self):
	#
		return Cube(self.Head, self.Direction.Clone(), self.Position.Clone(), self.Color)
	#
#

# Keyboard class to handle processing inputs from the player
class Keyboard(dict):
# 
	def __init__(self):
	#
		super().__init__(self)
		self[pygame.K_w] = 0
		self[pygame.K_a] = 0
		self[pygame.K_s] = 0
		self[pygame.K_d] = 0
	#

	# sum the x and y direction values to get an absolute direction.
	def GetDirection(self):
	#
		return Direction(self[pygame.K_d] - self[pygame.K_a], self[pygame.K_s] - self[pygame.K_w])
	#

	# called every frame to process key presses, caches the keys into a dictionary
	# so that we don't have to request them when we move the snake
	def GetKeys(self):
	#
		for event in pygame.event.get():
		#
			if event.type == pygame.QUIT:
			#
				global g_bShouldRun
				g_bShouldRun = False
				pygame.quit()
				return
			#
			
			if event.type == pygame.KEYDOWN:
			#
				key = event.key
				self[key] = 1
			#

			# if any key is released
			elif event.type == pygame.KEYUP:
			#
				key = event.key
				self[key] = 0
			#
		#
	#
#

# global singleton of the keyboard class
g_KeyBoard = Keyboard()

# Snake entity that the player controls
class Snake(object):
#
	def __init__(self, pos):
	#
		self.Head = Cube(True, position=pos)
		self.Body = []
		self.DidEat = False

		# Create three cubes 1 position off from the previous
		cube = self.Head.Clone()
		cube.Head = False
		cube.Move()
		self.Body.append(cube)

		cube = cube.Clone()
		cube.Move()
		self.Body.append(cube)

		cube = cube.Clone()
		cube.Move()
		self.Body.append(cube)

		# flip the heads direction so that we don't run into the body in the first tick
		self.Head.Direction = Direction.Left
	#

	def Move(self):
	#
		global g_KeyBoard, g_iRows, g_bShouldRun, g_Snake
		newDirection = g_KeyBoard.GetDirection()
		# continue the old direction if they player isn't pressing any keys or they try to suicide
		if newDirection != Direction.Stop and newDirection != Direction.Invert(self.Head.Direction):
		#
			self.Head.Direction = newDirection
		#
		# create a copy of the head and it's position
		oldHeadPosition = self.Head.Position.Clone()
		copyHead = copy.deepcopy(self.Head)
		# move the heads copy one frame
		copyHead.Move()
		# if that position is in a wall then they lose
		if(copyHead.Position.x < 0 or copyHead.Position.y < 0
		or copyHead.Position.x >= g_iRows or copyHead.Position.y >= g_iRows):
		#
			if Game.AskQuestion("YOU LOSE!", "Your final score was " + str(len(g_Snake.Body)) + "!\nPlay Again?"):
			#
				g_Snake = Snake(Vector2D(g_iRows//2, g_iRows//2))
			#
			else:
			#
				g_bShouldRun = False
			#
			return
		#
		# otherwise move the player normally
		else:
		#
			# move the head first
			self.Head.Move()

			# if we ate something then just insert a cube into the heads old position
			if self.DidEat:
			#
				cube = Cube(False, position = oldHeadPosition)
				self.Body.insert(0, cube)
				self.DidEat = False
			#
			# otherwise move all the cubes up one
			else:
			#
				# have to make a copy so that it doesn't cascade into a blob
				dup = copy.deepcopy(self.Body)
				for i in range(1, len(dup)):
				#
					self.Body[i].Position = dup[i-1].Position.Clone()
				#

				self.Body[0].Position = oldHeadPosition
			#
		#
	#

	def Eat(self):
	#
		global g_Food
		if self.Head.Position == g_Food.Position:
		#
			self.DidEat = True
			g_Food = Food()
		#
	#

	def Draw(self):
	#
		self.Head.Draw()
		for body in self.Body:
		#
			body.Draw()
		#
	#
#

# food class that inherits from cube.
class Food(Cube):
#
	def __init__(self):
	#
		super().__init__(color=((0, 255, 0)))
		global g_iRows, g_Snake

		position = Vector2D(random.randrange(g_iRows), random.randrange(g_iRows))

		positionExistsInSnake = True

		while positionExistsInSnake:
		#
			positionExistsInSnake = False
			if position == g_Snake.Head.Position:
			#
				positionExistsInSnake = True
			#
			else:
			#
				for cube in g_Snake.Body:
				#
					if cube.Position == position:
					#
						position = Vector2D(random.randrange(g_iRows), random.randrange(g_iRows))
						positionExistsInSnake = True
						break
					#
				#
			#
		#
		self.Position = position
	#
#

# static class for certain game related functions
class Game():
#
	@staticmethod
	def Draw():
	#
		global g_Window, g_Snake, g_Food
		g_Window.fill((0, 0, 0))
		g_Snake.Draw()
		g_Food.Draw()
		Grid.Draw()
		pygame.display.update()
	#

	@staticmethod
	def Display(subject, content):
	#
		root = tk.Tk()
		root.attributes("-topmost", True)
		root.withdraw()
		messagebox.showinfo(subject, content)

		try:
		#
			root.destroy()
		#
		except:
		#
			pass
		#
	#

	@staticmethod
	def AskQuestion(subject, content):
	#
		root = tk.Tk()
		root.attributes("-topmost", True)
		root.withdraw()
		ans = messagebox.askquestion(subject, content)
		
		try:
		#
			root.destroy()
		#
		except:
		#
			pass
		#
		finally:
		#
			return ans == 'yes'
		#
	#
#

# Entry point of the program
def Main():
#
	global g_Window, g_Snake, g_Food, g_iFrameCount, g_bShouldRun  

	g_Window = pygame.display.set_mode((g_iSize, g_iSize), display=2)
	g_Snake = Snake(Vector2D(g_iRows//2, g_iRows//2))
	g_Food = Food()

	clock = pygame.time.Clock()

	try:
	#
		while g_bShouldRun:
		#
			clock.tick()
			Game.Draw()
			g_KeyBoard.GetKeys()
			print(g_KeyBoard.GetDirection())
			g_Snake.Move()
			g_Snake.Eat()
			snekInSnake = False
			for cube in g_Snake.Body:
			#
				if g_Snake.Head.Position == cube.Position:
				#
					snekInSnake = True
					g_bShouldRun = False
					break
				#
			#
			if snekInSnake:
			#
				if Game.AskQuestion("YOU LOSE!", "Your final score was " + str(len(g_Snake.Body)) + "!\nPlay Again?"):
				#
					g_Snake = Snake(Vector2D(g_iRows//2, g_iRows//2))
					g_bShouldRun = True
				# 
			#
			pygame.time.delay(200)
			g_iFrameCount = g_iFrameCount + 1
		#
	#
	except:
	#
		if Game.AskQuestion("YOU WIN!", "Your final score was " + str(len(g_Snake.Body)) + "!\nPlay Again?") == False:
		#
			g_bShouldRun = False
		# 
	#
#

Main()
