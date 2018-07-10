import random
from util import timepunch
from draw import drawSphere
from mapgen import prepareTilemap
from towngen import loadTowns
from fileio import *
from gfx import launch_game
import ginit as g

########## TODO ##########
# Move plane sprites to dedicated surface
# Instead of redrawing all tiles on camera move, have intelligent drawing method

######### MAIN BODY ##########

def main():
	random.seed(g.seed)
	g.have_savefile = tar_exists()

	prepareTilemap()
	timepunch("Map setup done: ")

	loadTowns()
	timepunch("City step done: ")

	if g.EXPERIMENT:
		# EXPERIMENT: Assigning land to countries
		def _floodFill2(tile,country,stack):
			if tile.country is not None:
				return
			if not(tile.isLand):
				return
			tile.country = country
			from mapgen import getTop, getBottom, getLeft, getRight
			t = getTop(tile)
			if t.country is None and t.isLand:
				stack.append(t)
			t = getBottom(tile)
			if t.country is None and t.isLand:
				stack.append(t)
			t = getLeft(tile)
			if t.country is None and t.isLand:
				stack.append(t)
			t = getRight(tile)
			if t.country is None and t.isLand:
				stack.append(t)

		def floodFill2(tile,c):
			stack = [tile]
			i = 0
			while len(stack) > 0 and i < 50000:
				#print(stack)
				i += 1
				_floodFill2(stack.pop(),c,stack)

		def _floodFill3(tile,country,stack):
			if tile.country is not None:
				return
			if not(tile.isLand):
				return
			tile.country = country
			from mapgen import getTop, getBottom, getLeft, getRight
			t = getTop(tile)
			if t.country is None and t.isLand:
				stack.append((t,country,))
			t = getBottom(tile)
			if t.country is None and t.isLand:
				stack.append((t,country,))
			t = getLeft(tile)
			if t.country is None and t.isLand:
				stack.append((t,country,))
			t = getRight(tile)
			if t.country is None and t.isLand:
				stack.append((t,country,))

		def floodFill3(tuplestack):
			i = 0
			while len(tuplestack) > 0 and i < 100000:
				i += 1
				top = tuplestack.pop(0)
				_floodFill3(top[0],top[1],tuplestack)

		tmp = []
		for land in g.lands:
			if len(land.towns) == 0:
				x,y = land.tiles[0]
				floodFill2(g.tiles[x][y],0)
			else:
				t = land.towns[0]
				c = g.town_grid[t[0]][t[1]].country
				brk = 0
				for town in land.towns:
					if c != g.town_grid[town[0]][town[1]].country:
						brk = 1
						break
				else: 
					x,y = land.tiles[0]
					floodFill2(g.tiles[x][y],c)
					continue
				if brk:
					tuplestack = [(g.tiles[t[0]][t[1]],g.town_grid[t[0]][t[1]].country) for t in land.towns]
					floodFill3(tuplestack)

		timepunch("Map drawing time")
		from enums import BiomeType
		heatpixels = []
		colors = [((N*73) % 192,(N*179)%192,(N*37)%192) for N in range(len(g.countries)+10)]
		colors[1] = (0,0,0)
		for x in range(g.mapx):
			heatpixels.append([])
			for y in range(g.mapy):
				h = g.tiles[x][y].country
				if g.tiles[x][y].biomeType == BiomeType.ICE:
					ival = (255,255,255)
				elif h is not None:
					ival = colors[h+1]
				else:
					ival = (0,0,212)
				heatpixels[x].append(ival)
		from draw import imageOutput
		imageOutput(heatpixels,"mapcount.png")

		timepunch("Rar")

	if g.DEBUG:
		from draw import makeHeatMap, makeWetMap
		makeHeatMap()
		makeWetMap()
		print("Capitals: ",len(list(filter(lambda x: x.isCapital,g.towns))))

		landpixels = [[(0,0,128) for _ in range(g.mapy)] for _ in range(g.mapx)]
		for land in g.lands:
			for tile in land.tiles:
				if tile.biomeType == BiomeType.ICE:
					landpixels[tile.X][tile.Y] = (255,255,255)
				else:
					landpixels[tile.X][tile.Y] = (0,0,0)

		for town in g.towns:
			x,y = inv_lat_long((town.lat,town.lon))
			x = wrap(x,g.mapx)
			y = wrap(y,g.mapy)
			if town.isCapital:
				landpixels[x][y] = (255,0,0)
			else:
				try:
					landpixels[x][y] = (128,0,128)
				except IndexError:
					print(x,y)
			landpixels[x][y] = colors[town.country + 1]

			imageOutput(landpixels,"mapland.png")

			with open("latlon.txt","w") as f:
				for town in g.towns:
					f.write("%.2f,%.2f\n"%(town.lat,town.lon))

	if not g.have_savefile:
		pic_data = []
		for i in range(4):
			pic_data.append((drawSphere(-180+90*i),"mapsphere%d.png"%(i+1)))
		add_to_tarfile(*pic_data)
		save_tarfile()

		timepunch("Spheres present: ")

	launch_game()

if __name__ == "__main__":
	main()