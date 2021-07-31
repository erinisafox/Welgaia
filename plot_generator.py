# ye-eun yu
# 7/19/2021

# PURPOSE: Plot various ACPL-related stats about a player.
# Try to detect distributional trends in a player's performance.

import chess.pgn
import os.path
import matplotlib.pyplot as plt
from tqdm import tqdm
from math import sqrt


# everywhere in the code uses evaluation from white's pov
# acpl calculations then need to be catered to whose turn it is to move
def calcCpl(weval, lasteval, turn):
    cpl = weval - lasteval
    if turn % 2 == 1:  # if black pov, fix the cpl calculation
        cpl *= -1
    if cpl < 0:
        cpl = 0
    return cpl


def calcPhase(fen):
    strippedfen = str(fen).lower()
    countpieces = 0
    for X in strippedfen:
        Y = X.lower()
        if Y == " ":
            break
        if Y == "b" or Y == "n" or Y == "r" or Y == "q":
            countpieces += 1

    #less than 4 pieces = endgame
    #less than 11 pieces = middlegame
    #number of pieces on the board correlates roughly with game phase
    #may as well have a more continuous game phase variable?
    return countpieces

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


# plot anything to do with acpl
# acpl/movetime, acpl/timeleft, etc.
# groups cpls into buckets defidned by max bucket a and bin width b
# then takes an average of those cpls per bucket to calculate acpls
def acplstuff(cpls, otherarray, a, b, c, xaxislabel, yaxislabel, file):
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
    # plt.ylim(0,yrangemax)
    plt.xlabel(xaxislabel)
    plt.ylabel(yaxislabel)
    plt.title(file)
    plt.show()

    return True


# file should be generated from api, for example:
# beware, every game should have analysis. this does not guarantee that.
# pgn may have 1000 games, but if only 10 games have analysis, it won't tell you

# https://lichess.org/api/games/user/erinyu?perfType=blitz&rated=true&max=1000&evals=true&clocks=true


## INPUT ##
file = "jul21bta"
focus = ""  # don't add a player name if its just a broad PGN and you don't care about specific players
# also see line 140
numgames = 4057  # number of games, purely for tqdm aesthetics reasons. make arbitrarily large if unsure.
## INPUT ##

singleordouble = 2 #to check whether to skip half the moves in a game or not
if focus == "":
    singleordouble = 1

pgn = open(file)
game = chess.pgn.read_game(pgn)

maxcpl = 2000  # upper bound for cpl. +/-10 is what lichess likes to do, but creates weird effects at extremes.

acpllist = []
movetimelist = []
remainingtimelist = []
evalslist = []
legalmoveslist = []
phaseslist = []
isamistakelist = []

# iterate through all the games
for X in tqdm(range(0, numgames)):
    # if you typed in numgames incorrectly, kill it before it throws an error
    game = chess.pgn.read_game(pgn)
    if game is None:
        break

    evallist = []  # temp list of evals
    timeleftlist = []  # temp list of clocks
    nummoveslist = []
    phaselist = []

    # figure out the focus player's pov
    if game.headers["White"].lower() in focus.lower():
        pov = True  # we got white
    else:
        pov = False  # we got black

    # figure out the increment
    timecontrol = game.headers["TimeControl"].split("+")
    basetc = int(timecontrol[0])
    inctc = int(timecontrol[1])
    if basetc != 180 or inctc != 0:
        pass
    # get evals and clock times for both players
    # will only care about pov player later on

    board = game.board()
    board.reset()
    for node in game.mainline():
        weval = node.eval()
        board.push(node.move)
        if weval is None:
            continue
        weval = weval.white().score(mate_score=2000)
        if weval < -maxcpl:
            weval = -maxcpl
        if weval > maxcpl:
            weval = maxcpl

        timeleft = node.clock()
        phaselist.append(calcPhase(board.fen()))
        evallist.append(weval)
        timeleftlist.append(timeleft)
        nummoveslist.append(board.legal_moves.count())
    # end

    # figure out where to start analyzing only pov player
    # move 1 is excluded
    if pov:
        start = 2
    else:
        start = 3

    # calculation of acpl, move time, etc. uses evals, time remaining, etc.
    # change the step size to 2 if you care about a specific player
    for X in range(start, len(timeleftlist), singleordouble):
        acpllist.append(calcCpl(evallist[X - 1], evallist[X], X))
        movetimelist.append(timeleftlist[X - 2] - timeleftlist[X] + inctc)
        remainingtimelist.append(timeleftlist[X])
        evalslist.append(evallist[X])
        legalmoveslist.append(nummoveslist[X])
        phaseslist.append(phaselist[X])
        if acpllist[-1] > 100:
            isamistakelist.append(100)
        else:
            isamistakelist.append(0)
# end

# disclaimers
print("")
print("Important note: beware of using CIs founded on low sample size.")
print("Good sample size per bar is 500 moves.")
print("This code does not show sample size per bar.")

# plotting magic here
# args: yarray, xarray, minbucket, overflow, binwidth, xlabel, ylabel, file
acplstuff(acpllist, remainingtimelist, 0, 180, 6, "Remaining Time (sec)", "ACPL", file)
acplstuff(acpllist, movetimelist, 0, 10, 1, "Move Time (sec)", "ACPL", file)
acplstuff(acpllist, evalslist, -900, 900, 150, "Evaluation", "ACPL", file)
acplstuff(movetimelist, evalslist, -900, 900, 150, "Evaluation", "Move Time (sec)", file)
acplstuff(acpllist, legalmoveslist, 1, 30, 1, "Number of Legal Moves", "ACPL", file)
acplstuff(movetimelist, legalmoveslist, 1, 40, 1, "Number of Legal Moves", "Move Time (sec)", file)
acplstuff(remainingtimelist, legalmoveslist, 1, 40, 1, "Number of Legal Moves", "Remaining Time (sec)", file)
acplstuff(evalslist, legalmoveslist, 1, 40, 1, "Number of Legal Moves", "Evaluation", file)
acplstuff(acpllist, phaseslist, 1, 14, 1, "Game Phase", "ACPL", file)
acplstuff(movetimelist, remainingtimelist, 0, 180, 6, "Remaining Time (sec)", "Move Time (sec)", file)
acplstuff(remainingtimelist, phaseslist, 1, 14, 1, "Game Phase", "Remaining Time (sec)", file)
acplstuff(legalmoveslist, phaseslist, 1, 14, 1, "Game Phase", "Number of Legal Moves", file)
acplstuff(isamistakelist, legalmoveslist, 1, 40, 1, "Number of Legal Moves", "Percentage Mistakes", file)
acplstuff(isamistakelist, movetimelist, 0, 10, 1, "Move Time (sec)", "Percentage Mistakes", file)

# end of file
