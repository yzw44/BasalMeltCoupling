import numpy as np
import xarray as xr
import pandas as pd
from glob import glob
import os

class LevermannSectors:
    eais1 = [-76,-65,0,173]
    eais2 = [-76,-65,350,0]
    wedd = [-90,-72,295,350]
    amun = [-90,-70,210,295]
    ross = [-90,-76,150,210]
    apen1 = [-70,-65,294,310]
    apen2 = [-75,-70,285,295]

    # Sectors
    sectors = ['eais','wedd','amun','ross','apen']

    # Sector-specific depths (based on shelf base depth)
    find_shelf_depth = {
    'eais': 369,
    'wedd': 420,
    'amun': 305,
    'ross': 312,
    'apen': 420
    }

    def __init__(self, ds):
        self.ds = ds

    def create_mask(self,coords):
        """ create a mask based on coordinates
        Args:
            ds (xarray dataset): thetao dataset
            lat1,lat2,lon1,lon2 (int): coordinates of sector
        Returns:
            mask (): mask of sector
        """
        try:
            lat='latitude'
            lon='longitude'
        except:
            lat='lat'
            lon='lon'

        mask = ((self.ds.coords[lat] > coords[0])
            & (self.ds.coords[lat] < coords[1])
            & (self.ds.coords[lon] > coords[2])
            & (self.ds.coords[lon] < coords[3])
        )
        return mask

    def sector_masks(self):
        '''select mask of sector
        Args:
            ds (xarray dataset): thetao dataset
            sector (str): sector name
        Returns:
            mask (): mask of sector
        '''

        mask_eais = self.create_mask(self.eais1)     
        + self.create_mask(self.eais2)
        mask_wedd = self.create_mask(self.wedd)
        mask_amun = self.create_mask(self.amun)
        mask_ross = self.create_mask(self.ross)
        mask_apen = self.create_mask(self.apen1) 
        + self.create_mask(self.apen2)
        masks = {'eais': mask_eais, 'wedd': mask_wedd,  
        'amun': mask_amun, 'ross': mask_ross, 'apen': mask_apen}

        return masks
    pass


