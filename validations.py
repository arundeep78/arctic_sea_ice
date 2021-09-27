import pandas as pd

############################### Global paramteters ###########################################

# # emissions data
tbl_ghg = "t_emissions_climatewatch"

# # emissions sectors hierarchy
# t_cw_sectors = "t_emissions_climatewatch_sectors"

# sea_ice _area
# tbl_sia = "t_nsidc_sea_ice_area"

# sea_ice age
tbl_siage = "t_siage_nsidc"

# World population
tbl_population = "t_ref_un_population"


def siage_val(p_val, p_type: str, conn = None):
    """
    Query parameter validation for sea ice age application

    Args:
        p_val ([object]): parameter value to be validated
        p_type (str): parameter type/name that need to be validated
        conn ([SQLalchemy], optional): SQL alchmey connection to the database
    """

    if p_type == "month":

        if p_val > 0 or p_val < 13:
            return p_val
        else:
            return "Error: Month has to be a number between 1 and 12"
    
    if p_type == "by":
        if not p_val in ["month", "year", "total"]:
            return "Error: trends can be shown by month or annual. Please select 'month'or 'year"
        else:
            return p_val

    if p_type == "year":
        stmt = f"select year, count(month) as cnt from {tbl_siage} group by year"
        df_years = pd.read_sql(stmt, con= conn)
        ds_years = df_years["year"].sort_values(ascending=False)

        if p_val == None:
            
            year = df_years.loc[df_years["cnt"]== 52, "year"].max()
            return year, ds_years
        else:
            if p_val in ds_years.values :
                return p_val, ds_years
            else:
                return f"Error: There is no data for the selected year. Select year between {ds_years.min()} and {ds_years.max()}", None


    elif p_type == "pct":
        return True if p_val == "y" else False

    elif p_type == "siac":

        if p_val is None:
            return "y"

        if not p_val in [ "y", "c"]:
            return " Error: Sea ice age can be categorized either by years or in categories. Value should be with y or c "
        else:
            return p_val 

    elif p_type == "agg":

        if p_val == None:
            return "m"
        if not p_val in ["m", "w"]:
            return "Error : annual aggregation can be either weekly of monthly. value should be wither m or w"
        else:
            return p_val


def sia_val_args( p_val, p_type: str, conn= None):
    """
    query parameter validaton for the sia loss applications that are passed to Sea ice area loss applications. 

    Args:
        p_value (str): parameter value to be validated
        p_type (str): type of parameter

    Returns:
        ret: returns a validated parameter or sent "Error message" if it not validated 
    """

    if p_type == "iso_a3":
        
        iso_list = pd.read_sql(f"select distinct(iso_a3) from { tbl_ghg}",con=conn).squeeze()
        
        return p_val if p_val in iso_list.to_list() else "Error: Please select a valid country"

    elif p_type == "cum":
        return False if p_val == "n" else True

    elif p_type == "per_cap": 
        return True if p_val == "y" else False

    elif p_type == "data_by":
        return p_val if p_val in ["s", "c"] else "Error: Please select valid entry for data selection by countries (c) or sectors (s)"

    elif p_type == "ds":
        return p_val if p_val in ["CAIT", "PIK", "GCP"] else "Error: Please select a valid data source"


