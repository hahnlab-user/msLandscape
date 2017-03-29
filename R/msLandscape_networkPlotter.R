#' Plot the landscape configuration (populations and their migration connections) in an \emph{ms} flag file.
#' 
#' This uses a network graph to automatically represent the landscape configuration specified in the input \emph{ms} flag file.
#' In this network graph, the nodes represent populations on the landscape and the edges represent 
#' pairwise migration connections between populations.  Node size is proportional to the number of individuals
#' sampled from each population, and edge width is proportional to the migration rate specified for each pair
#' of populations. Populations that only have one specified migration connection in the ms flag file (and therefore
#' uni-directional migration) are connected with a dashed line instead of a solid line.
#' The network plotting engine is from the igraph package. Importantly the network plot uses layout 'layout_with_kk';
#'  other layouts did not work well and this one works extremely well.
#' @param msFlagFileName is the name (with the path if the file is not in the working directory) of the ms flag file to plot.
#' @param addPopnLabels boolean (TRUE/FALSE); default TRUE. Whether population labels (numbers) should be added to each population (point)
#' on the network plot. This is useful when specifying the populations to edit (either to remove or to change the number
#' of individuals sampled per population), and is useful too for determining the orientation of the landscape when the
#' network plotter rotates or reflects it compared to what is expected.
#' @param savePlotToFile boolean (TRUE/FALSE); default FALSE. Chooses whether the plot is saved directly to a file (pdf), or 
#' printed to the screen instead. 
#' @param plotWidth define the width of the saved .pdf plot (in inches). Only used if savePlotToFile is TRUE.
#' @param plotHeight define the height of the saved .pdf plot (in inches). Only used if savePlotToFile is TRUE.
#' @param outputFileName specify the name (and path if necessary) of the output .pdf plot file. Only used if savePlotToFile is TRUE.
#' @return None
#' @name msLandscape_networkPlotter
#' @export

