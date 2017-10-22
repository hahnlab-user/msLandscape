#' msLandscape_convertToEEMSDiffs is a utility function to convert \emph{ms} output for use with \emph{EEMS}
#' 
#' This function is the second processing step required to convert raw \emph{ms} simulation output into the
#' pairwise genetic differences format required by \emph{EEMS}. The accompanying Python script 
#' ghostLands_msOutputConvertFor_SpaceMix_EEMS_for_msLandscape.py takes the raw \emph{ms} simulation results
#' and converts them to the intermediate '.4eemsdiffs' files. This msLandscape_convertToEEMSDiffs
#' function then converts those '4eemsdiffs' files to '.diffs' files for use with EEMS.
#' 
#' @param dirWith_4eemsdiffs_files The path to the directory containing the .4eemsdiffs files to convert to .diffs files for 
#' EEMS using pairwise genetic differences between each individual at each locus. NOTE - the Python msLandscape script to 
#' convert ms output into SpaceMix input and EEMS .4eemsdiffs files needs to be run before this script. 
#' @return None
#' @name msLandscape_convertToEEMSDiffs
#' @export


# This is working correctly as part of msLandscape pending further tests 031717. Works correctly
# with diploid tests with uneven sampling and extra -e flags in flag file (this script really sees none of that
# though - it's already taken care of.) 031717.

# This is a stand alone version of this converter, where it is run in a dir that contains multiple .4eemsdiffs
# intermediate files that have already been converted from the raw ms output, and here each input file is
# converted into the .diffs file needed for EEMS to run.

# There are no external arguments to this script, but need to make sure the path to the dir with the .4eemsdiffs
# files to convert, and the structure of the parser to recover the iteration number from the .4eemsdiffs file names
# are correct (both specified below).

# This calculates the matrix of average pairwise genetic distance for use in EEMS (calculated
# following the method used for EEMS) using the same dataset format as needed for
# running SpaceMix in R (which is convenient!). Use the
# /Users/geoffreyhouse/Documents/Python_programming/Landscape_Genetics/ghostLands_Python/ghostLands_msOutput_convertForSpaceMix.py
# script to convert the ms simulated output into the format needed here for easy R importing and manipulation.

msLandscape_convertToEEMSDiffs <- function(dirWith_4eemsdiffs_files){

    setwd(dirWith_4eemsdiffs_files)
    
    fileList <- list.files(dirWith_4eemsdiffs_files, pattern = ".4eemsdiffs")
    
    convertFileToEEMSDiffs <- function(inputFileName){
        
        # Remove the extension from each .4eemsdiffs file and replace with .diffs for the output file name for each file.
        fileNameSplit <- strsplit(inputFileName, ".4eemsdiffs")
        
        fileNameRoot <- fileNameSplit[[1]][1]
        
        outputFileName <- paste0(fileNameRoot, ".diffs")
        
        print(paste0("The output file name is ", outputFileName))
        
        
        # This R implementation of the calculation of the pairwise genetic distance is based almost
        # exclusively on Prasad Chalasani's answer to this post:
        # http://stackoverflow.com/questions/6269526/r-applying-a-function-to-all-row-pairs-of-a-matrix-without-for-loop
        
        # This is calculated using the equation used for the EEMS paper, which is used
        # in the bed2diffs_v1 script of the EEMS package following the equation given for
        # those calculations:
        
        # D[i,j] = (1/ #SNP loci) * summation of m (from 1 to # SNP loci) of (X[i,m] - X[j,m] ^2)
        # where X is the input genotype matrix with individuals on the rows and SNPs on the columns,
        # and D is the pairwise comparison entry for row i and row j of X, encoded as row i and col j of D.
        
        # This input files is csv and has already been converted from the raw ms output to SpaceMix format
        # using my Python conversion script in the previous step called by the shell script that
        # calls this R script.
        genotypeMatrix <- as.matrix(utils::read.table(file = inputFileName,sep=',',header=FALSE))
        
        # For testing only
        #genotypeMatrix <- genotypeMatrix[1:10,1:10]
        
        # Because this is all simulated data, there are no missing entries (which would otherwise be a big problem)
        # so the number of SNPs is just the number of colums here.
        nSNPs <- ncol(genotypeMatrix)
        
        nIndiv <- nrow(genotypeMatrix)
        
        # This is where all the magic happens! This avoids the nested for loops completely. Outer generates
        # all pairwise combinations of different individuals (the row numbers in the genotypeMatrix), and the
        # Vectorize wrapper is still a bit of a mystery to me, but is necessary to make this work right, and
        # it wraps the function call for mapply. The sum(x[i,] - x[j,])^2 call is already essentially vectorized -
        # it returns the sum of the element-wise (ie column-wise) squared differences between
        # values of x in row i and values of x in row j.
        
        
        pairGeneticDiffForEEMS <- outer(1:nIndiv,1:nIndiv, FUN = Vectorize(function(i,j) sum((genotypeMatrix[i,] - genotypeMatrix[j,])^2)/nSNPs))
        
        # The .diffs file output format is space separated distance entries with newlines between rows of the diff matrix entries
        utils::write.table(x = pairGeneticDiffForEEMS, file = outputFileName, append = FALSE, sep = " ",
                    eol = "\n", row.names=FALSE, col.names=FALSE)
        
    }
    # Invisible supresses extra printing from lapply.
    invisible(lapply(fileList, convertFileToEEMSDiffs))
}