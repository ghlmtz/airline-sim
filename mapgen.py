import random
import math
import noise

import json
from multiprocessing import Pool

from enums import *
from util import *
from fileio import *
import ginit as g

from time import process_time

class TileGroup:
	def __init__(self):
		self.tiles = []
		self.towns = []
		self.area = 0

class Tile:
	def __init__(self):
		self.floodFilled = False
		self.country = None

	def updateBitmask(self):
		self.count = 0

		if self.Top.heightType == self.heightType:
			self.count += 1
		if self.Right.heightType == self.heightType:
			self.count += 2
		if self.Bottom.heightType == self.heightType:
			self.count += 4
		if self.Left.heightType == self.heightType:
			self.count += 8

class MapData:
	def __init__(self,width,height):
		self.data = [ [ 0 for y in range(g.mapy) ] for x in range(g.mapx)]
		self.maxValue = -1000
		self.minValue = 1000

def getBiomeType(t):
	biomeTable = [[BiomeType.ICE, BiomeType.TUNDRA, BiomeType.BOREAL, BiomeType.TEMPERATE, BiomeType.RAINFOREST, BiomeType.RAINFOREST],
			  [BiomeType.ICE, BiomeType.TUNDRA, BiomeType.BOREAL, BiomeType.SEASONAL, BiomeType.RAINFOREST, BiomeType.RAINFOREST],
			  [BiomeType.ICE, BiomeType.TUNDRA, BiomeType.BOREAL, BiomeType.WOODLAND, BiomeType.SAVANNA, BiomeType.SAVANNA],
			  [BiomeType.ICE, BiomeType.TUNDRA, BiomeType.WOODLAND, BiomeType.WOODLAND, BiomeType.SAVANNA, BiomeType.SAVANNA],
			  [BiomeType.ICE, BiomeType.TUNDRA, BiomeType.GRASSLAND, BiomeType.DESERT, BiomeType.DESERT, BiomeType.DESERT],
			  [BiomeType.ICE, BiomeType.TUNDRA, BiomeType.GRASSLAND, BiomeType.DESERT, BiomeType.DESERT, BiomeType.DESERT]]
	return biomeTable[t.moistureType.value-1][t.heatType.value-1]

def setHeightType(t):
	value = t.heightValue
	if value < 0.9*g.sea_level:
		t.heightType = HType.DEEPWATER
		ival = (0,0,128)
	elif 0.9*g.sea_level <= value < g.sea_level:
		t.heightType = HType.SHALLOW
		ival = (25,25,150)
	elif g.sea_level <= value < 1.08*g.sea_level:
		t.heightType = HType.SAND
		ival = (240,240,64)
	elif 1.08*g.sea_level <= value < 1.25*g.sea_level:
		t.heightType = HType.GRASS
		ival = (50,220,20)
	elif 1.25*g.sea_level <= value < 1.4*g.sea_level:
		t.heightType = HType.FOREST
		ival = (16,160,0)
	elif 1.4*g.sea_level <= value < 1.55*g.sea_level:
		t.heightType = HType.HILLS
		ival = (128,128,128)
	else:
		t.heightType = HType.MOUNTAIN
		ival = (255,255,255)

	if t.heightType in [HType.DEEPWATER,HType.SHALLOW]:
		t.isLand = False
	else:
		t.isLand = True
	return ival

def setHeatType(t):
	heatval = t.heatVal
	if heatval < 0.03:
		t.heatType = HeatType.COLDEST
	elif heatval < 0.18:
		t.heatType = HeatType.COLDER
	elif heatval < 0.37:
		t.heatType = HeatType.COLD
	elif heatval < 0.55:
		t.heatType = HeatType.WARM
	elif heatval < 0.8:
		t.heatType = HeatType.WARMER
	else:
		t.heatType = HeatType.WARMEST

def setMoistureType(t):
	moistval = t.moistVal
	if moistval < 0.27:
		t.moistureType = MoistureType.DRYEST
	elif moistval < 0.4:
		t.moistureType = MoistureType.DRYER
	elif moistval < 0.6:
		t.moistureType = MoistureType.DRY
	elif moistval < 0.75:
		t.moistureType = MoistureType.WET
	elif moistval < 0.85:
		t.moistureType = MoistureType.WETTER
	else:
		t.moistureType = MoistureType.WETTEST

