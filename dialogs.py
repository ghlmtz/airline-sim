import pygame
import ginit as g

from util import *

# Scroll up and down in a list
class ScrollableBox(pygame.sprite.Sprite):
	def border(self):
		if self.focus:
			return (255,0,0)
		else:
			return (128,128,128)

	def __init__(self,width,height,maxHeight,x,y):
		pygame.sprite.Sprite.__init__(self)
		self.focus = 1
		self.initFont()
		self.initImage(width,height,x,y)
		self.initGroup()
		self.visible = 0
		self.width = width
		self.height = height
		self.maxHeight = maxHeight
		self.scrollSurf = pygame.Surface((width,maxHeight))
		self.scrollSurf.fill((255, 255, 255))
		pygame.draw.rect(self.image, self.border(), pygame.Rect(0,0,width,height), 3)
		self.y_off = 0

	# Blits scroll image with border
	def blitBorder(self):
		self.image.blit(self.scrollSurf, (0, self.y_off))
		pygame.draw.rect(self.image, self.border(), pygame.Rect(0,0,self.width,self.height), 3)

	def scroll(self,amount):
		# No need to scroll if not enough text
		if self.maxHeight > self.height:
			top = self.y_off
			bottom = self.y_off + self.height
			self.y_off += amount

			if self.y_off > 0:
				self.y_off = 0
			elif -self.y_off + self.height > self.maxHeight:
				self.y_off = -self.maxHeight + self.height

			self.blitBorder()

	def setText(self,text):
		x_pos = 5
		y_pos = 5
		self.y_off = 0

		for t in text:
			x = self.font.render(t,False,(0,0,0))
			self.scrollSurf.blit(x,(x_pos,y_pos))
			y_pos += 22

			if (x_pos > self.scrollSurf.get_width()-5):
				x_pos = 5
				y_pos += 22

		self.blitBorder()
		self.maxHeight = y_pos + 22

	def clear(self):
		self.scrollSurf.fill((255, 255, 255))

	def initFont(self):
		pygame.font.init()
		self.font = pygame.font.SysFont('arial',14)

	def initImage(self,width,height,x,y):
		self.image = pygame.Surface((width,height))
		self.image.fill((255,255,255))
		self.rect = self.image.get_rect()
		pygame.draw.rect(self.image, self.border(), self.rect, 3)
		self.rect.topleft = (x,y)
		tmp = pygame.display.get_surface()
		tmp.blit(self.image,self.rect.topleft)

	def initGroup(self):
		self.group = pygame.sprite.GroupSingle()
		self.group.add(self)

	# Define this for subclass if dynamic dialog
	def update(self):
		pass

	# Extend this if we want to do more stuff
	def hide(self):
		self.visible = 0
		self.focus = 0

class PlaneList(ScrollableBox):
	def __init__(self,planes):
		super().__init__(400,600,1200,200,30)
		self.planes = planes
		self.visible = 1

	def update(self):
		self.clear()
		txt = []
		for p in sorted(self.planes,key=lambda x: (x.routedist - x.dist)):
			m, s = divmod(p.flighttime, 60)
			h, m = divmod(m, 60)
			d = p.routedist - p.dist
			t = fmt_time(g.clock.time_minutes+(d/p.speed)//60)
			txt.append("T: %d:%02d:%02d. %.0f miles left. ETA %s" % (h,m,s,(p.routedist-p.dist),t))
		self.setText(txt)
		
class TownDialog(ScrollableBox):
	def __init__(self):
		super().__init__(300,300,1200,700,30)
		self.town = None

	def setTown(self,town):
		if self.town != None:
			self.town.selected = 0
		town.selected = 1
		self.town = town
		self.visible = 1
		self.focus = 1
		self.clear()
		txt = []
		if town.isCapital:
			label = "Capital"
		elif town.population > 1000000:
			label = "City"
		else:
			label = "Town"
		txt.append("%s (%.2f,%.2f) (%d)" % (label,town.lat,town.lon,town.land))
		txt.append("Population: {:,}".format(town.population) + " Country: %d" % town.country)
		other_towns = []
		for t in g.countries[town.country]:
			if t.X == town.X and t.Y == town.Y:
				continue
			if t.isCapital:
				label = "Capital"
			elif t.population > 1000000:
				label = "City"
			else:
				label = "Town"
			dist = town_dist(t,town)
			other_towns.append(("%s (%.2f,%.2f) (%d) %.1f mi" % (label,t.lat,t.lon,t.land,dist),dist))
		if len(other_towns):
			txt.append("Other towns in country: (%d)"%len(other_towns))
			[txt.append(t[0]) for t in sorted(other_towns, key=lambda x:x[1])]
		self.setText(txt)

	def hide(self):
		self.town.selected = 0
		self.town = None
		super().hide()

class CityList(ScrollableBox):
	def __init__(self):
		super().__init__(300,300,5000,700,430)
		to_fmt = []
		for N, stadt in enumerate(g.countries):
			tmp = [N,len(stadt)]
			pop = 0
			a = 0
			for t in stadt:
				pop += t.population
				if t.isCapital:
					a = 1
					tmp.append(t.lat)
					tmp.append(t.lon)
			if a:
				tmp.append(pop)
				to_fmt.append(tmp)
		txt = []
		for x in sorted(to_fmt, key=lambda x:x[4]):
			txt.append("Country %d" % x[0] + " Capital: (%.2f %.2f)" % (x[2],x[3])) 
			txt.append("Population: {:,}".format(x[4]) + " Cities: %d" % x[1])
		self.setText(txt)
		self.visible = 1