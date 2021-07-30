############ Utility file to work with Greenhouse gases data ############################

import requests
import io, sys, glob
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from . import config
import datetime, time, random
from urllib.parse import urlparse, parse_qs
import psycopg2
from treelib import Tree, Node
import calendar
import ftplib
from shutil import copyfile


############################### Global paramteters ###########################################

# emissions data
tbl_ghg = "t_climatewatch_emissions"

# emissions sectors hierarchy
t_sectors = "t_climatewatch_sectors"

# sea_ice _area
tbl_sia = "t_nsidc_sea_ice_area"

# World population
tbl_population = "t_ref_un_population"

# Sea Ice age table
tbl_siage = "t_nsidc_sea_ice_age"

# Sea ice factor for CO2 emisssions
si_co2_factor = 3

# Color codes for various GHG emissions sector
sec_color_dict = {"Building": "#a6cee3",
             "Bunker Fuels": "#b2df8a",
             "Electricity/Heat": "#dfc27d", #ff9933" , #dd4c51" ,
             "Fugitive Emissions" : "#ffff99",
             "Industrial Processes" : "#fdbf6f", 
             "Industrial Processes and Product Use" : "#fdbf6f",
             #"Land-Use Change and Forestry" : "#33a02c",
             "Manufacturing/Construction" : "#cab2d6", 
             "Other Fuel Combustion" : "#fb9a99",
             "Transportation" : "#74add1",#1f78b4",
             "Others" : "#EAEAEA",
             "Energy" :  "#dd4c51",
             "Total excluding LUCF" : "#ff9933",
             "Total excluding LULUCF" : "#ff9933",
             "Agriculture" : "#35978f",
             "Waste" : "#9970ab",
             "Other" : "#EAEAEA"
            }
gas_colors_dict = {"All GHG": "#a6cee3",
             "CO2": "#b2df8a",
             "CH4": "#dfc27d", #ff9933" , #dd4c51" ,
             "N2O" : "#ffff99",
             "F-Gas" : "#fdbf6f", 
             "KYOTOGHG" : "#fdbf6f"

        }

country_color_dict = {"CHN": "#da1d23",
             "EUU": "#003399",
             "IND": "#87CEEB" ,
             "IDN" : "#fdbf6f",
             "USA" : "darkblue", 
             "JPN" : "#E8F48C",
             "RUS" : "blue", 
             "BRA" : "yellow",
             "IRN" : "#1f78b4",
             "KOR" : "black",
             "Others" : "#D1D1D1",
             "GBR" : "green",
             "CAN" : "darkgray" ,
             "UKR" : "#ffd700",
             "MEX" : "#F653A6"
            }

group_color_dict = {"Others": "#D1D1D1", #ADADAD",
                    "Top": "#01665e"
                    }

siage_color_dict = {
        "new" : "#B2FFFF",
        "0-1" : "#3D50A4", #"blue",
        "1-2" : "#6FCDDE", #"lightblue",
        "2-3" :  "#6FC042", #"green",
        "3-4" :  "#FCB210", #"yellow",
        "4+" :  "#F02009",#'red',
        "loss" : 'black'
    }


siage_color_dict_y = {
        "new" : "#B2FFFF",
        "y1" : "#3D50A4", #"blue",
        "y2" : "#6FCDDE", #"lightblue",
        "y3" :  "#6FC042", #"green",
        "y4" :  "#FCB210", #"yellow",
        "y5" :  "#F02009",#'red',
        "loss" : 'black'
    }


sia_cities = ("Beijing", "Los Angeles","London", "Tokyo", "Moscow", "Delhi", "Toronto", "Madrid", "Paris")
############################################################################################

####### General DB related functions ########

def psql_connect(params_dic):
    """ Connect to the PostgreSQL database server using psycopg2 driver """
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params_dic)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1) 
    print("Connection successful")
    return conn

def get_alchemy_connection(db_config):
    """
    Takes db config dictionary and returns a DB connection to execte SQL queries
    """
    db_url = f'postgresql+psycopg2://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}'
    
    print(db_url)

    # Create a SQLAlchemy engine instance

    alchemyEngine   = create_engine(db_url)
    # Connect to PostgreSQL server

    dbConnection    = alchemyEngine.connect()
    
    return dbConnection



##########################################################################################

############# GHG emissions Tree structre for E- charts sunburst API #####################

##########################################################################################

def create_pctree(df_data,node_id_col,node_col,parent_id_col):
    """
    Create a tree structure from a dataframe of parent child relationships in columns
    
    Input:
        df_data ( DataFrame): pandas Dataframe that craetes node IDs, parent IDs and node names
        node_id_col ( String) : Column name that contain IDs for each Node
        node_col ( String) : Column name for the descriptive name for each respective node ID
        parent_id_col (String) : Column name for the parent IDs for each respective Node ID

    Output:
        tree ( treelib.Tree) : Tree structure
    """
    
    
    # If parent ID does not exist as ID, then mark it NAN
    df_data.loc[~df_data[parent_id_col].isin(df_data[node_id_col]),parent_id_col] = np.nan
    # Use tree lib to create the base tree structure

    # Use tree lib to create the base tree structure

    tree= Tree()
    # Create first parent node
    tree.create_node("Total" ,0)    

    #Loop to enter all nodes
    for i, c  in df_data.iterrows():
        #print(c[parent_id_col])
        tree.create_node(c[node_col],c[node_id_col],parent =0 )

    # Loop to move all nodes at the appropriate place in the tree
    for i, c  in df_data.iterrows():
        #print(c[parent_id_col])
        
        if isinstance(c[parent_id_col],str):
            tree.move_node(c[node_id_col], c[parent_id_col] )

        elif ~ np.isnan(c[parent_id_col]): 
            #print(c[parent_id_col])
            tree.move_node(c[node_id_col], int(c[parent_id_col]) )
        
            # Remove the top level
    #child = tree.children(0)[0]
    #tree = tree.subtree(child.identifier)
    
    #tree.show()
    
    return tree