def heightNoise(x, y, z,r_offset):
	multiplier = 10
	return (noise.snoise3(multiplier*(x+r_offset)*0.5,multiplier*(y+r_offset)*0.5,multiplier*(z+r_offset)*0.5,octaves=8, persistence=0.5, lacunarity=2.0))

def heatNoise(x, y, z,r_offset):
	multiplier = 10
	return (noise.snoise3(multiplier*(x+r_offset)*0.5,multiplier*(y+r_offset)*0.5,multiplier*(z+r_offset)*0.5,octaves=6, persistence=0.5, lacunarity=2.0)+1)/2

def moistureNoise(x, y, z,r_offset):
	multiplier = 10
	return (noise.snoise3(multiplier*(x+r_offset)*0.5,multiplier*(y+r_offset)*0.5,multiplier*(z+r_offset)*0.5,octaves=6, persistence=0.5, lacunarity=2.0)+1)/2

def heatGradient(y):
	return 1 - abs(g.mapy/2 - y)/(g.mapy/2)

def getTop(t):
	return g.tiles[t.X][wrap(t.Y-1,g.mapy)]
def getBottom(t):
	return g.tiles[t.X][wrap(t.Y+1,g.mapy)]
def getLeft(t):
	return g.tiles[wrap(t.X-1,g.mapx)][t.Y]
def getRight(t):
	return g.tiles[wrap(t.X+1,g.mapx)][t.Y]

def setMapDataXY(arandom,hrandom,mrandom,xy,yin=-1):
	if yin != -1:
		x = xy
		y = yin
	else:
		x,y = xy
	x1 = 0
	x2 = 1
	dx = (x2 - x1)

	s = x/g.mapx
	t = y/g.mapy

	nx = x1 + math.cos(s*2*math.pi) * dx / (2*math.pi)
	ny = x1 + math.sin(s*2*math.pi) * dx / (2*math.pi)
	nz = t/(g.mapx/g.mapy)

	value = heightNoise(nx,ny,nz,arandom)
	heatval = heatNoise(nx,ny,nz,hrandom)
	wetval = moistureNoise(nx,ny,nz,mrandom)

	return (value,heatval,wetval)

def updateNeighbours():
	for x in range(g.mapx):
		for y in range(g.mapy):
			t = g.tiles[x][y]

			t.Top = getTop(t)
			t.Bottom = getBottom(t)
			t.Left = getLeft(t)
			t.Right = getRight(t)

def updateBitmasks():
	for x in range(g.mapx):
		for y in range(g.mapy):
			g.tiles[x][y].updateBitmask()

def setTile(aval,hval,mval,xy,yin=-1):
	if yin != -1:
		x = xy
		y = yin
	else:
		x,y = xy
	t = Tile()
	t.X = x
	t.Y = y

	t.heightValue = aval
	value = aval

	ival = setHeightType(t)

	heatval = hval*0.9

	lat,lon = lat_long((x,y))
	coldness = (abs(lat) / 90)**1.1
	heat = 1 - (abs(lat) / 90)**1
	heatval += heat
	heatval -= coldness

	if t.heightType == HType.GRASS:
		heatval -= 0.1 * value
	elif t.heightType == HType.FOREST:
		heatval -= 0.25 * value
	elif t.heightType == HType.HILLS:
		heatval -= 0.4 * value
	elif t.heightType == HType.MOUNTAIN:
		heatval -= 0.75 * value

	t.heatVal = heatval

	setHeatType(t)

	moistval = mval

	if t.heightType == HType.DEEPWATER:
		moistval += 8 * t.heightValue
	elif t.heightType == HType.SHALLOW:
		moistval += 3 * t.heightValue
	elif t.heightType == HType.SAND:
		moistval += 0.5 * t.heightValue
	elif t.heightType == HType.GRASS:
		moistval += 0.25 * t.heightValue

	t.moistVal = moistval

	setMoistureType(t)

	t.biomeType = getBiomeType(t)

	g.tiles[x][y] = t
	return (t.biomeType,aval,hval)

