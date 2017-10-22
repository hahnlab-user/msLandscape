# *msLandscape*
A toolbox to streamline the creation of landscape-scale simulations using the coalescent simulator *ms*.
*msLandscape* comprises an R package and a toolbox of other scripts that work seamlessly together with the R package.

The main *msLandscape* webpage is <a href="https://hahnlab.github.io/msLandscape/">here</a>

To install the R package easily, make sure the devtools package is installed (using the command ```install.packages("devtools")``` in R if necessary). In R, then type ```devtools::install_github("hahnlab/msLandscape")```. The package should load automatically.

For a full walkthrough guide on how to use *msLandscape* to automatically generate landscape-scale *ms* flag files and the workflow
for editing and 'sculpting' these landscapes to meet the desired shape, sampling patterns, and migration patterns for the
landscape, including using them to run *ms*, see the linked tutorial <a href="https://hahnlab.github.io/msLandscape/msLandscape_plotSculpt_tutorial_062017.html">here</a>. 

For a guide to using the scripts in the *msLandscape* toolbox to help convert *ms* output data to formats that *smartPCA* (for running PCA), *un-PC*, *SpaceMix*, and *EEMS* can use as input, see the linked tutorial <a href="https://hahnlab.github.io/msLandscape/msLandscape_dataConversion_tutorial_102217.html">here</a>.

For a tutorial about how to use the msLandscape_layerPNGImages function in *msLandscape* to create layered composite images of multiple input images (e.g. *SpaceMix*, *EEMS*, or *un-PC* results from different scenarios) that allow direct comparisons between them, see the linked tutorial <a href="https://hahnlab.github.io/msLandscape/msLandscape_layerPNGImages_tutorial.html">here</a>.

The toolbox of other (non-R) scripts that are part of *msLandscape* are found in the ```msLandscape_toolboxScripts``` directory.
