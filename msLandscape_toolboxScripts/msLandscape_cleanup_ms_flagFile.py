#!/usr/bin/env python

# This is a script to clean up msFlag files to make sure the specified number of 
# populations (with the -I flag) match the number of populations
# sampled (following the -I flag) and match the number of populations specified
# in the migration connections. This also makes the numbering of the populations in the 
# migration connections consecutive to avoid an ms SegmentationFault error.

# All the code here so far is working correctly 020917. If the population numbers 
# from the -m flag portion of the file are not in sequential order, and the number of 
# populations represented in the -m flag portion is less than the number specified by the 
# -I flag and the number of entries in the sampling list after the -I flag (and therefore
# the populations in the -m flag portion have been manually edited), then this is 
# correctly fixing the population numbers in the -m flag portion to be sequential

# For stability/guaranteed parsing by the R network plotter (which has a very picky parser)
# Use the '-r' flag and provide a file with population numbers to remove, instead of manually
# removing them and then running this script to clean up the msFlagFile (this script is 
# still able to do that, though, and in an effort to maintain that functionality, the 
# popCoord screening with the -p flag does not use the popnsToRemove file, the -r flag, so
# can use the -p with or without the -r flag). 021417.

# Added ability to simultaneously clean up the population coordinates file that can 
# be created by the msCallConstruction helper and is used downstream of ms to 
# make input files for SMARTPCA/un-PC, SpaceMix and EEMS. This is working correctly 021417.

# Removed the ability to specify an output file stem and are instead using the input file name
# (minus '_msFlagFile', which prevents it from continually adding more to the file name)
# as the output stem (to keep the haploid/diploid label that is important in the input file name). 022817

# After every run through this function, the output files get an automatically iterated
# 'screened' label with count. E.g. first time through will output 'screened_1_time' in the 
# ms flag file name and popn coord file name (if used), second time will be 'screened_2_times', etc.
# Can be handy to keep track of how many times each file has been screened, and keeps
# later screens of the same file from overwriting earlier screens. 022817

# Added functionality to automatically update the ms nsam number to use for the ms 
# simulations in the output file name of the ms flag file when focal populations are
# removed from the ms flag file. The nsam is the sum of chromosomes
# to sample from the focal populations. This works correctly regardless of haploid/diploid. 022817

# Verified this can clean up ms flag files that contain extra white space between entries (spaces or tabs)
# that can happen after manual editing. To do this, just supply the ms flag file to this script;
# It reads it in, takes it apart regardless of the amount of white space, and then puts
# the pieces back together with all single spaces. This fixes ms flag files that 
# fail to parse with the R network grapher if it is caused by a whitespace issue. ms does
# not care about these whitespace problems. 022817

# Fixed bug in removing correct populations from the popnCoordsFile (if supplied) 022817

# Added functionality to keep untouched any flags before the -I flag or any flags
# between the end of the -I flag and the start of the -m flags.
# NOTE - the '0.0' entry at the end of the -I flag list of population samples HAS to be there
# (It makes the flexible flag reading work so the only required flags are '-I' and '-m',
# and any other flags used either before or after the -I flag will be parsed correctly and 
# kept in the output file. This is working correctly in both the 'clean up only' and the 'remove popns then cleanup' 
# blocks of code 030317

# Need to add a descriptive error message if list length num != (mFlag num == I Flag Num) - 
# can't process the file because don't know which population number was deleted from the -I flag entries. 030317

# Added functionality to modify the number of individuals sampled from any of the 
# population numbers sampled (after the -I flag). This uses the same user-specified
# file as the list of populations to delete, but whereas the format for the popns to delete
# is a list of one popn per line, the format of the popns to modify the sampling is
# the popn number and the new sampling number sep by white space (space or tab) eg. '1 20'
# The parser looks to see whether the split line has length 1 or 2 to determine whether 
# this is a population to delete or a population to change the sampling. It causes no errors
# to specify the same population number multiple times in the same edit file - 
# if it is specified several times to change the sampling, the one closest to the 
# bottom of the file will be the one used; if it is specified several times as a deletion,
# it will be deleted (safely without passing the multiple entries to anything else),
# and if it is specified to have changed sampling as well as deletion, it will just be deleted.
# NOTE - this CAN be used to successfully turn ghost popns into focals and vice versa, BUT
# this will botch the updating of the population coords file (if that is being used in the screening) - 
# it will mis-delete populations and will not add the newly formed focal populations, but the R network plotter
# still works fine with this, and ms should too. Also, if this is a diploid file 
# (requiring an even number of sampled chromosomes for each population) 
# and the user enters an odd sampling number for any population, this will use the 
# next lower even number instead and print a warning. 030417.

