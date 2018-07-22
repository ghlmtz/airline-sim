import pygame, sys
from pygame.locals import *

from enums import *
from fileio import *
from util import *
from dialogs import *

class Plane(pygame.sprite.Sprite):
	def __init__(self,src,dest):
		pygame.sprite.Sprite.__init__(self)
		self.baseImage = pygame.image.load('tiles/plane.png').convert_alpha()
		self.image = self.baseImage
		self.rect = self.baseImage.get_rect()
		self.speed = 0.2	# In miles/frame, I guess
		self.dist = 0
		self.lat = src.lat
		self.lon = src.lon
		self.src = src
		self.flighttime = 0
		self.dlat = dest.lat
		self.dlon = dest.lon
		self.dest = dest
		self.visible = 0
		self.routedist = lat_lon_dist(self.lat,self.lon,self.dlat,self.dlon)
		bearing = self.course()
		self.azimuth = math.asin(sin(bearing)*cos(self.lat))
		self.azcos = math.cos(self.azimuth)
		self.azsin = math.sin(self.azimuth)
		self.sigma01 = math.atan2(tan(self.lat),cos(bearing)) 
		self.lon0 = self.lon - math.degrees(math.atan2(math.sin(self.azimuth)*math.sin(self.sigma01),math.cos(self.sigma01)))

	def update_coords(self):
		self.x0 = round((self.lon/(360)+0.5)*g.mapx*32) - disp_x * 32
		self.y0 = round(32*(-g.mapx*math.log(tan(self.lat)+1/cos(self.lat))/6+g.mapy/2)) - disp_y * 32
		if self.x0 < -5000:
			self.x0 += 16384
		elif self.x0 > 5000:
			self.x0 -= 16384
		self.i = self.x0//32
		self.j = self.y0//32

	def update(self,bound,redraw_list):
		self.flighttime += 1

		if lat_long_bound(self.lat,self.lon,bound):
			self.update_coords()

			a = disp_x + self.i
			b = disp_y + self.j
			a = wrap(a,g.mapx)

			for u in [-1,0,1]:
				for v in [-1,0,1]:
					chk_tile = [a+u,b+v,self.i+u,self.j+v]
					if chk_tile not in redraw_list:
						redraw_list.append(chk_tile)

			self.visible = 1
		else:
			self.visible = 0

		# Plot new position
		sigma = self.sigma01 + self.flighttime * self.speed/3959
		self.lat = math.degrees(math.asin(self.azcos*math.sin(sigma)))
		self.lon = math.degrees(math.atan2(self.azsin*math.sin(sigma),math.cos(sigma)))+self.lon0
		self.dist += self.speed

	def display(self,changed_rects):
		tmp = pygame.display.get_surface()
		self.update_coords()

		oldCenter = self.rect.center

		self.image = pygame.transform.rotate(self.baseImage, -(self.course()-90))
		self.rect = self.image.get_rect(center=self.rect.center)
		tmp.blit(self.image,(self.x0-self.rect.width/2,self.y0-self.rect.height/2))

		self.drawn_rect = pygame.Rect((self.i-1)*32,(self.j-1)*32,32*3,32*3)
		changed_rects.append(self.drawn_rect)

	def dist_left(self):
		return lat_lon_dist(self.lat,self.lon,self.dlat,self.dlon)

	def course(self):
		return math.degrees(math.atan2(sin(self.dlon-self.lon),(cos(self.lat)*tan(self.dlat)-sin(self.lat)*cos(self.dlon-self.lon))))

def redraw_tile(params):
	x,y,i,j = params
	drawTile(x,y,i,j)

def sphere_plot(lat,lon):
	for i in range(4):
		if cos(lat) * cos(lon+180-90*i) < 0:
			dotx = int(192/2 - 192/2 * cos(lat) * sin(lon+180-90*i))
			doty = int(192/2 - 192/2*sin(lat)) + i*192
			pygame.draw.circle(DOTSURF, (255,0,0), (dotx, doty), 3)

def drawTown(t):
	x0,y0 = ((t.X-disp_x)*32,(t.Y-disp_y)*32)
	if x0 > 2000:
		x0 -= 16384
	if x0 < -2000:
		x0 += 16384
	DISPLAYSURF = pygame.display.get_surface()
	radius = math.ceil(t.population / 250000) + 3
	if t.population > 1000000:
		radius = math.ceil(t.population / 1000000) + 7
	if radius > 12:
		radius = 12
	if t.isCapital:
		pygame.draw.circle(DISPLAYSURF, colors[t.country + 1], (x0+12, y0+12), radius)
		pygame.draw.circle(DISPLAYSURF, (0,0,0), (x0+12, y0+12), radius,2)
		DISPLAYSURF.blit(textures["CAPITAL"],(x0, y0))
	else:
		if t.population > 1000000:
			pygame.draw.circle(DISPLAYSURF, colors[t.country + 1], (x0+12, y0+12), radius)
			pygame.draw.circle(DISPLAYSURF, (0,0,0), (x0+12, y0+12), radius,2)
			DISPLAYSURF.blit(textures["CITY"],(x0, y0))
		else:
			pygame.draw.circle(DISPLAYSURF, colors[t.country + 1], (x0+16, y0+14), radius)
			pygame.draw.circle(DISPLAYSURF, (0,0,0), (x0+16, y0+14), radius,2)
			DISPLAYSURF.blit(textures["TOWN"],(x0+4, y0+8))
			
	if t.selected:
		pygame.draw.rect(DISPLAYSURF, (255,0,0), (x0,y0,32,32), 2)

