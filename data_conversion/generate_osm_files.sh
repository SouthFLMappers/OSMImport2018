#!/bin/bash

path=$(pwd)

dsn="PG:dbname=osm_test user=postgres password=postgres host=localhost"

# Find ogr2osm in parent directories
  while [[ "$path" != "" && ! -e "$path/ogr2osm" ]]; do
    path=${path%/*}
  done

ogr2osm_dir="$path/ogr2osm"

echo "DB connection: $dsn"
echo "Translation file: $translation"
echo "ogr2osm dir: $ogr2osm_dir"

if [ "$1" == 'test' ]; then
  echo "Generating test osm files"
  
  mkdir -p test
  out_folder='test'

  python $ogr2osm_dir/ogr2osm.py "$dsn" -t ../translations/mia_address_trans.py -f -o $out_folder"/mia_address_test1.osm" --sql "SELECT hse_num, st_type, zip, mailing_mu, st_name, pre_dir, suf_dir, geom from address_with_condo where in_osm = false and assigned_to_bldg = false and st_within(geom, st_setsrid(st_makeenvelope(-80.42691,25.695398,-80.314335,25.852301), 4326))" --id="-1"
  python $ogr2osm_dir/ogr2osm.py "$dsn" -t ../translations/mia_building_trans.py -f -o $out_folder"/mia_building_test1.osm" --sql "SELECT height, hse_num,st_type, zip, mailing_mu, st_name, pre_dir, suf_dir, road_intersect, geom from building_footprint_2d where in_osm = false and st_within(geom, st_setsrid(st_makeenvelope(-80.42691,25.695398,-80.314335,25.852301), 4326))" --id="-1000000"

  osmconvert $out_folder/mia_building_test1.osm --fake-author -o=$out_folder/mia_building_test1_fake.osm
  osmconvert $out_folder/mia_address_test1.osm --fake-author -o=$out_folder/mia_address_test1_fake.osm 

  osmosis --read-xml $out_folder/mia_building_test1_fake.osm --sort type="TypeThenId" --write-xml $out_folder/mia_building_test1_sort.osm
  osmosis --read-xml $out_folder/mia_address_test1_fake.osm --sort type="TypeThenId" --write-xml $out_folder/mia_address_test1_sort.osm
  osmosis --read-xml $out_folder/mia_building_test1_sort.osm --read-xml $out_folder/mia_building_test1_sort.osm --merge --write-xml $out_folder/mia_merged_test1.osm


    python $ogr2osm_dir/ogr2osm.py "$dsn" -t ../translations/mia_address_trans.py -f -o $out_folder"/mia_address_test2.osm" --sql "SELECT hse_num, st_type, zip, mailing_mu, st_name, pre_dir, suf_dir, geom from address_with_condo where in_osm = false and assigned_to_bldg = false and st_within(geom, st_setsrid(st_makeenvelope(-80.222478,25.834611,-80.109904,25.878328), 4326))" --id="-1"
  python $ogr2osm_dir/ogr2osm.py "$dsn" -t ../translations/mia_building_trans.py -f -o $out_folder"/mia_building_test2.osm" --sql "SELECT height, hse_num,st_type, zip, mailing_mu, st_name, pre_dir, suf_dir, road_intersect, geom from building_footprint_2d where in_osm = false and st_within(geom, st_setsrid(st_makeenvelope(-80.222478,25.834611,-80.109904,25.878328), 4326))" --id="-1000000"

  osmconvert $out_folder/mia_building_test2.osm --fake-author -o=$out_folder/mia_building_test2_fake.osm
  osmconvert $out_folder/mia_address_test2.osm --fake-author -o=$out_folder/mia_address_test2_fake.osm 

  osmosis --read-xml $out_folder/mia_building_test2_fake.osm --sort type="TypeThenId" --write-xml $out_folder/mia_building_test2_sort.osm
  osmosis --read-xml $out_folder/mia_address_test2_fake.osm --sort type="TypeThenId" --write-xml $out_folder/mia_address_test2_sort.osm
  osmosis --read-xml $out_folder/mia_building_test2_sort.osm --read-xml $out_folder/mia_address_test2_sort.osm --merge --write-xml $out_folder/mia_merged_test2.osm



fi

if [ "$1" == 'tract' ]; then
  echo "Generating osm files based on US Census tracts..."
  curr_dir=`pwd`;
  mkdir -p tracts
  out_folder='tracts'

  while IFS='' read -r objectid; do
    # echo  "$objectid"
    output_name=$objectid"_building.osm"
    translation="../translations/mia_building_trans.py"

    # Get buildings
    sql="SELECT height, hse_num,st_type, zip, mailing_mu, st_name, pre_dir, suf_dir, road_intersect, b.geom from building_footprint_2d b, tracts t where b.in_osm = false and st_within(b.geom, t.geom) and t.objectid = $objectid"
    python $ogr2osm_dir/ogr2osm.py "$dsn" -t $translation -f -o $out_folder"/"$output_name --sql "$sql" --id="-1"

    # Get address
    translation="../translations/mia_address_trans.py"
    output_name=$objectid"_address.osm"
    sql="SELECT hse_num, st_type, zip, mailing_mu, st_name, pre_dir, suf_dir, a.geom from address_with_condo a, tracts t where a.in_osm = false and a.assigned_to_bldg = false and st_within(a.geom, t.geom) and t.objectid = $objectid"
    python $ogr2osm_dir/ogr2osm.py "$dsn" -t $translation -f -o $out_folder"/"$output_name --sql "$sql" --id="-1000000"

    # Fake version, timestamps
    osmconvert $out_folder"/"$objectid"_building.osm" --fake-author -o=$out_folder"/"$objectid"_building_fake.osm"
    osmconvert $out_folder"/"$objectid"_address.osm" --fake-author -o=$out_folder"/"$objectid"_address_fake.osm"

    # Sort and merge
    osmosis --read-xml $out_folder"/"$objectid"_address_fake.osm" --sort type="TypeThenId" --write-xml $out_folder"/"$objectid"_address_sort.osm"
    osmosis --read-xml $out_folder"/"$objectid"_building_fake.osm" --sort type="TypeThenId" --write-xml $out_folder"/"$objectid"_building_sort.osm"
    osmosis --read-xml $out_folder"/"$objectid"_building_sort.osm" --read-xml $out_folder"/"$objectid"_address_sort.osm" --merge --write-xml $out_folder"/mia_"$objectid".osm"

    # Cleanup
    rm $out_folder"/"$objectid"_building.osm" $out_folder"/"$objectid"_building_fake.osm" $out_folder"/"$objectid"_building_sort.osm" $out_folder"/"$objectid"_address.osm" $out_folder"/"$objectid"_address_fake.osm" $out_folder"/"$objectid"_address_sort.osm"

    done < $curr_dir/"tract_objectids.csv"

    echo '\nGenerating extra osm files for special cases...\n'
    # Get buildings outside blocks

    # output_name="building_outside.osm"
    # translation="mia_building_trans.py"

    # sql="SELECT b.height, b.objectid, b.geom from buildings_overlap b, (select st_union(geom) as geom from block_groups_2010) block where not st_intersects(b.geom, block.geom)"
    # python $ogr2osm_dir/ogr2osm.py "$dsn" -t $translation -f -o $out_folder"/"$output_name --sql "$sql" --id="-1"

    # # Get address
    # translation="mia_address_trans.py"
    # output_name="address_outside.osm"

    # sql="SELECT a.objectid, zip, mailing_mu as city, pre_dir, st_name, st_type, suf_dir, hse_num as house_num, a.geom from address a,
    #     (SELECT b.geom from buildings_overlap b, (select st_union(geom) as geom from block_groups_2010) block where
    #     not st_intersects(b.geom,block.geom)) x where st_within(a.geom, x.geom)"
    # python $ogr2osm_dir/ogr2osm.py "$dsn" -t $translation -f -o $out_folder"/"$output_name --sql "$sql" --id="-20001"

    # # Fake version, timestamps
    # osmconvert $out_folder"/building_outside.osm" --fake-author -o=$out_folder"/building_outside_fake.osm"
    # osmconvert $out_folder"/address_outside.osm" --fake-author -o=$out_folder"/address_outside_fake.osm"

    # # Sort and merge
    # osmosis --read-xml $out_folder"/address_outside_fake.osm" --sort type="TypeThenId" --write-xml $out_folder"/address_outside_sort.osm"
    # osmosis --read-xml $out_folder"/building_outside_fake.osm" --sort type="TypeThenId" --write-xml $out_folder"/building_outside_sort.osm"
    # osmosis --read-xml $out_folder"/building_outside_sort.osm" --read-xml $out_folder"/address_outside_sort.osm" --merge --write-xml $out_folder"/outside.osm"

    # # Get buildings overlapping with block boundaries (i.e. share space with 2 blocks)

    # output_name="building_border.osm"
    # translation="mia_building_trans.py"

    # sql="SELECT b.height, b.objectid, b.geom from buildings_overlap b, (select geom as geom from block_groups_2010) block where st_overlaps(b.geom, block.geom) and not st_within(b.geom, block.geom)"
    # python $ogr2osm_dir/ogr2osm.py "$dsn" -t $translation -f -o $out_folder"/"$output_name --sql "$sql" --id="-1"

    # # Get address
    # translation="mia_address_trans.py"
    # output_name="address_border.osm"

    # sql="SELECT a.objectid, zip, mailing_mu as city, pre_dir, st_name, st_type, suf_dir, hse_num as house_num, a.geom from address a,
    #     (SELECT b.geom from buildings_overlap b, (select geom as geom from block_groups_2010) block where
    #      st_overlaps(b.geom, block.geom) and not st_within(b.geom, block.geom)) x where st_within(a.geom, x.geom)"
    # python $ogr2osm_dir/ogr2osm.py "$dsn" -t $translation -f -o $out_folder"/"$output_name --sql "$sql" --id="-20001"

    # # Fake version, timestamps
    # osmconvert $out_folder"/building_border.osm" --fake-author -o=$out_folder"/building_border_fake.osm"
    # osmconvert $out_folder"/address_border.osm" --fake-author -o=$out_folder"/address_border_fake.osm"

    # # Sort and merge
    # osmosis --read-xml $out_folder"/address_border_fake.osm" --sort type="TypeThenId" --write-xml $out_folder"/address_border_sort.osm"
    # osmosis --read-xml $out_folder"/building_border_fake.osm" --sort type="TypeThenId" --write-xml $out_folder"/building_border_sort.osm"
    # osmosis --read-xml $out_folder"/building_border_sort.osm" --read-xml $out_folder"/address_border_sort.osm" --merge --write-xml $out_folder"/border.osm"

    #  # Cleanup
    #   rm $out_folder"/building_border.osm" $out_folder"/building_border_fake.osm" $out_folder"/building_border_sort.osm" $out_folder"/address_border.osm" $out_folder"/address_border_fake.osm" $out_folder"/address_border_sort.osm" $out_folder"/building_outside.osm" $out_folder"/building_outside_fake.osm" $out_folder"/building_outside_sort.osm" $out_folder"/address_outside.osm" $out_folder"/address_outside_fake.osm" $out_folder"/address_outside_sort.osm"

fi
