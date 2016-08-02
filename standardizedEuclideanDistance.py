#!/usr/bin/env python
################################################################################
# Date: 2016/July/07
# 
# Module: standarizedEuclideanDistance.py
#
# VERSION: 1.0
# 
# AUTHOR: Miguel Ibarra (miguelib@ufl.edu)
#
# DESCRIPTION: This program does a pairwise and to mean  standarized euclidean
#               comparison for a given dataset.
#
################################################################################

# Built-in packages
import os
import logging
import argparse

# Add-on packages
import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from sklearn.neighbors import DistanceMetric
from matplotlib.backends.backend_pdf import PdfPages

# Local packages
import logger as sl
import module_box as box
import manager_color as ch
import module_lines as lines
import  module_scatter as  scatter
from interface import wideToDesign
from manager_figure import figureHandlers

def getOptions():
    """ Function to pull in arguments """

    description = """For mutivariate data, the standardized Euclidean distance
    (SED) takes the variance into consideration. If we assume all the vectors
    are identically and independent multinormally distributed with a diagonal
    covariance matrix (assuming the correlations are 0), the SED follows a
    certain distribution associated with the dimension of the vector. Thus,
    samples with SEDs higher than the cutoff are dubious and conflict to the
    multinormal assumption.

    The scripts estimate the variance according to the input data and calculate
    the SEDs from all samples to the estimated Mean and also the sample 
    pairwise SEDs by group.

    The output includes 3 plots for each group and 3 plots in the end for all
    the samples altogether.
    """

    parser = argparse.ArgumentParser(description=description, formatter_class=
                                    argparse.RawDescriptionHelpFormatter)

    standard = parser.add_argument_group(description="Required Input")
    standard.add_argument("-i","--input", dest="input", action='store',required=True,
                         help="Dataset in Wide format")
    standard.add_argument("-d","--design", dest="design", action='store', 
                         required=True, help="Design file")
    standard.add_argument("-id","--ID", dest="uniqID", action='store', required=True, 
                         help="Name of the column with unique identifiers.")

    output = parser.add_argument_group(description="Output Files")
    output.add_argument("-f", "--figure", dest="figure", action='store', 
                        required=True, help="""PDF Output of standardized 
                        Euclidean distance plot""")
    output.add_argument("-m","--SEDtoMean", dest="toMean", action='store', 
                        required=True, help="""TSV Output of standardized 
                        Euclidean distances from samples to the mean.""")
    output.add_argument("-pw","--SEDpairwise", dest="pairwise", action='store', 
                        required=True, help="""TSV Output of sample-pairwise 
                        standardized Euclidean distances.""")

    optional = parser.add_argument_group(description="Optional Input")
    optional.add_argument("-g","--group", dest="group",default=False, action='store', 
                        required=False, help="Treatment group")
    optional.add_argument("-o","--order",dest="order",action="store",
                        default=False,help="Run Order")
    optional.add_argument("-p","--per", dest="p", action='store', required=False, 
                        default=0.95, type=float, help="""The percentile cutoff 
                        for standard distributions. The default is 0.95. """)
    optional.add_argument("-l","--levels",dest="levels",action="store", 
                        required=False, default=False, help="""Different groups to
                         sort by separeted by comas.""")
    optional.add_argument("-lg","--log",dest="log",action="store",required=False, 
                        default=False,help="Log file")

    args = parser.parse_args()
    return(args)

def plotCutoffs(cut_S,ax,p):
    """
    Plot the cutoff lines to each plot

    :Arguments:
        :type cut_S: pandas.Series
        :param cut_S: contains a cutoff value, name and color

        :type ax: matplotlib.axes._subplots.AxesSubplot
        :param ax: Gets an ax project.

        :type p: float
        :param p: percentile of cutoff
    """
    lines.drawCutoffHoriz(ax=ax,y=float(cut_S.values[0]),
            cl=cutPalette.ugColors[cut_S.name],
            lb="{0} {1}% Cutoff: {2}".format(cut_S.name,round(p*100,3),
            round(float(cut_S.values[0]),1)),ls="--",lw=2)

