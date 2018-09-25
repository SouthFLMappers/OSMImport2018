from string import capwords

'''
Translate function used with ogr2osm for Miami-Date Large Building Footprints import.

https://github.com/jlevente/MiamiOSM-buildings

Fields used:

FIELD           DESC                    OSM_TAG
objectid        id of feature           miami_buildings:objectid
height          height of building [ft] height [m]
zip             zip code                addr:postcode
city            mailing municipality    addr:city
pre_dir         prefix of street        addr:street
suf_dir         suffix of street        addr:street
house_num       house number            addr:housenumber
st_name        name of street          addr:street
st_type        type of street          addr:street


Address abbreviation source: USPS (https://pe.usps.com/text/pub28/28apc_002.htm)
'''

def pretty_type(type):
    types_dict = {
        "ALY": "Alley",
        "ANX": "Anex",
        "ARC": "Arcade",
        "AVE": "Avenue",
        "BYU": "Bayou",
        "BCH": "Beach",
        "BND": "Bend",
        "BLF": "Bluff",
        "BLFS": "Bluffs",
        "BTM": "Bottom",
        "BLVD": "Boulevard",
        "BR": "Branch",
        "BRK": "Brook",
        "BRKS": "Brooks",
        "BG": "Burg",
        "BGS": "Burgs",
        "BYP": "Bypass",
        "CP": "Camp",
        "CYN": "Canyon",
        "CTR": "Center",
        "CSWY": "Causeway",
        "CPE": "Cape",
        "CTRS": "Centers",
        "CIR": "Circle",
        "CIRS": "Circles",
        "CLF": "Cliff",
        "CLFS": "Cliffs",
        "CLB": "Club",
        "CMN": "Common",
        "CMNS": "Commons",
        "COR": "Corner",
        "CORS": "Corners",
        "CRSE": "Course",
        "CT": "Court",
        "CTS": "Courts",
        "CV": "Cove",
        "CVS": "Coves",
        "CRK": "Creek", 
        "CRKS": "Creeks",
        "CRES": "Crescent",
        "XING": "Crossing",
        "CRST": "Crest",
        "CURV": "Curve",
        "XRD": "Crossroad",
        "XRDS": "Crossroads",
        "DL": "Dale",
        "DM": "Dam",
        "DV": "Divide",
        "DR": "Drive",
        "DRS": "Drives",
        "EST": "Estate",
        "ESTS": "Estates",
        "EXPY": "Expressway",
        "EXT": "Extension",
        "EXTS": "Extensions",
        "FALL": "Fall",
        "FLS": "Falls",
        "FRY": "Ferry",
        "FLD": "Field",
        "FLDS": "Fields",
        "FLT": "Flat",
        "FLTS": "Flats",
        "FRD": "Fords",
        "FRDS": "Fords",
        "FRST": "Forest",
        "FRG": "Forge",
        "FRGS": "Forges",
        "FRK": "Fork",
        "FRKS": "Forks",
        "FT": "Fort",
        "FWY": "Freeway",
        "GDN": "Garden",
        "GDNS": "Gardens",
        "GTWY": "Gateway",
        "GLN": "Glen",
        "GLNS": "Glens",
        "GRN": "Green",
        "GRNS": "Greens",
        "GRV": "Grove",
        "GRVS": "Groves",
        "HBR": "Harbor",
        "HBRS": "Harbors",
        "HVN": "Haven", 
        "HTS": "Heights",
        "HWY": "Highway",
        "HL": "Hill",
        "HLS": "Hills",
        "HOLW": "Hollow",
        "INLT": "Inlet",
        "IS": "Island", 
        "ISS": "Islands",
        "ISLE": "Isle",
        "JCT": "Juction", 
        "JCTS": "Junctions",
        "KY": "Key",
        "KYS": "Keys",
        "KNL": "Knoll",
        "KNLS": "Knolls",
        "LK": "Lake",
        "LKS": "Lakes",
        "LAND": "Land",
        "LNDG": "Landing",
        "LN": "Lane", 
        "LGT": "Light",
        "LGTS": "Lights",
        "LCK": "Lock",
        "LCKS": "Locks",
        "LDG": "Lodge",
        "LOOP": "Loop",
        "MALL": "Mall",
        "MNR": "Manor",
        "MNRS": "Manors",
        "MDW": "Meadow",
        "MDWS": "Meadows",
        "MEWS": "Mews",
        "ML": "Mill",
        "MLS": "Mills",
        "MSN": "Mission",
        "MT": "Mount",
        "MTN": "Mountain",
        "MNTS": "Mountains",
        "NCK": "Neck",
        "ORCH": "Orchard",
        "OVAL": "Oval",
        "OPAS": "Overpass",
        "PARK": "Park",
        "PKWY": "Parkway",
        "PASS": "Pass",
        "PSGE": "Passage",
        "PATH": "Path",
        "PIKE": "Pike",
        "PNE": "Pine",
        "PNES": "Pines",
        "PL": "Place",
        "PLN": "Plain",
        "PLNS": "Plains",
        "PLZ": "Plaza",
        "PT": "Point",
        "PTS": "Points",
        "PRT": "Port",
        "PRTS": "Ports",
        "PR": "Prairie",
        "RADL": "Radial",
        "RAMP": "Ramp",
        "RNCH" : "Ranch",
        "RPD": "Rapid",
        "RPDS": "Rapids",
        "RST": "Rest",
        "RDG": "Ridge",
        "RDGS": "Ridges",
        "RIV": "River",
        "RD": "Road",
        "RDS": "Roads",
        "RTE": "Route",
        "ROW": "Row",
        "RUE": "Rue",
        "SHL": "Shoals", 
        "SHLS": "Shoals",
        "SHR": "Shore",
        "SHRS": "Shores",
        "SKWY": "Skyway",
        "SPG": "Spring",
        "SPGS": "Springs",
        "SPUR": "Spur",
        "SQ": "Square",
        "SQS": "Squares",
        "STA": "Station",
        "STRA": "Stravenue",
        "STRM": "Stream",
        "ST": "Street",
        "STS": "Streets",
        "SMT": "Summit",
        "TER": "Terrace",
        "TRWY": "Throughway",
        "TRCE": "Trace",
        "TRAK": "Track",
        "TRFY": "Trafficway",
        "TRL": "Trail",
        "TRLR": "Trailer",
        "TUNL": "Tunnel",
        "TPKE": "Turnpike",
        "UPAS": "Underpass",
        "UN": "Union",
        "UNS": "Unions",
        "VLY": "Valley",
        "VLYS": "Valleys",
        "VIA": "Viaduct",
        "VW": "View",
        "VWS": "Views",
        "VLG": "Village",
        "VLGS": "Villages",
        "VL": "Ville",
        "VIS": "Vista",
        "WALK": "Walk",
        "WALL": "Walls",
        "WAY": "Way",
        "WAYS": "Ways",
        "WL": "Well",
        "WLS": "Wells"
        }
    return types_dict[type]

