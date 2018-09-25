import requests
import json

class OSMHandler():
    def __init__(self, bbox):
        self.overpassAPI = 'http://overpass-api.de/api/interpreter'
        # Alternatively, use the French instance: overpassAPI = 'http://api.openstreetmap.fr/oapi/interpreter/'

        if bbox is not None:
            self.bbox = bbox
        else:
            # Test area
            self.bbox = '25.770098, -80.200582,25.780107,-80.185132'
            self.bbox= '25.757413,-80.207625,25.775658,-80.1876'
            # Extent of address dataset
            self.bbox = '25.2672765809675,-80.6460812102679, 25.9750071473187,-80.1187632511064'

    def query_buildings(self):
        postdata = '''
            [out:json][bbox:%s][timeout:180];
            (
              node["building"];
              relation["building"];
              way["building"];
            );
            out geom;
            >;
            '''
        data = requests.post(self.overpassAPI, postdata % (self.bbox), timeout=180)
        try:
            data = json.loads(data.text)
        except:
            print 'Something went wrong when querying OverpassAPI (timeout, no json, etc.). Try it again bit later.'
        return data

    def query_address(self):
        postdata = '''
        [out:json][bbox:%s][timeout:180];
        (
          node["addr:housenumber"];
          way["addr:housenumber"];
          relation["addr:housenumber"];
        );
        out geom;
        >;
        '''
        data = requests.post(self.overpassAPI, postdata % (self.bbox), timeout=180)
        try:
            data = json.loads(data.text)
        except:
            print 'Something went wrong when querying OverpassAPI (timeout, no json, etc.). Try it again bit later.'
        return data

    def query_roads(self):
        postdata = '''
        [out:json][bbox:%s][timeout:120];
            (
              relation["highway"];
              way["highway"];
              relation["railway"];
              way["railway"];
            );
            out geom;
            >;
        '''
        data = requests.post(self.overpassAPI, postdata % (self.bbox))
        try:
            data = json.loads(data.text)
        except:
            print 'Something went wrong when querying OverpassAPI (timeout, no json, etc.). Try it again bit later.'
        return data

def get_outer_way(id):
    overpassAPI = 'http://overpass-api.de/api/interpreter'
    # Alternatively, use the French instance: overpassAPI = 'http://api.openstreetmap.fr/oapi/interpreter/'
    print 'multi: %s' % id
    postdata = '''
    [out:json][timeout:30];
    (
        way(%s);
    );
    out geom;
    >;
    '''
    try:
        data = requests.post(overpassAPI, postdata % (id), timeout=30)
        data = json.loads(data.text)
        return data['elements'][0]
    # Upload something to null island if OverpassAPI fails (timeout, no json, etc.)
    # TODO: create function to update FIXME features later
    except:
        return {
                "type": "way",
                "id": id,
                "bounds": {
                "minlat": 0,
                "minlon": 0,
                "maxlat": 0,
                "maxlon": 0
                },
                "nodes": [
                ],
                "geometry": [
                    {"lat": 0, "lon": 0 },
                    {"lat": 0, "lon": 0 }
                ],
                "tags": {
                    "type": "FIXME"
                }
            }
