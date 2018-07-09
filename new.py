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

	if g.DEBUG:
		from draw import makeHeatMap, makeWetMap
		makeHeatMap()
		makeWetMap()
		imageOutput(biomepixels,"mapbiome.png")
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