def makePlots (SEDData, design, pdf, groupName, cutoff, p, plotType, ugColors, levels):
    """
    Manage all the plots for this script

    :Arguments:
        :type SEDData: pandas.dataFrame
        :param SEDData: Contains SED data either to Mean or pairwise

        :type design: pandas.dataFrame
        :param design: Design file after getColor

        :type pdf: PDF object
        :param pdf: PDF for output plots

        :type groupName: string
        :param groupName: Name of the group (figure title).

        :type cutoff: pandas.dataFrame
        :param cutoff: Cutoff values, beta, chi-sqr and normal.

        :type p: float
        :param p: Percentil for cutoff.

        :type plotType: string
        :param plotType: Type of plot, the possible types are scatterplot to mean
            scatterplot pairwise and boxplot pairwise.

    """

    #Geting number of features in dataframe
    nFeatures = len(SEDData.index)

    #Calculates the widht for the figure base on the number of features
    figWidth = max(nFeatures/4, 12)

    # Create figure object with a single axis and initiate the figss
    figure = figureHandler(proj='2d', figsize=(figWidth, 8))

    # Choose type of plot
    # Plot scatterplot to mean
    if(plotType=="scatterToMean"):
        #Adds Figure title, x axis limits and set the xticks
        figure.formatAxis(figTitle="Standardized Euclidean Distance from samples {} to the mean".
                        format(groupName),xlim=(-0.5,-0.5+nFeatures),ylim="ignore",
                        xticks=SEDData.index.values,xTitle="Index",
                        yTitle="Standardized Euclidean Distance")

        #Plot scatterplot quickplot
        scatter.scatter2D(ax=figure.ax[0],colorList=design["colors"],
                        x=range(len(SEDData.index)), y=SEDData["SED_to_Mean"])

    #Plot scatterplot pairwise
    elif(plotType=="scatterPairwise"):
        # Adds Figure title, x axis limits and set the xticks
        figure.formatAxis(figTitle="Pairwise standardized Euclidean Distance from samples {}".
                        format(groupName),xlim=(-0.5,-0.5+nFeatures),ylim="ignore",
                        xticks=SEDData.index.values,xTitle="Index",
                        yTitle="Standardized Euclidean Distance")

        # Plot scatterplot
        for index in SEDData.index.values:
            scatter.scatter2D(ax=figure.ax[0],colorList=design["colors"][index],
                            x=range(len(SEDData.index)), y=SEDData[index])

    #Plot boxplot pairwise
    elif(plotType=="boxplotPairwise"):
        # Add Figure title, x axis limits and set the xticks
        figure.formatAxis(figTitle="Box-plots for pairwise standardized Euclidean Distance from samples {}".
                        format(groupName),xlim=(-0.5,-0.5+nFeatures),ylim="ignore",
                        xticks=SEDData.index.values,xTitle="Index",
                        yTitle="Standardized Euclidean Distance")
        # Plot Box plot
        box.boxDF(ax=figure.ax[0], colors=design["colors"].values, dat=SEDData)

    #Add a cutoof line
    cutoff.apply(lambda x: plotCutoffs(x,ax=figure.ax[0],p=p),axis=0)
    figure.shrink()
    # Plot legend
    figure.makeLegend(figure.ax[0], ugColors, levels)

    # Add figure to PDF and close the figure afterwards
    figure.addToPdf(pdf)

def prepareSED(data_df, design, pdf, groupName, p, ugColors, levels):
    """
    Core for processing all the data.

    :Arguments:
        :type data_df: pandas.Series.
        :param data_df: contains a cutoff value, name and color.

        :type design: matplotlib.axes._subplots.AxesSubplot.
        :param design: Gets an ax project.

        :type pdf: PDF object.
        :param pdf: PDF for output plots.

        :type groupName: string.
        :param groupName: Name of the group (figure title).

        :type p: float.
        :param p: percentile of cutoff.

    :Returns:
        :rtype pdf: PDF object.
        :return pdf: PDF for output plots.

        :rtype SEDtoMean: pd.DataFrames
        :return SEDtoMean: SEd for Mean
        
        :rtype SEDpairwise: pd.DataFrames
        :return SEDpairwise: SED for pairwise data
    """
    #Calculate SED without groups
    SEDtoMean, SEDpairwise = getSED(data_df)

    #Calculate cutOffs
    cutoff1,cutoff2 = getCutOffs(data_df, p)

    # Call function to do a scatter plot on SEDs from samples to the Mean
    makePlots(SEDtoMean, design, pdf, groupName, cutoff1, p, "scatterToMean",
                ugColors, levels)

    #Call function to do a scatter plot on SEDs for pairwise samples
    makePlots(SEDpairwise, design, pdf, groupName, cutoff2, p, "scatterPairwise",
                ugColors, levels)

    # Call function to do a boxplot on SEDs for pairwise samples
    makePlots(SEDpairwise, design, pdf, groupName, cutoff2, p, "boxplotPairwise",
                ugColors, levels)

    #Returning data
    return pdf, SEDtoMean, SEDpairwise

