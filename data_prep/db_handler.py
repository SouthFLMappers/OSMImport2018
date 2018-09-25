import psycopg2
import psycopg2.extras
import requests
from osm_handler import get_outer_way

class DBHandler():
    def __init__(self, dsn):
        pg_host = 'localhost'
        pg_port = 5432
        pg_user = 'postgres'
        pg_pass = 'postgres'
        pg_db = 'osm_test'

        # Extent of Large Building Footprints dataset
        self.bbox = '25.23561, -80.87864, 25.97467, -80.11845'
        # Downtown MIA
        self.bbox = '25.770098, -80.200582,25.780107,-80.185132'

        if dsn is not None:
            self.conn = psycopg2.connect(dsn)
        else:
            self.conn = psycopg2.connect(
                    host=pg_host,
                    port=pg_port,
                    user=pg_user,
                    password=pg_pass,
                    dbname=pg_db)
        try:
            psycopg2.extras.register_hstore(self.conn)
        except:
            print 'Could not register hstore. Are you running it for the first time (no hstore data in DB). You should be OK next time though.'
        self.cursor = self.conn.cursor()

    def close_db_conn(self):
        self.conn.close()

    def setup_db(self):
        create_extension_sql = '''
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE EXTENSION IF NOT EXISTS hstore;
        '''
        create_building_table_sql = '''
            CREATE TABLE IF NOT EXISTS osm_buildings (
                id bigint,
                type varchar,
                tags hstore,
                constraint pk_building_id_type primary key (id, type)
            );
        -- Use generic GEOMETRY type so we can store nodes and ways together
            ALTER TABLE osm_buildings drop column IF EXISTS geom;
            SELECT AddGeometryColumn('osm_buildings', 'geom', 4326, 'GEOMETRY', 2);
        '''
        create_highway_railway_table_sql = '''
            CREATE TABLE IF NOT EXISTS osm_highway_railway (
                id bigint,
                type varchar,
                tags hstore,
                constraint pk_road_id_type primary key (id, type)
            );
        -- Use generic GEOMETRY type so we can store nodes and ways together
            ALTER TABLE osm_highway_railway DROP COLUMN IF EXISTS geom;
            SELECT AddGeometryColumn('osm_highway_railway', 'geom', 4326, 'GEOMETRY', 2);
        '''
        create_address_table_sql = '''
            CREATE TABLE IF NOT EXISTS osm_addresses (
                id bigint,
                type varchar,
                tags hstore,
                constraint pk_address_id_type primary key (id, type)
            );
            ALTER TABLE osm_addresses DROP COLUMN IF EXISTS geom;
            SELECT AddGeometryColumn('osm_addresses', 'geom', 4326, 'GEOMETRY', 2);
        '''

        populate_geom_sql = 'select Populate_Geometry_Columns();'

        self.cursor.execute(create_extension_sql)
        self.cursor.execute(create_building_table_sql)
        self.cursor.execute(create_address_table_sql)
        self.cursor.execute(create_highway_railway_table_sql)
        self.cursor.execute(populate_geom_sql)
        self.conn.commit()

    def create_index(self):
        building_index_sql = 'CREATE INDEX osm_building_geom_idx ON osm_buildings USING GIST (geom);'
        address_index_sql = 'CREATE INDEX osm_address_geom_idx ON osm_addresses USING GIST (geom);'
        highway_index_sql = 'CREATE INDEX osm_highway_railway_geom_idx ON osm_highway_railway USING GIST (geom);'
        address_county_index_sql = 'CREATE INDEX address_geom_idx ON address_with_condo USING GIST (geom);'
        building_county_index_sql = 'CREATE INDEX building_geom_idx ON building_footprint_2d USING GIST (geom)'
        self.cursor.execute(building_index_sql)
        self.cursor.execute(address_index_sql)
        self.cursor.execute(highway_index_sql)
        self.conn.commit()

    def update_stats(self):
        old_isolation_level = self.conn.isolation_level
        self.conn.set_isolation_level(0)
        self.cursor.execute('VACUUM ANALYZE')
        self.conn.set_isolation_level(old_isolation_level)
        self.conn.commit()

    def dedupe_address(self):
        dedupe_tmp_sql = '''CREATE TABLE address_tmp AS
                                        SELECT DISTINCT ON (geom) * FROM address_with_condo;
        '''
        dedupe_drop_old_sql = "drop table address_with_condo;"
        dedupe_rename_sql = "alter table address_tmp rename to address_with_condo;"
        dedupe_populate_geom_sql = 'select Populate_Geometry_Columns();'
        dedupe_index_sql = 'create index address_county_geom_idx on address_with_condo using gist (geom);'
        self.cursor.execute(dedupe_tmp_sql)
        self.cursor.execute(dedupe_drop_old_sql)
        self.cursor.execute(dedupe_rename_sql)
        self.conn.commit()
        self.cursor.execute(dedupe_populate_geom_sql)
        self.cursor.execute(dedupe_index_sql)
        self.conn.commit()
        #self.cursor.execute('vacuum analyze;')

    def insert_osm(self, data, table):
        i = 0
        sql_pre = 'INSERT INTO %s ' % table
        sql =  sql_pre + '(id, type, tags, geom) VALUES (%s, %s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326));'
        for el in data['elements']:
            if 'railway' in el['tags'].keys():
                if el['tags']['railway'] == 'abandoned':
                    continue
            if 'highway' in el['tags'].keys():
                if el['tags']['highway'] == 'abandoned':
                    continue
            if i % 10000 == 0:
                print '%s: %s/%s' % (table, i, len(data['elements']))
            i += 1
    #        print building
    #        print el['type'],  el['id']
            if el['type'] == 'node':
                self.cursor.execute(sql, (el['id'], el['type'], el['tags'], 'POINT (' + str(el['lon']) + ' ' + str(el['lat']) + ')'))
            # Upload them as Linestring 
            if el['type'] == 'way':
                geom = 'LINESTRING ('
                try:
                    geom += self.build_wkt_coord_list(el['geometry'])
                    geom += ')'
                    self.cursor.execute(sql, (el['id'], el['type'],  el['tags'], geom))
                except KeyError:
                    continue
                    
            # Safe to assume relations are polygons but let's stick to Linestrings. Use only outer as we're interested in spatial overlaps.
            if el['type'] == 'relation':
                geom = 'LINESTRING('
                membercnt = 0
                for member in el['members']:
                    if member['role'] == 'outer':
                        membercnt += 1
                if membercnt > 1:
                    # it's already been returned if there's no bounds... passing
                    try:
                        bounds = el['bounds']
                    except KeyError:
                        continue
                    lower_left = str(bounds['minlon']) + ' ' + str(bounds['minlat'])
                    lower_right = str(bounds['maxlon']) + ' ' + str(bounds['minlat'])
                    upper_right = str(bounds['maxlon']) + ' ' + str(bounds['maxlat'])
                    upper_left = str(bounds['minlon']) + ' ' + str(bounds['maxlat'])
                    geom = 'POLYGON((' + lower_left + ',' + lower_right + ',' + upper_right + ',' + upper_left + ',' + lower_left + '))'
                else:
                    print el['id'], el['type']
                    for member in el['members']:
                        if member['role'] == 'outer':
                            geom += self.build_wkt_coord_list(get_outer_way(member['ref'])['geometry'])
                    geom += ')'
                if geom == 'LINESTRING()':
                    print 'geometry error with %s id: %s. geom: %s' % (el['type'], str(el['id']), geom)
                    continue
                self.cursor.execute(sql, (el['id'], el['type'],  el['tags'], geom))
            # Upload bounds if it's a multipolygon
            if el['type'] == 'multipolygon':
                bounds = el['bounds']
                lower_left = str(bounds['minlon']) + ' ' + str(bounds['minlat'])
                lower_right = str(bounds['maxlon']) + ' ' + str(bounds['minlat'])
                upper_right = str(bounds['maxlon']) + ' ' + str(bounds['maxlat'])
                upper_left = str(bounds['minlon']) + ' ' + str(bounds['maxlat'])
                geom = 'POLYGON((' + lower_left + ',' + lower_right + ',' + upper_right + ',' + upper_left + ',' + lower_left + '))'
                self.cursor.execute(sql, (el['id'], el['type'],  el['tags'], geom))
        self.conn.commit()

    def build_wkt_coord_list(self, geometry):
        i = 0
        coord_list = ''
        for node in geometry:
            if i > 0:
                coord_list += ', '
            coord_list += str(node['lon']) + ' ' + str(node['lat'])
            i += 1
        return coord_list

    def convert_to_poly(self):
        self.cursor.execute("update osm_addresses set geom = st_buildarea(geom) where st_geometrytype(geom)  != 'ST_Point'")
        self.cursor.execute("update osm_buildings set geom = st_buildarea(geom) where st_geometrytype(geom)  != 'ST_Point'")
        self.conn.commit()

    def simplify_buildings(self):
        # Simplify geometry using 0.3m tolerance (get rid of unnecesary nodes
        self.cursor.execute("update osm_buildings set geom = st_transform(st_simplify(st_transform(geom, 3857), 0.3), 4326) where st_geometrytype(geom) != 'ST_Point'")
        self.connection.commit()

    def add_fields_input_data(self):
        self.cursor.execute('alter table address_with_condo drop column if exists in_osm')
        self.cursor.execute('alter table address_with_condo add column in_osm boolean')
        self.cursor.execute('update address_with_condo set in_osm = false')
        self.cursor.execute('alter table building_footprint_2d drop column if exists in_osm')
        self.cursor.execute('alter table building_footprint_2d add column in_osm boolean')
        self.cursor.execute('update building_footprint_2d set in_osm = false')
        
        self.cursor.execute('''alter table building_footprint_2d
                                                    add column addr_assigned boolean,
                                                    add column zip int,
                                                    add column mailing_mu varchar,
                                                    add column hse_num int,
                                                    add column pre_dir varchar,
                                                    add column suf_dir varchar,
                                                    add column st_type varchar,
                                                    add column st_name varchar;
                                        update building_footprint_2d set addr_assigned = false;
                                        alter table address_with_condo add column assigned_to_bldg boolean;
                                        update address_with_condo set assigned_to_bldg = false; 
                                            ''')
        self.conn.commit()

    def check_exitsing_addresses(self):
        self.cursor.execute('''
                        update address_with_condo county
                            set in_osm = True
                            from 
                                (select * from osm_addresses where st_geometrytype(geom) = 'ST_Polygon') osm 
                            where 
                                st_within(county.geom, osm.geom) and county.hse_num = (osm.tags->'addr:housenumber')::numeric
        ''')
        self.connection.commit()
        self.cursor.execute('''
                        update address_with_condo county
                            set in_osm = True
                            from osm_addresses osm 
                            where
                                st_dwithin(county.geom::geography, osm.geom::geography, 20) and county.hse_num = (osm.tags->'addr:housenumber')::numeric
        ''')
        self.connection.commit()

    def check_existing_buildings(self):
        self.cursor.execute('''
            update building_footprint_2d county
                set in_osm = True
                from osm_buildings osm 
                where
                    st_intersects(county.geom, osm.geom)
        ''')
        self.conn.commit()

    def assign_address(self):
        self.cursor.execute('''
        -- update buildings where there's only one address point within
            update building_footprint_2d
            set
                zip = x.zip,
                mailing_mu = x.mailing_mu,
                hse_num = x.hse_num,
                st_name = x.st_name,
                st_type = x.st_type,
                pre_dir = x.pre_dir,
                suf_dir = x.suf_dir,
				addr_assigned = true
            from (select b.objectid as building_id, a.hse_num, a.sname, a.mailing_mu, a.zip, num_address.count as count_addresses, a.pre_dir, a.suf_dir, a.st_name, a.st_type
                from
                    building_footprint_2d b,
                    address_with_condo a,
                    -- Get number of addresses within each large building
                    (select building.objectid as building_id, count(a.objectid) 
                    	from 
                            building_footprint_2d building,
                        	address_with_condo a
                   		where
                        	st_within(a.geom, building.geom) and building.in_osm = false
                    	group by building_id) num_address
 				where
                    b.objectid = num_address.building_id and
                    num_address.count = 1 and
                    b.geom && a.geom and
                    st_within(a.geom, b.geom)
            ) x
			where
                building_footprint_2d.objectid = x.building_id
        ''')
        self.conn.commit()
        self.cursor.execute('''
            update address_with_condo a
            set
                assigned_to_bldg = true
            from (select geom from building_footprint_2d where addr_assigned = true) b
            where 
                st_within(a.geom, b.geom )
        ''')
        self.conn.commit()
        self.cursor.execute('''
        -- update buildings where they are close
            update building_footprint_2d
            set
                zip = x.zip,
                mailing_mu = x.mailing_mu,
                hse_num = x.hse_num,
                st_name = x.st_name,
                st_type = x.st_type,
                pre_dir = x.pre_dir,
                suf_dir = x.suf_dir,
				addr_assigned = true
            from (select b.objectid as building_id, a.hse_num, a.sname, a.mailing_mu, a.zip, num_address.count as count_addresses, a.pre_dir, a.suf_dir, a.st_name, a.st_type
                from
                    building_footprint_2d b,
                    address_with_condo a,
                    -- Get number of addresses within each large building
                    (select building.objectid as building_id, count(a.objectid) 
                    	from 
                        	building_footprint_2d building,
                        	address_with_condo a
                   		where
							(building.addr_assigned = false and building.in_osm = false) and (a.assigned_to_bldg is false and a.in_osm = false) and 
                        	st_dwithin(a.geom::geography, building.geom::geography, 5)
                    	group by building_id) num_address
 				where
                    b.objectid = num_address.building_id and
                    num_address.count = 1 and
                    b.geom && a.geom and
                    st_dwithin(a.geom::geography, b.geom::geography, 5)
            ) x
			where
                building_footprint_2d.objectid = x.building_id
        ''')
        self.conn.commit()
        self.cursor.execute('''
            update address_with_condo a
            set
                assigned_to_bldg = true
            from (select geom from building_footprint_2d where addr_assigned = true) b
            where 
                a.assigned_to_bldg = false and 
                st_dwithin(a.geom::geography, b.geom::geography, 5 )
        ''')
        self.conn.commit()

    def check_building_highway_railway(self):
        self.cursor.execute('''
        update building_footprint_2d b
            set
                road_intersect = true
            from osm_highway_railway r
            where
                st_intersects(b.geom, r.geom) and (
                            (not (exist(tags, 'highway') and tags->'highway' = 'abandoned')) and
                            (not (exist(tags,'railway') and tags->'railway' = 'abandoned')) and
                            not exist(tags, 'abandoned:highway') and
                            not exist(tags, 'abandoned:railway'));
        ''')
        self.conn.commit()

    def print_report(self):
        self.cursor.execute('select count(objectid) from address_with_condo')
        total_address = self.cursor.fetchone()[0]
        self.cursor.execute('select count(objectid) fromb building_footprint_2d')
        total_bldg = self.cursor.fetchone()[0]
        self.cursor.execute('select count(objectid) from building_footprint_2d where in_osm = false')
        new_bldg  = self.cursor.fetchone()[0]
        self.cursor.execute('select count(objectid) from building_footprint_2d where in_osm = false and assigned_address = true')
        bldg_assigned_address = self.cursor.fetchone()[0]
        self.cursor.execute('select count(objectid) from building_footprint_2d where in_osm = false and highway_intersect = true')
        bldg_highway = self.cursor.fetchone()[0]
        self.cursor.execute('select count(objectid) from building_footprint_2d where in_osm = false and assigned_to_bldg = false')
        new_addr = self.cursor.fetchone()[0]


        text = '''
        ----------------------- QUICK REPORT -----------------------
        ------------------------------------------------------------
        Total # of unique addresses (county):                   %s
        Total # of buildings (county):                          %s
        New buildings to import:                                %s
        New buildings with address:                             %s
        New buildings crossing highway/railway (fixme):         %s
        New addr: points to import:                             %s
        ------------------------------------------------------------
        '''
        print text % (total_address, total_bldg, new_bldg, bldg_assigned_address, bldg_highway, new_address)