# Now in cases where population sampling is changed so previous focal populations are 
# edited to become ghost populations (e.g. using an entry like '20 0' where population 20
# was previously sampled), this now removes these new ghost populations from the popn coords
# file (that continues to only include the coords of focal populations). This is working correctly 030917.

# Updated the haploid/diploid to that the user enters the num indivs to sample now, and 
# it doubles the num indivs to give num chromosomes for the ms flag file if it is for a 
# diploid; this actually simplifies the code quite a bit. Added try-catch to deal with 
# unexpected sting entries as population names in the population to edit file. Fixed 2 other bugs. 031317

# This errors when a ghost population is turned into a focal popn in the editing file
# before the same population is specified to be deleted (this is not a big problem) 031317.

# Need to think of other scenarios than can happen and will need to be screened for.


import argparse
import copy

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--inputFile', required = True, help = "The input ms flag file to clean up.")
parser.add_argument('-e', '--popnsToEditFile', help = "Optional. A file that contains population editing (deleting or modifying the number of sampled individuals) instructions. To specify populations to remove, enter the population numbers to remove (one per line). To specify changes to the number of individuals sampled in a population, give the population number and the new number of individuals to sample on the same line and separated by a space or a tab only.")
parser.add_argument('-p', '--popnCoordsFile', help = "Optional name of the population coordinates file that corresponds to the populations in the msFlagFile")

args = parser.parse_args()

inputFileName = args.inputFile

# Parse the original ms nsam number from the file name (this is not overly robust)

# Gives something like:
# ["TESTER_022817_diploidSamples_", "120_screened_2_times_msFlagFile.txt"]
inputFileSplit1 = inputFileName.split("ms_nsam_")

# Determine whether the current file is for diploids or not (triggers doubling the number
# of specified individuals to sample from a population in order to get the number
# of chromosomes sampled, which is used in the ms flag file). Only
# used if there is also a population editing file. 

if len(inputFileSplit1[0].split("diploid")) >= 2:
    isDiploidFile = 1
else:
    isDiploidFile = 0

outputNameStem = inputFileSplit1[0]

# Gives something like:
# ["120","screened", "2", "times", "msFlagFile.txt"]
inputFileSplit2 = inputFileSplit1[1].split("_")

# Parse the iteration number
msnsam = int(inputFileSplit2[0])

# If this file has already been screened at least once, get the number of times it has
# been screened.
if "screened" in inputFileSplit2:
    numScreenedTimes = int(inputFileSplit2[2])
    # Increment the number of times screened for the current screening
    numScreenedTimes += 1
# Else this is being screened for the first time.
else:
    numScreenedTimes = 1

outputFlagFileName = outputNameStem + "_screened_msFlagFile.txt"

#print(inputFileName)


migrationLocHolder = []
sFlagIndex = 0
sFlagHolder = 0

IFlagIndex = 0
IFlagHolder = 0

# Booleans for whether the -I flag and the first -m flag have been reached when
# traversing the splitLine
reachedIFlagStart = 0
reachedIFlagEnd = 0
reachedMFlag = 0

# Keep all of the split line entries before the -I flag (will always have)
# and after the -I flag samples but before the first -m flag (may or may not have)
beforeIFlagList = []
afterIFlagList = []

migrationConnectionCounter = 0
migrationDict = {}

