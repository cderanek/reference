import geopandas as gpd
import pandas as pd
import json


# Landcover types based on NLCD classification
LANDSAT_LANDCOVER_TYPES = {
    1: 'Null',
    11: 'Water',
    12: 'Snow',
    21: 'Dev/Open',
    22: 'Dev/LowInt',
    23: 'Dev/MedInt',
    24: 'Dev/HighInt',
    31: 'Barren',
    41: 'DecidForest',
    42: 'EvgForest',
    43: 'MixForest',
    51: 'DwarfScrub',
    52: 'Shrub/Scrub',
    71: 'Grassland',
    72: 'Sedge',
    73: 'Lichens',
    74: 'Moss',
    81: 'Pasture',
    82: 'Crops',
    90: 'WoodyWetlands',
    95: 'EmHerbWetlands'
}


## FIRE ##
file_path = '/Users/cd/Downloads/fullROI_imageReduct_30Scale_1982_2024_formatted.geojson'
save_path = '/Users/cd/Downloads/processed_test.csv'
keep_cols = ['id', 'Event_ID', 'Ig_Date_Formatted', 'Incid_Name', 'Incid_Type', 'BurnBndAc', 'dominant_lc']
reduct_col = 'lsReduct'

# Read in geojson, apply json.loads to convert to dict/lists from str
test_js = gpd.read_file(file_path)[keep_cols.append(reduct_col)]
test_js[reduct_col] = test_js[reduct_col].apply(json.loads)

# explode lsReduct col, which makes a new row for each date for each fire

test_js= test_js.explode('lsReduct')

# merge the unnested lsReduct col with the fire metadata
test_js = pd.concat(
    [test_js[keep_cols].reset_index(drop=True), # preserve fire metadata
     pd.json_normalize(test_js[reduct_col])
     .drop(columns=['type', 'geometry', 'id'])], # expand 1st layer of json col into many cols, but we only care about the resulting properties.vals.groups col
    axis=1)

# merge the fire metadata with the exploded mean/std/count values for each severity
test_js = (test_js
           .drop(columns=["properties.vals.groups"])
           .join(
               test_js["properties.vals.groups"]
               .explode()
               .apply(pd.Series)
               )
           .rename(columns={'properties.timestamp': 'ls_timestamp'})
           )

# create a column with the LC names
test_js['dominant_lc_name'] = test_js['dominant_lc'] .replace(LANDSAT_LANDCOVER_TYPES)

test_js.to_csv(save_path)


## DROUGHT ##
# Read in geojson, apply json.loads to convert to dict/lists from str
file_path = '/Users/cd/Downloads/drive-download-20231121T163400Z-001/elevation_fullROI_drought_2012_2016.geojson'
ELEV_LC_DS = False
LC = False
to_explode = 'vals'
keep_cols = ['id', 'timestamp', 'vals']

test_js = gpd.read_file(file_path)
test_js = gpd.read_file(file_path)[keep_cols]


# merge the unnested lsReduct col with the fire metadata
test_js = pd.concat(
    [test_js[keep_cols].reset_index(drop=True), # preserve fire metadata
     pd.json_normalize(test_js[to_explode])],
    axis=1)

# merge the fire metadata with the exploded mean/std/count values for each severity
test_js = (test_js
           .drop(columns=["vals", 'id'])
           .join(
               test_js["groups"]
               .explode()
               .apply(pd.Series)
               )
           .drop(columns=["groups"])
        )

if ELEV_LC_DS:
    test_js['drought_severity'] = test_js['elev_lc_droughtsev'] % 10 # last digit is drought severity
    test_js['landcover'] = ((test_js['elev_lc_droughtsev'] - test_js['drought_severity']) / 10) % 100 # middle 2 digits are LC
    test_js['elevation'] = (test_js['elev_lc_droughtsev'] - (test_js['elev_lc_droughtsev'] % 1000)) / 1000 # first digit is elevation group
    test_js['landcover_name'] = test_js['landcover'].replace(LANDSAT_LANDCOVER_TYPES)
    
if LC:
    test_js['landcover_name'] = test_js['landcover'].replace(LANDSAT_LANDCOVER_TYPES)

print(test_js)
test_js.to_csv('/Users/cd/Downloads/elev_processed_test.csv')