# Various Arctic Sea Ice change graphic visualizations

- Sea Ice loss contribution by countries and sectors based on GHG emissions
- Sea Ice loss trend for countries by industry sectors
- Sea Ice age trends over time

**NONE: None of these are developed to be production ready applications. Just for education purposes.**

# Configuration and run
- use requirements.txt (pip) or environments,.yml(conda) to setup flask environment.
- To run from VS Code 
  - make sure that .vscode/settings.json points to the correct python.
  - Check .vscode/launch.json for settingsif you have changed any file name.
  - Run the envoronment in VS code by selecting the correct configuration
- To run from commond prompt
  - make sure that current working directory is root directory of this application
  - Set the FLASK_APP="webapp" in your python virtual environment.
    - For powershell - $env:FLASK_APP="webapp"
    - For windows cmd - set FLASK_APP="webapp"
    - For unix/MacOS - export set FLASK_APP="webapp" 

# Application endpoints

## /siage
- Simple tool to assess Arctic sea ice age changes over time
- parameters:
    - by : trends by year or by month
    - age categorization : by year or age categories
    - %age : show values or percentage
- Also shows a sankey chart of the change over time.
- Comparison of the latest week image available on NSIDC server in comparison to same week in 1984. NOTE: images are not updated by this falsk app, another script needs to be run monthly to downloaded latest images from NSICD server
- Small description of the Sea Ice and datasources used.

## /sialoss
- Arctic Sea ice loss contribution by countries and sectors based on GHG emissions.
- filters
  - Data by : Countries or sectors
  - Cumulative : cumulative contribution or for a given year
  - Data source : CAIT or PIK
  - per capita: total or per capita contribution
  - year : to select a given year 
- Gives some examples of the size of sea ice loss in comparison to popular city sizes

## /sia_country
- Trends by industry sectors for a given country or region
- filters
  - cumulative : cumulative or annual values
  - data source: CAIT or PIK
  - per capita : total or per capita trends
  - country/region : select option for country or regions