def calculateSED(dat, levels, combName, pdf, p):
    """
    Manage all the plots for this script

    :Arguments:
        :type dat: wideToDesign
        :param dat: Contains data parsed by interface

        :type args: argparse.data
        :param args: All input data

        :type levels: string
        :param levels: Name of the column on desing file (after get colors)
                         with the name of the column containing the combinations.

        :type combName: dictionary 
        :param combName: dictionary with colors and different groups
    """
    

    if len(levels.keys()) > 1:
        #Creates dataframes for later use for SED results
        SEDtoMean=pd.DataFrame(columns=['SED_to_Mean', 'group'])
        SEDpairwise=pd.DataFrame(columns=["group"])

        #Calculates pairwise and to mean distances by group(or levels)
        for level, group in dat.design.groupby(combName):
            #Subsetting wide
            currentFrame = dat.wide[group.index]

            #Getting SED per group
            logger.info("Getting SED for {0}".format(level))
            pdf, SEDtoMean_G, SEDpairwise_G = prepareSED(currentFrame, group, 
                                                pdf, "in group "+str(level), p,
                                                levels, combName)

            #Add 'group' column to the current group
            SEDtoMean_G['group'] = [level]*len(currentFrame.columns)
            SEDpairwise_G['group'] = [level]*len(currentFrame.columns)

            #Merges dataframes onto an All dataframe 
            SEDtoMean = pd.DataFrame.merge(SEDtoMean,
                                            SEDtoMean_G, 
                                            on=['SED_to_Mean', 'group'], 
                                            left_index=True, 
                                            right_index=True, 
                                            how='outer', 
                                            sort=False)
            SEDpairwise = pd.DataFrame.merge(SEDpairwise, 
                                            SEDpairwise_G, 
                                            on=["group"], 
                                            left_index=True, 
                                            right_index=True,
                                            how='outer', 
                                            sort=False)

        #Get means of all different groupss
        logger.info("Getting SED for all data")
        cutoffAllMean,cutoffAllPairwise = getCutOffs(dat.wide,p)

        #Sort df by group
        SEDtoMean = SEDtoMean.sort_values(by='group')
        SEDpairwise = SEDpairwise.sort_values(by='group')

        # Plot a scatter plot on SEDs from samples to the Mean
        makePlots (SEDtoMean, dat.design, pdf, "", cutoffAllMean, p, 
                    "scatterToMean", levels, combName)

        # Plot a scatter plot on SEDs for pairwise samples
        makePlots (SEDpairwise, dat.design, pdf, "", cutoffAllPairwise, p, 
                    "scatterPairwise", levels, combName)

        # Plot a boxplot on SEDs for pairwise samples
        makePlots (SEDpairwise, dat.design, pdf, "", cutoffAllPairwise, p, 
                    "boxplotPairwise", levels, combName)

        #If group drop "group" column
        SEDtoMean.drop('group', axis=1, inplace=True)
        SEDpairwise.drop('group', axis=1, inplace=True)

    else:
        logger.info("Getting SED for all data")
        pdf,SEDtoMean,SEDpairwise = prepareSED(dat.wide, dat.design, pdf,'', p,
                                        levels, combName)

    return SEDtoMean,SEDpairwise

def getSED(wide):
    """ 
    Calculate the Standardized Euclidean Distance and return an array of 
    distances to the Mean and a matrix of pairwise distances.

    :Arguments:
        :type wide: pandas.DataFrame
        :param wide: A wide formatted data frame with samples as columns and 
                     compounds as rows.

    :Returns:
        :return: Return 4 pd.DataFrames with SED values and cutoffs.
        :rtype: pd.DataFrames
    """
    #Calculate means
    mean = pd.DataFrame(wide.mean(axis=1))

    #Calculate variance
    variance = wide.var(axis=1,ddof=1)

    #Flag if variance == 0
    variance[variance==0]=1

    #Get SED distances!
    dist = DistanceMetric.get_metric('seuclidean', V=variance)

    #Calculate the SED from all samples to the mean
    SEDtoMean = dist.pairwise(wide.values.T, mean.T)
    SEDtoMean = pd.DataFrame(SEDtoMean, columns = ['SED_to_Mean'], 
                               index = wide.columns)

    #Calculate the pairwise standardized Euclidean Distance of all samples
    SEDpairwise = dist.pairwise(wide.values.T)
    SEDpairwise = pd.DataFrame(SEDpairwise, columns=wide.columns, 
                               index=wide.columns)

    #Converts to NaN the diagonal
    for index, row in SEDpairwise.iterrows():
        SEDpairwise.loc[index, index] = np.nan

    #Returning data
    return SEDtoMean,SEDpairwise