msLandscape_networkPlotter <- function(msFlagFileName, addPopnLabels = TRUE, savePlotToFile = FALSE, plotWidth = 8, plotHeight = 8, outputFileName = "msLandscape_NetworkPlot.pdf"){
    
    # This imports a data.frame with 1 row and 1 col for each white space delimited string. Using sep = "" instead of sep = " " (white space compared to space splitting) makes this much less fragile.
    # The colClasses "character" preserves the '0.0' entry after the -I flag population list
    # (setting all migration connections not specified in the -m flags to 0.0), otherwise
    # it is converted to 0 and is not uniquely parsable. This is the same parsing that 
    # the python flag file clean up script uses.
    msFlagFile <- read.table(msFlagFileName, sep = "", colClasses = "character")
    
    # parse the file name to determine whether this scenario is for haploid or diploid simulation. Returns TRUE/FALSE
    isDiploid <- grepl("diploid", msFlagFileName)
    #print(isDiploid)
    # parse the sampling done per population
    # Get the number of populations as the entry following the -I, and use that as an index
    iIndex <- which(msFlagFile == "-I")
    numPopns <- as.numeric(msFlagFile[iIndex + 1])
    startPos <- iIndex + 2
    
    # NEEDS TO BE FIXED FOR ROBUST PARSING - It is possible for the endPos to have multiple entries if e.g. -es ... 0.0 flag is used.  
    endPos <- which(msFlagFile == '0.0') - 1
    # R can't parse on the '0.0' following  
    #endPos <- iIndex + numPopns + 2 - 1
    popnVector <- msFlagFile[startPos:endPos]
    
    if(length(popnVector) != numPopns){
        warning("The number of populations specified after the -I flag does not match the number of populations in the population sampling list following the -I flag.")
    }
    
    # The migration part of the msFlagFile starts with '-m', so isolate that here into a matrix
    pairMigrIndexList <- which(msFlagFile == "-m")
    
    firstPairMigrIndex <- pairMigrIndexList[1]
    
    #rawPairMigrMatrix <- matrix(msFlagFile[firstPairMigrIndex:length(msFlagFile)],ncol = 4, byrow = TRUE)
    
    # Little messy; need to subtract 3 for the last connection (it is added back in the + 1)
    numPairMigr <- ((length(msFlagFile) - firstPairMigrIndex - 3) / 4) + 1
    
    generatePairMigrMatrix <- function (pairMigrNum) {
        
        startIndex <- pairMigrIndexList[pairMigrNum] + 1
        if(pairMigrNum < length(pairMigrIndexList)){
            endIndex <- pairMigrIndexList[pairMigrNum + 1] - 1
        } else{
            endIndex <- length(msFlagFile)
        }
        currPairMigr <- as.numeric(msFlagFile[startIndex:endIndex])
        return(currPairMigr)
    } 
    
    pairMigrMatrix <- sapply(seq(1,numPairMigr,1), generatePairMigrMatrix)
    
    pairMigrMatrix <- t(pairMigrMatrix)
    
    orderPairMigrMatrix <- function(pairMigr) {
        
        pop1 <- as.numeric(pairMigr[1])
        pop2 <- as.numeric(pairMigr[2])
        migr <- as.numeric(pairMigr[3])
        
        if(pop1 < pop2){
            holder <- c(pop1, pop2, migr)
        } else {
            holder <- c(pop2, pop1, migr)
        }
        return(holder)   
    }
    
    orderedPairMigrMatrix <- apply(pairMigrMatrix, 1, orderPairMigrMatrix)
    orderedPairMigrMatrix <- t(orderedPairMigrMatrix)
    orderedPairMigrDF <- data.frame(orderedPairMigrMatrix)
    names(orderedPairMigrDF) <- c("Popn1","Popn2","MigrRate")
    
    sortedOrderedPairMigrDF_1 <- dplyr::group_by(orderedPairMigrDF, Popn1)
    sortedOrderedPairMigrDF <- dplyr::group_by(sortedOrderedPairMigrDF_1, Popn2)
    
    # This is so ugly; have to merge the 2 cols into a combined string to count the occurences of that
    # string (migration pair) in the migration connections right now.
    sortedOrderedPairMigrPasted <- apply(sortedOrderedPairMigrDF, 1, function(x){return(paste(x[1],x[2],x[3]))})
    
    calcAggregateMigrConnections <- function(migrConnectString){
        # The number of times this migration connection appears in the ms file.
        numOccur <- sum(sortedOrderedPairMigrPasted == migrConnectString)
        
        migrConnectString <- paste(migrConnectString, numOccur)
        
    }
    
    aggregatedMigrConnections <- sapply(sortedOrderedPairMigrPasted, calcAggregateMigrConnections)
    # aggregatedMigrConnections <- t(aggregatedMigrConnections)
    
    aggregatedMigrConnections <- unique(aggregatedMigrConnections)
    
    #re-form a numeric vector from the string and add the numOccur    
    
    reformMatrix <- function(migrConnectString){
        
        splitString <- strsplit(migrConnectString, " ")
        outputVect <- as.numeric(c(splitString[[1]][1], splitString[[1]][2], splitString[[1]][3], splitString[[1]][4]))
    }
    
    reformedAggregatedMigrConnections <- sapply(aggregatedMigrConnections, reformMatrix)
    reformedAggregatedMigrConnections <- as.data.frame(t(reformedAggregatedMigrConnections))
    rownames(reformedAggregatedMigrConnections) <- seq(1,nrow(reformedAggregatedMigrConnections))
    
    # This is the edges file
    colnames(reformedAggregatedMigrConnections) <- c("popn1","popn2","migrationRate","numMigrConnections")
    
    msEdges <- reformedAggregatedMigrConnections
    
    # This pulls out the unique population numbers from the reformedAggregatedMigrConnections
    uniquePopnNumbers <- unique(c(reformedAggregatedMigrConnections$popn1, reformedAggregatedMigrConnections$popn2))
    
    sortedUniquePopnNumbers <- uniquePopnNumbers[order(uniquePopnNumbers)]
    
    # Need to transpose the popnVector here in the cbind
    # This is where to check and make sure the number of sorted unique popn numbers (from 
    # the -m flag portion of the flag file) matches the number of populations specified in the 
    # -I flag portion of the flag file. If it does not, then cannot continue with the script,
    # and need to run the Python clean up script first.
    
    if(length(sortedUniquePopnNumbers) != length(popnVector)){
        stop("The number of populations ")    
    }
    
    msVertices <- data.frame("popnNum" = sortedUniquePopnNumbers, 
                             "numIndivsSampled" = as.numeric(t(popnVector)), stringsAsFactors = FALSE)
    
    msNetwork <- igraph::graph_from_data_frame(d = msEdges, vertices = msVertices)
    
    # The layout with 'kk', as opposed to 'fr' is pretty excellent!!!
    # Will need to try to fix the rotation, but this has all the information
    # already parsed that it needs to change the node size in proportion to the num
    # indivs sampled per population, the width of the arrows to change with migration
    # rate, and to go dashed arrows if the pairwise connection is only
    # specified in one direction in the ms file.
    
    # set up the vertex size divisor to that the populations are plotted with sizes proportional to the number of individuals
    # (regardless of whether haploid or diploid simulation)
    
    rawDivisor <- 2
    
    if(isDiploid == TRUE){
        divisorToUse <- rawDivisor * 2
    } else{
        divisorToUse <- rawDivisor
    }
    
    # The ifelse in the edge.lty argument of the plot functions below sets the line style for unidirectional migration connections
    # to be dotted; the color for the unidirectional vs. the bidirectional migration connections is 
    # also specified below. 
    # This works correctly but gives warning about # items to replace are 
    # not multiple of replacement length, even though as far as I can tell, they are. I have suppressed warnings
    # from these 2 lines.
    # Unidirectional color
    suppressWarnings(igraph::E(msNetwork)$color[which(msEdges$numMigrConnections == 1)] <- "#e7298a")
    #Bidirectional color
    suppressWarnings(igraph::E(msNetwork)$color[which(msEdges$numMigrConnections == 2)] <- "gray70")
    
    
    if(isTRUE(addPopnLabels)){
        
        if(isTRUE(savePlotToFile)){
            pdf(outputFileName, width = plotWidth, height = plotHeight)
            
            plot(msNetwork, layout = igraph::layout_with_kk, vertex.size =(msVertices$numIndivsSampled)/divisorToUse, 
                edge.arrow.size = 0, edge.width = msEdges$migrationRate, vertex.color = ifelse(msVertices$numIndivsSampled == 0, rgb(1, 1, 1, 0), "chartreuse2"),
                vertex.shape = "circle", 
                edge.lty = 1)
                #edge.lty = ifelse(msEdges$numMigrConnections == 2, 1, 3))
            
            dev.off()
        } else{
            
            plot(msNetwork, layout = igraph::layout_with_kk, vertex.size =(msVertices$numIndivsSampled)/divisorToUse, 
                edge.arrow.size = 0, edge.width = msEdges$migrationRate, vertex.color = ifelse(msVertices$numIndivsSampled == 0, rgb(1, 1, 1, 0), "chartreuse2"),
                vertex.shape = "circle", 
                edge.lty = 1)
               
        # Add the number of individuals sampled per population
        #reformedAggregatedMigrConnections <- cbind(reformedAggregatedMigrConnections, popnVector)
        }
    } else{
        
        if(isTRUE(savePlotToFile)){
            pdf(outputFileName, width = plotWidth, height = plotHeight)
            
            plot(msNetwork, layout = igraph::layout_with_kk, vertex.size =(msVertices$numIndivsSampled)/divisorToUse, 
                 edge.arrow.size = 0, edge.width = msEdges$migrationRate, vertex.color = ifelse(msVertices$numIndivsSampled == 0, rgb(1, 1, 1, 0), "chartreuse2"),
                 vertex.shape = "circle", vertex.label = "", 
                 edge.lty = 1)
            
            dev.off()
        } else{
        
            # Use edge.width / 2 for figures (save as 8x8, and allows scaling down to 2 x 2 in Illustrator.)
            plot(msNetwork, layout = igraph::layout_with_kk, vertex.size =(msVertices$numIndivsSampled)/divisorToUse, 
                edge.arrow.size = 0, edge.width = msEdges$migrationRate, vertex.color = ifelse(msVertices$numIndivsSampled == 0, rgb(1, 1, 1, 0), "chartreuse2"),
                vertex.shape = "circle", vertex.label = "", 
                edge.lty = 1)
        }
    }
    
}