def sunburst_tree(pc, df_data,key_col,val_col):
    """
    Takes in tree structure from "treelib" and convert it into the format as needed by E-Charts sunburst chart.

    Input :
        pc (Dict) : Dictionary object from treelib library with complete structure till top. Treelib.Tree().to_dict()
        df_data (DataFrame) : Dataframe object that contains data/values for the given tree e.g. GHG emissions for each key
        key_col (String) : column name in the data frame for node keys
        val_col (String) : column name in the dataframe for node values
        
    Output:
        rets(Dict) : Dictionary structure as required by e-Chart Sunburst api
        
    """

    
    if isinstance(pc, list):

        return [sunburst_tree(item, df_data,key_col,val_col) for item in pc]

    if isinstance(pc, dict):
        for key, value in pc.items():
            if key == "children":
                return sunburst_tree(value, df_data,key_col,val_col)
            else:
                #print(key)
                rets= {}
                if df_data[df_data[key_col]==key][val_col].values.size>0:
                    rets["value"] = np.round(df_data[df_data[key_col]==key][val_col].values[0],2)
                
                rets["name"] = key #+"\n\n" + str(rets.get("value",""))
                rets["children"] = sunburst_tree(value, df_data,key_col,val_col)
                       
                return rets

    if isinstance(pc, str):
            rets = {}
            if df_data[df_data[key_col]==pc][val_col].values.size>0:
                rets["value"] = np.round(df_data[df_data[key_col]==pc][val_col].values[0],2)
            
            rets["name"] = pc #+ "\n\n" + str(rets.get("value",""))
                    
            return rets




##################### Sea Ice loss by top emitters #######################################


##########################################################################################


def get_country_list(db_conn, source ="CAIT"):
    """
    Get country code list from Climate watch GHG emissions
    """

    stmt = """select distinct(tce.iso_a3), truic.country as name
            from {} as tce
            left join t_ref_un_iso_codes truic 
                on tce.iso_a3 = truic.iso_a3 
            where
                tce.data_source = '{}'
            """
    stmt = stmt.format(tbl_ghg, source)

    df_ccodes = pd.read_sql(stmt,con= db_conn)
    
    df_ccodes["name"].mask(df_ccodes["name"].isnull(), df_ccodes["iso_a3"], inplace= True)
    

    return df_ccodes.sort_values("name", ascending = False)


def get_group_ccodes(db_conn, g_code = "EUU"):
    """
    Get List of iso_a3 country codes of EU countries

    Inputs:
        g_code ( String) : Country group code as defined by worldbank
        db_conn (SQLAlchemy connection) : SQL Alchemy connection to database

    Outputs:
        ccodes (tuple): Tuple of country codes included in the given group
    """
    # Find EU countries to exclude as individuals
    # Get data by countries and sectors from database

    t_wb_class = "t_ref_worldbank_world_class"

    stmt = f"select iso_a3 from {t_wb_class} where groupcode = '{g_code}'"

    #print(stmt)
    stmt = stmt.format(t_wb_class, g_code)

    df_ccodes = pd.read_sql(stmt, con= db_conn)
    ccodes = tuple(df_ccodes.iso_a3.to_list())
    return ccodes


def sialoss_top_per_cap(db_conn, source = "CAIT", year = 1990,top_n= 10):
    """
    Function to get sea ice area loss for a given year by top emitters and other countries countries ( EU is considered as single entity)

    Inputs:
        year(int) : Year for which sea ice loss contributions has to be calculated
        db_conn (SQLAlchemy connection) : SQL Alchemy connection to database
        top_n (int) : Number of top countries to select. Max 10
        
    """
    # CLip input to 3,10
    top_n = np.clip(top_n,3,20)
    
    # GHG gas
    gas = "CO2"
   
    # Exclude EU individual countries from the list and WORLD as a category
    exl_ccodes = get_group_ccodes(db_conn,"EUU")
    exl_loc = ('WORLD', ) + exl_ccodes

     # IDs to be exluced from the source DS for CAIT. These are top level categories and Land usage and change, which is usually negative
    exl_ids = (1298,1300,1299,1304,1313)

    # Declare statements
    # Select total emissions without LUCF  
    stmt_year = "select "\
            "tce.iso_a3,"\
            "tce.value "\
        " from {} as tce "\
       "where " \
            "tce.data_source ='{}' and "\
            "tce.gas = '{}' and "\
            "tce.iso_a3 not in {} and "\
            "tce.year = '{}' and "\
            "tce.sector = '{}' "

    sector = "Total excluding LUCF" if source == "CAIT" else "Total excluding LULUCF"


    stmt = f"select distinct(year) as year from {tbl_ghg} where data_source = '{source}' and gas = '{gas}'"
    
    ds_years = pd.read_sql(stmt, con= db_conn).squeeze()

    ds_years = ds_years.sort_values(ascending=False)
    
    min_year = ds_years.min()
    max_year = ds_years.max()
    
    if not year is None: 
        year = np.clip(year, min_year, max_year)
    else:
        year = max_year

    # Get GHG emissions data    
    stmt = stmt_year.format(tbl_ghg, source, gas, exl_loc, year, sector)
    
    #print( stmt)
    df_emissions = pd.read_sql(stmt, con= db_conn)

    # Merge population data without EUU
    stmt = f"select iso_a3, population from {tbl_population} where  iso_a3 not in {exl_loc} and year = {year}"
    df_pop = pd.read_sql(stmt, con= db_conn)
    df_emissions = df_emissions.merge(df_pop,left_on="iso_a3", right_on="iso_a3",how='left')
    
    # get population of EUU as total and add in the Dataframe
    stmt = f"select sum(population) as pop from { tbl_population} where iso_a3 in {exl_ccodes} and year = {year}"
    pop_euu = pd.read_sql(stmt,con=db_conn).values[0][0]
    df_emissions.loc[df_emissions["iso_a3"] == "EUU", "population"] = pop_euu

    # original data is in thousands
    df_emissions["population"] *= 1000

    # convert emissions in tons ( original values are in million tons) 
    df_emissions["value"] = ( 1000 * 1000 * df_emissions["value"]) 
    
    # world's average per capita emissions
    world_avg = np.round(df_emissions["value"].sum()/df_emissions["population"].sum()* si_co2_factor,1)
 

    # Calculate per capital
    df_emissions["value"] /= df_emissions["population"] 

    


    df_emissions = df_emissions.dropna()
    df_emissions = df_emissions[df_emissions["value"] != np.infty] 

    # Create groups for top_n and Others
    l_top_n = df_emissions.nlargest(top_n, "value")["iso_a3"].to_list()
    
    #print( f"topc : { top_n} length = {len(l_top_n)}")

    df_emissions["group"] = "Others"

    top_n_grp_str = "Top " + str(top_n)
    #print(top_n_grp_str)

    df_emissions.loc[df_emissions["iso_a3"].isin(l_top_n), "group"] = top_n_grp_str

    # Convert values to sea ice from CO2 emissions. This is now in m2
    df_emissions["value"] *= si_co2_factor

    # Build stucture for doughnut chart

    country_colors = list(country_color_dict.values())

    series = []

    df_emissions = df_emissions.sort_values(["group", "value"], ascending= False)

    df_emissions["value"] = np.round(df_emissions["value"],1)

    #print(f"countries in top {(df_emissions.group=='Top 10').sum() }")
    for idx, row in df_emissions.iterrows():
    

        c_dict = {}
        
        c_dict["value"] = row[ "value"]

        c_dict["name"] = row["iso_a3"]
        # Set country colors for Others group same as group color
        # Set labels to transparent for other countries
        if row["group"] == "Others": 
            c_dict["itemStyle"] = { "color": country_color_dict.get("Others")}
            #  c_dict["label"] = { "show" : False}
        else:
            c_dict["itemStyle"] = { "color": country_colors[l_top_n.index(row["iso_a3"])]}
            c_dict["label"] = { "show": 'true'}
        
        series.append(c_dict)

  
    title = f"Arctic Sea Ice loss per capita contribution by country for year {year}"
    subtitle = f"{world_avg} m² of sea ice loss per capita for the World" 
        

    return series, year, ds_years, title,subtitle, world_avg

