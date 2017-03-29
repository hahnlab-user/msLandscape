#!/usr/bin/env python

# This is for creating the ghostLands full hex grid with ghost populations between 
# all focal populations and rings of ghost populations around the focal population 'core'.

# NOTE - THIS DOES NOT CURRENTLY GENERATE THE FULL MS CALL WITH THE SAMPLING SPECIFIED, 
# IT ONLY CREATES THE MIGRATION PATH CALL.

# This is working correctly for both right- and left-shifted rows including the 
# tile plotting 9/16/16.

# This generates tiles for tesselation one at a time (and concatenates them into a row of the desired
# length. This then also concatenates the rows so that a single call to this script
# gives the entire '-m' call needed for ms. 

# There are flags to specify whether the current row of tiles is right-shifted  or left-shifted 

# Updated 021417 to add command line flags and testing, option for output file re-direction
# and added population coordinate calculation and output for focal files. Working correctly.

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--numRows', type = int, help = "The number of rows of focal populations to generate. Defaults to 2")
parser.add_argument('-c', '--numCols', type = int, help = "The number of columns of focal populations to generate. Defaults to 3")
parser.add_argument('-g', '--numGhostRings', help = "The number of rings of ghost populations to surround the focal population grid. Defaults to 0")
parser.add_argument('-m', '--migrRate', help = "The migration rate to use for all of the pairwise migration connections. Defaults to 3.0")
parser.add_argument('-n', '--numIndivPerPopn' , type = int, help = "The number of individuals to sample from each focal population. Defaults to 10")
parser.add_argument('-d', '--isDiploid', choices=["0", "1", "n", "y", "no", "yes", "N", "Y", "No", "Yes", "NO", "YES", "FALSE", "TRUE", "False", "True", "false", "true"], help = "Should this be a simulation for diploid organisms (ie having 2 independent alleles from the coalescent simulation) or not (and therefore simulated as being haploid)? Defaults to no")
parser.add_argument('-s', '--isRightShifted', choices=["0", "1", "n", "y", "no", "yes", "N", "Y", "No", "Yes", "NO", "YES", "FALSE", "TRUE", "False", "True", "false", "true"], help = "Should the first row of the tiles to simulate (regardless of whether it is a ring of ghost populations or the focal populations) be right-shifted compared to the second row? Defaults to no")
parser.add_argument('-o', '--outputFileStem', help = "Optional. The stem of the output file name (without an extension). This name will be used to create a file for the ms flag file and another file for the ASCII tile representation instead of printing them to the screen. Optional - no default")
args = parser.parse_args()

#inputFileName = args.inputFile
#outputFileName = args.outputFile

# Assign arguments to variables if entered on the command line, otherwise use default
# values.

if args.numRows:
    if int(args.numRows) < 0:
        print("Warning - the number of rows needs to be positive. Setting to 2.")
        numRows = 2
    else:
        numRows = int(args.numRows)
else:
    numRows = 2

if args.numCols:
    if int(args.numCols) < 0:
        print("Warning - the number of columns needs to be positive. Setting to 3.")
        numTilesInEachRow = 3
    else:
        numTilesInEachRow = int(args.numCols)
else:
    numTilesInEachRow = 3

if args.numGhostRings:
    if int(args.numGhostRings) < 0:
        print("Warning - the number of rings of ghost populations cannot be negative. Setting to 0.")
        numBorderingGhostPopRings = 0
    else:
        numBorderingGhostPopRings = int(args.numGhostRings)
        #print(int(args.numGhostRings))
else:
    numBorderingGhostPopRings = 0

if args.migrRate:
    if float(args.migrRate) < 0:
        print("Warning - the pairwise migration rate cannot be negative. Setting to 3.0.")
        migrationRate = 3.0
    else:
        migrationRate = float(args.migrRate)
else:
    migrationRate = 3.0
    
if args.numIndivPerPopn:
    if int(args.numIndivPerPopn) < 0:
        print("Warning - the number of individuals sampled per population cannot be negative. Setting to 10.")
        numIndividualsSampledPerPopn = 10
    else:
        numIndividualsSampledPerPopn = int(args.numIndivPerPopn)
else:
    numIndividualsSampledPerPopn = 10
    
if args.isDiploid:
    if args.isDiploid in ["0", "n", "no", "N", "No", "NO", "FALSE", "False", "false"]:
        isDiploid = 0
    elif args.isDiploid in ["1", "y", "yes", "Y", "Yes", "YES", "TRUE","True", "true"]:
        isDiploid = 1