def drawTile(x,y,i,j):
	x = wrap(x,g.mapx)
	y = wrap(y,g.mapy)
	tmp = pygame.display.get_surface()
	biome = g.tiles[x][y].biomeType
	if biome == BiomeType.ICE:
		tmp.blit(textures[biome],(i*32,j*32))
	elif stadt_mode:
		cell = pygame.Surface((32,32))
		if not g.tiles[x][y].isLand:
			cell.fill((14,76,105))
		else:
			try:
				cell.fill(colors[g.tiles[x][y].country+1])
			except TypeError:
				print(x,y,g.tiles[x][y])
		tmp.blit(cell,(i*32,j*32))
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

	if g.tiles[x][y].town is not None:
		drawTown(g.tiles[x][y].town)

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

def clear_focus(dialogs):
	for d in dialogs:
		d.focus = 0

def launch_game():
	global DOTSURF
	global PLANESURF
	global disp_x
	global disp_y
	global colors
	global visibletowns
	global stadt_mode
	global time_minutes
	pygame.init()
	DISPLAYSURF = pygame.display.set_mode((1024, 768), 0, 32)
	SPHERESURF = pygame.Surface((192, 768), 0, 32)
	DOTSURF = pygame.Surface((192, 768), 0, 32)
	SPHERESURF.set_colorkey((255,0,255))
	DOTSURF.set_colorkey((255,0,255))
	SPHERESURF.fill((255,0,255))
	DOTSURF.fill((255,0,255))
	fpsClock = pygame.time.Clock()
	FPS = 60
	disp_x = 100
	disp_y = 200
	
	ll_bound = [lat_long((wrap(disp_x-1,g.mapx),disp_y-1)),lat_long((wrap(disp_x+33,g.mapx),disp_y+25))]

	pygame.display.set_caption('Flyin\' High')

	planes = pygame.sprite.Group()

	stadt_mode = 0

	load_textures()

	spheres = []

	for i in range(4):
		f_obj = get_tar_fileobj("mapsphere%d.png"%(i+1))
		spheres.append(pygame.image.load(f_obj,'a.png').convert_alpha())
		SPHERESURF.blit(spheres[i],(0,i*192))

	viewchange = 1
	buttondown = False
	towndialog = TownDialog()
	cdialog = CityList()
	pdialog = PlaneList(planes)

	colors = [((N*73) % 192,(N*179)%192,(N*37)%192) for N in range(len(g.countries)+10)]
	colors[0] = (0,0,0)

	changed_rects = []

	# Set up refresh event
	pygame.time.set_timer(USEREVENT + 1, 1000)

	dialogs = [towndialog, cdialog, pdialog]
	activedialog = None

	timepunch("Setup done!\nEntering main gfx loop at: ")
	frame = 0
	while True: # main game loop
		changed_rects.clear()
		for event in pygame.event.get():
			if event.type == QUIT:
				pygame.quit()
				sys.exit()
			elif event.type == USEREVENT:
				g.clock.inc(1)
				print(g.clock.fmt_time())
			elif event.type == USEREVENT + 1:
				# Refresh dynamic windows, if any
				for d in dialogs:
					if d.visible:
						d.update()
			elif event.type == KEYDOWN:
				if event.key == K_c:
					stadt_mode = 1 - stadt_mode
					viewchange = 1
				elif event.key == K_n:
					if cdialog.visible:
						cdialog.hide()
					else:
						clear_focus(dialogs)
						cdialog.visible = 1
						cdialog.focus = 1
						activedialog = cdialog
					viewchange = 1
				elif event.key == K_p:
					if pdialog.visible:
						pdialog.hide()
					else:
						clear_focus(dialogs)
						pdialog.visible = 1
						pdialog.focus = 1
						activedialog = pdialog
					viewchange = 1
			elif event.type == MOUSEBUTTONDOWN:
				if event.button == 4: # Mouse wheel up
					if activedialog:
						activedialog.scroll(20)
						changed_rects.append(activedialog.rect)
				elif event.button == 5: # Mouse wheel down
					if activedialog:
						activedialog.scroll(-20)
						changed_rects.append(activedialog.rect)
				elif event.button == 1: # Left button, store click
					buttondown = True
				elif event.button == 2: # Middle button
					pass
			elif event.type == MOUSEBUTTONUP and event.button == 1 and buttondown:
				# We clicked on something
				buttondown = False
				if event.pos[0] < 192 and event.pos[1] < 192*4:
					# Clicked on a sphere. Move to associated location
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
					# Clicked on dialog box?
					for d in dialogs:
						if d.visible and d.rect.collidepoint(event.pos):
							d.hide()
							print("hiding",type(d),d.visible)
							viewchange = 1
							break
					else:
						# Clicked on plane?
						for p in planes:
							if p.visible:
								# Check if click is within 12 px (half the img size)
								if abs(event.pos[0] - p.x0) + abs(event.pos[1] - p.y0) <= 12:
									m, s = divmod(p.flighttime, 60)
									h, m = divmod(m, 60)
									d = p.routedist - p.dist
									t = fmt_time(g.clock.time_minutes+(d/p.speed)//60)
									print("T: %d:%02d:%02d. %.0f miles left. ETA %s" % (h,m,s,(p.routedist-p.dist),t))
									break
						else:
							# Clicked on town?
							x0,y0 = (disp_x+(event.pos[0]//32),disp_y+(event.pos[1]//32))
							x0 = wrap(x0,g.mapx)
							if g.tiles[x0][y0].town is not None:
								town = g.tiles[x0][y0].town
								if town.X == x0 and town.Y == y0:
									# For now, spawn a plane from the town and open dialog
									disp_x = x0 - 16
									disp_y = y0 - 12
									disp_x = wrap(disp_x,g.mapx)
									clear_focus(dialogs)
									towndialog.setTown(town)
									activedialog = towndialog
									planes.add(Plane(town,g.towns[0]))
									viewchange = 1
									break
							else:
								# Clicked on normal tile: print debug info for now
								print(lat_long((x0,y0)),g.tiles[x0][y0].heightType, g.tiles[x0][y0].biomeType, g.tiles[x0][y0].country)

		keys_pressed = pygame.key.get_pressed()

		if keys_pressed[K_LEFT]:
			disp_x -= 1
			disp_x = wrap(disp_x,g.mapx)
			viewchange = 1
		if keys_pressed[K_RIGHT]:
			disp_x -= -1
			disp_x = wrap(disp_x,g.mapx)
			viewchange = 1
		if keys_pressed[K_UP] and disp_y > 96:
			disp_y -= 1
			viewchange = 1
		if keys_pressed[K_DOWN] and disp_y < (512-96):
			disp_y -= -1
			viewchange = 1

		if viewchange:
			# Draw the whole screen again
			# Change this in the future???
			for i in range(32):
				for j in range(24):
					x = disp_x + i
					y = disp_y + j

					drawTile(x,y,i,j)

			# Update lat lon bounding box
			ll_bound = [lat_long((wrap(disp_x-1,g.mapx),disp_y-1)),lat_long((wrap(disp_x+33,g.mapx),disp_y+25))]

		redraw_list = []
		planes.update(ll_bound,redraw_list)

		for tile in redraw_list:
			redraw_tile(tile)

		for plane in planes.sprites():
			if plane.visible:
				plane.display(changed_rects)
				if plane.dist_left() < plane.speed:
					changed_rects.append(plane.rect)
					plane.kill()

		for d in dialogs:
			if d.visible:
				d.group.draw(DISPLAYSURF)
				if not viewchange:
					changed_rects.append(d.rect)

		# Plot on spheres
		DISPLAYSURF.blit(SPHERESURF,(0,0))

		if viewchange or frame % 60 == 0:
			DOTSURF.fill((255,0,255))
			lat,lon = lat_long((wrap(disp_x+20,g.mapx),disp_y+12))
			sphere_plot(lat,lon)
			for plane in planes.sprites():
				sphere_plot(plane.lat,plane.lon)

		DISPLAYSURF.blit(DOTSURF,(0,0))
		if not(viewchange) or frame % 60 == 0:
			changed_rects.append(pygame.Rect(0,0,192,192*4))
		if viewchange:
			pygame.display.update()
		else:
			pygame.display.update(changed_rects)

		viewchange = 0
		frame += 1
		if frame > 3600:
			frame -= 3600
		fpsClock.tick(FPS)
		if frame % 60 == 0:
			# Advance in-game clock by 1 minute every 60 frames (temporary)
			pygame.event.post(pygame.event.Event(USEREVENT))
		# Randomly spawn in planes every 10 seconds or so (temporary)
		import random
		if frame % random.randint(1,200) == 0:
			town1, town2 = random.sample(g.towns, 2)
			while town_dist(town1,town2) > 7000:
				town1, town2 = random.sample(g.towns, 2)
			planes.add(Plane(town1,town2))
		#if frame % 120 == 0:
		#	print(fpsClock.get_fps(),len(planes))