def sialoss_top_cum(db_conn, source = "CAIT", year = 1990,top_n= 10, cum = True) :
    """
    Function to get sea ice area loss for a given year by top emitters ( countries ( EU is considered as single entity and sectors)

    INputs:
        year(int) : Year for which sea ice loss contributions has to be calculated
        db_conn (SQLAlchemy connection) : SQL Alchemy connection to database
        top_n (int) : Number of top countries to select. Max 10
        cum ( boolean) : To get cummulative emissions or for a given year"
        per_cap (string} "per capita share
        sec_gas (string) : Show data by sectors or gas type
    """
    # CLip input to 3,10
    top_n = np.clip(top_n,3,20)
    
    # GHG gas
    gas = "CO2"
    # IDs to be exluced from the source DS for CAIT. These are top level categories and Land usage and change, which is usually negative
    exl_ids = (1298,1300,1299,1304,1313)

    # Exclude EU individual countries from the list and WORLD as a category
    exl_ccodes = get_group_ccodes(db_conn,"EUU")
    exl_loc = ('WORLD', "ANNEXI", "UMBRELLA", "NONANNEXI", "BASIC") + exl_ccodes


    # Declare statements
    
    # Declare statement
    stmt_cum = "select "\
            "tce.iso_a3,"\
            "tce.sector,"\
            "sum(tce.value) as value "\
		"from {} tce "\
            "join {} tcs on tce.sector = tcs.name "\
            "join t_climatewatch_datasources tcd on tce.data_source = tcd.name "\
        "where " \
            "tce.data_source ='{}' and "\
            "tce.gas = '{}' and "\
            "tce.iso_a3 not in {} and "\
            "tce.year >= '{}' and  "\
            "tcs.id not in {} and "\
            "tcs.data_source_id = tcd.id "\
        "group by tce.iso_a3, tce.sector"
        
    stmt_year = "select "\
            "tce.iso_a3,"\
            "tcs.id,"\
            "tcs.parent_id,"\
            "tce.sector,"\
            "tce.value "\
		"from {} tce "\
            "join {} tcs on tce.sector = tcs.name "\
            "join t_climatewatch_datasources tcd on tce.data_source = tcd.name "\
        "where " \
            "tce.data_source ='{}' and "\
            "tce.gas = '{}' and "\
            "tce.iso_a3 not in {} and "\
            "tce.year = '{}' and  "\
            "tcs.id not in {} and "\
            "tcs.data_source_id = tcd.id" # hard coded for CAIT
            
    #print(f"year : {year}")
    stmt = f"select distinct(year) as year from {tbl_ghg} where data_source = '{source}' and gas = '{gas}'"
    ds_years = pd.read_sql(stmt, con= db_conn).squeeze()
    ds_years= ds_years.sort_values(ascending =False)
    min_year = ds_years.min() 
    max_year = ds_years.max()
    
    if not year is None: 
        year = np.clip(year, min_year, max_year)

    if cum:
        if year is None:
            year = min_year
        stmt = stmt_cum.format(tbl_ghg,t_sectors, source, gas, exl_loc, year, exl_ids)   
        #print( f"cum : {cum}") 
    else:
        if year is None:
            year = max_year
        stmt = stmt_year.format(tbl_ghg,t_sectors, source, gas, exl_loc, year, exl_ids)
    
    df_emissions = pd.read_sql(stmt, con= db_conn)
    

    # Create groups for top_n and Others
    l_top_n = df_emissions.groupby("iso_a3")["value"].sum().nlargest(top_n).index.to_list()
    
    df_emissions["group"] = "Others"

    top_n_grp_str = "Top " + str(top_n) 
    #print(top_n_grp_str)

    df_emissions.loc[df_emissions.iso_a3.isin(l_top_n), "group"] = top_n_grp_str


    # Convert values to sea ice from CO2 emissions
    df_emissions["value"] *= si_co2_factor

    # top_n contribution percentage towards sea ice area loss
    top_contr = np.round(df_emissions.loc[df_emissions["group"] ==  top_n_grp_str, "value"].sum()/ df_emissions["value"].sum() *100,2)
  

    # Build tree stucture for sunburst chart
    exclude_others = False

    
    tree = []
    for group in df_emissions.group.unique():
        
        if exclude_others and group == "Others":
            continue
        #print(group)
        grp_dict = {}

        grp_dict["value"] = np.round(df_emissions.loc[df_emissions["group"] == group, "value"].sum(),1)

        grp_dict["name"] = group #+ "\n"+ str(np.round(grp_dict["value"],2))

        # Set group colors
        if group == "Others":
            grp_dict["itemStyle"] = { "color": group_color_dict.get(group)}

        else:
            grp_dict["itemStyle"] = { "color": group_color_dict.get("Top")}

        grp_dict["children"] = []
        
        for country in df_emissions.loc[df_emissions["group"]== group, "iso_a3"].unique():
            
            c_dict = {}
            
            c_dict["value"] = np.round(df_emissions.loc[df_emissions.iso_a3 == country, "value"].sum(),2)
        
            # If value of section is more than 10% of parent section, then show value in the label
            # if c_dict["value"]/grp_dict["value"] > .05:
            #     c_dict["name"] = country + "\n" + str(np.round(c_dict["value"],2))
            # else:

            c_dict["name"] = country
            # Set country colors for Others group same as group color
            # Set labels to transparent for other countries
            if group == "Others": 
                c_dict["itemStyle"] = { "color": country_color_dict.get(group)}
              #  c_dict["label"] = { "show" : False}
            else:
                c_dict["itemStyle"] = { "color": country_color_dict.get(country)}
            
            c_dict["children"] = []
            
            for sec in df_emissions.loc[df_emissions.iso_a3 == country, "sector"]:
                sec_dict = {}
                
                sec_dict["name"] = sec
                val = df_emissions.loc[(df_emissions.iso_a3 == country) & (df_emissions.sector == sec), "value"].values[0]
                
                sec_dict["value"] = 0 if np.isnan(val) else np.round(val,2) 
                
                if group =="Others": # All with colors

                    sec_dict["itemStyle"] = { "color": sec_color_dict.get(group)}
                else:
                    sec_dict["itemStyle"] = { "color": sec_color_dict.get(sec)}
                
                c_dict["children"].append(sec_dict)
            
    
            grp_dict["children"].append(c_dict)

        tree.append(grp_dict)

        emissions = { "name" : "Total Sea Ice Loss " + str(year),
                            "children" : tree,
                            "value" : np.round(df_emissions.value.sum(),1)
                            }
    
    if cum:
        emissions["name"] = " Total sea ice loss since " + str(year)

    
    sec_legend = { sec: sec_color_dict[sec] for sec in df_emissions["sector"].unique()}

    tot_loss_n = emissions["value"]
    tot_loss = "{:,}".format(tot_loss_n)

    if cum:
        title = f"{tot_loss} km² Cumulative Arctic Sea Ice loss contribution by Top emitters since {year}"
    else:
        title = f"{tot_loss} km² Arctic Sea Ice loss contribution by Top emitters for year {year}"
   

    return [emissions], top_contr, year, sec_legend, ds_years, title, tot_loss_n