with open(inputFileName, 'r') as inFile:
    

    
    for lineNum, line in enumerate(inFile):
        splitLine = line.split()
        # This is the whole ms flag file call but split by whitespace (any white space,
        # including any number of spaces).
        #print(splitLine)
        
        for index, element in enumerate(splitLine):
            
            if element == '-m':
                
                reachedMFlag = 1
                migrationLocHolder.append(index)
                # The dict keys are 0-based.
                migrationDict[migrationConnectionCounter] = splitLine[index + 1 : index + 4]
                migrationConnectionCounter += 1
                
#             if element == '-s':
#                 sFlagIndex = index
#                 sFlagHolder = splitLine[index + 1]
            if element == '-I':
                reachedIFlagStart = 1
                IFlagIndex = index
                IFlagHolder = splitLine[index + 1]
            
            # This is here because do not want to add the '0.0' that triggers the reachedIFlagEnd (below)
            # to the list, so put this above the flag to catch elements starting after that.
            if reachedIFlagEnd == 1 and reachedMFlag == 0:
                afterIFlagList.append(element)
            
            # This signals the end of the -I flag population sampling list (sets all migration
            # rates to 0 except those specified in the -m flags)
            if element == '0.0':
                reachedIFlagEnd = 1
            
            if reachedIFlagStart == 0:
                beforeIFlagList.append(element)
            
        
        
#print("The migration locations are: %r" % migrationLocHolder)
# print("The s flag location is: %d" % sFlagIndex)
#print("The I flag location is: %d" % IFlagIndex)

numPopnsIFlag = int(IFlagHolder)

#print("There are %s populations to simulate based on the -I flag" % numPopnsIFlag)

# ----
# This finds num popns following -I flag using -I flag number (not so good.)
# 
# popnSampleList = splitLine[IFlagHolder + 2: IFlagHolder + 2 + numPopnsIFlag]
# 
# print(popnSampleList)
# print("The length of the popn sampling list is %d" % len(popnSampleList))
# ---------

# ----------
# This finds the num popns following the -I flag by looking for the '0.0' entry at the 
# end of the -I flag entries that sets all non-specified migration connections to values of 0.
# This is not required for ms to run, but this is output by the msFlagFile generator script
# and was used in the original SpaceMix paper.

endOfIFlagIndex = splitLine.index('0.0')
#print(endOfIFlagIndex)

popnSampleList = splitLine[IFlagIndex + 2 : endOfIFlagIndex]

#print("The sampling list is:")
#print(popnSampleList)

#print("The split line is:")
#print(splitLine)

numPopnsL = len(popnSampleList)
#print("There are %s populations to simulate based on the length of the popn sampling list. " % numPopnsL)

# This gets the original population numbers (these are numbered wrt all popns including
# ghost popns) of focal populations in the sampling list.
originalFocalPopnNumbers = [index + 1 for index, num in enumerate(popnSampleList) if int(num) > 0]
#print(originalFocalPopnNumbers)

# ------------

#print(migrationDict)

