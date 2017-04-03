# This reads in ms output file(s) to convert (having the '.msout' extension) - 
# Can either be a single file or a directory containing multiple files,
# and reads in the msFlagFile used to generate the ms output files.
# It then creates the .eigenstratgeno genotype file and the .par specification file
# for smartpca for each ms output file, and the .ind and .snp files required to only
# be made once for the ms output originating from each msFlagFile.

# This is working correctly 021717.

# Updated to correctly parse haploid/diploid from the ms flag file and then parse the 
# entries accordingly. 031617.

import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--msOutputToConvert', help = "The ms output to convert for PCA. This can either be a single file (with a '.msout' extension) or a directory that contains multiple files with '.msout' extensions to individually convert. TIP: To specify processing all files in the current directory, use '-m .' Note: if this is a directory, it cannot contain spaces without escape characters.")
parser.add_argument('-f', '--msFlagFile', help = "The msFlagFile that was used to generate the ms output that is being converted for PCA. This is used to assign each individual to the correct population for the PCA run.")
parser.add_argument('-o', '--outputFileStem', help = "The output file stem (no file extension) to use for the files converted for PCA. File extensions ('.eigenstratgeno', '.inp', '.snp', and '.par') will be added.")

args = parser.parse_args()

SNPFileName = args.outputFileStem + '.snp'
indivFileName = args.outputFileStem + '.ind'

msFlagFile = args.msFlagFile

inputToConvert = args.msOutputToConvert

print(inputToConvert)

# Determine whether the input is a single file or a directory with many files, and 
# parse the input into a list of file names to process.
def checkInput():

    # This is a list of files to convert. If the user passed a single file as input, then
    # that will be the only entry. If they passed a directory, then each file in that dir
    # with the '.msout' extension will be added to this list. This makes it possible to 
    # process the files in the same for loop regardless of whether the input to the script
    # was a single file or a directory.
    fileListToConvert = []

    # Check whether the input to convert is an individual file (has the '.msout' extension) and 
    # is an accessible file
    # or is an accessible directory (which will then loop through the files in that dir that have the .msout extension)
    if inputToConvert[-6:] == ".msout" and os.path.isfile(inputToConvert):
        print("This is an individual file.")
        fileListToConvert.append(inputToConvert)
    
    
    elif os.path.isdir(inputToConvert):
        print("This is a directory.")
        fileList = os.listdir(inputToConvert)
    
        fileCounter = 0
        for file in fileList:
            if file[-6:] == ".msout":
                fileCounter += 1
                fileListToConvert.append(file)
    
        # Print the number of files if there are any, otherwise exit.
        if fileCounter >= 1:
            print("There are {} files with .msout extensions to convert in this directory.".format(fileCounter))
        else:
            print("There are no files with the '.msout' extension to convert in this directory.")
            print("Exiting.")
            sys.exit()
        
    else:
        print("The input was not recognized as an accessible file with an '.msout' extension or as a directory containing accessible '.msout' file(s).")
        print("Exiting.")
        sys.exit()

    print(fileListToConvert)
    return(fileListToConvert)

# This is a stripped down version of the msFlagFile reader/parser. It does not deal with 
# any of the pairwise migration connections; it parses/counts population sampling information
# from the sampling specifications at the start of the file.    
def readFlagFile():
    
    
    # Determine whether the current file is for diploids or not for parsing the ms file
    # entries either one at a time (for haploid) or in pairs (for diploid) 

    # Gives something like:
    # ["TESTER_022817_diploidSamples_", "120_screened_2_times_msFlagFile.txt"]
    inputFileSplit1 = msFlagFile.split("ms_nsam_")

    if len(inputFileSplit1[0].split("diploid")) >= 2:
        isDiploidFile = 1
    elif len(inputFileSplit1[0].split("haploid")) >= 2:
        isDiploidFile = 0
    else:
        print("WARNING - Could not correctly parse whether the input ms flag file simulated haploids or diploids. Will parse it as haploid.")
        isDiploidFile = 0

    
    with open(msFlagFile, 'r') as inFile:

        for lineNum, line in enumerate(inFile):
            splitLine = line.split()
            # This is the whole ms flag file call but split by whitespace (any white space,
            # including any number of spaces).
            #print(splitLine)
        
            for index, element in enumerate(splitLine):
                
                if element == '-s':
                    sFlagIndex = index
                    sFlagHolder = splitLine[index + 1]
                if element == '-I':
                    IFlagIndex = index
                    IFlagHolder = splitLine[index + 1]
        
    print("The s flag location is: %d" % sFlagIndex)
    print("The I flag location is: %d" % IFlagIndex)

    numPopnsIFlag = int(IFlagHolder)

    print("There are %s populations to simulate based on the -I flag" % numPopnsIFlag)