def sialoss_sectors(db_conn, source = "CAIT", year = 1990,cum=True, per_cap=False):
    """
    Function to get sea ice area loss for a given year by top emitters and other countries countries ( EU is considered as single entity)

    Inputs:
        year(int) : Year for which sea ice loss contributions has to be calculated
        db_conn (SQLAlchemy connection) : SQL Alchemy connection to database
        cum( String) : To have a cumulative view since year OR for a given year
        
    """
    
    # GHG gas
    gas = "CO2"
   

    iso_a3 = 'WORLD'

     # IDs to be exluced from the source DS for CAIT. These are top level categories and Land usage and change, which is usually negative
    exl_ids = (1298,1300,1299,1304,1313)

    # Declare statements
    # 
    stmt_year = "select "\
            "tce.sector,"\
            "tce.value "\
        " from {} as tce "\
        "join t_climatewatch_sectors as tcs on tce.sector = tcs.name "\
        "join t_climatewatch_datasources tcd on tce.data_source = tcd.name "\
        "where " \
            "tce.data_source ='{}' and "\
            "tce.gas = '{}' and "\
            "tce.iso_a3 = '{}' and "\
            "tce.year = '{}' and "\
            "tcs.id not in {} and "\
            "tcs.data_source_id = tcd.id"
            
    stmt_cum = "select "\
            "tce.sector,"\
            "sum(tce.value) as value"\
        " from {} as tce "\
        "join t_climatewatch_sectors as tcs on tce.sector = tcs.name "\
        "join t_climatewatch_datasources tcd on tce.data_source = tcd.name "\
        "where " \
            "tce.data_source ='{}' and "\
            "tce.gas = '{}' and "\
            "tce.iso_a3 = '{}' and "\
            "tce.year >= '{}' and "\
            "tcs.id not in {} and "\
            "tcs.data_source_id = tcd.id "\
        "group by tce.sector"
            

    stmt = f"select distinct(year) as year from {tbl_ghg} where data_source = '{source}' and gas = '{gas}'"


    ds_years = pd.read_sql(stmt, con= db_conn).squeeze()

    ds_years = ds_years.sort_values(ascending=False)
    
    min_year = ds_years.min()
    max_year = ds_years.max()
    
    if not year is None: 
        year = np.clip(year, min_year, max_year)
    else:
        if cum :
            year = min_year
        else:
            year = max_year

    # Get GHG emissions data  
    if cum:   
        stmt = stmt_cum.format(tbl_ghg, source, gas, iso_a3, year, exl_ids)

    else:
        stmt = stmt_year.format(tbl_ghg, source, gas, iso_a3, year, exl_ids)
 
    df_emissions = pd.read_sql(stmt, con= db_conn)


    if per_cap:
        # Select population for the world.
        stmt = f"select population from {tbl_population} where  iso_n = '900' and year = '{year}'"

        pop = pd.read_sql(stmt, con= db_conn).values[0][0] * 1000 # Original values are in thousands
        df_emissions["value"] = (df_emissions["value"] * 1000 * 1000)/pop # emissions values converted to m2

    df_emissions = df_emissions.dropna()
    df_emissions = df_emissions[df_emissions["value"] != np.infty] 

    # Convert values to sea ice from CO2 emissions. This is now in m2
    df_emissions["value"] *= si_co2_factor

    # Build stucture for doughnut chart

    series = []

    df_emissions = df_emissions.sort_values(["value"], ascending= False)

    df_emissions["value"] = np.round(df_emissions["value"],1)

    for idx, row in df_emissions.iterrows():
    

        s_dict = {}
        
        s_dict["value"] = row[ "value"]

        s_dict["name"] = row["sector"]
        s_dict["itemStyle"] = { "color": sec_color_dict.get(row["sector"])}
        
        series.append(s_dict)
  
    sec_legend = { sec: sec_color_dict[sec] for sec in df_emissions["sector"].unique()}
    
    tot_loss_n = np.round(df_emissions["value"].sum(),1) 

    tot_loss = "{:,}".format(tot_loss_n)

    if cum:
        title = f"Cumulative Arctic Sea Ice loss ( in km² ) contribution by sectors since {year}"
        subtitle = f"{tot_loss} km² by all sectors"
    else:
        if per_cap:
            title = f"Arctic Sea Ice loss contribution per capita (in m²) by sectors for year {year}"
            subtitle = f"{tot_loss} m2 per capita by all sectors"
            
        else:
            title = f"Arctic Sea Ice loss contribution ( in km² ) by sectors for year {year}"
            subtitle = f"{tot_loss} km² by all sectors"



    return series, year, ds_years, sec_legend, title, subtitle, tot_loss_n


