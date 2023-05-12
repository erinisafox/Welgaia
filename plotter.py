from math import *
import matplotlib.pyplot as plt
import os

def avg(array):
    temp = [x for x in array if x is not None]
    return sum(temp)/len(temp)

# normal confidence intervals, 95%
# should not be taken seriously, since nothing in chess is normally distributed
def normalci(array):
    if len(array) < 2:
        return [0,0]
    mean = sum(array) / len(array)
    stdev = 0
    for X in array:
        stdev += (mean - X) ** 2
    daci = 1.96 * sqrt(stdev / (len(array) - 1)) / sqrt(len(array))
    return [daci, daci]

# saves plots into a folder, given the plot and the axis labels and file name
def savePlot(plt, xaxislabel, yaxislabel, file):
    newdir = f"plot/{file.split('_')[0].split(os.sep)[-1]}/{file.split(os.sep)[-1][:-4]}"
    if not os.path.exists(os.path.dirname(newdir)):
        os.makedirs(os.path.dirname(newdir))
    plt.savefig(f"{newdir}_{xaxislabel}_{yaxislabel}.png")

    return

def storePlotData(ystuff, ysizes, ystdevs, file):
    storefile = open(f"{file.split(os.sep)[-1][:-4]}_plotdata_storedata.txt", "a")
    storefile.write(f"{ystuff}\n{ysizes}\n{ystdevs}\n\n")
    return

# plot anything comparing two factors
# acpl/movetime, acpl/timeleft, etc.
# groups cpls into buckets defined by max bucket a and bin width b
def compare(yarray, xarray, a, b, c, xaxislabel, yaxislabel, boxyay, file):
    plt.clf()

    # clear out any nonetypes
    yarraytemp = []
    xarraytemp = []
    for X in range(0, len(yarray)):
        if yarray[X] is not None and xarray[X] is not None:
            yarraytemp.append(yarray[X])
            xarraytemp.append(xarray[X])
    yarray = yarraytemp
    xarray = xarraytemp

    # various initializations
    minmt = a
    maxmt = b  # seconds for overflow bucket
    spacing = c  # seconds for bin width
    numbuckets = ((maxmt - minmt) // spacing + 1)
    yfreq = [[] for _ in range(numbuckets)]
    cis = [0] * numbuckets
    xaxis = range(minmt, maxmt + spacing, spacing)

    # sorts y datapoints for boxplots
    for X in range(0, len(xarray)):
        temp = (int(xarray[X]) - minmt) // spacing
        if temp > numbuckets - 1:
            temp = numbuckets - 1
        if temp < 0:
            temp = 0
        yfreq[temp].append(yarray[X])

    # calculates mean and 95% CI for errorbar overlay onto boxplot
    yavg = yfreq[:]
    samplesizes = yavg[:]
    lowercis = []
    uppercis = []
    for X in range(0, len(cis)):
        # if there weren't any cpls in the bucket, assign arbitrary acpl
        if len(yavg[X]) == 0:
            yavg[X] = [-100]
        cis = normalci(yavg[X])
        lowercis.append(cis[0])
        uppercis.append(cis[1])
        samplesizes[X] = len(yavg[X])
        yavg[X] = sum(yavg[X]) / len(yavg[X])

    # plotting business
    if boxyay: # sometimes you don't want a boxplot because variables are discrete and synthetic
        plt.boxplot(yfreq,showfliers=False,vert=True,positions=xaxis,widths=spacing/2)
    plt.errorbar(xaxis, yavg, yerr=[lowercis, uppercis], fmt="^", color="green", elinewidth=3, markersize=7)
    storePlotData(str(yavg)[1:-1], str(samplesizes)[1:-1], str(lowercis)[1:-1], file)
    print(str(yavg)[1:-1])

    samplesizebox = ""
    for X in range(0,len(xaxis)):
        samplesizebox = samplesizebox + f"{xaxis[X]} % {samplesizes[X]}\n"

    plt.ylim(bottom=0)

    plt.xlabel(xaxislabel)
    plt.ylabel(yaxislabel)
    #plt.title(file.split(os.sep)[-1])
    plt.gcf().text(0.9, 0.1, samplesizebox, fontsize=8)
    #plt.show()

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

    print(f"{str(freq)[1:-1]}")
    storePlotData(str(freq)[1:-1], str(freq)[1:-1], str(freq)[1:-1], file)
    xaxis = range(a, b + c, c)
    plt.bar(xaxis, freq, width=c*0.75)
    plt.ylim(bottom=0)
    plt.xlabel(xaxislabel)
    plt.ylabel("frequency")
    #plt.title(file.split(os.sep)[-1])

    return savePlot(plt, xaxislabel, "frequency", file)

# end of file