# If there was a list of populations to edit (either remove or change the number of
# individuals sampled), then parse it here, update the population sampling list 
# (which follows the -I flag) if necessary, and remove any specified populations
# from the -m flag dictionary. (The actual removal of entries from the population
# sampling list to match those removed from the -m flag dict is done in the code 
# further below for flexibility of input.
if args.popnsToEditFile:

    #--------------
    # This is for the sampling list clean up
    removePopnFileName = args.popnsToEditFile
    listOfPopnsToRemove = []
    dictOfPopnsToChangeSampling = {}
    with open(removePopnFileName, 'r') as inFile:
        for line in inFile:
            # If a population to remove - 
            # (just the population number)
            if len(line.strip().split()) == 1:
                listOfPopnsToRemove.append(int(line.strip()))
            
            # If a population to change the sampling (the population number and
            # the new number of individuals to sample from it - white space delimited)
            elif len(line.strip().split()) == 2:
                splitLine = line.strip().split()
                # Keep these as strings
                popnNum = splitLine[0]
                
                enteredSamplingVal = splitLine[1]
                # Right now this is # chromosomes sampled; need to change to # indivs sampled instead.
                # Put the value in the dict (after checking for > 0). It will be checked for even/odd
                # with the diploid status of this ms flag file below.
                if int(enteredSamplingVal) < 0:
                    print("WARNING - the new number of individuals to sample in the following line is negative:")
                    print(line.strip())
                    print("Cannot set the sampling to a negative value. Setting to 0 instead.")
                    dictOfPopnsToChangeSampling[popnNum] = str(0)
                else:
                    dictOfPopnsToChangeSampling[popnNum] = enteredSamplingVal
            # This lets empty lines (like at the end of the file) pass.                            
            elif line.strip() != "":
                print("WARNING - could not parse the following line in the populations to edit file:")
                print(line.strip())
                print("Skipping this line.")
    
    # Remove any duplicate entries.        
    sortedListOfPopnsToRemove = sorted(list(set(listOfPopnsToRemove)))
    #print(sortedListOfPopnsToRemove)
    
    #print(removePopnFileName)
    
    # If there are populations that need to have their population sampling entries
    # changed
    if len(dictOfPopnsToChangeSampling) != 0:
        for popnNumString in dictOfPopnsToChangeSampling:
            # As long as the specified population number can be used as an index
            # into the popnSampleList, change the sampling for that population
            # based on the dict value (after diploid checking).
            
            try:
                int(popnNumString)
            except ValueError:
                print("WARNING: Could not convert the following population number entry in the edit file into an integer:")
                print(popnNumString)
                print("Skipping this line in the edit file.")
                continue
            
            if int(popnNumString) in range(1,len(popnSampleList) + 1):
                # If this is a haploid file, then use the sampling value entered by the 
                # user directly because numIndivs == numChromosomes. If it is diploid 
                # then double the number of individuals specified in the edit file to 
                # get the number of chromosomes to sample in the ms flag file. 
                
                originalSamplingValue = dictOfPopnsToChangeSampling[popnNumString]
                
                if isDiploidFile == 0:
                    popnSampleList[int(popnNumString) - 1] = originalSamplingValue
                
                else:
                    popnSampleList[int(popnNumString) - 1] = str(int(originalSamplingValue) * 2)
                    
            else:
                print("WARNING: Could not change the sampling for population: {}. That population number is outside the number of entries of the sampling list following the -I flag.".format(popnNumString))
        #print(popnSampleList)
        #print(isDiploidFile)
    
    # This gets the updated focal population numbers after the sampling changes have 
    # been made to the popnSampleList. This is used below to correctly parse the popnCoords
    # if that flag is used AND previous focal populations (sampling > 1) are turned
    # into ghost populations (sampling = 0) through the file editing.
    afterEditFocalPopnNumbers = [index + 1 for index, num in enumerate(popnSampleList) if int(num) > 0]
    #print(afterEditFocalPopnNumbers)
    
    #print("The changed sampling list is:")
    #print(popnSampleList)

    # ------------------
    #-------------------
    # This is for the migration flag clean up
    cleanedUpMigrationDict = {}
    
    # These keys need to stay consecutive, regardless of the connections that are
    # removed from the first dict, so keep a separate counter to become the consecutive
    # key values in the cleaned dict.
    cleanedKey = 0
    
    for key in migrationDict.keys():
        
        if int(migrationDict[key][0]) not in sortedListOfPopnsToRemove and \
        int(migrationDict[key][1]) not in sortedListOfPopnsToRemove:
            #print("----True for:")
            #print(migrationDict[key][0])
            #print("True for-----:")
            #print(migrationDict[key][1])
            cleanedUpMigrationDict[cleanedKey] = migrationDict[key]
            cleanedKey += 1
    #print("Cleaned.")
    #print(cleanedUpMigrationDict)
    # Replace the migrationDict with the new version that contains no migration
    # connections for the populations specified in the file of populations to remove.
    # This new migration dict and will continue be processed as normal below.
    
    migrationDict = copy.deepcopy(cleanedUpMigrationDict)
    
    #print('*' *10)
    #print(migrationDict)
    #print('*' *10)
    
    # ------------------


# Will be a list of the unique population numbers that occur in the migration section 
# of the flag file (the section with '-m' flags). This searches through all populations
# listed following the -m flag, regardless of their position after the flag.
popnsInMigrationSectionHolder = []

