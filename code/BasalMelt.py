import numpy as np
import xarray as xr
import pandas as pd
from AntarcticSectors import LevermannSectors as levermann


class OceanData():
    """Class of ocean output file related calculations
    ...

    Attributes
    ----------
    thetao (str): name of ocean temperature file
    area (str): name of areacello file

    Methods
    -------
    area_weighted_mean
        Compute area weighted mean of ocean temperature over a sector
    nearest_mask
        Mask the values outside of target depth
    nearest_above
        Find nearest value above target value
    nearest_below
        Find nearest value below target value
    lev_weighted_mean
        Compute depth weighted mean oceanic temperature over specific 
        oceanic sector and specific depth layers 
    ShelfBase
        select oceanic layers based on shelf depth
    select_depth_range
        Select depth bounds of sector
    select_lev_mean
        Compute mean of depth bounds
    select_area_mean
        Compute area mean of sector
    weighted_mean_df
        Compute volume weighted mean for one year of thetao
    """

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


    def __init__(self,thetao,area):
        self.thetao = thetao
        self.area = area

    def openDatasets(self):
        '''Open datasets
        Args:
            thetao (str): path to ocean temperature dataset
            area (str): path to area dataset
        Returns: 
            xarray datasets of ocean temperature and area dataset
        '''
        ds = xr.open_dataset(self.thetao)
        area_ds = xr.open_dataset(self.area)
        return ds, area_ds



    def area_weighted_mean(self, ds_sel,ds_area):
        '''Compute area weighted mean oceanic temperature over specific oceanic sector
        Args:
            ds_var (xarray dataset): thetao dataset
            ds_area (xarray dataset): areacello dataset
        Returns:
            area_weighted_mean (dataarray): area weighted mean of thetao
        '''

        area_weights = ds_area.areacello.fillna(0)
        area_weighted = ds_sel.weighted(area_weights)
        lat = ds_sel.dims[2]
        lon = ds_sel.dims[3]

        area_weighted_mean = area_weighted.mean((lat,lon))

        return area_weighted_mean

    def nearest_mask(self, diff):
        """Mask the values outside of target
        Args:
            diff (xarray dataset): 
        Returns:
            masked_diff (xarray dataset): 
        """
        mask = np.ma.less_equal(diff, 0)
        if np.all(mask):
            return None
        masked_diff = np.ma.masked_array(diff, mask)
        return masked_diff


    def nearest_above(self, my_array, target):
        '''Find nearest value in array that is greater than target value and return corresponding index
        Args:
            my_array (xarray dataset): ocean data array
            target (float): depth to calculate around
        Returns:
            masked_diff.argmin() ():
        '''
        diff = my_array - target
        masked_diff = self.nearest_mask(diff)
        return masked_diff.argmin() 


    def nearest_below(self, my_array, target):
        '''Find nearest value in array that is smaller than target value and return corresponding index
            Args:
            my_array (xarray dataset): ocean data array
            target (float): depth to calculate around
        Returns:
            masked_diff.argmin() ():
        '''
        diff = target - my_array
        masked_diff = self.nearest_mask(diff)
        return masked_diff.argmin()

    
    def lev_weighted_mean(self, ds,lev_bnds, top, bottom):
        '''Compute volume or depth weighted mean oceanic temperature over specific oceanic
        sector and specific depth layers (centered around ice shelf depth)
        Args:
            ds (xarray dataset): 2D or 3D thetao dataset
            lev_bnds (xarray dataarray): ocean depth bands array
            sector (str): sector name
        Returns:
            levs_weighted_means (float): volume weighted mean of ocean temperature
        '''

        # Find oceanic layers covering the depth bounds and take a slice of these
        # layers
        lev_ind_bottom= self.nearest_above(lev_bnds[:,1],bottom)
        lev_ind_top = self.nearest_below(lev_bnds[:,0],top)
        levs_slice = ds.isel(lev=slice(lev_ind_top,lev_ind_bottom+1))
        
        # Create weights for each oceanic layer, correcting for layers that fall only partly within specified depth range 
        lev_bnds_sel = lev_bnds.values[lev_ind_top:lev_ind_bottom+1]
        lev_bnds_sel[lev_bnds_sel > bottom] = bottom
        lev_bnds_sel[lev_bnds_sel < top] = top
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


    def ShelfBase(self, sector):
        '''select oceanic layers based on shelf depth
        Args: 
            sector (str): name of sector
        Returns:
            ocean_slice (numpy array): shelfbase slice which is dependent on sector
        '''

        shelf_depth = self.find_shelf_depth[sector]
        ocean_slice = np.array([shelf_depth-50,shelf_depth+50])
        
        return ocean_slice

    
    def select_depth_range(self,sector):
        """Select depth bounds of sector
        Args:
            sector (str): name of sector
        Returns:
            top (float) and bottom (float) ocean depth range limits
        """
        depth_bnds_sector = self.ShelfBase(sector)     
        top = depth_bnds_sector[0]
        bottom = depth_bnds_sector[1]
        return top, bottom
    

    def sector_lev_mean(self, ds, lev_bnds, sector):
        """Compute mean of depth bounds
        Args:
            ds (xarray dataset): ocean temperature dataset
            lev_bands (array): array of depth level bands
            sector (str): sector name
        Returns:
            lev_weighted_mean (xarray dataarray) depth weighted mean of ocean depth range
        """
        top, bottom = self.select_depth_range(sector)
        lev_weighted_mean = self.lev_weighted_mean(ds,lev_bnds,top,bottom)
        return lev_weighted_mean


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
        ds, area_ds = self.openDatasets()
        ds_year = ds.groupby('time.year').mean('time') #Compute annual mean
        masks = levermann().sector_masks(ds)

        # Loop over oceanic sectors
        df = pd.DataFrame()
        for sector in self.sectors:
            mask = masks[sector]
            ds_sel = ds_year["thetao"].where(mask)
            thetaoAWM = self.area_weighted_mean(ds_sel,area_ds)
            thetaoVWM = self.sector_lev_mean(thetaoAWM, ds_year.lev_bnds.mean("year").copy(), sector)
            df[sector] = thetaoVWM

        ds_year.close()
        area_ds.close()
        return df
    pass


