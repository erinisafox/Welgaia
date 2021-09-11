import matplotlib.pyplot as plt
import os
from math import sqrt
from math import exp
from math import factorial

# normal confidence intervals, 95%
# abc method courtesy of Constantine Evans at caltech, is preferred, but ran into memory issues
def normalci(array):
    if len(array) < 2:
        return 0
    mean = sum(array) / len(array)
    stdev = 0
    for X in array:
        stdev += (mean - X) ** 2
    return 1.96 * sqrt(stdev / (len(array) - 1)) / sqrt(len(array))

# saves plots into a folder, given the plot and the axis labels and file name
def savePlot(plt, xaxislabel, yaxislabel, file):
    newdir = f"plot/{file.split('_')[0].split(os.sep)[-1]}/{file.split(os.sep)[-1][:-4]}"
    if not os.path.exists(os.path.dirname(newdir)):
        os.makedirs(os.path.dirname(newdir))
    plt.savefig(f"{newdir}_{xaxislabel}_{yaxislabel}.png")

    print(f"Saved {newdir}_{xaxislabel}_{yaxislabel}.png")
    return

# plot anything comparing two factors
# acpl/movetime, acpl/timeleft, etc.
# groups cpls into buckets defidned by max bucket a and bin width b
# then takes an average of those cpls per bucket to calculate acpls
def compare(cpls, otherarray, a, b, c, xaxislabel, yaxislabel, file):
    plt.clf()

    # clear out any nonetypes
    cplstemp = []
    otherarraytemp = []
    for X in range(0, len(cpls)):
        if cpls[X] is not None and otherarray[X] is not None:
            cplstemp.append(cpls[X])
            otherarraytemp.append(otherarray[X])
    cpls = cplstemp
    otherarray = otherarraytemp

    minmt = a
    maxmt = b  # seconds for overflow bucket
    spacing = c  # seconds for bin width

    numbuckets = ((maxmt - minmt) // spacing + 1)
    acpls = [[] for _ in range(numbuckets)]
    cis = [0] * numbuckets
    for X in range(0, len(otherarray)):
        temp = (int(otherarray[X]) - minmt) // spacing
        if temp > numbuckets - 1:
            temp = numbuckets - 1
        if temp < 0:
            temp = 0
        acpls[temp].append(cpls[X])

    for X in range(0, len(cis)):
        # if there weren't any cpls in the bucket, assign arbitrary acpl
        if len(acpls[X]) == 0:
            acpls[X] = [-100]
        cis[X] = normalci(acpls[X])
        acpls[X] = sum(acpls[X]) / len(acpls[X])

    xaxis = range(minmt, maxmt + spacing, spacing)
    plt.scatter(xaxis, acpls)
    plt.errorbar(xaxis, acpls, yerr=cis, fmt="o")
    plt.ylim(bottom=0)
    plt.xlabel(xaxislabel)
    plt.ylabel(yaxislabel)
    plt.title(file.split(os.sep)[-1])

    return savePlot(plt, xaxislabel, yaxislabel, file)

# plot any single array with frequency on the y-axis
# cpl distribution, movetime distribution, etc.
def frequency(array, a, b, c, xaxislabel, file):
    plt.clf()

    # clear out any nonetypes
    array = [x for x in array if x is not None]

    freq = [0] * ((b - a) // c + 1)
    for X in array:
        temp = int((X - a) // c)
        if temp < 0:
            temp = 0
        if temp >= len(freq):
            temp = len(freq)-1
        freq[temp] += 1

    xaxis = range(a, b + c, c)
    plt.bar(xaxis, freq, width=c*0.75)
    plt.ylim(bottom=0)
    plt.xlabel(xaxislabel)
    plt.ylabel("frequency")
    plt.title(file.split(os.sep)[-1])

    return savePlot(plt, xaxislabel, "frequency", file)

# end of file
