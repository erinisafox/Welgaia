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
    singleordouble = 2 #to check whether to skip half the moves in a game or not
    if focus == "":
        singleordouble = 1

    pgn = open(file)

    maxcpl = 1000  # upper bound for cpl. +/-10 is what lichess likes to do, but creates weird effects at extremes.

    acpllist = []
    movetimelist = []
    remainingtimelist = []
    evalslist = []
    legalmoveslist = []
    phaseslist = []
    isamistakelist = []
    mistakespergamelist = []

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
        for X in range(start, len(timeleftlist), singleordouble):
            if evallist[X-1] is not None and evallist[X] is not None:
                acpllist.append(calcCpl(evallist[X - 1], evallist[X], X))
                if acpllist[-1] > 100:
                    isamistakelist.append(100)
                    mistakespergame += 1
                else:
                    isamistakelist.append(0)
            else:
                acpllist.append(None)
                isamistakelist.append(None)
            if timeleftlist[X-2] is not None and timeleftlist[X] is not None:
                movetimelist.append(timeleftlist[X - 2] - timeleftlist[X] + inctccolor[X % 2])
                remainingtimelist.append(timeleftlist[X])
            else:
                movetimelist.append(None)
                remainingtimelist.append(None)
            evalslist.append(evallist[X])
            legalmoveslist.append(nummoveslist[X])
            phaseslist.append(phaselist[X])
        if len(evallist) > 1 and evallist[0] is not None:
            mistakespergamelist.append(mistakespergame)
        else:
            mistakespergamelist.append(None)

    return evalslist, remainingtimelist, acpllist, movetimelist, isamistakelist, legalmoveslist, phaseslist, mistakespergamelist

# end of file
