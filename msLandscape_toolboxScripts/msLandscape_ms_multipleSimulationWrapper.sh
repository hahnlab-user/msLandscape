#!/bin/bash

# This is a very basic shell script wrapper for ms to run multiple independent invocations
# of ms using the same ms flag file, but with different random number seeds each time
# (the random seeds are provided by an internal call to Python). This is working correctly 021617.


# Enter the help menu if specified, otherwise run the script.
if [ "$1" == -h ] || [ "$1" == help ] || [ "$1" == "" ]
then
    echo ""
    echo "This is msLandscape_ms_multipleSimulationWrapper.sh"
    echo ""
    echo "Use this shell script to run multiple independent invocations of ms using the same ms flag file."
    echo ""
    echo "NOTE: This script uses Python to generate the random seeds for ms. The path to Python needs to be in the \$PATH variable."
    echo ""
    echo "Usage: bash msLandscape_ms_multipleSimulationWrapper.sh <nsam> <howmany> <msFlagFile> <numItersToRun> <outputFileStem>"
    echo ""
    echo "nsam is the number of chromosomes for ms to sample, just like in the ms documentation."
    echo "howmany is the number of independent loci to simulate, just like in the ms documentation."
    echo "msFlagFile is the path to the msFlagFile to use when running ms (the -f flag in ms)"
    echo "numItersToRun is the number of independent invocations of ms desired. Each invocation uses different random number seeds but the same msFlagFile."
    echo "outputFileStem is the desired output file name (without a file extension). The invocation (iteration) number and a '.msout' extension are appended."
    echo ""

else
nsam=$1
howmany=$2
msFlagFile=$3
numItersToRun=$4
outputFileStem=$5

# Loop through the number of independent simulations required.
for ((num=1;num<=numItersToRun;num++))
do

outputFileName="${outputFileStem}_Iter_${num}.msout"

echo "Output name is: $outputFileName"

# wrap in a bash function
function randomNum {

# redirect all commands until 'END' to Python
# (the '-' sets Python to read commands from standard input - in this case the redirection)
python - <<END
import random
print(random.randint(1000,1000000))
END
}

# run the randomNum function and assign the returned value to a variable
randNum1=$(randomNum)
randNum2=$(randomNum)
randNum3=$(randomNum)

#echo "${randNum1} ${randNum2} ${randNum3}"

# Build ms call
msCall="ms ${nsam} ${howmany} -seeds ${randNum1} ${randNum2} ${randNum3} -f ${msFlagFile}"

# Run ms call and redirect output to the file
$msCall > $outputFileName

done
fi
