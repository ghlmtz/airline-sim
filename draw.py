from PIL import Image, ImageDraw
from io import BytesIO
from math import hypot
from multiprocessing import Pool

import ginit as g
import math
from enums import *
from util import *

def imageOutput(pixels,output,maskfile=None):
	iSize = (len(pixels),len(pixels))
	picture = Image.new("RGB",iSize)
	for x in range(len(pixels)):
		for y in range(len(pixels[x])):
			picture.putpixel((x,y),pixels[x][y])
	if maskfile:
		mask = Image.open(maskfile).convert('L')
		picture.putalpha(mask)
	picture.save(output,'PNG')

def makeHeatMap():
	heatpixels = []
	for x in range(g.mapx):
		heatpixels.append([])
		for y in range(g.mapy):
			h = g.tiles[x][y].heatType
			if h == HeatType.COLDEST:
				ival = (0,255,255)
			elif h == HeatType.COLDER:
				ival = (170,255,255) 
			elif h == HeatType.COLD:
				ival = (0,229,133)
			elif h == HeatType.WARM:
				ival = (255,255,100)
			elif h == HeatType.WARMER:
				ival = (255,100,0)
			else:
				ival = (241,12,0)
			if g.tiles[x][y].count != 15 and y != 0 and y != g.mapy-1:
				ival = (0,0,0)
			heatpixels[x].append(ival)
	imageOutput(heatpixels,"mapheat.png")

def makeWetMap():
	wetpixels = []
	for x in range(g.mapx):
		wetpixels.append([])
		for y in range(g.mapy):
			w = g.tiles[x][y].moistureType
			if w == MoistureType.WETTEST:
				ival = (0,0,100)
			elif w == MoistureType.WETTER:
				ival = (20,70,255)
			elif w == MoistureType.WET:
				ival = (85,255,255)
			elif w == MoistureType.DRY:
				ival = (80,255,0)
			elif w == MoistureType.DRYER:
				ival = (245,245,23)
			else:
				ival = (255,139,17)
			wetpixels[x].append(ival)
	imageOutput(wetpixels,"mapmoist.png")

def makeBiomeMap(state={'calculate':True}):
	if state['calculate']:
		biomepixels = []
		for x in range(g.mapx):
			biomepixels.append([])
			for y in range(g.mapy):
				b = g.tiles[x][y].biomeType
				if b == BiomeType.ICE:
					ival = (255,255,255)
				elif b == BiomeType.TUNDRA:
					ival = (96,131,112)
				elif b == BiomeType.DESERT:
					ival = (238,218,130)
				elif b == BiomeType.GRASSLAND:
					ival = (164,225,99)
				elif b == BiomeType.BOREAL:
					ival = (95,115,62)
				elif b == BiomeType.WOODLAND:
					ival = (139,175,90)
				elif b == BiomeType.SAVANNA and g.tiles[x][y].heightType in [HType.FOREST,HType.SAND]:
					ival = (139,175,90)
				elif b == BiomeType.RAINFOREST and g.tiles[x][y].heightType in [HType.FOREST,HType.GRASS, HType.HILLS]:
					ival = (139,175,90)
				else:
					ival = (164,225,99)

				if g.tiles[x][y].heightType == HType.DEEPWATER and g.tiles[x][y].heatVal > -0.1:
					ival = (0,0,128)
				elif g.tiles[x][y].heightType == HType.SHALLOW and g.tiles[x][y].heatVal > 0:
					ival = (25,25,150)

				biomepixels[x].append(ival)
		state['result'] = biomepixels
		state['calculate'] = False
	return state['result']

def drawSphereXY(longitude,biomepixels,size,mapx,x,y):
	x0 = x - size/2
	y0 = size/2 - y
	p = math.hypot(x0,y0)
	d = p*2/(size)
	if d <= 1:
		C = math.asin(d)
		if p == 0:
			lat = 0
			lon = 0
		else:
			lat = math.degrees(math.asin(y0*math.sin(C)/p))
			lon = longitude + math.degrees(math.atan2(x0*math.sin(C),(p*math.cos(C))))
			lon = wrap(lon,360) - 180
		if abs(lat) < 84:
			x1,y1 = inv_lat_long((lat,lon))
			x1 = wrap(x1,mapx)
			ival = biomepixels[x1][y1]
		else:
			ival = (255,255,255)
	else:
		ival = (128,128,128)
	return ival

def drawSphere(longitude):
	size = 192
	spherepixels = [[0 for _ in range(size)] for _ in range(size)]
	biomepixels = makeBiomeMap()
	pixel_list = []
	for x in range(size):
		for y in range(size):
			pixel_list.append((longitude,biomepixels,size,g.mapx,x,y))

	with Pool() as p:
		pixels = p.starmap(drawSphereXY,pixel_list)
	for N,pixel in enumerate(pixels):
		x = N//size
		y = N %size
		spherepixels[x][y] = pixel

	pic_data = BytesIO()
	imageOutput(spherepixels,pic_data,maskfile="spheremask.png")
	pic_data.seek(0)
	return pic_data