# Defaults to haploid simulations
else:
    isDiploid = 0

if args.isRightShifted:
    if args.isRightShifted in ["0", "n", "no", "N", "No", "NO", "FALSE", "False", "false"]:
        rightShiftedRow = 0
    elif args.isRightShifted in ["1", "y", "yes", "Y", "Yes", "YES", "TRUE","True", "true"]:
        rightShiftedRow = 1
# Defaults to a right shifted first row
else:
    rightShiftedRow = 0
    
    
if args.outputFileStem:
    outputFileStem = args.outputFileStem 
else:
    outputFileStem = ""
    outputASCIIFile = ""

# This is only used for creating the msFlagFile, and is passed as the '-s' flag to ms
# in that file. This is not currently user selectable due to potential downstream processing
# problems after ms simulations.
msNumSegregatingSites = 1

# *****************

# Each tile looks like (along with the order of segment creation):

#         o
#        /|\
#       / | \
#     o/  |  \o
#     |\  |  /|
#     | \ | / |
#     |  \|/  |
#     |   o   |
#     |  /|\  |
#     | / | \ |
#     |/  |  \|
#     o\  |  /o
#       \ | /
#        \|/
#         o


# Basic Tesselation tile

#         o
#      3 /|\ 5
#       / | \
#     o/  |4 \o
#     |\2 |  /
#   1 | \ | /6 
#     |  \|/
#     |   o    
#     |  /|\  
#     | / | \7 
#     |/9 |8 \
#     o   |   o
#         | 
#         |
#         o


# Right shifted rows start as above, and end with:


#         o
#      3 /|\ 5
#       / | \
#     o/  |4 \o
#     |\2 |  /|
#     | \ | /6| 
#     |  \|/  |
#   1 |   o   | 10 
#     |  /|\  |
#     | / | \7| 
#     |/9 |8 \|
#     o   |  /o
#         | / 
#         |/ 11
#         o

# Left shifted rows start with:

#         o
#      3 /|\ 5
#       / | \
#     o/  |4 \o
#     |\2 |  /
#     | \ | /6 
#     |  \|/
#   1 |   o    
#     |  /|\  
#     | / | \7 
#     |/9 |8 \
#     o   |   o
#      \  | 
#    12 \ |
#        \o


# and end with:

#         o
#      3 /|\ 5
#       / | \
#     o/  |4 \o
#     |\2 |  /|
#     | \ | /6| 
#     |  \|/  |
#   1 |   o   | 10 
#     |  /|\  |
#     | / | \7| 
#     |/9 |8 \|
#     o   |   o
#         |  
#         | 
#         o


# Tiles used for plotting the resulting grid:

tile_a = {}
tile_a[0] = "           *          "
tile_a[1] = "       :   :   :      "
tile_a[2] = "    :      :      :   "
tile_a[3] = "*          :          "


tile_b = {}
tile_b[0] = "           *          "
tile_b[1] = "       :   :   :      "
tile_b[2] = "    :      :      :   "
tile_b[3] = "*          :          *"

tile_c = {}
tile_c[0] = ":   :      :      :   "
tile_c[1] = ":      :   :   :      "
tile_c[2] = ":          *          "
tile_c[3] = ":      :   :   :      "
tile_c[4] = ":   :      :      :   "

tile_d = {}
tile_d[0] = ":   :      :      :   :"
tile_d[1] = ":      :   :   :      :"
tile_d[2] = ":          *          :"
tile_d[3] = ":      :   :   :      :"
tile_d[4] = ":   :      :      :   :"

tile_e = {}
tile_e[0] =     "*          "
tile_e[1] =     "    :      "
tile_e[2] =     "      :    "
tile_e[3] =     "           "

tile_f = {}
tile_f[0] = ":          *          "
tile_f[1] = ":      :   :   :      "
tile_f[2] = ":   :      :      :   "
tile_f[3] = "*          :          "

tile_g = {}
tile_g[0] = ":          *           "
tile_g[1] = ":      :   :   :       "
tile_g[2] = ":   :      :      :    "
tile_g[3] = "*          :          *"

tile_h = {}
tile_h[0] = ":          *"
tile_h[1] = ":      :    "
tile_h[2] = ":   :       "
tile_h[3] = "*           "

