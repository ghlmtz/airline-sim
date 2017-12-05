import pygame, sys
from pygame.locals import *

from enums import *
from fileio import *
from util import *

class DialogBox(pygame.sprite.Sprite):
	def __init__(self,width,height,x,y):
		pygame.sprite.Sprite.__init__(self)
		self.initFont()
		self.initImage(width,height,x,y)
		self.initGroup()

	def initFont(self):
		pygame.font.init()
		self.font = pygame.font.SysFont('arial',14)

	def initImage(self,width,height,x,y):
		self.image = pygame.Surface((width,height))
		self.image.fill((255,255,255))
		self.rect = self.image.get_rect()
		self.rect.topleft = (x,y)
		tmp = pygame.display.get_surface()
		tmp.blit(self.image,self.rect.topleft)

	def initGroup(self):
		self.group = pygame.sprite.GroupSingle()
		self.group.add(self)
		
	def setText(self,text):
		x_pos = 5
		y_pos = 5

		for t in text:
			x = self.font.render(t,False,(0,0,0))
			self.image.blit(x,(x_pos,y_pos))
			y_pos += 22

			if (x_pos > self.image.get_width()-5):
				x_pos = 5
				y_pos += 22

class TownDialog(DialogBox):
	def __init__(self,town):
		super().__init__(300,700,700,30)
		self.visible = 0
		self.town = town

	def setTown(self,town):
		if self.town != None:
			self.town.selected = 0
		town.selected = 1
		self.town = town
		self.visible = 1
		self.image.fill((255,255,255))
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
	