for key in migrationDict.keys():
    #print("The dict entry for key %d is: %r" %(key, migrationDict[key]))
    if int(migrationDict[key][0]) not in popnsInMigrationSectionHolder:
        popnsInMigrationSectionHolder.append(int(migrationDict[key][0]))
    if int(migrationDict[key][1]) not in popnsInMigrationSectionHolder:
        popnsInMigrationSectionHolder.append(int(migrationDict[key][1]))

numPopnsMFlag = len(popnsInMigrationSectionHolder)
#print("There are %s populations to simulate based on the length of pairwise migration connection list." % numPopnsMFlag)


sortedPopnsInMigrationSectionHolder = sorted(popnsInMigrationSectionHolder)

# Test whether the sorted population number holder is sequential (ie holds consecutive 
# population numbers up to its length) - this needs to be 1-based.

arePopnsInMigrationSectionSequential = (sortedPopnsInMigrationSectionHolder == range(1,len(sortedPopnsInMigrationSectionHolder) + 1))
#print(sortedPopnsInMigrationSectionHolder)
#print(range(1,len(sortedPopnsInMigrationSectionHolder) + 1))

#print("Are the population numbers represented in the migration portion of the flag file sequential? %r" % arePopnsInMigrationSectionSequential)

    

# If the population numbers from the m flag ARE sequential, and the population number from 
# the -m flag, from the -I flag, and from the length of the population sampling list,
# then the ms flag file does not need any clean-up and should be ready for either plotting
# in R or running with ms (assuming all other formatting is correct.)

#print("mFlagNumPopns is: {}, IFlagNumPopns is: {}, and lNumPopns is: {}".format(numPopnsMFlag, numPopnsIFlag, numPopnsL))

if arePopnsInMigrationSectionSequential == True and (numPopnsMFlag == numPopnsIFlag == numPopnsL):
	
    print("There appear to be no populations removed from the ms flag file (all population numbers are sequential).")
    print("Only making any specified changes to the number of individuals sampled per population.")
    
    # Put the screened ms flag file together using the different screened pieces
    msOutputHolder = ''