tile_i = {}
tile_i[0] = "*          :          "
tile_i[1] = "    :      :      :   "
tile_i[2] = "      :    :   :      "
tile_i[3] = "           *          "

tile_j = {}
tile_j[0] = "*          :          *"
tile_j[1] = "    :      :      :    "
tile_j[2] = "      :    :   :       "
tile_j[3] = "           *           "

tile_k = {}
tile_k[0] = ":   :      :      :   "
tile_k[1] = ":      :   @   :      "
tile_k[2] = ":         @0@         "
tile_k[3] = ":      :   @   :      "
tile_k[4] = ":   :      :      :   "

tile_l = {}
tile_l[0] = ":   :      :      :   :"
tile_l[1] = ":      :   @   :      :"
tile_l[2] = ":         @0@         :"
tile_l[3] = ":      :   @   :      :"
tile_l[4] = ":   :      :      :   :"



tileOutputHolder = ""

samplingHolder = ""

numSamples = 0

# This is a class to create objects (with specified size - aka number of lines) to work
# with aggregating the various basic tile types defined above to form a row of tiles, 
# and then printing them to the screen (or to an outputfile - still need to code).
# isRightShifted is a boolean (0/1) denoting whether the row of tiles represented by the object
# is shifted to the right (and therefore the first tile is padded with '    ' or not).
# by the object. isFirstLastRow is a boolean (0/1) for whether this is the first or last tile row
# in the simulation (needed to generate correct tile indenting in addTilesToTileRun below)
class tileHolder(object):
    def __init__(self, numLines, isRightShifted, isFirstLastRow):
        self.tileRunDict = {}
        self.numTileLines = numLines
        for num in range(numLines):
            self.tileRunDict[num] = ""
        self.isDictEmpty = 1
        self.isRightShifted = isRightShifted
        self.isFirstLastRow = isFirstLastRow
        
        
    def addTileRunToOutputHolder(self):
        # access the global tileOutputHolder var.
        global tileOutputHolder
        for key in self.tileRunDict:
            # Add the current line (key of self.tileRunDict) to the 
            # global tileOutputHolder. Also need to add the newline at the end of 
            # each current line.
            tileOutputHolder += self.tileRunDict[key] + '\n'
            #print(self.tileRunDict[key])
        
    # Add multiple tiles at once (passed as a list of tile dicts to add)
    def addTilesToTileRun(self, listOfTileDictsToAdd):
        for tileDictIndex, tileToAddDict in enumerate(listOfTileDictsToAdd):
            for num in range(self.numTileLines):
                # Pad the first tile entries if this row is right-shifted; This is ugly right
                # now. need to only pad the middle tile (which CURRENTLY has 5 lines) 
                # of right-shifted rows (not the bottom
                # tile).
                if (self.isDictEmpty == 1 and self.isRightShifted == 1 and 
                (self.numTileLines == 5 or self.isFirstLastRow == 1)):
                    self.tileRunDict[num] += "           " + tileToAddDict[num]
                else:
                    self.tileRunDict[num] += tileToAddDict[num]
            self.isDictEmpty = 0


# initialize bottomRow to 0 for false (NOTE - this assumes more than 1 row of tiles are 
# being created).
bottomRow = 0

# Keep track of whether the first row is right-shifted or not.
if rightShiftedRow == 0:
    firstRowRightShifted = 0
else:
    firstRowRightShifted = 1

# This holds the ms simulation call for tile grid - extends 1 row at a time.
tileCallHolder = ''

# Called by the function below to toggle the right-shift var for successive simulated
# rows
def toggleRightShift(rightShiftedRow):
    if rightShiftedRow == 0:
        rightShiftedRow = 1    
    else:
        rightShiftedRow = 0
    return rightShiftedRow
    

# pad the numRows and the numCellsPerRow with the number of bordering ghost popn rings
# the user specified (need to pad both ends)
numRows = numRows + (2*numBorderingGhostPopRings)
numTilesInEachRow = numTilesInEachRow + (2 * numBorderingGhostPopRings)

# ASCII - Before start looping through the rows, make the graphical tiles for the top of the first 
# row of tiles.
# Set the isFirstLast boolean flag to 1 for true.
topTileHolder = tileHolder(4, rightShiftedRow, 1)
for num in range(numTilesInEachRow - 1):
    topTileHolder.addTilesToTileRun([tile_a])
    
topTileHolder.addTilesToTileRun([tile_b])

