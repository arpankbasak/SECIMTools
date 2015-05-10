#!/usr/bin/env python

# Built-in packages
from __future__ import division
import logging
import argparse
from argparse import RawDescriptionHelpFormatter
import cPickle as pickle

# Add-on packages
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.predstd import wls_prediction_std

# Local Packages
from interface import wideToDesign
import logger as sl


def getOptions(myopts=None):
    """ Function to pull in arguments """
    description = """ """
    parser = argparse.ArgumentParser(description=description, formatter_class=RawDescriptionHelpFormatter)
    group1 = parser.add_argument_group(title='Standard input', description='Standard input for SECIM tools.')
    group1.add_argument('--input', dest='fname', action='store', required=True, help="Input dataset in wide format.")
    group1.add_argument('--design', dest='dname', action='store', required=True, help="Design file.")
    group1.add_argument('--ID', dest='uniqID', action='store', required=True, help="Name of the column with unique identifiers.")
    group1.add_argument('--group', dest='group', action='store', required=True, help="Group/treatment identifier in design file [Optional].")
    group1.add_argument('--order', dest='order', action='store', required=True, help='')

    group2 = parser.add_argument_group(title='Required Output')
    group2.add_argument('--out', dest='oname', action='store', required=True, help="Name of PDF to save scatter plots.")

    group4 = parser.add_argument_group(title='Development Settings')
    group4.add_argument("--debug", dest="debug", action='store_true', required=False, help="Add debugging log output.")

    if myopts:
        args = parser.parse_args(myopts)
    else:
        args = parser.parse_args()

    return (args)


def runOrder(col):

    """ run order regression """
    # Drop missing values and make sure everything is numeric
    clean = col.dropna().reset_index().convert_objects(convert_numeric=True)
    clean.columns = ['run', 'val']

    # Fit model
    model = smf.ols(formula='val ~ run', data=clean)
    results = model.fit()
    return col.name, clean['run'], clean['val'], results


def makeScatter(row, pdf):

    """ Plot a scatter plot of x vs y. """
    # Split out row results
    name, x, y, res = row

    # Get fitted values
    fitted = res.fittedvalues

    # Get slope and p-value
    slope = res.params['run']
    pval = res.pvalues['run']
    rsq = res.rsquared

    # Get 95% CI
    prstd, lower, upper = wls_prediction_std(res)

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    ax.scatter(x, y)
    ax.plot(x, lower, 'r-')
    ax.plot(x, fitted, 'c-')
    ax.plot(x, upper, 'r-')
    ax.set_xlabel('Run Order')
    ax.set_ylabel('Value')
    ax.set_title(u'{}\nScatter plot'.format(name))
    ax.text(.7, .85, u'Slope: {0:.4f}\n(p-value = {1:.4f})\nR^2: {2:4f}'.format(slope, pval, rsq), transform=ax.transAxes, fontsize=12)

    # Save to PDF
    pdf.savefig(fig)
    plt.close(fig)

def main(args):
    # Import data
    logger.info('Importing Data')
    dat = wideToDesign(args.fname, args.dname, args.uniqID, args.group, anno=[args.order, ])

    # Transpose Data so compounds are columns
    trans = dat.transpose()
    trans.set_index(args.order, inplace=True)

    # Drop group
    trans.drop(args.group, axis=1, inplace=True)

    # Run each column through regression
    logger.info('Running Regressions')
    res = trans.apply(runOrder, axis=0)

    # Plot Results
    # Open a multiple page PDF for plots
    logger.info('Plotting Results')
    pp = PdfPages(args.oname)
    res.apply(makeScatter, args=(pp, ))
    pp.close()


if __name__ == '__main__':
    # Command line options
    args = getOptions()

    logger = logging.getLogger()
    if args.debug:
        sl.setLogger(logger, logLevel='debug')
        DEBUG = True
    else:
        sl.setLogger(logger)

    main(args)
