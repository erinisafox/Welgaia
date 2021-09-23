import chess.pgn
import chess.variant
from tqdm import tqdm


# everywhere in the code uses evaluation from white's pov
# acpl calculations then need to be catered to whose turn it is to move
def calcCpl(weval, lasteval, turn):
    cpl = weval - lasteval
    if turn % 2 == 1:  # if black pov, fix the cpl calculation
        cpl *= -1
    if cpl < 0:
        cpl = 0
    return cpl

# less than 4 pieces = endgame
# less than 11 pieces = middlegame
# number of pieces on the board correlates roughly with game phase
# may as well have a more continuous game phase variable?
def calcPhase(fen):
    strippedfen = str(fen).lower()
    countpieces = 0
    for X in strippedfen:
        Y = X.lower()
        if Y == " ":
            break
        if Y == "b" or Y == "n" or Y == "r" or Y == "q":
            countpieces += 1

    return countpieces

# run through every game and scavenge clock and eval data, if it exists
def hound(file, focus, numgames):
    singleordouble = 2 # to check whether to skip half the moves in a game or not
    if focus == "":
        singleordouble = 1

    pgn = open(file)

    maxcpl = 1000  # upper bound for cpl. +/-10 is what lichess likes to do, but creates weird effects at extremes
    results = [ [] for _ in range(15) ] # 15 is arbitrary. increase if more space is needed

    # iterate through all the games
    for X in tqdm(range(0, numgames)):
        # try to process a game. catch it if something goes wrong (ex. foreign language or some weird bug)
        try:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            evallist = []  # temp list of evals
            timeleftlist = []  # temp list of clocks
            nummoveslist = []
            phaselist = []
            mistakespergame = 0

            # figure out the focus player's pov
            if game.headers["White"].replace("_","-").lower() in focus.lower():
                pov = True  # we got white
            else:
                pov = False  # we got black

            # figure out the increment
            timecontrol = game.headers["TimeControl"].split("+")
            basetc = int(timecontrol[0])
            inctc = int(timecontrol[1])

            # initialize variables for white and black increment (in case of berserk)
            inctccolor = [inctc, inctc]

            whitegameresult = game.headers["Result"]
            if whitegameresult == "1-0":
                whitegameresult = 1
            elif whitegameresult == "0-1":
                whitegameresult = 0
            elif whitegameresult == "1/2-1/2":
                whitegameresult = 0.5
            else:
                whitegameresult = None

            # get evals and clock times for both players
            # will only care about pov player later on
            board = game.board()
            board.reset()
            for node in game.mainline():
                weval = node.eval()
                timeleft = node.clock()
                board.push(node.move)

                if weval is not None:
                    weval = weval.white().score(mate_score=2000)
                    if weval < -maxcpl:
                        weval = -maxcpl
                    if weval > maxcpl:
                        weval = maxcpl

                phaselist.append(calcPhase(board.fen()))
                evallist.append(weval)
                timeleftlist.append(timeleft)
                nummoveslist.append(board.legal_moves.count())
        except:
            print(f"Skipped Game {X+1} because some nonsense happened. {game.headers['Site']}")
            continue
        # end

        # figure out where to start analyzing only pov player
        # move 1 is excluded
        if pov:
            start = 2
        else:
            start = 3

        # adjust increment in presence of berserk
        if len(timeleftlist) > 2:
            if timeleftlist[0] < basetc:
                inctccolor[0] = 0
            if timeleftlist[1] < basetc:
                inctccolor[1] = 0

        # calculation of acpl, move time, etc. uses evals, time remaining, etc.
        # change the step size to 2 if you care about a specific player

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
        for X in range(start, len(timeleftlist), singleordouble):
            if evallist[X-1] is not None and evallist[X] is not None:
                results[3].append(calcCpl(evallist[X - 1], evallist[X], X))
                if results[3][-1] > 100:
                    results[5].append(100)
                    mistakespergame += 1
                else:
                    results[5].append(0)
            else:
                results[3].append(None)
                results[5].append(None)
            if timeleftlist[X-2] is not None and timeleftlist[X] is not None:
                results[4].append(timeleftlist[X - 2] - timeleftlist[X] + inctccolor[X % 2])
                results[2].append(timeleftlist[X])
            else:
                results[4].append(None)
                results[2].append(None)
            if evallist[X] is not None:
                results[1].append((-1)**(X%2) * evallist[X])
            else:
                results[1].append(evallist[X])
            results[6].append(nummoveslist[X])
            results[7].append(phaselist[X])

            if X % 2 == 0: # white is making the move
                if whitegameresult is not None:
                    results[11].append(whitegameresult)
                else:
                    results[11].append(None)
                results[9].append(int(game.headers["WhiteElo"]))
                results[10].append(int(game.headers["BlackElo"])-int(game.headers["WhiteElo"]))
            else:
                if whitegameresult is not None:
                    if X%2 == 1:
                        results[11].append(1-whitegameresult)
                    else:
                        results[11].append(whitegameresult)
                else:
                    results[11].append(None)
                results[9].append(int(game.headers["BlackElo"]))
                results[10].append(int(game.headers["WhiteElo"])-int(game.headers["BlackElo"]))

        if len(evallist) > 1 and evallist[0] is not None:
            results[8].append(mistakespergame)
        else:
            results[8].append(None)

    return results

# end of file