topTileHolder.addTileRunToOutputHolder()

# Set up a holder for the coordinates of the sampled focal populations (coordinates
# increase from left to right in increments of 2 to accomodate the staggering, 
# and bottom to top in increments of 1. This makes the lower left focal population 
# have coordinates of either (1,1) or (1,2) depending on staggering.

coordHolder = ""

for row in range(numRows):
    #print("Row is: {}".format(row))
    
    # Instantiate a tileHolder object to hold the graphical representation (as tiles)
    # for the current row.
    currRowTileHolderMid = tileHolder(5, rightShiftedRow, 0)
    if row != numRows - 1:
        currRowTileHolderBot = tileHolder(4, rightShiftedRow, 0)
    else:
        currRowTileHolderBot = tileHolder(4, rightShiftedRow, 1)
    
    # This is the number of populations represented in the current row of tesselation tiles.
    # This is calculated using the number of tiles by counting the top left and top center
    # ghost populations, and the focal population in each tile for all tiles. For the 
    # left-most tile in the row (for right-shifted rows)
    # and the right-most tile in the row (for left-shifted rows), also need to count
    #  the population in the
    # 'overhanging' tile from the previous tile row. This is the 
    # offset of the population numbers from the first tile in each successive row. 
    
    # For starting with left-shifted rows, or when the prev. row was right-shifted (ie the 
    # current row is left-shifted), then the offset is one pop less
    #if ((row == 0 and firstRowRightShifted == 0) or rightShiftedRow == 0):
    
    
    # Special case of smaller population num offset if the first row is left-shifted
    if row == 0 and firstRowRightShifted == 0:
        numPopnOffsetPerRow = (3 * numTilesInEachRow) + 1
    else:
        numPopnOffsetPerRow = (3 * numTilesInEachRow) + 2
    
    #print("numPopnOffsetPerRow is: {}".format(numPopnOffsetPerRow))
    
    # This is the first population number in the current row of tiles being created. 
    # Note - this starts numbering from population 1 in the upper left hand corner of the 
    # tile grid.
    # The value of the first popn changes depending on whether the current
    # row is right-shifted or not
    
    # This is relative to the left-shifted rows, so the firstPopNum in the right-shifted
    # rows is 1 more than in the left-shifted rows.    
    if row == 0:
        firstPopNum = 1
    elif rightShiftedRow == 0:
        firstPopNum = (row * numPopnOffsetPerRow)
    elif rightShiftedRow == 1:
        firstPopNum = (row * numPopnOffsetPerRow) + 1
    
    # Set the boolean if this is the bottom row of the simulation grid
    if row == numRows - 1:
        bottomRow = 1
    
    #print("Row is: {}".format(row))
    #print("First pop num is: {}".format(firstPopNum))

    for currTile in range(numTilesInEachRow):
        tileMSCall = ''
        
        # --------------------------------
        # For the ascii graphics tiles
        
        # Middle tiles
        # if this is not the last tile in the row
        if currTile != numTilesInEachRow - 1:
            # Check if this needs to be a tile with a ghost population in the middle
            # or not (ie whether this tile is one of the bordering ghost rings)
            if (row <= numBorderingGhostPopRings - 1 or row >= numRows - numBorderingGhostPopRings) or \
                (currTile<= numBorderingGhostPopRings - 1 or currTile >= numTilesInEachRow - numBorderingGhostPopRings):
                currRowTileHolderMid.addTilesToTileRun([tile_c])
                
            # Else this is a regular tile
            else:
                currRowTileHolderMid.addTilesToTileRun([tile_k])
                
                # add to the population coordinate holder
                yCoord = numRows - row - numBorderingGhostPopRings
                if rightShiftedRow == 1:
                    xCoord = 2 * (1 + (currTile - numBorderingGhostPopRings))
                else:
                    xCoord = 1 + (2 * (currTile - numBorderingGhostPopRings))
                coordHolder += str(yCoord) + ' ' + str(xCoord) + '\n'
               
        # else this is the last tile in the row, and it needs to have a different tile.
        else:
            # Check if this needs to be a tile with a ghost population in the middle
            # or not (ie whether this tile is one of the bordering ghost rings)
            if (row <= numBorderingGhostPopRings - 1 or row >= numRows - numBorderingGhostPopRings) or \
                (currTile<= numBorderingGhostPopRings - 1 or currTile >= numTilesInEachRow - numBorderingGhostPopRings):
                currRowTileHolderMid.addTilesToTileRun([tile_d])
                
            # Else this is a regular tile
            else:
                currRowTileHolderMid.addTilesToTileRun([tile_l])
                
                # add to the population coordinate holder
                yCoord = numRows - row - numBorderingGhostPopRings
                if rightShiftedRow == 1:
                    xCoord = 2 * (1 + (currTile - numBorderingGhostPopRings))
                else:
                    xCoord = 1 + (2 * (currTile - numBorderingGhostPopRings))
                coordHolder += str(yCoord) + ' ' + str(xCoord) + '\n'
        
        # Bottom tiles
        
        # If the current row is not the last one
        if row != numRows - 1:
            if rightShiftedRow == 0:
                if currTile == 0:
                    currRowTileHolderBot.addTilesToTileRun([tile_e])

                # Need to add 2 tiles to finish the row
                elif currTile == numTilesInEachRow - 1:
                    currRowTileHolderBot.addTilesToTileRun([tile_f, tile_g])

                else:
                    currRowTileHolderBot.addTilesToTileRun([tile_f])

            else:
                if currTile == 0:
                    currRowTileHolderBot.addTilesToTileRun([tile_a])

                # Need to add 2 tiles to finish the row
                elif currTile == numTilesInEachRow - 1:
                    currRowTileHolderBot.addTilesToTileRun([tile_f, tile_h])

                else:
                    currRowTileHolderBot.addTilesToTileRun([tile_f])

        # else this is the last row; treat the same for right/left shifted rows
        # (the class definition takes care of shifting this last row right/left.)
        else:
            if currTile != numTilesInEachRow - 1:
                currRowTileHolderBot.addTilesToTileRun([tile_i])

            else:
                currRowTileHolderBot.addTilesToTileRun([tile_j])

        # ----------------------------------
        
        #print("Current tile is: {}".format(currTile))
        
        topLeftValue = firstPopNum + (2 * currTile)
        
        #print("topLeftValue: {}".format(topLeftValue))
        
        # This is the offset between the first popn number for the tile row (which is a ghost popn)
        # and the first focal popn in that same tile row. This is for ease of reading, and 
        # is used to calculate the focal popn number for a given tile based on right/left-shifted
        # below.
      
        numPopnOffsetForFocalPopns = ((2 * numTilesInEachRow) + 2)

        #print("numPopnOffsetForFocalPopns is: {}".format(numPopnOffsetForFocalPopns))

        # This does not intuitively make sense to me, but the offset difference between the 
        # top left ghost and the center focal population decreases by 1 for each 
        # successive tile from L to R.
        
        if (row == 0 or rightShiftedRow == 1):
        
            focalPopnValue = topLeftValue + numPopnOffsetForFocalPopns - currTile - 1
        
        else:
            focalPopnValue = topLeftValue + numPopnOffsetForFocalPopns - currTile