# ----------
    # This finds the num popns following the -I flag by looking for the first '-' flag,
    # not considering the '0.0' before the first flag, which initially sets 
    # all migration rates to 0. In most cases, the first flag will be '-m', but
    # this makes it flexible to cases whether the user has manually added other flags
    # e.g. '-ej' before the first '-m' flag. If this is the case, the first flag MUST
    # still come after the '0.0'. 

    for index, entry in enumerate(splitLine):
        if index != sFlagIndex and index != IFlagIndex and entry.startswith('-'):
            flagStartIndex = index
            break
    
    popnSampleList = splitLine[IFlagIndex + 2 : flagStartIndex - 1]

    popnSamplingDict = {}
    
    # NOTE: At this point the population numbers are 'collapsed' to be consecutive among the 
    # focal populations that were simulated. Any intervening ghost populations in the population
    # numbering are disregarded, and the first focal population becomes population '1'.
    # Focal populations are entries > 0 in the populationSample list.
    numFocalPopn = 0
    
    for populationSample in popnSampleList:
        if int(populationSample) > 0:
            numFocalPopn += 1
            popnSamplingDict[numFocalPopn] = int(populationSample)
    
    print(popnSamplingDict)
    
    return(popnSamplingDict, numPopnsIFlag, isDiploidFile)

def makeGenotypeFiles(fileListForConversion, numPopns, isDiploidFile):
    
    for file in fileListForConversion:
    
        fileSplit = file.split('_')
        print(fileSplit)
        
        # The file split will return the full filename string (and therefore have 
        # length 1) if it does not contain '_'
        if len(fileSplit) > 1:
            iterNumSplit = fileSplit[len(fileSplit) - 1].split('.')[0]
            
            eigenstratGenoOutputFile = args.outputFileStem + '_Iter_' + str(iterNumSplit) + '.eigenstratgeno'
            
        # if the file name does not contain a parsable iteration number, then just make the 
        # input file name into the output name for this file to keep as much identifying information
        # as possible.    
        else:
            print("WARNING - could not parse the iteration number from file: {}.".format(file))
            print("The iteration number in the input file names should be formatted as: <restOfFileName>_Iter_<num>.msout.")
            print("Using the input file name to make the output file name instead of the user-specified stem for the output file name.")
            
            fileStem = file.split('.')[0]
            eigenstratGenoOutputFile = fileStem + '.eigenstratgeno'
            
        print(eigenstratGenoOutputFile)
        
        
        numIndividuals = 0
        
        # This is used to aggregate by pairs of chromosomes for each individual
        if isDiploidFile:
            diploidHolder = 0
            prevLine = 1
        
        with open(file,'r') as inputFile, open(eigenstratGenoOutputFile,'w') as outputFile:
        
            SNPHolder = ''
        
            numSNPs = 0
            entryStart = 0
        
            for line in inputFile:
            
                #print(line.strip())
                if line.strip() == '//':
                
                    numSNPs += 1
                
                    if SNPHolder != '':
                                                
                        numIndividuals = len(SNPHolder)
                        #print(str(numIndividuals))
                        outputFile.write(SNPHolder + '\n')
                            
                        SNPHolder = ''
                    
                    continue
                    
                    #print('Yes for //')
                    #entryStart = 1
                
                if line.startswith('segsites:'):
                    continue
            
                if line.startswith('positions:'):
                    continue
            
                if line.startswith('prob:'):
                    continue
            
                # If this line is within the ms output entry (and therefore is a simulated seq)
                # From ms, '0' alleles are ancestral, and '1' alleles are derived.
                # For SmartPCA, the number for each locus is the number of ancestral alleles,
                # so '0' from ms becomes '1' for SmartPCA, and '1' becomes '0' (assuming haploids for now).
                if line.startswith('1') or line.startswith('0'):
                    
                    
                    if line.strip() == '0':
                        
                        if isDiploidFile == 0:
                            SNPHolder += '1'
                        
                        if isDiploidFile == 1:
                            diploidHolder += 1
                
                    if line.strip() == '1':
                        
                        if isDiploidFile == 0:
                            SNPHolder += '0'
                        
                        if isDiploidFile == 1:
                            diploidHolder += 0
                            
                    if isDiploidFile == 1:
                        
                        # Increment the previous line if this was line 1 of 2 for the diploid;
                        # The 'continue' is critical.
                        if prevLine == 1:
                            prevLine = 2
                            continue
                        
                        # If this was line 2 of 2 for the diploid, then process the diploidHolder,
                        # add to the SNPHolder, and reset the counters for the next diploid
                        # represented in the file.    
                        if prevLine == 2:
                            SNPHolder += str(diploidHolder)
                            prevLine = 1
                            diploidHolder = 0
                        
                        

            #print(numSNPs)

            if SNPHolder != '':
                                        
                numIndividuals = len(SNPHolder)
                outputFile.write(SNPHolder + '\n')
    
        # Nested function to make the .par parameter file    
        makeParameterFile(eigenstratGenoOutputFile, numPopns)


    return(numIndividuals,numSNPs)            