class Plane(pygame.sprite.Sprite):
	def __init__(self,lat,lon,dlat,dlon):
		pygame.sprite.Sprite.__init__(self)
		self.baseImage = pygame.image.load('tiles/plane.png').convert_alpha()
		self.image = self.baseImage
		self.rect = self.baseImage.get_rect()
		self.speed = 5	# In miles/frame, I guess
		self.dist = 0
		self.initGroup()
		self.lat = lat
		self.lon = lon
		self.dlat = dlat
		self.dlon = dlon

		self.display()

	def update(self):
		x = round((self.lon/(360)+0.5)*g.mapx*32)
		y = round(32*(-g.mapx*math.log(tan(self.lat)+1/cos(self.lat))/6+g.mapy/2))

		x0 = (x - disp_x*32)
		if x0 < -5000:
			x0 += 16384
		elif x0 > 5000:
			x0 -= 16384
		y0 = y - disp_y*32

		# Test blit
		a = disp_x + (x0//32)
		b = disp_y + (y0//32)
		a = wrap(a,g.mapx)
		i = (x0//32)
		j = (y0//32)

		redraw_tile9(a,b,(x0//32),(y0//32))

	def display(self):
		x = round((self.lon/(360)+0.5)*g.mapx*32)
		y = round(32*(-g.mapx*math.log(tan(self.lat)+1/cos(self.lat))/6+g.mapy/2))

		tmp = pygame.display.get_surface()
		x0 = (x - disp_x*32)
		if x0 < -5000:
			x0 += 16384
		elif x0 > 5000:
			x0 -= 16384
		y0 = y - disp_y*32

		i = (x0//32)
		j = (y0//32)

		oldCenter = self.rect.center
		bearing = self.course()
		self.image = pygame.transform.rotate(self.baseImage, -(bearing-90))
		self.rect = self.image.get_rect(center=self.rect.center)
		tmp.blit(self.image,(x0-self.rect.width/2,y0-self.rect.height/2))

		rect = pygame.Rect((i-1)*32,(j-1)*32,32*3,32*3)
		global changed_rects
		changed_rects.append(rect)

		# Find central angle and azimuth, use to plot new position
		azimuth = math.asin(sin(bearing)*cos(self.lat))
		sigma01 = math.atan2(tan(self.lat),cos(bearing)) 
		lon0 = self.lon - math.degrees(math.atan2(math.sin(azimuth)*math.sin(sigma01),math.cos(sigma01)))
		sigma = sigma01 + self.speed/3959
		self.lat = math.degrees(math.asin(math.cos(azimuth)*math.sin(sigma)))
		self.lon = math.degrees(math.atan2(math.sin(azimuth)*math.sin(sigma),math.cos(sigma)))+lon0
		self.dist += self.speed

	def dist_left(self):
		return lat_lon_dist(self.lat,self.lon,self.dlat,self.dlon)

	def course(self):
		return math.degrees(math.atan2(sin(self.dlon-self.lon),(cos(self.lat)*tan(self.dlat)-sin(self.lat)*cos(self.dlon-self.lon))))

	def initGroup(self):
		planes.add(self)

def redraw_tile9(x,y,i,j):
	for a in [-1,0,1]:
		for b in [-1,0,1]:
			drawTile(x+a,y+b,i+a,j+b)
			for town in visibletowns:
				if town.X == x+a and town.Y == y+b:
					drawTown(town)

def sphere_plot(lat,lon):
	for i in range(4):
		if cos(lat) * cos(lon+180-90*i) < 0:
			dotx = int(192/2 - 192/2 * cos(lat) * sin(lon+180-90*i))
			doty = int(192/2 - 192/2*sin(lat)) + i*192
			pygame.draw.circle(DISPLAYSURF, (255,0,0), (dotx, doty), 3)

def drawTown(town):
	x0,y0 = ((town.X-disp_x)*32,(town.Y-disp_y)*32)
	if x0 > 2000:
		x0 -= 16384
	if x0 < -2000:
		x0 += 16384
	radius = math.ceil(town.population / 250000) + 3
	if town.population > 1000000:
		radius = math.ceil(town.population / 1000000) + 7
	if radius > 12:
		radius = 12
	if town.isCapital:
		pygame.draw.circle(DISPLAYSURF, colors[town.country + 1], (x0+12, y0+12), radius)
		pygame.draw.circle(DISPLAYSURF, (0,0,0), (x0+12, y0+12), radius,2)
		DISPLAYSURF.blit(textures["CAPITAL"],(x0, y0))
	else:
		if town.population > 1000000:
			pygame.draw.circle(DISPLAYSURF, colors[town.country + 1], (x0+12, y0+12), radius)
			pygame.draw.circle(DISPLAYSURF, (0,0,0), (x0+12, y0+12), radius,2)
			DISPLAYSURF.blit(textures["CITY"],(x0, y0))
		else:
			pygame.draw.circle(DISPLAYSURF, colors[town.country + 1], (x0+16, y0+14), radius)
			pygame.draw.circle(DISPLAYSURF, (0,0,0), (x0+16, y0+14), radius,2)
			DISPLAYSURF.blit(textures["TOWN"],(x0+4, y0+8))
			
	if town.selected:
		pygame.draw.rect(DISPLAYSURF, (255,0,0), (x0,y0,32,32), 2)

def drawTile(x,y,i,j):
	x = wrap(x,g.mapx)
	y = wrap(y,g.mapy)
	tmp = pygame.display.get_surface()
	try:
		biome = g.tiles[x][y].biomeType
	except IndexError:
		print("ERROR!",x,y,disp_x,disp_y)
		exit()
	if biome == BiomeType.ICE:
		tmp.blit(textures[biome],(i*32,j*32))
	elif not g.tiles[x][y].isLand:
		tmp.blit(textures[g.tiles[x][y].heightType.name],(i*32,j*32))
	elif g.tiles[x][y].heightType in [HType.FOREST,HType.GRASS] and biome == BiomeType.RAINFOREST:
		tmp.blit(textures[BiomeType.WOODLAND],(i*32,j*32))
	elif g.tiles[x][y].heightType == HType.GRASS and biome == BiomeType.SAVANNA:
		tmp.blit(textures[BiomeType.GRASSLAND],(i*32,j*32))
	elif g.tiles[x][y].heightType == HType.HILLS:
		if biome in [BiomeType.SAVANNA, BiomeType.GRASSLAND, BiomeType.SEASONAL]:
			tmp.blit(textures["GRASSHILLS"],(i*32,j*32))
		elif biome in [BiomeType.WOODLAND,BiomeType.RAINFOREST]:
			tmp.blit(textures["WOODSHILLS"],(i*32,j*32))
		elif biome == BiomeType.DESERT:
			tmp.blit(textures["DESERTHILLS"],(i*32,j*32))
		elif biome == BiomeType.TUNDRA:
			tmp.blit(textures["TUNDRAHILLS"],(i*32,j*32))
		elif biome == BiomeType.BOREAL:
			tmp.blit(textures["BOREALHILLS"],(i*32,j*32))
		else:
			tmp.blit(textures["NONE"],(i*32,j*32))
	elif g.tiles[x][y].heightType == HType.MOUNTAIN:
		if biome in [BiomeType.SAVANNA, BiomeType.GRASSLAND, BiomeType.SEASONAL]:
			tmp.blit(textures["GRASSMOUNT"],(i*32,j*32))
		elif biome in [BiomeType.WOODLAND,BiomeType.RAINFOREST]:
			tmp.blit(textures["WOODSMOUNT"],(i*32,j*32))
		elif biome == BiomeType.DESERT:
			tmp.blit(textures["DESERTMOUNT"],(i*32,j*32))
		elif biome == BiomeType.TUNDRA:
			tmp.blit(textures["TUNDRAMOUNT"],(i*32,j*32))
		elif biome == BiomeType.BOREAL:
			tmp.blit(textures["BOREALMOUNT"],(i*32,j*32))
		else:
			tmp.blit(textures["NONE"],(i*32,j*32))
	elif biome in textures.keys():
		tmp.blit(textures[biome],(i*32,j*32))
	else:
		tmp.blit(textures["NONE"],(i*32,j*32))

def load_textures():
	global textures
	textures = {
		"DEEPWATER" : pygame.image.load('tiles/deepwater.png').convert(),
		"SHALLOW"   : pygame.image.load('tiles/shallow.png').convert(),
		"GRASSHILLS" : pygame.image.load('tiles/grasslandhills.png').convert(),
		"GRASSMOUNT" : pygame.image.load('tiles/grasslandmountain.png').convert(),
		"WOODSHILLS" : pygame.image.load('tiles/woodshills.png').convert(),
		"WOODSMOUNT" : pygame.image.load('tiles/woodsmountain.png').convert(),
		"DESERTHILLS" : pygame.image.load('tiles/deserthills.png').convert(),
		"TUNDRAHILLS" : pygame.image.load('tiles/tundrahills.png').convert(),
		"BOREALHILLS" : pygame.image.load('tiles/borealhills.png').convert(),
		"DESERTMOUNT" : pygame.image.load('tiles/desertmountain.png').convert(),
		"TUNDRAMOUNT" : pygame.image.load('tiles/tundramountain.png').convert(),
		"BOREALMOUNT" : pygame.image.load('tiles/borealmountain.png').convert(),
		BiomeType.DESERT    : pygame.image.load('tiles/desert.png').convert(),
		BiomeType.GRASSLAND : pygame.image.load('tiles/grassland.png').convert(),
		BiomeType.ICE       : pygame.image.load('tiles/ice.png').convert(),
		BiomeType.BOREAL    : pygame.image.load('tiles/boreal.png').convert(),
		BiomeType.SAVANNA   : pygame.image.load('tiles/woodland.png').convert(),
		BiomeType.TUNDRA    : pygame.image.load('tiles/tundra.png').convert(),
		BiomeType.WOODLAND  : pygame.image.load('tiles/woodland.png').convert(),
		BiomeType.TEMPERATE  : pygame.image.load('tiles/grassland.png').convert(),
		BiomeType.SEASONAL  : pygame.image.load('tiles/grassland.png').convert(),
		BiomeType.RAINFOREST : pygame.image.load('tiles/grassland.png').convert(),
		"CITY" : pygame.image.load('tiles/city.png').convert_alpha(),	
		"TOWN" : pygame.image.load('tiles/town.png').convert_alpha(),
		"CAPITAL" : pygame.image.load('tiles/capital.png').convert_alpha(),
		"NONE"      : pygame.image.load('tiles/notfound.png')
	}

def launch_game():
	global DISPLAYSURF
	global disp_x
	global disp_y
	global colors
	global planes
	global changed_rects
	global visibletowns
	pygame.init()
	DISPLAYSURF = pygame.display.set_mode((1024, 768), 0, 32)
	fpsClock = pygame.time.Clock()
	FPS = 60
	disp_x = 100
	disp_y = 200
	pygame.display.set_caption('Flyin\' High')

	planes = pygame.sprite.Group()

	load_textures()

	spheres = []

	for i in range(4):
		f_obj = get_tar_fileobj("mapsphere%d.png"%(i+1))
		spheres.append(pygame.image.load(f_obj,'a.png').convert_alpha())
		DISPLAYSURF.blit(spheres[i],(0,i*192))

	viewchange = 1
	buttondown = False
	towndialog = TownDialog(None)

	colors = [((N*73) % 192,(N*179)%192,(N*37)%192) for N in range(len(g.countries)+10)]
	colors[0] = (255,255,255)

	changed_rects = []
	tile_calc = 0
	tile_queue = [g.tiles[disp_x][disp_y]]

	timepunch("Setup done!\nEntering main gfx loop at: ")
	frame = 0
	while True: # main game loop
		changed_rects = []
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == MOUSEBUTTONDOWN and event.button == 1:
				buttondown = True
			elif event.type == MOUSEBUTTONDOWN and event.button == 2:
				x0,y0 = (disp_x+(event.pos[0]//32),disp_y+(event.pos[1]//32))
				x0 = wrap(x0,g.mapx)
				a,b = lat_long((x0,y0))
				for town in g.towns:
					if town.selected:
						planes.add(Plane(town.lat,town.lon,a,b))
						break
			elif event.type == MOUSEBUTTONUP and event.button == 1 and buttondown:
				buttondown = False
				if event.pos[0] < 192 and event.pos[1] < 192*4:
					sphere_click = event.pos[1]//192
					x0 = event.pos[0] - 192/2
					y0 = 192/2 - (event.pos[1] % 192)
					p = math.hypot(x0,y0)
					d = p*2/(192)
					if d <= 1:
						c = math.asin(d)
						if p == 0:
							lat = 0
							lon = 0
						else:
							lat = math.degrees(math.asin(y0*math.sin(c)/p))
							lon = -180 + 90*sphere_click + math.degrees(math.atan2(x0*math.sin(c),(p*math.cos(c))))
							lon = wrap(lon,360) - 180
						if abs(lat) < 84:
							x1,y1 = inv_lat_long((lat,lon))
							disp_x = wrap(x1-20,g.mapx)
							disp_y = y1 - 12
							viewchange = 1
				if not viewchange:
					if towndialog.visible and towndialog.rect.collidepoint(event.pos):
						for town in g.towns:
							town.selected = 0
						towndialog.visible = 0
						viewchange = 1
					else:
						x0,y0 = (disp_x+(event.pos[0]//32),disp_y+(event.pos[1]//32))
						x0 = wrap(x0,g.mapx)
						for town in visibletowns:
							if town.X == x0 and town.Y == y0:
								disp_x = x0 - 16
								disp_y = y0 - 12
								disp_x = wrap(disp_x,g.mapx)
								towndialog.setTown(town)
								planes.add(Plane(town.lat,town.lon,0,0))
								viewchange = 1
								break
						else:
							print(lat_long((x0,y0)),g.tiles[x0][y0].heightType, g.tiles[x0][y0].biomeType, g.tiles[x0][y0].isLand)

		keys_pressed = pygame.key.get_pressed()

		if keys_pressed[K_LEFT]:
			disp_x -= 1
			viewchange = 1
		if keys_pressed[K_RIGHT]:
			disp_x -= -1
			viewchange = 1
		if keys_pressed[K_UP] and disp_y > 96:
			disp_y -= 1
			viewchange = 1
		if keys_pressed[K_DOWN] and disp_y < (512-96):
			disp_y -= -1
			viewchange = 1

		if viewchange:
			for i in range(32):
				for j in range(24):
					x = disp_x + i
					y = disp_y + j
					disp_x = wrap(disp_x,g.mapx)
					drawTile(x,y,i,j)

			lat,lon = lat_long((wrap(disp_x+20,g.mapx),disp_y+12))
			visibletowns = []
			k = 0
			for town in g.towns:
				if lat_lon_dist(lat,lon,town.lat,town.lon) < 1000:
					k += 1
					drawTown(town)
					visibletowns.append(town)

		planes.update()
		for plane in planes.sprites():
			plane.display()
			if plane.dist_left() < plane.speed:
				print(plane.dist)
				plane.kill()
		if towndialog.visible:
			towndialog.group.draw(DISPLAYSURF)
			if not viewchange:
				changed_rects.append(towndialog.rect)
		for i in range(4):
			DISPLAYSURF.blit(spheres[i],(0,i*192))
		sphere_plot(lat,lon)
		for plane in planes.sprites():
			sphere_plot(plane.lat,plane.lon)
		if not viewchange:
			changed_rects.append(pygame.Rect(0,0,192,192*4))
		if viewchange:
			pygame.display.update()
		else:
			pygame.display.update(changed_rects)
		viewchange = 0
		fpsClock.tick(FPS)