#     msOutputHolder += '-s '
#     msOutputHolder += sFlagHolder + ' '

    # Add all of the flags that occurred before the -I flag and their values.
    for entry in beforeIFlagList:
        msOutputHolder += str(entry) + ' '
    
    msOutputHolder += '-I '
    msOutputHolder += str(numPopnsIFlag) + ' '
    
    # Keep track of the number of chromosomes sampled in the screened sampling
    # list (this is nsam for ms and will be included in the name of the output file).
    nsamCounter = 0
    
    #print(popnSampleList)
    
    # Add the population sampling list
    for sampleEntry in popnSampleList:
        msOutputHolder += sampleEntry + ' '
        nsamCounter += int(sampleEntry)
        
    # Add the final 0.0 entry specifying the migration rate between any population pair
    # Not specified in the -m flag section should be set to 0.0.
    
    msOutputHolder += '0.0 '
    
    # Add any flags that occurred after the -I flag and before the first -m flag
    if afterIFlagList != []:
        for entry in afterIFlagList:
            msOutputHolder += entry + ' '
    
    
    # Add the pairwise migration connections.
    # The keys in the migration dict are nums from 0 to len(dict) - 1, which matches
    # the output from range(len(dict))
    for dictKey in migrationDict.keys():
        msOutputHolder += '-m '
        popNum1 = int(migrationDict[dictKey][0])
        popNum2 = int(migrationDict[dictKey][1])
        migrRate = float(migrationDict[dictKey][2])
        
        #print("The orig popnNum1 is: %d, and the mapped popnNum1 is: %d" % (origPopNum1, mappedPopNum1))
        #print("The orig popnNum2 is: %d, and the mapped popnNum2 is: %d" % (origPopNum2, mappedPopNum2))            
        
        #*** NOTE: THERE CANNOT BE A SPACE FOLLOWING THE LAST MIGRATION RATE ENTRY
        # IN THE FILE (IE IF AFTER THE LAST ENTRY IS A '\S\N' INSTEAD OF JUST '\N',
        # THE R PLOTTER FAILS.*****
        if dictKey != len(migrationDict.keys()) - 1:
            msOutputHolder += str(popNum1) + ' ' + str(popNum2) + ' ' + str(migrRate) + ' '
        else:
            #print("Firing for {}".format(dictKey))
            #print(len(migrationDict.keys()) - 1)
            msOutputHolder += str(popNum1) + ' ' + str(popNum2) + ' ' + str(migrRate)
    msOutputHolder += '\n'
    
    if numScreenedTimes == 1:
        outputFlagFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_time_msFlagFile.txt"
    else:
        outputFlagFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_times_msFlagFile.txt"
    
    with open(outputFlagFileName, 'w') as outFile:
        outFile.write(msOutputHolder)
        
    # Write out the popn coord file with a 'screened' counter in its file name. If no 
    # popns to edit file is used, then this will be identical to the input, but if
    # the popns to edit file is used, this will successfully remove the coordinates
    # of previous focal populations if they are set to ghost populations using the edit
    # file (e.g. '10 0')
    
    outputCoordHolder = ""
    
    if args.popnCoordsFile:
        
        if args.popnsToEditFile:
            
            # This is a list of the focal popn numbers (numbered sequentially from the
            # first original focal population as 1 to num focal populations in the original
            # flag file before any editing. This is used to determine which lines of the 
            # popn coords file to keep and which to remove because they are now ghosts 
            # after editing. 
            focalPopnNumsToKeep = []
            for popNum in afterEditFocalPopnNumbers:
                focalPopnNumsToKeep.append(originalFocalPopnNumbers.index(popNum))
            
            popnNumberCounter = 0
            #print('%%%%%')
            #print(focalPopnNumsToKeep)
            with open(args.popnCoordsFile, 'r') as inFile:
            
                for coordLine in inFile:
                    popnNumberCounter += 1
                
                    if popnNumberCounter - 1 in focalPopnNumsToKeep:
                        # Don't strip the \n
                        outputCoordHolder += coordLine
                        #print("Included.")
                        #print(coordLine)
                        wasEditedFlag = 1
                    else:
                        #print("Skipped.")
                        continue
                    #print('-'*10)
                    
        else:
            
            print("Because there were no populations to remove and there was no population editing file specified, the output popnCoordsFile is identical to the input file, but with a different 'screened' count in its name to match the msFlagFile.")
            with open(args.popnCoordsFile, 'r') as inFile:
            
                for coordLine in inFile:
                    # Don't strip the \n
                    outputCoordHolder += coordLine
        
        
        if numScreenedTimes == 1:
            outputPopnCoordsFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_time_popnCoordsFile.txt"
        else:
            outputPopnCoordsFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_times_popnCoordsFile.txt"
    
        with open(outputPopnCoordsFileName, 'w') as outFile:
            outFile.write(outputCoordHolder)
    
    
    
    
    