class OceanData(LevermannSectors):
    # Parameters to compute basal ice shelf melt (Favier 2019)
    rho_i = 917. #ice density kg m-3
    rho_sw = 1028. # sea water density
    c_po = 3974. # specific heat capacity of ocean mixed layer J kg-1 K-1
    L_i = 3.34*10**5 # latent heat of fusion of ice
    Tf = -1.6
    baseline = 1

    def __init__(self,thetao,area,gamma):
        self.thetao = thetao
        self.area = area
        self.gamma = gamma

    def ShelfBase(self, sector):
        '''select oceanic layers based on shelf depth
        Args: 
            sector (str): name of sector
        Returns:
            ocean_slice (): shelfbase slice which is dependent on sector
        '''

        shelf_depth = self.find_shelf_depth[sector]
        ocean_slice = np.array([shelf_depth-50,shelf_depth+50])
        
        return ocean_slice


    def area_weighted_mean(self, ds_var,ds_area,mask):
        '''Compute area weighted mean oceanic temperature over specific oceanic sector
        Args:
            ds_var (xarray dataset): thetao dataset
            ds_area (xarray dataset): areacello dataset
            sector (str): sector name
        Returns:
            area_weighted_mean (dataarray): area weighted mean of thetao
        '''

        area_weights = ds_area.areacello
        area_weighted = ds_var.where(mask).weighted(area_weights.fillna(0)) #DataArrayWeighted with weights along dimensions: j, i
        lat = ds_var.dims[2]
        lon = ds_var.dims[3]
        
        try: 
            ((lat=='y') or (lat=='j') or (lat=='lat') or (lat=='latitude')) and ((lon=='x') or (lon=='i') or (lon=='lon') or (lon =='longitude'))
        except:
            print("Check if these dimensions are correct to compute weighted mean")

        area_weighted_mean = area_weighted.mean((lat,lon))
        return area_weighted_mean #2D field: time,levs
        

    def nearest_mask(self, diff):
        """Mask the values outside of target
        Args:
            diff ():
        Returns:
            masked_diff (): 
        """
        mask = np.ma.less_equal(diff, 0)
        if np.all(mask):
            return None # returns None if target is greater than any value
        masked_diff = np.ma.masked_array(diff, mask)
        # Returns the index of the minimum value
        return masked_diff


    def nearest_above(self, my_array, target):
        '''Find nearest value in array that is greater than target value and return corresponding index
        Args:
            my_array ():
            target ():
        Returns:
            masked_diff.argmin() ():
        '''
        diff = my_array - target
        masked_diff = self.nearest_mask(diff)
        return masked_diff.argmin() 


    def nearest_below(self, my_array, target):
        '''Find nearest value in array that is smaller than target value and return corresponding index
            Args:
            my_array ():
            target ():
        Returns:
            masked_diff.argmin() ():
        '''
        diff = target - my_array
        masked_diff = self.nearest_mask(diff)
        return masked_diff.argmin()


    def lev_weighted_mean(self, ds,lev_bnds,sector):
        '''Compute volume or depth weighted mean oceanic temperature over specific oceanic
        sector and specific depth layers (centered around ice shelf depth)
        Args:
            ds (xarray dataset): 2D or 3D thetao dataset
            lev_bnds (xarray dataarray): ocean depth bands array
            sector (str): sector name
        Returns:
            levs_weighted_means (float): volume weighted mean of ocean temperature
        '''
    
        # Select depth bounds of sector
        depth_bnds_sector = self.ShelfBase(sector)     
        depth_top = depth_bnds_sector[0]
        depth_bottom = depth_bnds_sector[1]
        #print(depth_bnds_sector)
        
        # Find oceanic layers covering the depth bounds and take a slice of these
        # layers
        lev_ind_bottom= self.nearest_above(lev_bnds[:,1],depth_bottom)
        lev_ind_top = self.nearest_below(lev_bnds[:,0],depth_top)
        levs_slice = ds.isel(lev=slice(lev_ind_top,lev_ind_bottom+1))
        
        # Create weights for each oceanic layer, correcting for layers that fall only partly within specified depth range 
        lev_bnds_sel = lev_bnds.values[lev_ind_top:lev_ind_bottom+1]
        lev_bnds_sel[lev_bnds_sel > depth_bottom] = depth_bottom
        lev_bnds_sel[lev_bnds_sel < depth_top] = depth_top
        # Weight equals thickness of each layer
        levs_weights = lev_bnds_sel[:,1]-lev_bnds_sel[:,0] 
        # DataArray required to apply .weighted on DataArray
        levs_weights_DA = xr.DataArray(levs_weights,coords={'lev': levs_slice.lev},
                dims=['lev'])
        
        # Compute depth weighted mean of ocean slice
        levs_slice_weighted = levs_slice.weighted(levs_weights_DA)
        levs_weighted_mean = levs_slice_weighted.mean(("lev"))
        
        # Return layer-weighted ocean temperature
        return levs_weighted_mean
    

    def weighted_mean(self, masks, sector, ds_year, area_ds):
        mask = masks[sector]
        # Compute area weighted mean     
        thetaoAWM = self.area_weighted_mean(ds_year["thetao"],area_ds,mask)
        thetaoVWM = self.lev_weighted_mean(thetaoAWM, ds_year.lev_bnds.mean("year").copy(),sector)
        return thetaoVWM


    def weighted_mean_df(self):
        """ Compute volume weighted mean for one year of thetao
        Args:
            area_file (str): file name for file containing areacello data
            thetao_file (str): file name for file containing ocean data
            sectors (list of str): list of sector names
        Returns:
            df (pandas dataframe): dataframe with volume weighted mean for each sector
        """
        # Open thetao dataset
        ds = xr.open_dataset(self.thetao)
        ds_year = ds.groupby('time.year').mean('time') #Compute annual mean
        ds.close()
        area_ds = xr.open_dataset(self.area)
        sec = LevermannSectors(ds)
        masks = sec.sector_masks()

        # Loop over oceanic sectors
        df = pd.DataFrame()
        for sector in self.sectors:
            thetaoVWM = self.weighted_mean(masks,sector,ds_year,area_ds)
            df[sector] = thetaoVWM

        ds_year.close()
        area_ds.close()
        return df


    def calc_cquad(self):
        c_lin = (self.rho_sw*self.c_po)/(self.rho_i*self.L_i)
        c_quad = (c_lin)**2
        return c_quad


    def quadBasalMeltAnomalies(self, thetao):
        ## Compute quadratic basal melt anomalies with gamma
        c_quad = self.calc_cquad()
        ms = self.gamma * 10**5 * c_quad # Quadratic constant
        # Quadratic melt baseline (negative if To < Tf)
        BM_base = (self.baseline - self.Tf)*(abs(self.baseline) - self.Tf) * ms
        # Compute basal melt
        BM = (thetao - self.Tf) * (abs(thetao) - self.Tf) * ms  
        # Compute basal melt anomalies
        dBM = BM - BM_base
        return dBM

    def thetao2basalmelt(self):
        df = self.weighted_mean_df()
        df2 =  pd.DataFrame()
        for column in df:
            thetao = df[column].values
            dBM = self.quadBasalMeltAnomalies(thetao)
            df2[column]=dBM
        return df2
    pass


class LevermannMask(OceanData):
    def __init__(self,mask_path,nc_out,driver):
        self.mask_path = mask_path
        self.nc_out = nc_out
        self.driver = driver
        
    def OpenMasks(self):
        self.nc_files = glob(os.path.join(self.mask_path, "*.2d.nc"))
        bisicles_masks = {}
        for file in self.nc_files:
            key = os.path.splitext(os.path.basename(file))[0][15:-3]
            name = 'smask' + str(key)
            dat = xr.open_dataset(file)
            bisicles_masks[name] = np.array(dat['smask'])

        x = np.array(dat['x'])
        y = np.array(dat['y'])
        return x,y,bisicles_masks

    def map2amr(self,name,df2):
        x,y,bisicles_masks = self.OpenMasks()
        #df2 = self.thetao2basalmelt()
        for i, row in df2.iterrows():
            new_mask = np.where(bisicles_masks['smask1'] == 1, row.apen, bisicles_masks['smask1'])
            new_mask = np.where(bisicles_masks['smask2'] == 1, row.amun, new_mask)
            new_mask = np.where(bisicles_masks['smask3'] == 1, row.ross, new_mask)
            new_mask = np.where(bisicles_masks['smask4'] == 1, row.eais, new_mask)
            new_mask = np.where(bisicles_masks['smask5'] == 1, row.wedd, new_mask)
            da = xr.DataArray(data= new_mask, coords=[("x", x),("y",y)], name="bm")
            da.to_netcdf(self.nc_out+ name + '.nc')
            os.system(self.driver + " " + self.nc_out + name + ".nc " + self.nc_out + name + ".2d.hdf5 bm")
    pass