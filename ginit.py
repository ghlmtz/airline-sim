import timeit

mapx = 512
mapy = 512
# Good seeds:
#	772855	Spaced out continents
#	15213	Tight continents
#	1238	What I've been working with, for the most part
#	374539	Sparse continents
#	99999
seed = 4
sea_level = 0.6
DEBUG = 0
EXPERIMENT = 0

setup_time = timeit.default_timer()

tiles = [[None] * mapx for _ in range(mapy)]
town_grid = [[None] * mapx for _ in range(mapy)]
lands = []
towns = []
countries = []
have_savefile = False
