# first created 7/31/2021
# last updated 5/12/2023

# PURPOSE: Plot various stats about a player or entire PGNs.
# Try to detect distributional trends in a player's performance.

import glob
import os
import datahound
import plotter
import requests

# pgn files should be generated from api, for example see below
# if a given pgn does not have analysis, then analysis will be skipped
# the number _XXXX.pgn on a pgn does not necessarily refer to the number of games actually in the file

# https://lichess.org/api/games/user/erinyu?perfType=blitz&rated=true&max=1000&evals=true&clocks=true

# use naming convention player_variant_numgames.pgn or arena_numgames.pgn

# selects a pgn from your file directory and prepares the contents to be hounded
def selectPGN():
    while True:
        listoffiles = glob.glob(f'pgn/*.pgn') #add .bz2 to the end if analyzing a .bz2
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
    results = []

    while True:
        print("")
        print("Welgaia")
        print("-------")
        print('(1) Choose PGN file to analyze')
        print('(2) Download a PGN file from Lichess')
        print(f'(3) Hound data from {file.split(os.sep)[-1]}')
        print('(4) Plot what there is to plot')
        print(f'(5) Load save file of {file.split(os.sep)[-1]}')
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
                file = f'.{os.sep}pgn{os.sep}{suspect.replace("_","-")}_{variant}_{numgame}.pgn'
                focus = suspect
                numgames = int(numgame)
            elif i == '2':
                suspect = input("\nEnter arena ID: ")
                numgame = input("Enter number of games: ")
                specific = input("Any specific player? (Else skip this): ")
                print("\nAre you sure?")
                print("(1) Let's start downloading")
                print("(2) Forget everything I said")
                if input() == "1":
                    try:
                        if specific != "":
                            specific.replace("_","-")
                            specific = specific + "_"
                        url = f'https://lichess.org/api/tournament/{suspect}/games?evals=true&clocks=true'
                        r = requests.get(url, allow_redirects=True)
                        writefile = open(f'.{os.sep}pgn{os.sep}{specific}{suspect}_{numgame}.pgn', 'wb')
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

            results = datahound.hound(file, focus, numgames)

            tempsave = open(f"{file.split(os.sep)[-1][:-4]}_save222.txt", "w")
            for X in range(0,len(results)):
                tempsave.write(str(results[X]))
                tempsave.write("\n")
            tempsave.close()
            continue

        if i == '4':
            if results is None:
                print("Nothing to plot since nothing was hounded")
                continue

            # plotting magic here
            # 0 = empty
            # 1 = evaluations (player)
            # 2 = remaining time (player)
            # 3 = acpl (player)
            # 4 = move times (player)
            # 5 = mistake flag (player)
            # 6 = number of legal moves (all)
            # 7 = number of pieces left
            # 8 = mistakes per game
            # 9 = player rating (player)
            # 10 = opponent rating
            # 11 = game result (player)
            # 12 = ply
            # 13 = evaluation (player, %)
            # 14 = acpl (player, %)
            # args: yarray, xarray, minbucket, overflow, binwidth, xlabel, ylabel, boxyay, file
            plotter.frequency(results[14], 0, 100, 2, "loss", file)
            plotter.frequency(results[4], 0, 30, 1, "movetime", file)
            #plotter.frequency(results[2], 0, 180, 2, "remainingtime", file)
            #plotter.frequency(results[6], 0, 72, 1, "legalmoves", file)
            #plotter.frequency(results[7], 0, 78, 1, "boardmaterial", file)
            #plotter.frequency(results[6], 0, 72, 1, "legalmoves", file)
            #plotter.frequency(results[13], 0, 100, 2, "evaluation", file)

            plotter.compare(results[14], results[4], 0, 30, 1, "movetime", "loss", False, file)
            plotter.compare(results[14], results[13], 0, 100, 2, "evaluation", "loss", False, file)
            plotter.compare(results[4], results[13], 0, 100, 2, "evaluation", "movetime", False, file)
            plotter.compare(results[14], results[7], 0, 78, 1, "gamephase", "loss", False, file)
            plotter.compare(results[4], results[7], 0, 78, 1, "gamephase", "movetime", False, file)
            plotter.compare(results[14], results[6], 0, 72, 1, "legalmoves", "loss", False, file)
            plotter.compare(results[4], results[6], 0, 72, 1, "legalmoves", "movetime", False, file)
            plotter.compare(results[14], results[2], 0, 180, 2, "remainingtime", "loss", False, file)
            plotter.compare(results[4], results[2], 0, 180, 2, "remainingtime", "movetime", False, file)

            #plotter.compare(results[2], results[12], 20, 60, 1, "ply", "remainingtime", False, file)
            #plotter.compare(results[4], results[12], 20, 60, 1, "ply", "movetime", False, file)
            #plotter.compare(results[6], results[12], 20, 60, 1, "ply", "legalmoves", False, file)
            #plotter.compare(results[7], results[12], 20, 60, 1, "ply", "boardmaterial", False, file)
            #plotter.compare(results[13], results[12], 20, 60, 1, "ply", "evaluation", False, file)
            #plotter.compare(results[14], results[12], 20, 60, 1, "ply", "loss", False, file)



            continue

        if i == '5': # loading save files
            try:
                savefile = open(f"save/{file.split(os.sep)[-1][:-4]}_save.txt", "r")
            except:
                print("File not found?")
                continue
            results = [[] for _ in range(15)]  # 15 is arbitrary. increase if more space is needed
            temp = savefile.readline()
            for X in range(1, len(results)):
                temp = (savefile.readline())[1:-2].split(", ")
                for Y in range(0,len(temp)):
                    try:
                        results[X].append(float(temp[Y]))
                    except:
                        results[X].append(None)
                print(f"Recovered row {X} of {len(results)-1}...")
            print("Recovery done!")
            continue
        if i == '0':
            return

if __name__ == "__main__":
    mainloop()

# end of file