# ---------------------------
# This makes the population sampling scheme for the ms flag tile (ie 1 entry per population
# with each entry being how many individuals should be sampled from that population)        
        # Update the sampling string based on the focalPopnValue and using the fact
        # that any populations other than the focal populations are always unsampled (ghosts)
        # (and sometimes the 'focal' ie populations in the middle of each tile) are too,
        # depending on how many ghost rings there were. 
        if currTile == 0:
            # This is true when row == 0
            if samplingHolder == "":
                # make an initial pad of zeros.
                for num in range(focalPopnValue - 1):
                    samplingHolder += "0 "
            # If this is past row == 0, and therefore there are already
            # entries in the samplingHolder (and crucially the last focal population
            # in the previous row is the last entry in the samplingHolder.
            else:
                prevFocalValue = len(samplingHolder.split(" ")) - 1
                #print("The prev focal value is {}".format(prevFocalValue))
                for num in range(focalPopnValue - prevFocalValue - 1):
                    samplingHolder += "0 "
        
        # Add the correct value for the population in the middle of the current tile,
        # based on whether it is in the bordering ghost ring or not and whether this 
        # simulation is for diploids (ie sampling twice the number of chromosomes as
        # the number of individuals specified by the user or not).
        
        if (row <= numBorderingGhostPopRings - 1 or row >= numRows - numBorderingGhostPopRings) or \
            (currTile<= numBorderingGhostPopRings - 1 or currTile >= numTilesInEachRow - numBorderingGhostPopRings):
            samplingHolder += "0 "
        else:
            if isDiploid == 1:
                samplingHolder += str(2* numIndividualsSampledPerPopn) + " "
                numSamples += 2 * numIndividualsSampledPerPopn
            else:
                samplingHolder += str(numIndividualsSampledPerPopn) + " "
                numSamples += numIndividualsSampledPerPopn
                
        # Finish padding the sampling holder with the final row of ghost populations 
        # (from the bottom border of the last row of tiles) when reach the last tile.
        
        if row == numRows - 1 and currTile == numTilesInEachRow - 1:
            # The number of ghost populations to add here is 2*numTilesInEachRow + 1
            for num in range(2*numTilesInEachRow + 1):
                samplingHolder += "0 "
        
