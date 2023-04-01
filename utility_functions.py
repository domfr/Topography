import math
import geocoder
from typing import Union
from application.config import ZOOM_DIMENSIONS, BOUNDING_BOX


cache = {}
ch_cache = {}


def to_seconds(angle):
    degrees = math.floor(angle)
    minutes_float = (angle - degrees) * 60
    minutes = math.floor(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return seconds + minutes * 60 + degrees * 3600


def get_easting(phi2, lambda2):
    return 2600072.37 + 211455.93 * lambda2 - 10938.51 * lambda2 * phi2 - 0.36 * lambda2 * math.pow(phi2, 2) - 44.54 * math.pow(lambda2, 3)


def get_northing(phi2, lambda2):
    return 1200147.07 + 308807.95 * phi2 + 3745.25 * math.pow(lambda2, 2) + 76.63 * math.pow(phi2, 2) - 194.56 * math.pow(lambda2, 2) * phi2 + 119.79 * math.pow(phi2, 3)


def get_x(phi2, lambda2):
    get_northing(phi2, lambda2) - 1000000


def get_y(phi2, lambda2):
    get_easting(phi2, lambda2) - 2000000

def get_y2_from_e(e):
    return (e - 2600000) / 1000000


def get_x2_from_n(n):
    return (n - 1200000) / 1000000


def get_lambda(y2, x2):
    return 2.6779094 + 4.728982 * y2 + 0.791484 * y2 * x2 + 0.1306 * y2 * math.pow(x2, 2) - 0.0436 * math.pow(y2, 3)


def get_phi(y2, x2):
    return 16.9023892 + 3.238272 * x2 - 0.270978 * math.pow(y2, 2) - 0.002528 * math.pow(x2, 2) - 0.0447 * math.pow(y2, 2) * x2 - 0.0140 * math.pow(x2, 3)


def to_degrees(n):
    return n * 100 / 36
  
  
def decimal_to_ch(lat, long):
  """ converts decimal coordinates to swiss coordinates"""
  if (lat, long, 'dch') in ch_cache:
      return ch_cache[(lat, long, 'dch')]
  phi2 = (to_seconds(lat) - 169028.66) / 10000
  lambda2 = (to_seconds(long) - 26782.5) / 10000
  ch_cache[(lat, long, 'dch')] = (get_easting(phi2, lambda2)), (get_northing(phi2, lambda2))
  return ch_cache[(lat, long, 'dch')]


def ch_to_decimal(x, y):
    """ converts swiss coordinates to decimal coordinates"""
  
    if (x, y, 'chd') in ch_cache:
        return ch_cache[(x, y, 'chd')]
    y2 = get_y2_from_e(x)
    x2 = get_x2_from_n(y)
    ch_cache[(x, y, 'chd')] = (to_degrees(get_phi(y2, x2))), (to_degrees(get_lambda(y2, x2)))
    return ch_cache[(x, y, 'chd')]


def decimal_to_osm(decimal_x: float, decimal_y: float, zoom: int) -> tuple:
    """ converts decimal coordinates to internal OSM coordinates"""

    zoom = int(round(zoom))
    if (decimal_x, decimal_y) in cache:
        (x, y) = cache[(decimal_x, decimal_y)]
    else:
        (x, y) = decimal_to_ch(decimal_x, decimal_y)
        cache[(decimal_x, decimal_y)] = (x, y)

    xtile = ((x - BOUNDING_BOX[zoom][0]) / (BOUNDING_BOX[zoom][1] - BOUNDING_BOX[zoom][0])) * ZOOM_DIMENSIONS[zoom][0]
    ytile = ((y - BOUNDING_BOX[zoom][3]) / (BOUNDING_BOX[zoom][2] - BOUNDING_BOX[zoom][3])) * ZOOM_DIMENSIONS[zoom][1]

    return xtile, ytile


def osm_to_decimal(tile_x: Union[int, float], tile_y: Union[int, float], zoom: int) -> tuple:
    """ converts internal OSM coordinates to decimal coordinates """

    x = ((tile_x / ZOOM_DIMENSIONS[zoom][0]) * (BOUNDING_BOX[zoom][1] - BOUNDING_BOX[zoom][0])) + BOUNDING_BOX[zoom][0]
    y = ((tile_y / ZOOM_DIMENSIONS[zoom][1]) * (BOUNDING_BOX[zoom][2] - BOUNDING_BOX[zoom][3])) + BOUNDING_BOX[zoom][3]

    if (x, y) in cache:
        (lat_deg, lon_deg) = cache[(x, y)]
    else:
        (lat_deg, lon_deg) = ch_to_decimal(x, y)
        cache[(x, y)] = (lat_deg, lon_deg)

    return lat_deg, lon_deg


def convert_coordinates_to_address(deg_x: float, deg_y: float) -> geocoder.osm_reverse.OsmReverse:
    """ returns address object with the following attributes:
        street, housenumber, postal, city, state, country, latlng
        Geocoder docs: https://geocoder.readthedocs.io/api.html#reverse-geocoding """

    result = geocoder.osm([deg_x, deg_y], method="reverse")
    return result


def convert_coordinates_to_city(deg_x: float, deg_y: float) -> str:
    """ returns city name """
    return geocoder.osm([deg_x, deg_y], method="reverse").city


def convert_coordinates_to_country(deg_x: float, deg_y: float) -> str:
    """ returns country name """
    return geocoder.osm([deg_x, deg_y], method="reverse").country


def convert_address_to_coordinates(address_string: str) -> tuple:
    """ returns address object for given coords or None if no address found """

    result = geocoder.osm(address_string)

    if result.ok:
        return tuple(result.latlng)

    return None