# This is a nested function within the makeGenotypeFiles().
# NOTE: Maxpops argument in the .par file is to override the arbitrary hard-coded error 
# that Eigenstrat gives when trying to analyze more than 100 populations
def makeParameterFile(fullGenoFileName, numPopns):
    
    fileNameBase = fullGenoFileName.split('.')[0]
    
    parOutHolder = ''
    
    parOutHolder += 'genotypename: ' + fullGenoFileName + '\n'
    parOutHolder += 'snpname: ' + SNPFileName + '\n'
    parOutHolder += 'indivname: ' + indivFileName + '\n'
    parOutHolder += 'evecoutname: ' + fileNameBase + '.evec\n'
    parOutHolder += 'evaloutname: ' + fileNameBase + '.eval\n'
    
    # This is only necessary if the number of populations to analyze is more than 100.
    # NEED TO MAKE SURE THIS WORKS WITH SMARTPCA 021617.
    if numPopns > 100:
        parOutHolder += 'maxpops: ' + str(numPopns) + '\n'

    with open(fileNameBase + '.par', 'w') as outParFile:
        outParFile.write(parOutHolder)
    
#--------------------------

# Use the number of SNPs (parsed from the .msout file) to generate the SNP file 
# This assigns all SNPs to the arbitrary chromosome 1, with genetic positions of '0.0', meaning
# 'unknown' following the Eigensoft documentation, and arbitrary physical positions that
# are each 1kb from each other.
def makeSNPFile(numSNPs):

    snpOutputHolder = ''
    for num in range(numSNPs):
        snpOutputHolder += 'SNP_' + str(num + 1) + ' 1 0.0 ' + str((num + 1) * 1000) + '\n'
    
    with open(SNPFileName,'w') as snpFileHandle:
        snpFileHandle.write(snpOutputHolder)


# Use the sampling list from the msFlagFile (the list of space delimited numbers 
# following the -I flag) to generate the .ind file, which links each individual to their 
# population number.
# NOTE: At this point the population numbers have been 'collapsed' to be consecutive among the 
# focal populations that were simulated. Any intervening ghost populations in the population
# numbering are disregarded, and the first focal population becomes population '1'.
def makeIndivFile(popnSamplingDict):
    #print("In make indiv file")
    #print(numIndividuals)
    
    #totalNumIndivs = sum(popnSamplingDict.values())

    cumulativeIndivNumCounter = 0
    individualOutputHolder = ''
    
    # the key numbers are the same as the population numbers (of the focal populations only).
    for popnNumKey in popnSamplingDict:
        for indiv in range(1,popnSamplingDict[popnNumKey] + 1):
            cumulativeIndivNumCounter += 1
            individualOutputHolder += 'Indiv_' + str(cumulativeIndivNumCounter) + ' U ' + str(popnNumKey) + '\n'
    
    with open(indivFileName,'w') as individualFileHandle:
        individualFileHandle.write(individualOutputHolder)





fileListToConvert = checkInput()
popnSamplingDict, numPopns, isDiploidFile= readFlagFile()
numIndividuals,numSNPs = makeGenotypeFiles(fileListToConvert, numPopns, isDiploidFile)

# Only need to make 1 .ind file and 1 .snp file per batch of ms output.
makeSNPFile(numSNPs)
makeIndivFile(popnSamplingDict)

