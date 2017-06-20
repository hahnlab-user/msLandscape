#' Layer .png images in the current directory on top of each other using transparency to retain features of each.
#' 
#' This takes as input the path to a directory that contains the .png files to layer, the desired output name stem
#' for the layered composite image, and the desired alpha (transparency) value for the final layered composite image.
#' 
#' The layered composite image is created by averaging each of the three color channels (r,g,b) separately for each pixel
#' across all of the images to be layered. This has the effect of making each image to be layered equally transparent in the final
#' layered composite image. The amount of transparency in each image is therefore proportional to the number of images to be layered.
#' 
#' For the layering to work correctly, the .png files to layer must all have the same dimensions, otherwise the function will exit with an error message
#' and not create the layered composite image. 
#' 
#' Although this can layer any number of .png images, the output is clearer when fewer images are used.
#' 
#' This function has a basic screen based on file name endings that attempts to prevent any previously layered composite images in the user-entered 
#' input directory from being used when creating any future layered composite images in the same directory. If desired, this screen can be circumvented
#' my manually removing the 'layered' suffix to the layered composite image's file name.
#'  
#' @param inputDirectory string The path to the directory that contains the .png files to use for the composite layered image.
#' @param outputFileStem string The desired name of the output layered composite image, but without the file extension. The string 
#' '_layered.png' will be automatically appended to the outputFileStem before saving the layered composite, giving it a .png file extension.
#' @param alpha numeric Controls the transparency of the final layered composite image. Setting to 0 makes it fully transparent (output will dissappear). 
#' Setting it to 1 makes it fully opaque (note - because the images are layered using the average color, which can make all of the colors 
#' much lighter in the layered composite than in the source images, when alpha is 1 the layered composite will still have the appearance of transparency)
#' @return None
#' @name msLandscape_layerPNGImages
#' @export


# This layers pngs on top of each other (for all png files without a 'layered.png' end) using
# a user entered alpha value to make the relative transparency of the different layers. It then averages
# r,g, and b separately for all of the input images to generate the final "flattened" image overlay. This
# means that even with an alpha value of 1, there will still be transparency (unless all layers have 
# the same colors in the same locations) because the alpha only applies to the final transparency of the 
# averaged color image. 

# This is working correctly, but the input files need to be exactly the same dimensions, otherwise this 
# will give bizarre-looking output. This now includes a check for that, and will not run if the input
# .png files do not all have the same dimensions.

# Check whether the png and abind packages are installed (they are suggested but not required for msLandscape)

if(sum(c("abind", "png") %in% installed.packages()[,1]) == 2){
    library(png)
    library(abind)  
} else{
    if("abind" %in% installed.packages()[,1] == FALSE){
        print("Need to install the package 'abind' for msLandscape_layerPNGImages to work.")
    }
    
    if("png" %in% installed.packages()[,1] == FALSE){
        print("Need to install the package 'png' for msLandscape_layerPNGImages to work.")
    }
    
    stop("Need to install package 'abind', 'png', or both for msLandscape_layerPNGImages to work. Please install them and try again.")
}

msLandscape_layerPNGImages <- function(inputDirectory, outputFileStem = "msLandscape_layeredPNGImages", alpha = 1){
    
    if(file.exists(inputDirectory)){
        setwd(inputDirectory)
    } else{
        stop("Error. the specified inputDirectory does not exist. Re-check the directory name and try again.")
    }
    
    # Get list of .png files 
    pngFileList <- list.files(pattern = "\\.png$")
    
    importImages <- function(pngFileName){
        
        pngFileNameLength <- nchar(pngFileName)
        
        # This tries to be smart about avoiding layering previous layering output (with the layered.png end of file name)
        if(substr(pngFileName, pngFileNameLength - 10, pngFileNameLength) == "layered.png"){
            print(paste("Skipping file:", pngFileName, "because it appears to be output from a previous layering."))
            return(NULL)
        } else{
            inputImage <- png::readPNG(pngFileName)
            
            inputHeight <- nrow(inputImage)
            inputWidth <- ncol(inputImage)
            
            alphaMatrix <- matrix(data = alpha, nrow = inputHeight, ncol = inputWidth)
            
            print(paste("Layering file:", pngFileName))
            
            inputImage <- abind::abind(inputImage, alphaMatrix, along = 3)
        }
    }
    
    importedImages <- lapply(X = pngFileList, FUN = importImages)
    
    # If a file was already layered and therefore skipped, it still keeps a NULL entry in the 
    # returned list. This makes a boolean vector of those NULL entries, and then they are 
    # removed with indexing below.
    successfulImportedFiles <- unlist(lapply(importedImages,FUN = function(x){!is.null(x)}))
    
    screenedSuccessfulImportedFiles <- importedImages[successfulImportedFiles]
    
    numSuccessfulImportedFiles <- sum(successfulImportedFiles)
    
    # Make a matrix of the dimensions of each imported image (where each image is a row, the first col is the 
    # image height, and the second col is the image width)
    importedFileDims <- matrix(unlist(lapply(importedImages[successfulImportedFiles],FUN = function(x){dim(x)})),ncol = 3, byrow = TRUE)
    
    # Screen to make sure all of the imported images have the same dimensions (which should be the column
    # averages)
    if(sum(mean(importedFileDims[,1]) == importedFileDims[,1]) == numSuccessfulImportedFiles &
       sum(mean(importedFileDims[,2]) == importedFileDims[,2]) == numSuccessfulImportedFiles){
        
        imageHeight <- mean(importedFileDims[,1])
        imageWidth <- mean(importedFileDims[,2])
        
    } else{
        
        stop("The imported .png files do not all have the same dimensions. Exiting. Ensure all .png files in the 
         directory have the same dimensions (height and width) and try again.")
    }
    
    
    # Create a 4-D array of the 3-D image matrices for each of the imported images
    allImagesArray <- array(unlist(screenedSuccessfulImportedFiles), c(imageHeight,imageWidth,4,numSuccessfulImportedFiles))
    
    # This is a 3-D array of the averaged image across the 3 colors and alpha.
    layeredImage <- rowMeans(allImagesArray, dims = 3)
    
    png::writePNG(image = layeredImage, target = paste0(outputFileStem,"_layered.png"))
}