def sialoss_country(db_conn, source = "CAIT" ,location = "WORLD", cum =False, per_cap=False) :
    """
    Function to get sea ice area loss for a given year or cumulative for a given country countries ( EU is considered as single entity) and sectors

    INputs:
        year(int) : Year for which sea ice loss contributions has to be calculated
        db_conn (SQLAlchemy connection) : SQL Alchemy connection to database
        cum ( String) : if the data has to cumulatie or not
    """
    
    # GHG emissions source
    
    # GHG gas
    gas = "CO2"    

    # Get WORLD data as well to find the contribution of a country
    location = location.upper()
    
    excl_ids = (1298,1300,1299,1304,1313) # Exclude Land use change and other parent categories
        
    stmt_year = "select "\
            "tce.year, "\
            "tce.sector,"\
            "tce.value "\
		"from {} tce "\
            "join {} tcs on tce.sector = tcs.name "\
            "join t_climatewatch_datasources tcd on tce.data_source = tcd.name "\
        "where " \
            "tce.data_source ='{}' and "\
            "tce.gas = '{}' and "\
            "tce.iso_a3 = '{}' and "\
            "tcs.id not in {} and "\
            "tcs.data_source_id = tcd.id" 
            #           "tce.year = '{}' and  "\
            
    #Find latest year for which data exists in GHG emissions table
    stmt = f"select max(year) from {tbl_ghg} where data_source = '{source}'"
    max_year = pd.read_sql( stmt, con = db_conn).iloc[0,0]
    
    stmt = stmt_year.format(tbl_ghg,t_sectors, source, gas, location, excl_ids)
    #print(stmt)
    df_emissions = pd.read_sql(stmt, con= db_conn)
    
    # world_ghg
    stmt = "select year, sum(value) as value from {} where data_source = '{}' and "\
            "iso_a3 = 'WORLD' and "\
            "sector in {} and "\
            "gas = '{}' "\
            "group by year"

    if source == "CAIT":
        stmt = stmt.format(tbl_ghg, source, ("Total excluding LUCF", "Bunker Fuels"), gas)
    elif source == "PIK":
        stmt = stmt.format(tbl_ghg, source, ("Total excluding LULUCF", "Bunker Fuels"), gas)

    df_world_ghg = pd.read_sql(stmt, con = db_conn)
    
    # Calculate Sea ice loss
    df_emissions["sia_loss"] = si_co2_factor * df_emissions["value"]
    
    start_year = df_emissions["year"].min()

    # Prepare title and subtitle for the chart and contributions
    
    if cum:
        tot_sia_loss= np.round(df_emissions["sia_loss"].sum(),1)
        
        # world GHG
        world_ghg = df_world_ghg[ "value"].sum()

        # Total GHG for the country
        tot_ghg = np.round(df_emissions["value"].sum(),1)        
        
        # Contribution
        contr = np.round((tot_ghg /world_ghg) * 100 ,1)

    
        title = f"Cumulative Arctic Sea Ice loss (km²) contribution by { location}"     
        subtitle = f"{location} caused {tot_sia_loss:,} km² ({contr} %) of Arcic Sea Ice loss since { start_year}!"
    
    else:
        if per_cap:
            
             # Select years for whch population data should be selected
            year_list = tuple(df_emissions["year"].unique())

            if location == "EUU":
                loc_list = get_group_ccodes(db_conn, location)
                stmt = f"select year, sum(population) as population from {tbl_population} where  iso_a3 in {loc_list} and year in {year_list} group by year"
            
            elif location == "WORLD": 
                stmt = f"select year, sum(population) as population from {tbl_population} where  iso_n = '900' and year in {year_list} group by year"
            else:
                stmt = f"select year, population from {tbl_population} where  iso_a3 = '{location}' and year in {year_list}"
            
            df_pop = pd.read_sql(stmt, con= db_conn, index_col= "year")
            
            # total sia loss for latest year        
            tot_sia_loss= df_emissions.loc[df_emissions["year"] == max_year, "sia_loss"].sum()
            # convert into per capita m2
            
            tot_sia_loss = np.round( 1000 * (tot_sia_loss / df_pop.loc[max_year].sum() ),1)

                
            # Total GHG for the country
            tot_ghg = df_emissions.loc[df_emissions["year"] == max_year, "value" ].sum()
            
            # convert to per capita
            tot_ghg =  np.round( 1000 * (tot_ghg / df_pop.loc[max_year].sum() ),1)
            
            # world GHG
            world_ghg = df_world_ghg.loc[df_world_ghg["year"] == max_year, "value"].sum()            
            
            # Get world population for recent year
            stmt = f"select sum(population) as population from {tbl_population} where  iso_n = '900' and year = {max_year} group by year"
            world_pop = pd.read_sql(stmt, con = db_conn).values[0][0]
            
            # convert to per capita
            world_ghg = np.round(si_co2_factor * 1000 * (world_ghg/world_pop),1)

            contr = tot_sia_loss/world_ghg

            title = f"Per capita Arctic Sea Ice loss (m²) contribution for { location}"     
            
            subtitle = f"{location} per capita is {tot_sia_loss:,} m² per capita"
            
            if location != "WORLD":
                subtitle+= f" against World\'s per capita {world_ghg} m² of Arcic Sea Ice loss in { max_year}!"

 
        else:
            tot_sia_loss= np.round(df_emissions.loc[df_emissions["year"] == max_year, "sia_loss"].sum(),1)
        
            # world GHG
            world_ghg = df_world_ghg.loc[df_world_ghg["year"] == max_year, "value"].sum()

            # Total GHG for the country
            tot_ghg = np.round(df_emissions.loc[df_emissions["year"] == max_year, "value"].sum(),1)
            
            # Contribution
            contr = np.round((tot_ghg /world_ghg) * 100 ,1)


            title = f"Annual Arctic Sea Ice loss (km²) contribution for { location}"     
            subtitle = f"{location} caused {tot_sia_loss:,} km² ({contr} %) of Arcic Sea Ice loss in { max_year}!"
    

    
    # Prepare data for   echarts line chart

    #df_emissions["sia_loss"] = np.round(df_emissions["sia_loss"],1)
    df_emissions = df_emissions.pivot_table(index = "year", columns="sector", values="sia_loss")


    if per_cap and  not cum:
        # Merge population data without EUU
        #print(f"calculating per cap. cum :{cum}")

        # Select years for whch population data should be selected
        year_list = tuple(df_emissions.index.to_list())

        if location == "EUU":
            loc_list = get_group_ccodes(db_conn, location)
            stmt = f"select year, sum(population) as population from {tbl_population} where  iso_a3 in {loc_list} and year in {year_list} group by year"
        
        elif location == "WORLD": 
            stmt = f"select year, sum(population) as population from {tbl_population} where  iso_n = '900' and year in {year_list} group by year"
        else:
            stmt = f"select year, population from {tbl_population} where  iso_a3 = '{location}' and year in {year_list}"
        
        df_pop = pd.read_sql(stmt, con= db_conn, index_col= "year")


        #Calculate per capita sea ice loss. Multiply factor of 1000 as population records are in 1000s
        df_emissions = df_emissions.div(df_pop.squeeze()*1000,axis ="index")* 1000* 1000 # SIA loss in m2
        df_emissions = df_emissions.dropna()

    
    if cum:
        df_emissions = df_emissions.cumsum()
    
    df_emissions = np.round(df_emissions,1)
    
    sectors= [df_emissions.columns.name] + df_emissions.columns.to_list()

    sialoss_source = []
    for sector in sectors:
        if sector in df_emissions.columns:
            series = [sector] + df_emissions[sector].to_list()

        else:
            series = [sector] + df_emissions.index.astype(str).to_list()
        
        sialoss_source.append(series)

    sia_series_list = []

    for i in range(len(sectors) -1):
        
        sia_series_list.append( {'type': 'line', 'smooth': 'true', 'seriesLayoutBy': 'row', 'emphasis': {'focus': 'series'}} )

    
    
    return sialoss_source, tot_sia_loss, tot_ghg, contr, sia_series_list, start_year, title, subtitle


