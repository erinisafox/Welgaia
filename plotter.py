import matplotlib.pyplot as plt
from math import sqrt

# 95% ci assuming gaussian, which is a bad assumption
# should use bca intervals, but implementation is not presently worth the time
def normalci(array):
    if len(array) < 2:
        return 0
    mean = sum(array) / len(array)
    stdev = 0
    for X in array:
        stdev += (mean - X) ** 2
    return 1.96 * sqrt(stdev / (len(array) - 1)) / sqrt(len(array))


# plot anything comparing two factors
# acpl/movetime, acpl/timeleft, etc.
# groups cpls into buckets defidned by max bucket a and bin width b
# then takes an average of those cpls per bucket to calculate acpls
def compare(cpls, otherarray, a, b, c, xaxislabel, yaxislabel, file):
    minmt = a
    maxmt = b  # seconds for overflow bucket
    spacing = c  # seconds for bin width

    numbuckets = ((maxmt - minmt) // spacing + 1)
    acpls = [[] for _ in range(numbuckets)]
    ssize = [0] * numbuckets
    cis = [0] * numbuckets
    for X in range(0, len(otherarray)):
        temp = (int(otherarray[X]) - minmt) // spacing
        if temp > numbuckets - 1:
            temp = numbuckets - 1
        if temp < 0:
            temp = 0
        acpls[temp].append(cpls[X])
        ssize[temp] += 1

    for X in range(0, len(cis)):
        cis[X] = normalci(acpls[X])
        # if there weren't any cpls in the bucket, assign arbitrary acpl
        if len(acpls[X]) == 0:
            acpls[X] = -100
            continue
        acpls[X] = sum(acpls[X]) / len(acpls[X])

    xaxis = range(minmt, maxmt + spacing, spacing)
    plt.scatter(xaxis, acpls)
    plt.errorbar(xaxis, acpls, yerr=cis, fmt="o")
    plt.ylim(bottom=0)
    plt.xlabel(xaxislabel)
    plt.ylabel(yaxislabel)
    plt.title(file.split("/")[-1])
    plt.show()

    return

# end of file
