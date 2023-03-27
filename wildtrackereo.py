'''
Code dedicated to the solution proposed at EMODnet Hackathon 2023

______ WILDLIFE TRACKER EO ______ 

Generate zones that support the MPA management delimitation with 
wildlife hotspots in a spatiotemporal perspective.

Input:
 - Biologging data with SST behavioral parameters
 - Water column temperature (SST) from EMODnet
 - MPA EU
 - Fishing Effort (to future development)

Output:
 - Ecological Zones at monthly level dedicated as wildlife hotspots

Author:
Bryan R. Vallejo
gis4 wildlife movement analytics
'''


import geopandas as gpd
import pandas as pd
import os

root = os.getcwd()

if not os.path.exists('output'):
    os.makedirs('output')


## ________________ BEHAVIORAL PARAMETERS PER INDIVIDUAL PER MONTH ____________________ 

wildlife = pd.read_csv(r'data\biologging\eco_annotation_Sea Surface Temperature.csv', sep=';', index_col='index')
wildlife = wildlife[['timestamp', 'location_long', 'location_lat', 'wild_id', 'prev_lon', 'prev_lat', 'eco_time', 'eco_celsius']]

# add unique month
wildlife['month'] = [time[:7] for time in wildlife.timestamp]

# info
print(f'\n[BEHAVIOR] Total n individuals: {wildlife.wild_id.nunique()}')
print(f'[BEHAVIOR] Prefered temperature at median: {wildlife.eco_celsius.median()}\n')

# monthly parameters per individual
individuals_eco_parameters = pd.DataFrame()

# months per individual
for individual in wildlife.wild_id.unique():    
    
    # subset
    wild = wildlife.loc[wildlife.wild_id==individual]
    
    print(f'[INDIVIDUAL] ID: {individual}')    
    print(f'[INDIVIDUAL] Timerange: {wild.timestamp.min()} to {wild.timestamp.max()}')

    
    for month in wild.month.unique():
        
        key = individual + '_' + month
        
        # monthly subset per individual
        wild_period = wild.loc[wild.month==month]
        
        # add month and individual
        individuals_eco_parameters.at[key, 'wild_id'] = key.split('_')[0]
        individuals_eco_parameters.at[key, 'month'] = key.split('_')[1]
        
        # eco parameters
        individuals_eco_parameters.at[key, 'eco_median'] = wild_period.eco_celsius.median()
        
        individuals_eco_parameters.at[key, 'eco_mean'] = wild_period.eco_celsius.mean()
        
        individuals_eco_parameters.at[key, 'eco_std'] = wild_period.eco_celsius.std()
        
        print(f'[INDIVIDUAL] Eco-habitat: {month} -> {wild_period.eco_celsius.median()}')

    print('\n')

print(individuals_eco_parameters)
individuals_eco_parameters.to_csv('output/eco_parameters_per_individual_monthly.csv', index=False)


# ____________________ MONTHLY ECO-GEOGRAPHICAL ZONING ____________________________ 

# for SST: 2009.09, 2009.06, 2009.07, 2009.08, 2010.05, 2010.06, 2010.07

print(f'\n____ Monthly zoning ____\n')

# all individual, monthly, zoning
eco_zoning = pd.DataFrame()

# create path of monthly data
for month in individuals_eco_parameters.month.unique():
    
    # path EO - monthly
    path_eo = os.path.join(root, f'data/emodnet/water_surface_temperature_{month}-15.csv')
    
    # read eo
    sst = pd.read_csv(path_eo)
        
    print(f'[ZONING] Month: {month}')
    
    # catch unique individuals per month
    eco_wild = individuals_eco_parameters.loc[individuals_eco_parameters.month==month]
    
    for eco_individual in eco_wild.wild_id.unique():
        
        key = eco_individual + '_' + month
        
        # parameters
        eco_parameter = eco_wild.at[key, 'eco_mean']
        eco_std = eco_wild.at[key, 'eco_std']
        
        # individual bounds
        traj = wildlife.loc[(wildlife.wild_id==eco_individual) & (wildlife.month==month)]
        
        gdf = gpd.GeoDataFrame(traj, geometry=gpd.points_from_xy(traj.location_lat, traj.location_long), crs=4326)
        
        bounds = gdf.total_bounds
        
        print(f'[ZONING] ID: {eco_individual} -> Celsius: {eco_parameter}')
        # print(f'[BOUNDS] {bounds}')
        # minx, miny, maxx, maxy
                
        # ____ SST ____
        eco_sst = sst.loc[(sst.latitude> bounds[0]) & (sst.latitude< bounds[2])]
        eco_sst = eco_sst.loc[(eco_sst.longitude> bounds[1]) & (eco_sst.longitude< bounds[3])]
        eco_sst = eco_sst.loc[(eco_sst.TEMP>=eco_parameter-eco_std) & (eco_sst.TEMP<=eco_parameter+eco_std)]
        
        # apply hotspot 80%
        print(f'[HOTSPOTS] 80% concentration\n')
        percentile = eco_sst['TEMP'].quantile(0.8)
        eco_sst = eco_sst.loc[eco_sst['TEMP']>=percentile]
        
        eco_sst['wild_id'] = eco_individual
        eco_sst['month'] = month
        
        
        eco_sst.to_csv(f'output/eco_zoning_wildlife_eo_{eco_individual}_{month}.csv', index=False)



##end