class BasalMelt(OceanData):
    """Class for Basal Melt calculation related calculations
    ...

    Attributes
    ----------
    rho_i (float): ice density kg m-3
    rho_sw (float): sea water density
    c_po (float): specific heat capacity of ocean mixed layer J kg-1 K-1
    L_i (float): latent heat of fusion of ice
    Tf (float): Freezing temperature
    baseline (float): baseline climate mean temperature
    gamma (float): gamma value for chosen model

    Methods
    -------
    quad_constant
        Calculate quadratic constant
    quadBasalMelt
        Calculate basal melt
    BasalMeltAnomalies
        Calculate basal melt anomaly
    thetao2basalmelt
        Calculate basal melt from 3D ocean temperature file
    mapBasalMelt
        Map basal melt values to Antarctic Sectors
    """

    # Parameters to compute basal ice shelf melt (Favier 2019)
    rho_i = 917. 
    rho_sw = 1028. 
    c_po = 3974. 
    L_i = 3.34*10**5 
    Tf = -1.6
    baseline = {'eais':0.27209795341055726,'wedd':-1.471784486780416,'amun':2.1510233407460326,'ross':0.5177848939696833,'apen':-0.6192596251283067}

    def __init__(self,thetao,area,gamma):
        OceanData.__init__(self,thetao,area)
        self.gamma = gamma

    def quad_constant(self):
        """Calculate quadratic constant
        Returns:
            ms (float) quadratic constant value
        """
        c_lin = (self.rho_sw*self.c_po)/(self.rho_i*self.L_i)
        c_quad = (c_lin)**2
        ms = self.gamma * 10**5 * c_quad # Quadratic constant
        return ms


    def quadBasalMelt(self,dat):
        """Calculate basal melt
        Args:
            dat (float): ocean temperature value
        Returns:
            bm (float): basal melt value
        """
        ms = self.quad_constant()
        bm = (dat - self.Tf)*(abs(dat-self.Tf)) * ms
        return bm


    def BasalMeltAnomalies(self, thetao, base):
        """Calculate basal melt anomaly
        Args:
            thetao (float): ocean temperature value
            base (float): ocean temperature baseline value
        Returns:
            dBM (float) basal melt anomaly
        """
        BM_base = self.quadBasalMelt(base)
        BM = self.quadBasalMelt(thetao) 
        dBM = BM - BM_base
        assert dBM < 100, "Basal melt too unrealistic"
        assert dBM > -100, "Basal melt too unrealistic"
        return dBM


    def thetao2basalmelt(self):
        """Calculate basal melt from 3D ocean temperature file   
        Returns:
            df2 (pandas dataframe) values of basal melt for each Antarctic region
        """
        df = self.weighted_mean_df()
        df2 =  pd.DataFrame()
        for column in df:
            thetao = df[column].values
            base = self.baseline.get(column)
            dBM = self.BasalMeltAnomalies(thetao, base)
            df2[column]=dBM
        assert df2.empty == False, "Dataframe should not be empty"
        print(df2)
        return df2

    def mapBasalMelt(self,mask_path,nc_out,driver,name):
        """Calculate basal melt values and map to Antarctic sectors
        Args:
            mask_path (str): path to mask files
            nc_out (str): path to where basal melt file will be output
            driver (str): path to filetools driver
            name (str): name of basal melt file
        Returns:
            basal melt dataframe and produces netcdf and hdf5 files
        """
        df = self.thetao2basalmelt()
        levermann().map2amr(mask_path,nc_out,driver,name,df)
        return df

    pass
