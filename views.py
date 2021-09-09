
from datetime import datetime
import calendar
from flask import Flask, render_template, jsonify, request
from flask import json
from . import app
from . import conn

from . import csutils
from . import config
from . import validations as val
    
# db_file = "./config/database.ini"

# conn = csutils.get_alchemy_connection(config.config_db(db_file))

@app.route("/")
# def hello():

#     return jsonify(hello = "world")
# @app.route("/seaice")
def seaice():
    """
     Main page that provides links to all other views

    
    """
    return render_template("index.html")

@app.route("/siage/")
def siage():
    """
    View to show change in amount of sea ice age segregated by age. variations are 
        annual change for a selected month since beginning
        monthly changes for a given year

    Input args:
        by ( String) : month or yearly. Defines type of trends to show on the graph
        month( String) : if by = month then number of the month
        year ( String) : if by = yearly then year
        pct( str) : y or n if the data has to be show as percentage or numbers

    Returns:
        [type]: [description]
    """

    # Get request parameters and check validity
    args = request.args

    by = val.siage_val(args.get("by", "month", type = str), "by")
    if by.find("Error") != -1:
        return render_template("sia_error.html", error= by )
    
    month = val.siage_val(args.get("month", 9, type = int), "month")
    if isinstance(month, str) :
        return render_template("sia_error.html", error= month )
    
    year, ds_years = val.siage_val(args.get("year", None, type = int), "year", conn= conn)
    if isinstance(year, str):
        return render_template("sia_error.html", error= year )
    
    pct = val.siage_val(args.get("pct"), "pct")

    agg = val.siage_val( args.get("agg"), "agg")
    if agg.find("Error") != -1:
        return render_template("sia_error.html", error= agg )

    siac = val.siage_val(args.get("siac"), "siac")
    if siac.find("Error") != -1:
        return render_template("sia_error.html", error= siac )

    

    siage = csutils.get_siage(conn = conn, by= by, month = month, year = year, pct= pct, agg = agg, siac = siac, polar=True)

    # Get NSIDC image names of the latest image and the corresponding image in 1984
    siafnames = csutils.get_sia_fnames()

    # get sankey elements for SI age echarts
    sankey_type = "ms"
    sankey = csutils.siage_sankey(conn = conn, month = month, hideLoss=True, hideY1= False,period=10, type =sankey_type)

    if isinstance(sankey,str) :
        return render_template("sia_error.html", error= sankey )


    return render_template("siage.html",    
                            years = ds_years,
                            month_names = calendar.month_name[1:],
                            sankey_type = sankey_type,
                            **sankey,
                            **siage,
                            **siafnames
                            )


@app.route('/sia_country/')
def sia_country():
    """
    View to show sia loss and GHG emissions by a country. Information contains
        1. total GHG emissions
        2. total SIA loss
        3. %age of worlds total
        4. data for E-charts by each Industry sector
        5. Samples of how much of that loss means in term of number of cities.
    
    Input args:
        iso_a3 (String) : Country or region code for which Sea ice loss and GH emisions data to be captured
        cum (String) : Y/N value to show cumulative contribution or for selected year
        year (int) : if cum= Y, then from that year . If cum =n then for the given year
        per_cap (String) : Y/N to give total emissions or per capita loss chart to be build

    Returns:
        [type]: [description]
    """

    # Get request parameters and set defaults in case not given
    args = request.args

    iso_a3 = val.sia_val_args(args.get("country", "WORLD").upper(), "iso_a3",conn=conn)

    if iso_a3.find("Error") != -1:
        return render_template("sia_error.html", error= iso_a3)

    cum = val.sia_val_args(args.get("cum", "n"),"cum")

    per_cap = val.sia_val_args(args.get("per_cap", "n"), "per_cap")
    
    ds = val.sia_val_args(args.get("ds", "CAIT"),"ds")
    if ds.find("Error") != -1:
        return render_template("sia_error.html", error= ds)


    data, tot_loss, tot_ghg, contr, sia_series,start_year, title, subtitle = csutils.sialoss_country(conn,cum=cum, source = ds, location = iso_a3, per_cap = per_cap)


    if per_cap :
        compare = csutils.co2_emissions_equivalent(tot_ghg, conn)
    
    else:
        compare = csutils.loc_area_multiplier(conn, reference=tot_loss)

    grp_countries = csutils.get_group_ccodes(db_conn=conn, g_code="EUU")

    country_list = csutils.get_country_list(db_conn= conn,source= ds)

    return render_template("sialoss_country.html", 
                                            title = title,
                                            subtitle = subtitle,
                                            data = data, 
                                            tot_loss = tot_loss, 
                                            tot_ghg= tot_ghg,
                                            compare = compare,
                                            grp_countries = grp_countries,
                                            sia_series = sia_series,
                                            iso_a3 = iso_a3,
                                            start_year = start_year,
                                            countries = country_list,
                                            per_cap = per_cap
                            )
    

