#!/usr/bin/env python
################################################################################
# DATE: 2016/Jun/01
#
# SCRIPT: hcheatmap.py
#
# VERSION: 2.0
# 
# AUTHOR: Miguel A Ibarra (miguelib@ufl.edu)
# 
# DESCRIPTION: This script takes a a wide format file and plots a heatmap of
#               the data. This tool is usefull to get a representation of the
#               data.
#
#     input     : Path to Wide formated file.
#     design    : Path to Design file corresponding to wide file.
#     id        : Uniq ID on wide file (ie. RowID).
#     heatmap   : Output path for loads heatmap.
# 
# The output is a heatmap that describes the wide dataset.
################################################################################

#Standar Libraries
import os
import argparse
import logging

#AddOn Libraries
import matplotlib
matplotlib.use('Agg')
import pandas as pd

# Local Packages
import logger as sl
import module_heatmap as hm
from interface import wideToDesign

#Import data
def getOptions():
    """Function to pull arguments"""
    parser = argparse.ArgumentParser(description="""Takes a wide and design file
                                    and plots a heatmap of the data """)

    #Standar input for SECIMtools
    standar = parser.add_argument_group(title='Standard input', description= 
                                        'Standard input for SECIM tools.')
    standar.add_argument("-i","--input",dest="input", action='store', 
                        required=True, help="Input dataset in wide format.")
    standar.add_argument("-d","--design",dest="design", action='store', 
                        required=True, help="Design file.")
    standar.add_argument("-ID","--uniqID",dest="uniqID",action="store",
                        required=True, help="""Name of the column with unique 
                        dentifiers.""")

    #Output Paths
    output = parser.add_argument_group(title='Output paths', description=
                                       "Paths for the output files")
    output.add_argument("-hm","--heatmap",dest="heatmap",action="store",
                        required=True,help="Output path for heatmap file[PDF]")

    #Optional Input
    optional = parser.add_argument_group(title='Optional input', 
                                         description="""Changes parameters for 
                                         the prorgram.""")
    optional.add_argument("-log", "--log", dest="log", action='store', 
                         required=False, default=False, 
                         help="Path and name of log file")

    args = parser.parse_args()
    return (args)

def main():
    #Import data
    args = getOptions()

    #Setting logger
    logger = logging.getLogger()
    sl.setLogger(logger)
    logger.info(u"""Importing data with following parameters:
                Input: {0}
                Design: {1}
                uniqID: {2}
                """.format(args.input, args.design, args.uniqID))

    #Importing data
    dat = wideToDesign(args.input, args.design, args.uniqID)
    #dat.wide.convert_objects(convert_numeric=True)
    for col in dat.wide.columns.values:
        dat.wide[col] = dat.wide[col].astype("float")
    #Creating axis
    hcFig = hm.plotHeatmap(dat.wide)

    #Saving figures
    hcFig.savefig(args.heatmap,format="pdf")

if __name__ == '__main__':
    main()