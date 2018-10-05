# Miami-Dade County Address + Building (+POI?) Import


Software tools and technical description of the Miami-Dade OSM import in 2018

Largely based on the [2016 Large Building Import](https://github.com/jlevente/MiamiOSM-buildings). Tool/documentation still **under construction**.


## Prerequisites 


Python 2.7.

Install `PostgreSQL` with `PostGIS` on your system. You can find some help [here](http://wiki.openstreetmap.org/wiki/PostGIS/Installation#).

You will also need the [`psycopg2`](http://initd.org/psycopg/docs/install.html#install-from-package) and `requests` python packages.

Install osmosis with `apt-get install osmosis` on Ubuntu/Debian (other platforms see http://wiki.openstreetmap.org/wiki/Osmosis/Installation).

Install `GDAL/OGR` for your system. Used for importing shapefiles to Postgres with `ogr2ogr`.

PLUS `osmconvert`, `ogr2osm`, ...

Download the data files from here:
```
Building Footprint 2D - http://gis-mdc.opendata.arcgis.com/datasets/building-footprint-2d
Address with condo - http://gis-mdc.opendata.arcgis.com/datasets/address-with-condo?geometry=-82.952%2C25.187%2C-77.854%2C26.054
Census Tracts - http://gis-mdc.opendata.arcgis.com/datasets/tract-2010
```

## Data preparation

- Create a PostgreSQL database and make sure user 'postgres' with the password 'postgres' has access to it.  Until the code is cleaned, `osm_test` is hardcoded in some cases. We will make the code base f more flexible so that it can be easily used for other imports.
- Set up the DB (extensions, tables)
```
python data_prep/main.py --setup
```

### Get the data

- Import shapefiles to db. (I store the shapefiles in a folder called data. Pass it as the first argument) to the following shell script. This step uses `ogr2ogr` to populate the `address_with_condo` and `building_footprint_2d` tables in Postgres.
```
./data_prep/import_shapefiles.sh data
```


The following steps import current OSM data to the same database.
- Grab OSM buildings from OverpassAPI (store them in osm_buildings table)
```
python data_prep/main.py --buildings_download
```
- Grab OSM Addresses from OverpassAPI (osm_addresses table)
```
python data_prep/main.py --address_download
```
- Grab OSM highways/railways from OverpassAPI (osm_highway_railway)
```
python data_prep/main.py --roads_download

```
### Prepare the data for processing/conversion

- Get rid of duplicate addresses in the import dataset (i.e. condo units).
```
python data_prep/main.py --dedupe_address
```
- Add some extra fields to tables.
```
python data_prep/main.py --add_fields
```
- Convert closed linestrings from Overpass to Polygon
```
python data_prep/main.py --convert_poly
```
- Create spatial indexes to ensure that spatial queries are effective. Update databaes statistics.
```
python data_prep/main.py --index_data
python data_prep/main.py --vacuum
```

## Data processing

- Check import addresses against OSM adddresses. Flag those in the proximity of existing addresses and exclude them.
```
python data_prep/main.py --check_address
```
- Check import buildings against OSM buildings. Flag those intersecting with existing buildings and exlude them.
```
python data_prep/main.py --check_building
```
- Check buildings crossing highway and railway features. Add `fixme=highway/railway crosses building`
```
python data_prep/main.py --check_road_rail
```
- Assign address to buildings where there is only one overlapping address point (or there is only one within 5 meters)
```
python data_prep/main.py --assign_address
```


## Data conversion

- Get rid of unnecessary nodes using the Douglas-Peucker algorithm (tolerance: 0.3 meters)
```
python data_prep/main.py --simplify
```

- Clone `ogr2osm` in parent directory
```
cd ..
git clone --recursive https://github.com/pnorman/ogr2osm
```

- Navigate back to the project folder
- Generate test datasets. Data files for all tract polygons: use `tract`
```
cd data_conversion
./generate_osm_files.sh test
```
