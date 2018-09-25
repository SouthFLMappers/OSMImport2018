import sys
from db_handler import DBHandler
from osm_handler import OSMHandler

def get_args():
    import argparse
    p = argparse.ArgumentParser(description="Data preparation for Miami's OSM Building import")
    p.add_argument('-setup', '--setup', help='Set up Postgres DB.', action='store_true')
    p.add_argument('-bd', '--buildings_download', help='Download Buildings from OSM', action="store_true")
    p.add_argument('-ad', '--address_download', help='Download Addresses from OSM', action="store_true")
    p.add_argument('-rd', '--roads_download', help='Download highway=* from OSM', action="store_true")
    p.add_argument('-d', '--dsn', help='Dsn for database connection.')
    p.add_argument('-s', '--simplify', help='Simplify geometry of import buildings', action='store_true')
    p.add_argument('-af', '--add_fields', help='Add/reset logical fields to import data.', action='store_true')
    p.add_argument('-v', '--vacuum', help='Vacuums Postgres DB.', action="store_true")
    p.add_argument('-cp', '--convert_poly', help='Convert OSM features from Overpass to polygon',  action='store_true')
    p.add_argument('-dd', '--dedupe_address',  help='Get rid of overlapping address points (unit)',  action='store_true')
    p.add_argument('-ca', '--check_address', help='Checks if addresses overlap with existing addresses.', action="store_true")
    p.add_argument('-cb', '--check_building', help='Checks whether buildings to upload overlap with existing OSM buildings.', action="store_true")
    p.add_argument('-crr', '--check_road_rail', help='Checks whether buildings to upload overlap with OSM highway=* or railway=*.', action="store_true")
    p.add_argument('-idx', '--index_data', help='Creates indexes on several tables.', action="store_true")
    p.add_argument('-a', '--assign_address', help='Assigns an address to buildings with only 1 overlapping address point.', action="store_true")
    p.add_argument('-r', '--report', help='Prints out a quick report.', action="store_true")
    p.add_argument('-b', '--bbox', help='Bounding box for data download, overpass format.')
    return p.parse_args()

if __name__ == "__main__":
    args = vars(get_args())
    setup = args["setup"]
    building_download = args["buildings_download"]
    address_download = args["address_download"]
    roads_download = args["roads_download"]
    simplify = args["simplify"]
    dsn = args["dsn"]
    assign_address = args["assign_address"]
    check_address = args["check_address"]
    check_building = args["check_building"]
    check_road_rail = args["check_road_rail"]
    vacuum = args["vacuum"]
    report = args["report"]
    index = args["index_data"]
    bbox = args["bbox"]
    add_fields = args["add_fields"]
    dedupe = args["dedupe_address"]
    convert_poly = args["convert_poly"]

    db = DBHandler(dsn)
    osm = OSMHandler(bbox)

    if setup:
        print 'Setting up the database.'
        db.setup_db()

    if building_download:
        print 'Querying OverpassAPI for buildings.'
        buildings = osm.query_buildings()
        print 'Uploading OSM buildings to Postgres...'
        db.insert_osm(buildings, 'osm_buildings')

    if address_download:
        print 'Querying OverpassAPI for addresses.'
        addresses = osm.query_address()
        print 'Uploading OSM addresses to Postgres...'
        db.insert_osm(addresses, 'osm_addresses')

    if dedupe:
        print 'Getting rid of overlapping address points...'
        db.dedupe_address()

    if roads_download:
        print 'Querying OverpassAPI for highway=* and railway=*.'
        roads = osm.query_roads()
        print 'Uploading OSM highway=* and railway=* to Postgres...'
        db.insert_osm(roads, 'osm_highway_railway')

    if vacuum:
        print 'Updating DB stats.'
        db.update_stats()

    if index:
        print 'Creating multiple indexes.'
        db.create_index()

    if simplify:
        print 'Simplifying import building geometries'
        db.simplify_buildings()

    if add_fields:
        print 'Adding logical fields to import data'
        db.add_fields_input_data()

    if check_address:
        print 'Checking and flagging import addresses near OSM addresses...'
        db.check_exitsing_addresses()

    if check_building:
        print 'Checking and flagging import buildings near existing buildings...'
        db. check_existing_buildings()

    if convert_poly:
        print 'Converting closed overpass features to polygon...'
        db.convert_to_poly()

    if assign_address:
        print 'Assigning adresses to import buildings...'
        db.assign_address()

    if check_road_rail:
        print 'Checking and flagging buildings overlapping with highway/railway.'
        db.check_building_highway_railway()

    if report:
        db.print_report()

    print 'Closing DB connection.'
    db.close_db_conn()