# ---------------------------------------            
            
        
        #print("First focal pop number is: {}".format(focalPopnValue))
        
        # index of the top left ghost pop.
        tlg = str(topLeftValue)
        
        # index of the middle focal population
        mfp = str(focalPopnValue)
        
        # index of bottom left ghost pop. This has a special reduced offset case if it
        # is the last tile row and it is right-shifted.
        if (row == numRows - 1 and rightShiftedRow == 1):
            blg = str(int(tlg) + numPopnOffsetPerRow - 1)
        else:
            blg = str(int(tlg) + numPopnOffsetPerRow)
        
        # spacer to construct properly formatted ms call
        sp = ' ' + str(migrationRate) + ' -m '
        
        # Prefix with '-m' if this is the first simulated tile
        if (row == 0 and currTile == 0):
            migr1F = '-m ' + tlg + ' ' + blg + sp
        
        else:
            migr1F = tlg + ' ' + blg + sp
        
        migr1R = blg + ' ' + tlg + sp
                
        migr2F = tlg + ' ' + mfp + sp
        migr2R = mfp + ' ' + tlg + sp

        migr3F = tlg + ' ' + str(int(tlg) + 1) + sp
        migr3R = str(int(tlg) + 1) + ' ' + tlg + sp

        migr4F = str(int(tlg) + 1) + ' ' + mfp + sp
        migr4R = mfp + ' ' + str(int(tlg) + 1) + sp

        migr5F = str(int(tlg) + 1) + ' ' + str(int(tlg) + 2) + sp
        migr5R = str(int(tlg) + 2) + ' ' + str(int(tlg) + 1) + sp

        migr6F = str(int(tlg) + 2) + ' ' + mfp + sp
        migr6R = mfp + ' ' + str(int(tlg) + 2) + sp

        migr7F = str(int(blg) + 2) + ' ' + mfp + sp
        migr7R = mfp + ' ' + str(int(blg) + 2) + sp

        migr8F = str(int(blg) + 1) + ' ' + mfp + sp
        migr8R = mfp + ' ' + str(int(blg) + 1) + sp

        migr9F = blg + ' ' + mfp + sp
        migr9R = mfp + ' ' + blg + sp

        
        # This is the basic tile set-up with 9 connections. If it is not added on
        # by any of the if statements below that are special cases for adding connections
        # 10, 11, and 12 depending on whether it is the end of the row, the bottom
        # of the grid, or right- or left-shifted rows.
        tileMSCall = (migr1F + migr1R + migr2F + migr2R + migr3F + migr3R + migr4F + 
                      migr4R + migr5F + migr5R + migr6F + migr6R + migr7F + migr7R + migr8F + 
                      migr8R + migr9F + migr9R)
        
        if bottomRow == 1:
            
            if currTile == numTilesInEachRow - 1:
                migr10F = str(int(tlg) + 2) + ' ' + str(int(blg) + 2) + sp
                migr10R = str(int(blg) + 2) + ' ' + str(int(tlg) + 2) + sp
                tileMSCall += (migr10F + migr10R)

            migr11F = str(int(blg) + 2) + ' ' + str(int(blg) + 1) + sp
            migr11R = str(int(blg) + 1) + ' ' + str(int(blg) + 2) + sp
             
                
            migr12F = str(int(blg) + 1) + ' ' + blg + sp
            
            if currTile == numTilesInEachRow - 1:
            
                migr12R = blg + ' ' + str(int(blg) + 1) + ' ' + str(migrationRate)
                    
            else:
                migr12R = blg + ' ' + str(int(blg) + 1) + sp
            
            tileMSCall += (migr11F + migr11R + migr12F + migr12R)
            tileCallHolder += tileMSCall
            continue
                
        # For the start of left-shifted rows
        elif (rightShiftedRow == 0 and currTile == 0):
                
            migr12F = str(int(blg) + 1) + ' ' + blg + sp
            migr12R = blg + ' ' + str(int(blg) + 1) + sp    
            
            tileMSCall += (migr12F + migr12R)
            tileCallHolder += tileMSCall
            
            continue
                
        
        # For the end of right-shifted rows
        elif (rightShiftedRow == 1 and currTile == numTilesInEachRow - 1):
        
            migr10F = str(int(tlg) + 2) + ' ' + str(int(blg) + 2) + sp
            migr10R = str(int(blg) + 2) + ' ' + str(int(tlg) + 2) + sp
                
            migr11F = str(int(blg) + 2) + ' ' + str(int(blg) + 1) + sp
            migr11R = str(int(blg) + 1) + ' ' + str(int(blg) + 2) + sp
            
            tileMSCall += (migr10F + migr10R + migr11F + migr11R)
            tileCallHolder += tileMSCall
            
            continue    
        
        # For the end of left-shifted rows
        elif (rightShiftedRow == 0 and currTile == numTilesInEachRow - 1):
        
            migr10F = str(int(tlg) + 2) + ' ' + str(int(blg) + 2) + sp
            migr10R = str(int(blg) + 2) + ' ' + str(int(tlg) + 2) + sp
            
            tileMSCall += (migr10F + migr10R)
            tileCallHolder += tileMSCall
            
            continue    
        
        # This is the base case for when none of the above 'if' statements (critically 
        # each with 'continue's triggered, then it is a regular 9 connection tile, and 
        # add it to the tileCallHolder
        
        else:
            tileCallHolder += tileMSCall
    
    # toggle the right shift value for the next row
    rightShiftedRow = toggleRightShift(rightShiftedRow)
    
    # Print the ascii tile holders for the current row:
    currRowTileHolderMid.addTileRunToOutputHolder()
    currRowTileHolderBot.addTileRunToOutputHolder()
    
        
