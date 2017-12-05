from enum import Enum

class HType(Enum):
	DEEPWATER = 1
	SHALLOW = 2
	SHORE = 3
	SAND = 4
	GRASS = 5
	FOREST = 6
	HILLS = 7
	MOUNTAIN = 8

class HeatType(Enum):
	COLDEST = 1
	COLDER = 2
	COLD = 3
	WARM = 4
	WARMER = 5
	WARMEST = 6

class MoistureType(Enum):
	WETTEST = 1
	WETTER = 2
	WET = 3
	DRY = 4
	DRYER = 5
	DRYEST = 6

class BiomeType(Enum):
	DESERT = 1
	SAVANNA = 2
	RAINFOREST = 3
	GRASSLAND = 4
	WOODLAND = 5
	SEASONAL = 6
	TEMPERATE = 7
	BOREAL = 8
	TUNDRA = 9
	ICE = 10