def co2_emissions_equivalent( reference , conn = None):
    """
    Use CO2 emissions equivalennce table to find number/ amount of a given activity needed to have Co2 emissions ( tons) as given in reference

    Args:
        con ([SQLAlchemy connection], optional): [Database connection]. Defaults to None.
        reference ([float]): [CO2 amount in metric tons for which co2 activity equivalence to be calculated]. 
    """
     # table name of the DB table where city area reference lookup is
    tbl_name = "t_ref_co2_emissions_equivalences"

    stmt_base = "select item, direction, co2 from {}"
    
    stmt = stmt_base.format(tbl_name)

    print( stmt)
    df_co2_eq = pd.read_sql(stmt, con=conn)

    df_co2_eq["count"] = np.round(reference / df_co2_eq["co2"],1)

    df_co2_eq = df_co2_eq.sort_values("count", ascending= False)

    return df_co2_eq


def loc_area_multiplier(conn = None, location = None, reference = None):
    """
    Calculates number of location units that can be contained in the reference value.
    Database table is t_ref_largest_cities
    Args:
        con (SQLAlchemy connection) : connectin object to the Database
        location (str, optional): City/ locality name to be referred in the table. Defaults to "London".
        reference ([type], optional): Value in km2 that needs to be used to calculate number of location units. Defaults to None.

    Returns:
        [dict]: Location : number of units dictionary
 """
    # table name of the DB table where city area reference lookup is
    tbl_name = "t_ref_largest_cities"

    stmt_base = "select city, country, area from {} where city in {}"
    
    if location is None:
        location = sia_cities

    if isinstance(location, str):
        location = (location)

    stmt = stmt_base.format(tbl_name, location)


    df_cities = pd.read_sql(stmt, con = conn)

    #df_cities["message" ] = (reference/ df_cities["area"]).astype(int).astype(str) + " times the size of " + df_cities["city"] + " (" + df_cities["country"] + " )"    
    df_cities["count"] = np.round( reference/ df_cities["area"],1)

    df_cities = df_cities.sort_values("area")
    return df_cities



##########################################################################################

################### Sea ice age chart ###################################################

############################################################################################

def get_siage(conn = None, by = "month", month = 9, year = None, agg = "m", pct= False, siac ="y", polar = True):
    """
    Returns series data for e-charts API to show Sea Ice age trends in different ways.
    Also return some key indicators.

    Args:
        conn ( SQLAlchemy connection) : DB connection
        by (str, optional): Possible options : . Defaults to "month".
            1. month :  Trend for a given month over years for all categories of sea ice age. This uses september month as default
            2. year : Shows weekly or monthly trends for given year. 
            3. total : Overall trends for all years for all months
        month (int, optional): Month for which to show trends over the years. Defaults to 9.
        year (int, optional): Year for which weekly trends to be shown. Defaults to latest year for which there is full 1 year of data available 
        agg ( str, optional) : If trend is yearly then it can be aggregate at weekly level of monthly level
        pct (bool, optional): To show results in percentage or absolute values
        siac ( str, optional): Categorize sea ice by years or by categories
    Returns:
        Dict: { series : series data that will feed the e-charts api
                5y (float): how much of 4+ year sea ice age has changed since the beginning compared to itself
                5y_pct (tuple): How much of 4+ year ice change has change in percentage of overall ice from the beginning to now
                }
    """

    
    area_factor = 12.5 * 12.5

    si_cols = [ "y" + str(i) for i in range(1,6)]
    
    si_col_y = ["-".join( [ str(i), str(i+1) ] ) if i < 4 else "4+" for i in range(5) ]

    si_col_c = ["new", "first year", "multi-year"]

    stmt_m = "select year, {}  from {} where month = '{}'"
    stmt_ym = "select month , {} from {} where year = '{}'"
    stmt_yw = "select week , {} from {} where year = '{}'"
    stmt_tot = "select date, {} from {}"
    

    # If trends are total or overall trends

    if by =="total":
        stmt = stmt_tot.format( ", ".join(si_cols), tbl_siage)
        df_sia = pd.read_sql(stmt, con = conn, index_col= "date")

        df_sia = df_sia.resample("M").median()
      

    # if trends of a given month has to be shown over years
    if by == "month":
        xname ="year"

        stmt = stmt_m.format(", ". join(si_cols), tbl_siage, month)

        df_sia = pd.read_sql(sql = stmt, con= conn )

        df_sia = df_sia.groupby("year").agg("median")

        # Prepare data for comparison indicators

        # Get first and last year
        y_first = df_sia.index.min()
        y_last = df_sia.index.max()

        # Get values of si age in the first year
        sia_y_first = df_sia.loc[y_first, si_cols].squeeze()
        
        # Get values of si age in the last year
        sia_y_last = df_sia.loc[ y_last, si_cols].squeeze()

    # Or if the trends for a given year by months has to be shown
    elif by == "year":
        

        if agg == "m": 
            xname = "month"
            stmt = stmt_ym.format( ", ".join(si_cols), tbl_siage, year)
            df_sia = pd.read_sql(stmt, con= conn)

            df_sia = df_sia.groupby("month").agg("median")
        elif agg == "w":
            stmt = stmt_yw.format( ", ".join(si_cols), tbl_siage, year)
            df_sia = pd.read_sql(stmt, con= conn, index_col = "week")


        # Prepare data for comparison indicators
        
        # Compare winter/ max extent/ March values 
        stmt = f"select distinct(year) from {tbl_siage} where month = '3'"
        ds_years = pd.read_sql(stmt, con = conn).squeeze()

        y_first = ds_years.min()
        y_last = ds_years.max()

        stmt_c = "select year, {} from {} where year = '{}' and month = '3'"

        stmt = stmt_c.format(" ,".join(si_cols), tbl_siage, y_first)
        sia_y_first = pd.read_sql(stmt, con = conn)
        sia_y_first = sia_y_first.groupby("year").median().squeeze()

        stmt = stmt_c.format(" ,".join(si_cols), tbl_siage, y_last)
        sia_y_last = pd.read_sql(stmt, con = conn)
        sia_y_last = sia_y_last.groupby("year").median().squeeze()

    # If Sea ice catogorization is by years
    if siac == "y": 
        si_col_text = si_col_y
    
    else:
        # multi years columns to be combined
        multi_col = [ "y" + str(i) for i in range(3,6) ]

        df_sia["m"] = df_sia[multi_col].sum( axis=1)

        sia_y_first["m"] = sia_y_first[multi_col].sum()
        sia_y_last["m"] = sia_y_last[multi_col].sum()
        
        df_sia = df_sia.drop(columns=multi_col)

        sia_y_first = sia_y_first.drop(multi_col)
        sia_y_last = sia_y_last.drop(multi_col)

        # Set columns to sea ice columns for categories
        si_col_text = si_col_c

    # prepare data for e Charts API
    df_sia.columns = si_col_text

    sia_y_first.index = si_col_text
    sia_y_last.index = si_col_text

    # Convert to percentage
    if pct:
        df_sia = 100 * df_sia.divide(df_sia.sum(axis=1), axis=0)
        yname = "percentage (%)"
    # Or to km2 in millions
    else:
        yname = "millions km²"
        df_sia = df_sia*area_factor/1000/1000

    df_sia = np.round(df_sia,2)

    # Create data for e-charts and other indicators
    if by =="year":
        xaxis_data = [calendar.month_abbr[i] for i in df_sia.index.to_list()]
    else:
        xaxis_data = df_sia.index.to_list()

    # calculate change in old sea ice
    # %age of y5 ice in the first reading
    
    pct_f = 100* (sia_y_first[si_col_text[-1]]/ sia_y_first.sum())

    # %age of y5 in last year
    pct_l = 100 * (sia_y_last[si_col_text[-1]]/ sia_y_last.sum())

    change = {
        "ice_name" : si_col_text[-1] + (" year" if siac =="y" else ""),
        "before" : {
                "year" : y_first,
                "pct" : pct_f
        },
        "after" : {
                "year" : y_last,
                "pct" : pct_l
        },
        "diff" : 100*(pct_f - pct_l)/pct_f,
        "month" : calendar.month_name[month] if by =="month" else "March"
    }



    si_col_text.reverse()
    series = []
    
    for i, col in enumerate(si_col_text):
        if by == "year" and polar:
            if True: #col != "0-1":
                single = {
                    "name" : col,
                    "type" : "bar",
                    "coordinateSystem" : "polar",
                    "stack" : "siage",
                    "data" : df_sia[col].to_list()
                }

        else:
            single = {
                "name" : col,
                "type" : "line",
                "stack" : "siage",
                "areaStyle" : {
                    "opacity" : 1
                },
                "emphasis": { "focus" : "series"},
                "data" : df_sia[col].to_list()
            }
        if siac == "y":
            if col == single["name"]:
                si = "4+" if i == 0 else str(len(si_col_text)-i-1) + "-" + str(len(si_col_text)-i)
                single["itemStyle"] = {
                    "color" : siage_color_dict[si]
                }

       
        series.append(single)


    return { 
            "xaxis_data" : xaxis_data,
            "series" : series,
            "yname" : yname ,
            "xname" : xname,
            "change" : change,
            "polar" : polar
        }

