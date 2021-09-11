# ye-eun yu
# 7/31/2021

# PURPOSE: Plot various stats about a player.
# Try to detect distributional trends in a player's performance.

import glob
import os
import datahound
import plotter
import requests

# file should be generated from api, for example see below
# beware, every game should have analysis. this does not guarantee that.
# pgn may have 1000 games, but if only 10 games have analysis, it won't tell you

# https://lichess.org/api/games/user/erinyu?perfType=blitz&rated=true&max=1000&evals=true&clocks=true

# use naming convention player_variant_numgames.pgn or arena_numgames.pgn

# selects a pgn from your file directory and prepares the contents to be hounded
def selectPGN():
    while True:
        listoffiles = glob.glob(f'.{os.sep}pgn{os.sep}*.pgn')
        print('')
        for i, f in enumerate(listoffiles, 1):
            print(f'({i}) {f}')
        print('(^) Select a file, of the format player_variant_numgames or arena_numgames')
        print('(0) Cancel')

        i = input()

        if i == '0':
            return "nothing, yet", "", 0
        try:
            f = str(listoffiles[int(i) - 1])
            fsplit = f.split("_")
            focus = fsplit[0].split(os.sep)[-1]
            numgames = int(fsplit[-1].split(".")[0])
            if len(fsplit) == 2:
                focus = ""
            return f, focus, numgames
        except (IndexError, ValueError):
            pass

# main loop to make the program interactive and fun to use
def mainloop():
    file = "nothing, yet"
    focus = ""
    numgames = 0
    evalslist = []
    remainingtimelist = []
    acpllist = []
    movetimelist = []
    isamistakelist = []
    legalmoveslist = []
    phaseslist = []
    mistakespergamelist = []

    while True:
        print("")
        print("Welgaia")
        print("-------")
        print('(1) Choose PGN file to analyze')
        print('(2) Download a PGN file from Lichess')
        print(f'(3) Hound data from {file.split(os.sep)[-1]}')
        print('(4) Plot what there is to plot')
        print('(0) Rage quit')

        i = input()

        if i == '1':
            file, focus, numgames = selectPGN()
        if i == '2':
            print("(1) Analyze a player")
            print("(2) Analyze a tournament")
            print("(3) I changed my mind")
            i = input()
            if i == '1':
                suspect = input("\nEnter name of player: ")
                variant = input("Enter name of variant: ")
                numgame = input("Enter number of games: ")
                print("\nAre you sure?")
                print("(1) Let's start downloading")
                print("(2) Forget everything I said")
                if input() == "1":
                    try:
                        url = f'https://lichess.org/api/games/user/{suspect}?perfType={variant}&rated=true&max={numgame}&evals=true&clocks=true'
                        r = requests.get(url, allow_redirects=True)
                        writefile = open(f'.{os.sep}pgn{os.sep}{suspect.replace("_","-")}_{variant}_{numgame}.pgn', 'wb')
                        writefile.write(r.content)
                    except:
                        print("Download failed?")
                        continue
                print("\nDownload successful!\n")
            elif i == '2':
                suspect = input("\nEnter arena ID: ")
                numgame = input("Enter number of games: ")
                print("\nAre you sure?")
                print("(1) Let's start downloading")
                print("(2) Forget everything I said")
                if input() == "1":
                    try:
                        url = f'https://lichess.org/api/tournament/{suspect}/games?evals=true&clocks=true'
                        r = requests.get(url, allow_redirects=True)
                        writefile = open(f'.{os.sep}pgn{os.sep}{suspect}_{numgame}.pgn', 'wb')
                        writefile.write(r.content)
                    except:
                        print("Download failed?")
                        continue
                print("\nDownload successful!\n")
            else:
                continue
        if i == '3':
            if file == "nothing, yet":
                print("No file selected, yet")
                continue
            evalslist, remainingtimelist, acpllist, movetimelist, isamistakelist, legalmoveslist, phaseslist, mistakespergamelist = datahound.hound(file, focus, numgames)
        if i == '4':
            if evalslist == []:
                print("Nothing to plot since nothing was hounded")
                continue
            # plotting magic here
            # args: yarray, xarray, minbucket, overflow, binwidth, xlabel, ylabel, file
            plotter.frequency(acpllist, 0, 200, 10, "acpl", file)
            plotter.frequency(movetimelist, 0, 20, 1, "movetime", file)
            plotter.frequency(mistakespergamelist, 0, 20, 1, "mistakespergame", file)
            plotter.compare(acpllist, movetimelist, 0, 10, 2, "movetime", "acpl", file)
            plotter.compare(acpllist, evalslist, -900, 900, 150, "evaluation", "acpl", file)
            plotter.compare(movetimelist, evalslist, -900, 900, 150, "evaluation", "movetime", file)
            plotter.compare(acpllist, phaseslist, 1, 14, 1, "gamephase", "acpl", file)
            plotter.compare(movetimelist, phaseslist, 1, 14, 1, "gamephase", "movetime", file)
            plotter.compare(remainingtimelist, phaseslist, 1, 14, 1, "gamephase", "remainingtime", file)
            plotter.compare(isamistakelist, movetimelist, 0, 10, 1, "movetime", "percentmistakes", file)
            plotter.compare(isamistakelist, evalslist, -900, 900, 150, "evaluation", "percentmistakes", file)
        if i == '0':
            return

if __name__ == "__main__":
    mainloop()

# end of file