def _floodFill(tile,group,stack):
	if tile.floodFilled:
		return
	if not(tile.isLand):
		return
	tile.floodFilled = True
	group.tiles.append((tile.X,tile.Y))
	lat,lon = lat_long((tile.X,tile.Y))
	group.area += (360/g.mapx*math.cos(math.radians(lat)))**2

	t = getTop(tile)
	if not(t.floodFilled and t.isLand == t.isLand):
		stack.append(t)
	t = getBottom(tile)
	if not(t.floodFilled and t.isLand == t.isLand):
		stack.append(t)
	t = getLeft(tile)
	if not(t.floodFilled and t.isLand == t.isLand):
		stack.append(t)
	t = getRight(tile)
	if not(t.floodFilled and t.isLand == t.isLand):
		stack.append(t)

def floodFill():
	stack = []

	for x in range(g.mapx):
		for y in range(g.mapy):
			t = g.tiles[x][y]

			if t.floodFilled:
				continue

			if t.isLand:
				stack.append(t)
				group = TileGroup()

				while len(stack) > 0:
						_floodFill(stack.pop(),group,stack)

				if len(group.tiles) > 0:
					g.lands.append(group)
			else:
				t.floodFilled = True

def prepareTilemap():
	global mapData
	global heatFractal
	global moistureFractal
	global r_offset 
	global heat_random 
	global moisture_random

	r_offset = random.random()*1234
	heat_random = random.random()*1234
	moisture_random = random.random()*1234
	mapData = MapData(g.mapx,g.mapy)
	heatFractal = [[0 for _ in range(g.mapy)] for _ in range(g.mapx)]
	moistureFractal = [[0 for _ in range(g.mapy)] for _ in range(g.mapx)]

	for x in range(g.mapx):
		for y in range(g.mapy):
			t = Tile()
			t.X = x
			t.Y = y
			t.isLand = True
			t.floodFilled = False
			t.heightType = 0
			t.biomeType = 0
			g.tiles[x][y] = t

	tile_list = []
	for x in range(g.mapx):
		for y in range(g.mapy):
			tile_list.append((r_offset,heat_random,moisture_random,x,y))
	with Pool() as p:
		squares = p.starmap(setMapDataXY,tile_list)
	for N,sq in enumerate(squares):
		x = N//512
		y = N %512
		mapData.data[x][y] = sq[0]
		heatFractal[x][y] = sq[1]
		moistureFractal[x][y] = sq[2]
		if sq[0] > mapData.maxValue:
			mapData.maxValue = sq[0]
		if sq[0] < mapData.minValue:
			mapData.minValue = sq[0]
	timepunch("Initial map data: ")
	tile_list = []
	for x in range(g.mapx):
		for y in range(g.mapy):
			hval = (mapData.data[x][y] - mapData.minValue) / (mapData.maxValue - mapData.minValue)
			tile_list.append((hval,heatFractal[x][y],moistureFractal[x][y],x,y))
	with Pool() as p:
		tiles = p.starmap(setTile,tile_list)
	for N,tile in enumerate(tiles):
		x = N//512
		y = N %512
		g.tiles[x][y].biomeType = tile[0]
		g.tiles[x][y].heightValue = tile[1]
		g.tiles[x][y].heatVal = tile[2]
		setHeightType(g.tiles[x][y])
		setHeatType(g.tiles[x][y])
	updateNeighbours()
	timepunch("Tile stuff: ")

	if g.have_savefile:
		f = get_tar_data('lands.dat')
		json_str = f.decode('utf-8')
		json_lands = json.loads(json_str)
		for land in json_lands:
			our_land = TileGroup()
			our_land.tiles = land['tiles']
			our_land.area = float(land['area'])
			g.lands.append(our_land)
		maxmin = json.loads(get_tar_data('map.dat').decode('utf-8'))
		mapData.maxValue = maxmin['max']
		mapData.minValue = maxmin['min']
		#updateBitmasks()
	else:
		#updateBitmasks()
		floodFill()
		timepunch("Flood filling: ")
		json_lands = []
		for land in g.lands:
			our_dict = {}
			our_dict['tiles'] = land.tiles
			our_dict['area'] = land.area
			json_lands.append(our_dict)
		json_str = json.dumps(json_lands)
		json_bytes = json_str.encode('utf-8')
		add_to_tarfile((json_bytes,"lands.dat"))
		json_str = json.dumps({'max':mapData.maxValue,'min':mapData.minValue})
		json_bytes = json_str.encode('utf-8')
		add_to_tarfile((json_bytes,"map.dat"))