def siage_sankey(conn = None, month= 10, hideLoss = False, hideY1 = False, period =10, type="ms"):
    """
    Generate Sea ice age data for echarts Sankey chart by decadal change. takes the data from start and sample the annual data for March based on decade closures.
    
    Input:
        conn(SQLAlchmey connection) : SQL Alchemy connection object to database 
        month( int) : Month of the year which will be used as a refereence for the year. Median of that month is used.
        hideLoss(bool) : Flag to show or hide "loss" node
        hideY1 (bool) : Flag to show or hide "year 1 or 0-1 year" old ice
        period (int) : number of years to be used as period e.g. 5 years or 10 years.
        type ( str) : type of calculation to perform
                    "ms": years are taken as milestones. Values represent the amount of sea ice for a given age in that specific year
                    "pd": periods are used as duration. Values represent median of the sea ice for the whole period for given month. 
                    "be" : begin and end of the observations only.
    Returns:
        sankey_nodes: name of the nodes to be given to sankey chart
        sankey_links : source and target links for sankey chart
    """


    siage_col_map = {}

    disp_col = [ str(i) + "-" + str(i+1)  if i < 4 else "4+" for i in range(5)]

    sel_cols = [ "y" + str(i) for i in range(1,6)]

    stmt = "select year, {} from {} where month = '{}'"

    stmt = stmt.format(", ".join(sel_cols), tbl_siage, month)
    df_siage = pd.read_sql(stmt, con= conn)

    y_min = df_siage["year"].min()
    y_max = df_siage["year"].max()

    
    # generate periods
    sel_years = list(range((y_min//period)*period, y_max+1, period))
    
    if type == "ms":
        sel_years = [ p for p in  sel_years if p >= y_min]
        df_siage["period"] = df_siage["year"]
        subtitle = "Each stage in chart shows median values for a give year for " + calendar.month_name[month]
    elif type =="pd":
        sel_years = [ p for p in  sel_years[:-1] if p >= y_min]

        df_siage["period"] = period* (df_siage["year"]//period)

        subtitle = "Each stage in chart is median of the decade for " + calendar.month_name[month]
    
    elif type == "be":
        sel_years =[y_min, y_max]
        df_siage["period"] = df_siage["year"]

        subtitle = "Each stage in the chart is median values for a given year for " + calendar.month_name[month]

    # select the records for given periods/ milestones and get median values
    df_siage = df_siage.loc[df_siage["period"].isin(sel_years)].groupby("period")[sel_cols].median()

    df_siage = df_siage.stack()
    # Covert into area in million km2 from grid count with each grid of size 12.5 x 12.5 km
    df_siage = np.round(df_siage * 12.5 * 12.5/1000/1000,2)


    links = []

    # for each milestone mark
    for d in range(len(sel_years)-1):
        y = sel_years[d]
        y1p = sel_years[d+1]
        
        # for milestone of ice till current milestone add links
        for i in range(d+1):
            if i == d:
                
                link_new = {
                            "source" : str(y) + " : new",
                            "target" : str(y1p) + " : " + "0-1",
                            "value" : 0 ,#df_siage[ y1p, "y1"],
                            "lineStyle" : {
                                "opacity" : 0
                            }
                }
                
            else:
                link_new = {
                            "source" : str(sel_years[i]) + " : new",
                            "target" : str( sel_years[i+1]) + " : new",
                            "value" : 0,
                            "lineStyle" : {
                                            "color": 'line',
                                            "opacity": 0
                                        }
                            }
                          
            links.append( link_new)
        
        # for each age category of sea ice
        for i, a in enumerate(sel_cols[:-1]):
            age = a
            age1p = "y"+ str(i+2)
            

            #if amount of next stage ice is less than previous stage, then all contribution came from previous stage and decade
            if df_siage[y1p,age1p] < df_siage[y,age]: 
                link = {
                        "source" : str(y) + " : " + disp_col[i],
                        "target" : str(y1p) + " : " + disp_col[i+1],
                        "value" : df_siage[y1p,  age1p]
                }
                links.append(link)
                
                link = {
                        "source" : str(y) + " : " + disp_col[i],
                        "target" : str(y1p) + " : loss",
                        "value" :  np.round(df_siage[y,age] - df_siage[y1p,  age1p],2) 
                      
                }
                links.append(link)

                # if the age in check is y5 that is last year of sea ice age
                if age1p == "y5":
                    link = {
                        "source" : str(y) + " : " + disp_col[i+1],
                        "target" : str(y1p) + " : loss",
                        "value" : df_siage[y, age1p]
                    }
                
                    links.append(link)
                
            # if amount of next stage ice is more than previous stage and decade 
            else:
                # connection that came from the previous stage and decade
                link = {
                    "source" : str(y) + " : " + disp_col[i],
                    "target" : str(y1p) + " : " + disp_col[i+1],
                    "value" : df_siage[y,  age]
                }

                links.append(link)

                # connection that came from same stage but previous decade
                link = {
                    "source" : str(y) + " : " + disp_col[i+1], 
                    "target" : str(y1p) + " : " + disp_col[i+1],
                    "value" : np.round(df_siage[y1p,  age1p] - df_siage[y,  age],2)
                }
                links.append(link)
                
                # connection how much was same stage ice loss in previous decade
                link = {
                    "source" : str(y) + " : " + disp_col[i+1], 
                    "target" : str(y1p) + " : loss",
                    "value" : np.round(abs(df_siage[ y,age1p] - df_siage[y1p,  age1p] + df_siage[y,  age]),2)
                }
                links.append(link)

    if hideLoss:
        for link in links:
            if "loss" in link["target"]:
                link["lineStyle"] = {
                                    "color": 'line',
                                    "opacity": 0
                                }

    if hideY1:
        for link in links:
            if "y1" in link["source"]:
                link["lineStyle"] = {
                                    "color": 'line',
                                    "opacity": 0
                                }

    nodes = []

    for i,y in enumerate(sel_years):
        for a in disp_col + ["new", "loss"]:
            
            if (i==0 and a == "loss") :#or (y == sel_years[-1] and a == "new"):
                continue
                
            elif a == "new":
                node = { 
                    "name" : str(y) + " : " +a,
                    "itemStyle": {
                        "color" : siage_color_dict[a],
                        "opacity" : 0

                    },
                    "label" : {
                        "show" :  False
                    }
                }
                

            else:
                node = { 
                    "name" : str(y) + " : " + a,
                    "itemStyle": {
                        "color" : siage_color_dict[a]

                    }
                }
            

            if (a == "loss" and hideLoss) or ( a =="0-1" and hideY1):
                node["itemStyle"]["opacity"] = 0
                node["label"] = {
                    "show" : False
                }

            if y == sel_years[-1] and a == "0-1":
                node["value"] = df_siage[y,"y1"]

            nodes.append(node)

    subtitle 
    sankey = {
        "sk_nodes" : nodes,
        "sk_links" : links,
        "sk_subtext" : subtitle
    }


    return sankey


import os
def get_sia_fnames(remote = False):
    """
    Give file names of the Sea Ice age images as plotted by by NSIDC. Names are for starting week and last file(week) of the last month.
    
    NSIDC updates images once a month in the latest NSIDC - 0749 QL dataset.
    Starting week file is obtained from NSIDC - -611v4.1 product
    
    Input:
        remmote ( boolean) : flag if latest files for NSIDC images to be search locally or on NSIDC FTP server

    Output:
        tuple( obj) : 
            start file name from 1984 
            latest file name from 0749 product
            week number
        
    """
    nsidc_server = "sidads.colorado.edu"
    nsidc_0749_path = "/pub/DATASETS/nsidc0749_ql_iceage"
    
    local_img_path = "../../sea_ice_age/imgs/"
    local_nc_path = "../../sea_ice_age/data/"

    # local_img_path = "./nsidc/imgs/"
    # local_nc_path = "./nsidc/data/"

    fname_start = "iceage_nh_12.5km_{}_{}_v4.1.png"
    fname_end = "iceage_nh_12.5km_{}_{}_ql.png"
    
    dest_file = "./static/images/siage_latest.png"

    # Get latest filenames from ftp server is remote is True
    if remote:
        ftp = ftplib.FTP(nsidc_server)
        ftp.login()
        ftp.cwd(nsidc_0749_path)
        fnames = ftp.nlst("*.nc")
    else:
        # search in local directory
        fnames = glob.glob( local_nc_path + "*.nc")

    # Get the timestamp of the last image that is available on ftp server
    ds_fnames = pd.Series([ datetime.datetime.strptime(f.split("_")[-2], "%Y%m%d") for f in fnames], name ="dates")
    wkend_date_end = ds_fnames.max()
    wkstart_date_end = wkend_date_end - datetime.timedelta(days = 6)
    
    # Get the timestamps for the starting year i.e 1984 for the same week as the latest image available.
    wkend_date_start = datetime.date( 1984, 1,1) + datetime.timedelta(wkend_date_end.timetuple().tm_yday-1)
    wkstart_date_start = wkend_date_start - datetime.timedelta(6)
    
    # Create filnemas for start and end reference weeks
    fname_start = fname_start.format(wkstart_date_start.strftime("%Y%m%d"), wkend_date_start.strftime("%Y%m%d"))
    fname_end = fname_end.format(wkstart_date_end.strftime("%Y%m%d"), wkend_date_end.strftime("%Y%m%d"))
    
    # Download latest file and store as local file on server
    if remote: 
        # from FTP server
        ftp.retrbinary( "RETR " + fname_end, open(dest_file,'wb').write)
    
        ftp.close()

    else:
        # from local storage
        copyfile(local_img_path + fname_end, dest_file)
    
    # Week number as reference
    wn = wkend_date_end.timetuple().tm_yday//7

    return {
            "start_image": fname_start,
            "latest_image" : dest_file.split("/")[-1],
            "siage_week" : wn
    }
    
  