def pretty_prefix(prefix):
    prefix_dict = {
        "N": "North",
        "S": "South",
        "W": "West",
        "E": "East",
        "NW": "Northwest",
        "NE": "Northeast",
        "SW": "Southwest",
        "SE": "Southeast"
    }
    return prefix_dict[prefix]

def filterTags(attrs):
    if not attrs:
        return
    tags = {}
    
    if 'height' in attrs:
        if attrs['height'] is not None:
            # Convert feet to meters, round
            tags['height'] = unicode(round(float(attrs['height']) * 0.3048, 1))

    if 'zip' in attrs:
        if len(attrs['zip']) > 0:
            tags['addr:postcode'] = attrs['zip']

    if 'mailing_mu' in attrs:
        if len(attrs['mailing_mu']) > 0:
            tags['addr:city'] = capwords(attrs['mailing_mu'])

    street = []

    if 'pre_dir' in attrs:
        if len(attrs['pre_dir']) > 0:
            street.append(pretty_prefix(attrs['pre_dir']))

    if 'st_name' in attrs:
        if len(attrs['st_name']) > 0:
            street.append(capwords(attrs['st_name'].lower()))

    if 'st_type' in attrs:
        if len(attrs['st_type']) > 0:
            street.append(pretty_type(attrs['st_type']))

    if 'suf_dir' in attrs:
        if len(attrs['suf_dir']) > 0:
            street.append(pretty_preffix(attrs['suf_dir']))

    street_name = ' '.join(street)
    if street_name is not '':
        tags['addr:street'] = street_name

    if 'hse_num' in attrs:
        if len(attrs['hse_num']) > 0:
            tags['addr:housenumber'] = attrs['hse_num']

    if 'road_intersect' in attrs:
        if attrs['road_intersect'] == '1':
            tags['fixme'] = "highway/railway crosses building"

    tags['building'] = 'yes'
    #tags['source'] = 'Miami-Dade County GIS Open Data, http://gis.mdc.opendata.arcgis.com'

    return tags
