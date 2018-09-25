#!/bin/bash

echo 'Importing building footprints...'
ogr2ogr -f "PostgreSQL" "PG:host=localhost user=postgres password=postgres dbname=osm_test" -lco GEOMETRY_NAME=geom $1"/Building_Footprint_2D.shp" -nlt PROMOTE_TO_MULTI

echo 'Importing Address dataset...'
ogr2ogr -f "PostgreSQL" "PG:host=localhost user=postgres password=postgres dbname=osm_test" -lco GEOMETRY_NAME=geom $1"/Address_With_Condo.shp"

echo 'Importing US Census Tracts...'
 ogr2ogr -f "PostgreSQL" "PG:host=localhost user=postgres password=postgres dbname=osm_test" -progress -nln tracts -lco GEOMETRY_NAME=geom $1"/Tract_10_Aligned_Feature_Layer.shp"