import json
import random
from multiprocessing import Pool
from gfx import Town

from util import *
from enums import *
from fileio import *
import ginit as g

def dist_calc(N,town,other_town):
	dist = town_dist(town,other_town)
	if dist <= 100 or (town.isCapital and other_town.isCapital and dist <= 165):
		return N
	return -1

def _countryFF(tile,country,stack):
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

def countryFF(tuplestack):
	i = 0
	tuplestack.append(None)
	while len(tuplestack) > 0 and i < 100000:
		i += 1
		top = tuplestack.pop(0)
		if top is None:
			if len(tuplestack) == 0:
				return
			random.shuffle(tuplestack)
			top = tuplestack.pop(0)
			tuplestack.append(None)
		_countryFF(top[0],top[1],tuplestack)

def loadTowns():
	if g.have_savefile:
		f = get_tar_data('towns.dat')
		json_str = f.decode('utf-8')
		json_town = json.loads(json_str)
		N = json_town.pop(0)['N']
		g.countries.extend([[] for _ in range(N)])
		for town in json_town:
			T = Town(town['lat'],town['lon'])
			T.isCapital = town['isCapital']
			T.country = town['country']
			T.land = town['land']
			T.population = town['population']
			g.countries[T.country].append(T)
			g.lands[T.land].towns.append((T.X,T.Y))
			g.towns.append(T)
			g.town_grid[T.X][T.Y] = T

		f = get_tar_data('tileland.dat')
		json_str = f.decode('utf-8')
		json_tileland = json.loads(json_str)
		for tileinfo in json_tileland:
			X = tileinfo["X"]
			Y = tileinfo["Y"]
			g.tiles[X][Y].country = tileinfo["c"]
		if g.DEBUG:
			print("Towns: %d" %len(g.towns))
	else:
		# Generate a bunch of towns
		ops = 0 
		for N,land in enumerate(g.lands):
			A = land.area
			if A < 10:
				continue
			elif 10 <= A < 100:
				pop = math.ceil(A/12)
			elif 100 <= A < 500:
				pop = math.ceil(A/7)
			elif 500 <= A < 2000:
				pop = math.ceil(A/6)
			else:
				pop = math.ceil(A/5)
			chosen = random.sample(range(len(land.tiles)),pop)
			for choice in chosen:
				ops += 1
				x,y = land.tiles[choice]
				lat,lon = lat_long((x,y))
				town = Town(lat+0.4-random.random()/5,lon+0.6-random.random()/3)
				x1,y1 = inv_lat_long((town.lat,town.lon))
				x = wrap(x1,g.mapx)
				y = y1
				if g.tiles[x][y].isLand and g.tiles[x][y].biomeType != BiomeType.ICE:
					score = (g.tiles[x][y].heightValue - g.sea_level)/(1 - g.sea_level)
					biome = g.tiles[x][y].biomeType
					if biome == BiomeType.TUNDRA:
						score += 0.9
					elif biome == BiomeType.BOREAL:
						score += 0.6
					elif biome == BiomeType.DESERT:
						score += 0.35
					if biome == BiomeType.RAINFOREST:
						score += 0.2
					r = random.random()
					if score < r:
						g.towns.append(town)
						town.land = N
						land.towns.append(town)

					if score + 0.5 < r and random.random() < 0.4:
						town.isCapital = True
						town.country = len(g.countries)
						g.countries.append([town])
					else:
						town.isCapital = False

		# Remove towns too close to other towns or cities
		remove = []
		for land in g.lands:
			town_list = []
			for N,town in enumerate(land.towns):
				for other_town in land.towns[N+1:]:
					if town is other_town:
						continue
					town_list.append((N,town,other_town))
			if len(town_list):
				with Pool() as p:
					remove = p.starmap(dist_calc,town_list)
				remove = list(set(remove))
				for N in sorted(remove,reverse=True):
					if N == -1:
						break
					town = land.towns[N]
					g.lands[town.land].towns.remove(town)
					if town.country != -1:
						g.countries[town.country].remove(town)
					g.towns.remove(town)

		timepunch('First remove: ')

		# Assign capitals to islands without capitals
		for land in g.lands:
			if land.area >= 10 and len(land.towns):
				for town in land.towns:
					if town.isCapital:
						break
				else:
					land.towns[0].isCapital = True
					land.towns[0].country = len(g.countries)
					g.countries.append([land.towns[0]])

		# Iterate through towns on landmass, find nearest capital
		for land in g.lands:
			capitals = list(filter(lambda x: x.isCapital,land.towns))
			for town in land.towns:
				if town.isCapital:
					continue
				minval = 1500
				mincountry = -1
				for cap in capitals:
					dist = town_dist(town,cap)
					if dist < minval:
						minval = dist
						mincountry = cap.country
				if mincountry != -1:
					g.countries[mincountry].append(town)
					town.country = mincountry
				else:
					town.country = len(g.countries)
					g.countries.append([town])
					town.isCapital = True

		#Quick check for orphan cities
		remove = []
		for town in g.towns:
			if town.country == -1:
				remove.append(town)
		remove = list(set(remove))
		if g.DEBUG:
			print("Removed %d orphans" %len(remove))
		for town in remove:
			g.lands[town.land].towns.remove(town)
			g.towns.remove(town)
		if g.DEBUG:
			print("%d towns remain" %len(g.towns))

		# Try to avoid 1-city countries
		capitals = list(filter(lambda x: x.isCapital,g.towns))
		for cap in capitals:
			if len(g.countries[cap.country]) == 1:
				if g.DEBUG:
					print("One capital country")
				for town in g.towns:
					if town_dist(cap,town) < 1000:
						g.countries[cap.country].remove(cap)
						g.countries[town.country].append(cap)
						cap.isCapital = False
						cap.country = town.country


		# Assign populations
		popsum = 0
		for town in g.towns:
			base_val = random.random()**(-0.8) * 250000
			x,y = town.X,town.Y
			score = g.tiles[x][y].heightType.value
			l = abs(town.lat) - 55
			if l < 0:
				l = 0
			score += l
			if town.isCapital:
				score -= 2
			csize = len(g.countries[town.country])
			if csize > 3:
				score -= 1
			if csize > 7:
				score -= 1
			if csize > 15:
				score -= 1
			pop = base_val
			pop -= score*random.random()*50000
			if pop < 100000:
				pop = random.random()*50000 + 100000
			if pop > 10000000:
				pop = random.random()*500000 + 9000000
			town.population = int(pop)
			popsum += int(pop)

			# Take this opportunity to populate town_grid as well
			g.town_grid[x][y] = town

		for N,country in enumerate(g.countries):
			capital = None
			if random.random() < 0.75 and len(country):
				maxpop = 0
				for town in country:
					if town.population > maxpop:
						maxpop = town.population
						maxtown = town
					if town.isCapital:
						capital = town
				if capital:
					capital.isCapital = False
				maxtown.isCapital = True

		# Assign countries to all the tiles now that we have towns
		for land in g.lands:
			if len(land.towns) == 0:
				x,y = land.tiles[0]
				countryFF([(g.tiles[x][y],-1)])
			else:
				t = land.towns[0]
				c = g.town_grid[t.X][t.Y].country
				brk = 0
				for town in land.towns:
					if c != g.town_grid[town.X][town.Y].country:
						tuplestack = [(g.tiles[t.X][t.Y],g.town_grid[t.X][t.Y].country) for t in land.towns]
						countryFF(tuplestack)
						break
				else: 
					x,y = land.tiles[0]
					countryFF([(g.tiles[x][y],c)])
					continue

		json_town = [{"N": len(g.countries)}]
		json_town.extend([vars(x) for x in g.towns])
		json_str = json.dumps(json_town)
		json_bytes = json_str.encode('utf-8')
		add_to_tarfile((json_bytes,"towns.dat"))

		json_tileland = []
		for land in g.lands:
			for t in land.tiles:
				X,Y = t
				if g.tiles[X][Y].country:
					d = {}
					d["X"] = X
					d["Y"] = Y
					d["c"] = g.tiles[X][Y].country
					b = [d]
					json_tileland.extend(b)
		json_str = json.dumps(json_tileland)
		json_bytes = json_str.encode('utf-8')
		add_to_tarfile((json_bytes,"tileland.dat"))