# If the population numbers from the m flag part of the flag file ARE NOT sequential and the 
# population number differs
# from either the population number parsed from the -I flag or the length of the sampling list,
# then clean up needs to happen.
if arePopnsInMigrationSectionSequential == False and (numPopnsMFlag != numPopnsIFlag or numPopnsMFlag != numPopnsL):
    print("Removing populations from the ms flag file.")
    
    # Need to put other conditions and messages here if there
    
    
    if(numPopnsMFlag < numPopnsIFlag and numPopnsMFlag < numPopnsL):
        
        # Use the numPopnsL to determine the upper number of expected population numbers, and give a 
        # warning if numPopnsL != numPopnsIFlag

        if numPopnsL != numPopnsIFlag:
            print("Warning: the number of populations specified by the -I flag does not match the \n\
            number of populations specified by the population sampling list. Using the number in the population\n\
            sampling list to find the missing populations in the -m flag portion of the file.")
        
        # reset the numPopnsIFlag to the numPopnsMFlag
        numPopnsIFlag = numPopnsMFlag
        
        # Figure out which populations are missing (this is more for printing to the screen
        # for user confirmation than any tabulation in this script - the populations 
        # that are represented are used for subsetting the sampling list instead of the 
        # populations that are missing.
        mFlagMissingPopnNumbers = sorted(list(set(range(1,numPopnsL)) - set(sortedPopnsInMigrationSectionHolder)))
    
        #print("The missing populations in the -m flag portion of the file are:")
        #print(mFlagMissingPopnNumbers)
        
        # This creates the newly subset population sampling list, only keeping the population
        # entries for the populations that are represented in the -m flag portion of the 
        # file.
        screenedPopnSampleList = [popnSampleList[popnNum - 1] for popnNum in sortedPopnsInMigrationSectionHolder]
        
        #print(screenedPopnSampleList)
        #print(len(screenedPopnSampleList))
        
        # Screen the popnCoordsFile using the screenedPopnSampleList if the -p flag was used
        # The population coords are only for the focal populations (there are no coords entered
        # for the ghost populations, since they are not used in any of the downstream analysis
        # methods). So the popn coords is 1 to number of focal populations, but when the 
        # populations are specified to remove from the file they are specified from 1 to 
        # the total number of focal AND ghost populations (because removing ghosts from
        # the landscape is important to due in order to 'sculpt' it). So first need to find
        # the focal population numbers in terms of the total number of populations we started
        # with (using the population sampling following the -I flag), and then determine
        # whether those focal populations were removed (and therefore should be removed
        # for the popnCoordsFile too).
        # to be able to do
        
    
        if args.popnCoordsFile:
        
            outputCoordHolder = ""
            
            if args.popnsToEditFile:
            
                # This is a list of the focal popn numbers (numbered sequentially from the
                # first original focal population as 1 to num focal populations in the original
                # flag file before any editing. This is used to determine which lines of the 
                # popn coords file to keep and which to remove because they are now ghosts 
                # after editing. 
                focalPopnNumsToKeep = []
                for popNum in afterEditFocalPopnNumbers:
                    focalPopnNumsToKeep.append(originalFocalPopnNumbers.index(popNum))
            
                popnNumberCounter = 0
                #print('%%%%%')
                #print(focalPopnNumsToKeep)
                with open(args.popnCoordsFile, 'r') as inFile:
            
                    wasEditedFlag = 0
            
                    for coordLine in inFile:
                        popnNumberCounter += 1
                
                        # Use the popnNumberCounter (sequential focal popn number) as an
                        # index into the list of focal population numbers that includes ghost
                        # population number. If this population number was not removed
                        # from the flag file, and has not been edited from a focal population
                        # to become a ghost population, then keep it.
                        if originalFocalPopnNumbers[popnNumberCounter - 1] not in mFlagMissingPopnNumbers\
                            and popnNumberCounter - 1 in focalPopnNumsToKeep:
                            # Don't strip the \n
                            outputCoordHolder += coordLine
                            #print("Included.")
                            #print(coordLine)
                            wasEditedFlag = 1
                        else:
                            #print("Skipped.")
                            continue
                        #print('-'*10)
                if wasEditedFlag == 1:
                    print("The popnCoordsFile has been updated to remove the previous focal populations that are now specified as ghost populations after editing.")
        
            else:
                with open(args.popnCoordsFile, 'r') as inFile:
                    
                    popnNumberCounter = 0
                    
                    for coordLine in inFile:
                        popnNumberCounter += 1
                        
                        # Use the popnNumberCounter (sequential focal popn number) as an
                        # index into the list of focal population numbers that includes ghost
                        # population number. If this population number was not removed
                        # from the flag file, then keep it in the population coords file.
                        if originalFocalPopnNumbers[popnNumberCounter - 1] not in mFlagMissingPopnNumbers:
                            # Don't strip the \n
                            outputCoordHolder += coordLine
                            #print("Included.")
                            #print(coordLine)
                            wasEditedFlag = 1
                        else:
                            #print("Skipped.")
                            continue
                        #print('-'*10)
        
        
        # Need to create a mapping between the original population numbers found in the 
        # -m flag portion of the file and sequential population numbers that will be 
        # used to generate the screened msFlag file output.
        
        mFlagPopnMappingDict = {}
        consecutivePopnNums = range(1,len(sortedPopnsInMigrationSectionHolder) + 1)
        for index, popnNum in enumerate(sortedPopnsInMigrationSectionHolder):
            mFlagPopnMappingDict[popnNum] = consecutivePopnNums[index]
        
        #print('*' *10)
        #print(migrationDict)
        #print('*' *10)
        
        #print("The mflag mapping dict is:")
        #print(mFlagPopnMappingDict)
        
        # Put the screened ms flag file together using the different screened pieces
        screenedMsOutputHolder = ''
