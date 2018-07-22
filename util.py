import math
import ginit as g
import timeit

def sin(theta):
	return math.sin(theta*math.pi/180)

def cos(theta):
	return math.cos(theta*math.pi/180)

def tan(theta):
	return math.tan(theta*math.pi/180)

def lat_long_bound(lat,lon,bound):
	if lat > bound[0][0] or lat < bound[1][0]:
		return 0
	if bound[0][1] > bound[1][1]:
		# Map edge
		if lon >= bound[0][1] and lon <= bound[1][1]:
			return 1
	else:
		if lon < bound[0][1] or lon > bound[1][1]:
			return 0

	return 1

def lat_long(xy):
	(x,y) = xy
	ynew = (g.mapy/2-y)/(g.mapy/6) * (g.mapy/g.mapx)
	return ((2*math.atan(math.exp(ynew)) - math.pi/2)*180/math.pi,(x-g.mapx/2)*360/g.mapx)

def inv_lat_long(latlong):
	(lat,lon) = latlong
	if lat > 90:
		lat -= 180
	if lat < -90:
		lat += 180
	return (round((lon/(360)+0.5)*g.mapx),round(-g.mapx*math.log(math.tan(math.radians(lat))+1/math.cos(math.radians(lat)))/6+g.mapy/2))

def town_dist(t1,t2):
	lat1,lon1 = (t1.lat,t1.lon)
	lat2,lon2 = (t2.lat,t2.lon)
	return lat_lon_dist(lat1,lon1,lat2,lon2)

def lat_lon_dist(lat1,lon1,lat2,lon2):
	return 2*3959*math.asin(math.sqrt(sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2))

def wrap(n,mod):
	if n < 0:
		return mod + n
	elif n >= mod:
		return n - mod
	else:
		return n

def timepunch(msg):
	print(msg,timeit.default_timer() - g.setup_time)

def fmt_time(t):
	m = t % 60
	h = t // 60
	return ("%02d%02dZ" % (h, m))