def getCutOffs(wide,p):
    """ 
    Calculate the Standardized Euclidean Distance and return an array of 
    distances to the Mean and a matrix of pairwise distances.

    :Arguments:
        :type wide: pandas.DataFrame
        :param wide: A wide formatted data frame with samples as columns and 
                     compounds as rows.

        :type p: float.
        :param p: percentile of cutoff.

    :Returns:
        :rtype cutoff1: pandas.dataFrame
        :return cutoff1: Cutoff values for mean, beta, chi-sqr and normal.

        :rtype cutoff2: pandas.dataFrame
        :return cutoff2: Cutoff values for pairwise, beta, chi-sqr and normal.
    """

    #Stablish iterations, and numer of colums ps and number of rows nf
    ps  = len(wide.columns)
    nf = len(wide.index)
    iters  = 20000

    #Calculates betaP
    betaP=np.percentile(pd.DataFrame(stats.beta.rvs(0.5, 0.5*(ps-2),size=iters*nf).reshape(iters,nf)).sum(axis=1), p*100.0)

    #casting to float so it behaves well
    ps = float(ps)
    nf = float(nf)    

    #Calculates cutoffs beta,norm & chisq for data to mean
    betaCut1  = np.sqrt((ps-1)**2/ps*betaP)
    normCut1  = np.sqrt(stats.norm.ppf(p, (ps-1)/ps*nf, 
                        np.sqrt(2*nf*(ps-2)*(ps-1)**2/ps**2/(ps+1))))
    chisqCut1 = np.sqrt((ps-1)/ps*stats.chi2.ppf(p, nf))

    #Calculates cutoffs beta,n norm & chisq for pairwise
    betaCut2  = np.sqrt((ps-1)*2*betaP)
    normCut2  = np.sqrt(stats.norm.ppf(p, 2*nf, np.sqrt(8*nf*(ps-2)/(ps+1))))
    chisqCut2 = np.sqrt(2*stats.chi2.ppf(p, nf))

    #Create data fram for ecah set of cut offs
    cutoff1   = pd.DataFrame([[betaCut1, normCut1, chisqCut1],
                            ['Beta(Exact)', 'Normal', 'Chi-sq']],index=["cut","name"],
                            columns=['Beta(Exact)', 'Normal', 'Chi-sq'])
    cutoff2   = pd.DataFrame([[betaCut2, normCut2, chisqCut2],
                            ['Beta(Exact)', 'Normal', 'Chi-sq']],index=["cut","name"],
                            columns=['Beta(Exact)', 'Normal', 'Chi-sq'])
    
    #Create Palette
    cutPalette.getColors(cutoff1.T,["name"])

    #Returning colors
    return cutoff1,cutoff2

def main(args):
    """ 
    Main Script 
    """

    #Getting palettes for data and cutoffs
    global cutPalette
    dataPalette = ch.colorHandler(pal="tableau",col="Tableau_10")
    cutPalette = ch.colorHandler(pal="tableau",col="TrafficLight_9")

    #Checking if levels
    subGroups = []
    if args.levels and args.group:
        subGroups = args.levels.split(",")
        levels = [args.group]+subGroups
    elif args.group and not args.levels:
        levels = [args.group]
    elif not args.group and args.levels:
        logger.error(u"Use --groups if you are using just one group")
        exit()
    else:
        levels = []
    logger.info(u"Groups used to color by :{}".format(",".join(levels)))

    #Checkig if order
    if args.order and args.levels:
        anno = [args.order] + subGroups
    elif args.order and not args.levels:
        anno = [args.order,]
    elif not args.order and args.levels:
        anno = [args.levels,]
    else:
        anno=False

    #Parsing data with interface
    dat = wideToDesign(args.input, args.design, args.uniqID, group=args.group, 
                        anno=anno)

    #Removing groups with just one sample
    if args.group:
        dat.removeSingle()
    
    #Select colors for data
    dat.design, ugColors, combName = dataPalette.getColors(design=dat.design,
                                                            groups=levels)
    #Open pdfPages
    with PdfPages(os.path.abspath(args.figure)) as pdf:
        # Calculate SED
        SEDtoMean,SEDpairwise=calculateSED(dat, ugColors, combName, pdf, args.p)


    #Outputing files for tsv files
    SEDtoMean.to_csv(os.path.abspath(args.toMean), sep='\t')
    SEDpairwise.to_csv(os.path.abspath(args.pairwise), sep='\t')

    #Ending script
    logger.info("Script complete.")

if __name__ == '__main__':
    # Turn on Logging if option -g was given
    args = getOptions()

    # Turn on logging
    logger = logging.getLogger()
    sl.setLogger(logger)

    # Standar logging
    logger.info(u"""Importing data with following parameters: 
                \tWide: {0}
                \tDesign: {1}
                \tUnique ID: {2}
                \tGroup: {3}
                \tRun Order: {4}
                """ .format(args.input, args.design, args.uniqID, args.group, 
                    args.order))

    #Main script
    main(args)