@app.route('/sialoss')
@app.route('/sialoss/')
def sialoss():
    """
    Sea Ice loss view E-charts sunburst view to show SIA loss by top countres and others, by countries and Industrial sectors
    Contains sample data to show a comparison of Sea Ice area lost in terms of known city sizes

    Returns:
        [type]: [description]
    """
    # Get year parameter, if passed


    args = request.args
    #print(args)
    year = args.get("year", None, type = int)

    top_n = args.get("top_n", 10, type = int)

    # Data source 
    ds = val.sia_val_args(args.get("ds", "CAIT", type = str).upper(), "ds")
    if ds.find("Error") != -1:
        return render_template("sia_error.html", error= ds)
    # Get cummulative paramter if passed
    cum = val.sia_val_args(args.get("cum", "y"), "cum")

    # get per_cap parameter
    per_cap = val.sia_val_args(args.get("per_cap", "n"), "per_cap")
    
    # get data_by parameter
    data_by = val.sia_val_args(args.get("data_by", "c", type = str),"data_by")
    if data_by.find("Error") != -1:
        return render_template("sia_error.html", error= data_by)

    if not year is None:
        year = int(year)


    grp_countries = csutils.get_group_ccodes(db_conn=conn, g_code="EUU")
    #print(cum)

    # If data to be shown b countries
    if data_by == "c":
        if per_cap:
        
            data, c_year, years, title,subtitle,tot_loss = csutils.sialoss_top_per_cap(db_conn = conn, source = ds, year= year,top_n= top_n)
        
            compare = csutils.co2_emissions_equivalent(tot_loss/csutils.si_co2_factor, conn)
    
    
            return render_template("sialoss_percap.html", year = c_year, 
                                                title = title,
                                                subtitle = subtitle,
                                                data = data, 
                                                per_cap= per_cap,
                                                compare = compare,
                                                years = years,
                                                tot_loss = tot_loss
                                )

        data, top_contr, c_year, sec_legend, years, title, tot_loss = csutils.sialoss_top_cum(conn,source = ds, year = year,cum=cum, top_n=top_n)

        compare_cities = csutils.loc_area_multiplier(conn, reference=tot_loss)
        return render_template("sialoss.html", source = ds,
                                                year = c_year, 
                                                title = title,
                                                data = data, 
                                                top_contr = top_contr, 
                                                sec_legend = sec_legend, 
                                                tot_loss= tot_loss,
                                                compare = compare_cities,
                                                grp_countries = grp_countries,
                                                per_cap= per_cap,
                                                years = years
                                )

    # If data to be shown by sectors
    if data_by =="s":
        data, c_year, years, sec_legend, title, subtitle, tot_loss = csutils.sialoss_sectors(conn,source = ds, year = year, cum=cum, per_cap = per_cap)
        if not per_cap : 
            compare = csutils.loc_area_multiplier(conn, reference=tot_loss)
        else:
            compare = csutils.co2_emissions_equivalent( reference=tot_loss/csutils.si_co2_factor, conn=conn)
            

        return render_template("sialoss_sectors.html", source = ds,
                                                year = c_year, 
                                                title = title,
                                                subtitle = subtitle,
                                                data = data, 
                                                sec_legend = sec_legend, 
                                                tot_loss= tot_loss,
                                                compare = compare,
                                                grp_countries = grp_countries,
                                                per_cap= per_cap,
                                                years = years
                                )





    
