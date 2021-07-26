
from configparser import ConfigParser

def config_db(filename = "../config/database.ini", section ="postgresql"):
    """
    Retreives the config section from the config file

    Args:
        filename (str, optional): File name of the config file. Defaults to "../config/database.ini".
        section (str, optional): section from the config file to be read. Defaults to "postgresql".
    """

    db = read_section(filename, section)
    
    return db


def get_table_config( table_name, filename = "../config/database.ini"):
    """
        reads the db config file and get definitions for table columns to create a table in database
        
        Inputs:
            filename [String] : filename where the db config is stored
            table_name [String] : it is the section name in the db config file
    """
    
    tbl = read_section(filename, table_name)
    
    return tbl

def get_table_comments(table_name, filename = "../config/database.ini"):
    """
    reads the comments section for a give table and return its values back as dictionaries.
    section name rule is "comments_<table_name"
    
    Inputs:
        table_name [String] : table name for which column comments needs to be provided
        filename [ String] : Path name for the config.ini file
    """
    
    tbl_comments = read_section(filename, f"comments_{table_name}")
    
    return tbl_comments

def read_section(filename, section):
    """
    read section o the config file and returns the dictionary
    
    Args:
        filename (str, optional): File name of the config file. Defaults to "../config/database.ini".
        section (str, optional): section from the config file to be read. 
    """

    # create a parser
    parser = ConfigParser()

    parser.read(filename)

    config = {}

    # Get the section and read the parameters

    if parser.has_section(section):
        params = parser.items(section)
        
        for param in params:
            config[param[0]] = param[1]

    else:
        raise Exception(f"section {section} not found in file {filename}")

    return config
    
    

    