#         screenedMsOutputHolder += '-s '
#         screenedMsOutputHolder += sFlagHolder + ' '
#         
        
        # Add all of the flags that occurred before the -I flag and their values.
        for entry in beforeIFlagList:
            screenedMsOutputHolder += str(entry) + ' '
        
        screenedMsOutputHolder += '-I '
        screenedMsOutputHolder += str(numPopnsIFlag) + ' '
        
        # Keep track of the number of chromosomes sampled in the screened sampling
        # list (this is nsam for ms and will be included in the name of the output file).
        nsamCounter = 0
        
        #print(screenedPopnSampleList)
        
        # Add the population sampling list
        for sampleEntry in screenedPopnSampleList:
            screenedMsOutputHolder += sampleEntry + ' '
            nsamCounter += int(sampleEntry)
            
        # Add the final 0.0 entry specifying the migration rate between any population pair
        # Not specified in the -m flag section should be set to 0.0.
        
        screenedMsOutputHolder += '0.0 '
        
        # Add any flags that occurred after the -I flag and before the first -m flag
        if afterIFlagList != []:
            for entry in afterIFlagList:
                screenedMsOutputHolder += entry + ' '
        
        # Add the pairwise migration connections.
        # The keys in the migration dict are nums from 0 to len(dict) - 1, which matches
        # the output from range(len(dict))
        for dictKey in migrationDict.keys():
            screenedMsOutputHolder += '-m '
            origPopNum1 = int(migrationDict[dictKey][0])
            origPopNum2 = int(migrationDict[dictKey][1])
            migrRate = float(migrationDict[dictKey][2])
            
            mappedPopNum1 = mFlagPopnMappingDict[origPopNum1]
            mappedPopNum2 = mFlagPopnMappingDict[origPopNum2]
            
            #print("The orig popnNum1 is: %d, and the mapped popnNum1 is: %d" % (origPopNum1, mappedPopNum1))
            #print("The orig popnNum2 is: %d, and the mapped popnNum2 is: %d" % (origPopNum2, mappedPopNum2))            
            
            #*** NOTE: THERE CANNOT BE A SPACE FOLLOWING THE LAST MIGRATION RATE ENTRY
            # IN THE FILE (IE IF AFTER THE LAST ENTRY IS A '\S\N' INSTEAD OF JUST '\N',
            # THE R PLOTTER FAILS.*****
            if dictKey != len(migrationDict.keys()) - 1:
                screenedMsOutputHolder += str(mappedPopNum1) + ' ' + str(mappedPopNum2) + ' ' + str(migrRate) + ' '
            else:
                #print("Firing for {}".format(dictKey))
                #print(len(migrationDict.keys()) - 1)
                screenedMsOutputHolder += str(mappedPopNum1) + ' ' + str(mappedPopNum2) + ' ' + str(migrRate)
        screenedMsOutputHolder += '\n'
        
        if numScreenedTimes == 1:
            outputFlagFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_time_msFlagFile.txt"
        else:
            outputFlagFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_times_msFlagFile.txt"
        
        with open(outputFlagFileName, 'w') as outFile:
            outFile.write(screenedMsOutputHolder)
            
        if args.popnCoordsFile:            
            if numScreenedTimes == 1:
                outputPopnCoordsFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_time_popnCoordsFile.txt"
            else:
                outputPopnCoordsFileName = outputNameStem + "ms_nsam_" + str(nsamCounter) + "_screened_" + str(numScreenedTimes) + "_times_popnCoordsFile.txt"
        
            with open(outputPopnCoordsFileName, 'w') as outFile:
                outFile.write(outputCoordHolder)