# This prints the ms call to screen
#print(tileCallHolder)

#print()

# This prints the population sampling scheme for ms based on the configuration of ghost
# and focal populations
#print(samplingHolder)
#print(len(samplingHolder.split(" ")) - 1)

# Start putting together the final msFlagFile content
finalNumPopns = len(samplingHolder.split(" ")) - 1

finalSamplingHolder = "-s "
finalSamplingHolder += str(msNumSegregatingSites) + " -I " + str(finalNumPopns) + " " + samplingHolder + "0.0 " + tileCallHolder + "\n"

# This finalSamplingHolder now contains the complete msFlagFile contents for the ms
# call based on the population configuration specified above.

# Either write the ms flag file and the ASCII tile representation to external files (if
# the user selected the '-o' flag, or print them to the screen if the '-o' flag was 
# not selected.

if outputFileStem != "" :
    
    if isDiploid == 1:
        outputFlagFile = outputFileStem + '_diploidSamples_ms_nsam_' + str(numSamples) + '_msFlagFile.txt'
    else:
        outputFlagFile = outputFileStem + '_haploidSamples_ms_nsam_' + str(numSamples) + '_msFlagFile.txt'
        
    outputASCIIFile = outputFileStem + '_ASCII_tilePlotFile.txt'
    outputPopnLocFile = outputFileStem + '_popnCoordinatesFile.txt'
    
    with open(outputFlagFile, 'w') as flagFileOut:
        flagFileOut.write(finalSamplingHolder)
    with open(outputASCIIFile, 'w') as asciiFileOut:
        asciiFileOut.write(tileOutputHolder)
    with open(outputPopnLocFile, 'w') as popnFileOut:
        popnFileOut.write(coordHolder)
else:
    print("")
    print("Copy the following into a plain text file and use as a flag file for ms using the '-f' flag (e.g. ms nsam howmany -f <path to the plain text flag file>)")
    print("")
    print(finalSamplingHolder)

    # This prints the ascii representation of the grid for the ms call to the screen.
    print("")
    print("This is the ASCII representation of the landscape that is simulated using the above ms simulation configuration:")
    print("")
    print(tileOutputHolder)

    # Also print out the coordinates of the focal populations
    print("")
    print("The coordinates for the focal (sampled) populations are (listed for populations from left to right, top to bottom):")
    print("")
    print(coordHolder)
    print("")
        
