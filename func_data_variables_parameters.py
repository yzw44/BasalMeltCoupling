from pathlib import Path

import numpy as np
import xarray as xr

### Function definitions ######################################################

def full_data_paths(DataDir, MIP, ModelList, EXP, VAR):
    '''Provides a list of full paths to CMIP6 data'''
    
    if VAR == 'areacello':
        version = 'Version'
        var_type = 'Ofx'
        if EXP == '1pctCO2':
            MIP = 'CMIP'
        if EXP == 'historical':
            MIP = 'CMIP'
    else:
        version = EXP+'_Version'
        var_type = 'Omon'
    
#     DataPath = (DataDir+MIP+'/'+ModelList.Center+'/'+ModelList.Model+
#                 '/'+EXP+'/'+ModelList.Ensemble+'/'+var_type+'/'+VAR+'/'+
#                 ModelList.Grid+'/'+ModelList[version])
    DataPath = (f'{DataDir}{MIP}/{ModelList.Center}/{ModelList.Model}'+
                f'/{EXP}/{ModelList.Ensemble}/{var_type}/{VAR}/'+
                f'{ModelList.Grid}/{ModelList[version]}')
    print('Looking for files there:')
    print(DataPath)
    p = Path(DataPath)
    all_files = sorted(p.glob('*'+VAR+'*.nc'))
    return all_files

def sel_mask(ds, sector):
    '''select coordinate names before selecting antarctic ocean sector'''
    #if ds.source_id == 'IPSL-CM6A-LR':
    #    lat='nav_lat'
    #    lon='nav_lon'
    #    mask = mask_sector(ds,sector,lat,lon)
    #else:
    try: 
        lat='latitude'
        lon='longitude'
        mask = mask_sector(ds,sector,lat,lon)
    except:
        lat='lat'
        lon='lon'
        mask = mask_sector(ds,sector,lat,lon) 
    return mask

def mask_sector(ds,sector,lat,lon):
    '''select mask of sector'''
    mask_eais = (
        (ds.coords[lat] > -76)
        & (ds.coords[lat] < -65)
        & (ds.coords[lon] < 173)
    ) + (
        (ds.coords[lat] > -76)
        & (ds.coords[lat] < -65)
        & (ds.coords[lon] > 350) 
    )
    
    mask_wedd = (
        (ds.coords[lat] < -72)
        & (ds.coords[lon] > 295)
        & (ds.coords[lon] < 350)
    )
    
    mask_amun = (
        (ds.coords[lat] < -70)
        & (ds.coords[lon] > 210)
        & (ds.coords[lon] < 295)
    )
    
    mask_ross = (
        (ds.coords[lat] < -76)
        & (ds.coords[lon] > 150)
        & (ds.coords[lon] < 210)
    ) 
    
    mask_apen = (
        (ds.coords[lat] > -70)
        & (ds.coords[lat] < -65)
        & (ds.coords[lon] > 294)
        & (ds.coords[lon] < 310)
    ) + (
        (ds.coords[lat] > -75)
        & (ds.coords[lat] < -70)
        & (ds.coords[lon] > 285)
        & (ds.coords[lon] < 295)
    )
    
    if sector == "eais":
        mask = mask_eais
    elif sector == "wedd":
        mask = mask_wedd
    elif sector == "amun":
        mask = mask_amun
    elif sector == "ross":
        mask = mask_ross 
    elif sector == 'apen':
        mask = mask_apen #!use Amundsen sector
    elif sector == "anta":
        mask = mask_eais + mask_wedd + mask_amun + mask_ross + mask_apen
    else: print("Sector does not exist in 'sel_mask'")
    return mask

#def mask_sector(ds,sector,lat,lon):
#    '''select mask of sector'''
#    if sector == "eais":
#        mask = ( 
#            (ds.coords[lat] > -76)
#            & (ds.coords[lat] < -65)
#            & (ds.coords[lon] < 173)
#        ) + (
#            (ds.coords[lat] > -76)
#            & (ds.coords[lat] < -65)
#            & (ds.coords[lon] > 350) 
#        )
#    elif sector == "wedd":
#            mask = (
#            (ds.coords[lat] < -72)
#            & (ds.coords[lon] > 295)
#            & (ds.coords[lon] < 350)
#        )
#    elif sector == "amun":
#            mask = (
#            (ds.coords[lat] < -70)
#            & (ds.coords[lon] > 210)
#            & (ds.coords[lon] < 295)
#        )
#    elif sector == "ross":
#            mask = (
#            (ds.coords[lat] < -76)
#            & (ds.coords[lon] > 150)
#            & (ds.coords[lon] < 210)
#        )  
#    else: print("Sector does not exist in 'sel_mask'")
#    return mask

def sel_depth_bnds(sector):
    '''select oceanic layers based on shelf depth'''
    print('Identify depth of ocean layers')
    
    # Sector-specific depths (baesd on shelf base depth)
    if type(sector) == str:
        find_shelf_depth = {
        'eais': 369,
        'wedd': 420,
        'amun': 305,
        'ross': 312,
        'apen': 420
        }

        shelf_depth = find_shelf_depth[sector]
        ocean_slice = np.array([shelf_depth-50,shelf_depth+50])
    
    # If number is specified, depth is the same for each sector
    if type(sector) == int:
        shelf_depth = sector
        if shelf_depth == 900: #800-1000m
            ocean_slice = np.array([shelf_depth-100,shelf_depth+100]) 
        if shelf_depth == 550: #400-700m
            ocean_slice = np.array([shelf_depth-150,shelf_depth+150])
      
    return ocean_slice


###############################################################################