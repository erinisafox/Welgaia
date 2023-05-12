import chess.pgn
import chess.variant
import bz2
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


# erin's model from a few regressions
# lichess uses -0.004, and regan uses 0.9837
# this hybrid model fits lichess data better than either model alone
# it does not matter what model is used, apart from aesthetics
def calcWinrate(eval):
    a = 0.9837
    b = 1
    c = -0.004
    exp = 2.71828

    return a / (1 + b * exp ** (c * eval))


def calcWinrateChange(weval, lasteval, turn):
    dwin = weval - lasteval
    if turn % 2 == 1:  # if black pov, fix the cpl calculation
        dwin *= -1
    if dwin < 0:
        dwin = 0
    return dwin


# material count on the board correlates roughly with game phase
# may as well have a more continuous game phase variable?
def calcPhase(fen):
    strippedfen = str(fen).lower()
    countpieces = 0
    for X in strippedfen:
        Y = X.lower()
        if Y == " ":
            break
        if Y == "r":
            countpieces += 5
        if Y == "n":
            countpieces += 3
        if Y == "b":
            countpieces += 3
        if Y == "q":
            countpieces += 9
        if Y == "p":
            countpieces += 1

    return countpieces


# run through every game and scavenge clock and eval data, if it exists
def hound(file, focus, numgames):
    singleordouble = 2  # to check whether to skip half the moves in a game or not
    if focus == "":
        singleordouble = 1
    pov = None
    # random initializations
    results = [[] for _ in range(15)]  # 15 is arbitrary. increase if more space is needed
    with open(file, "rt") as pgn:
        # iterate through all the games
        for X in tqdm(range(0, numgames)):
            maxcpl = 1000  # upper bound for cpl. +/-10 is what lichess likes to do, but creates weird effects at extremes
            wrl = []
            evallist = []  # temp list of evals
            timeleftlist = []  # temp list of clocks
            nummoveslist = []
            phaselist = []

            # try to process a game. catch it if something goes wrong (ex. foreign language or some weird bug)
            try:
                # load up the next game
                game = chess.pgn.read_game(pgn)

                if game is None:
                    break

                # figure out the focus player's pov
                if singleordouble == 2:
                    if game.headers["White"].replace("_", "-").lower() in focus.lower():
                        pov = False  # we got white
                    elif game.headers["Black"].replace("_", "-").lower() in focus.lower():
                        pov = True  # we got black
                    else:
                        continue  # player is not found in here, move onto the next game
                else:
                    pov = True
                # figure out the increment
                timecontrol = game.headers["TimeControl"].split("+")
                basetc = int(timecontrol[0])
                inctc = int(timecontrol[1])

                # initialize variables for white and black increment (in case of berserk)
                inctccolor = [inctc, inctc]

                # get evals and clock times for both players
                # will only care about pov player later on
                startingfen = None
                try:
                    startingfen = game.headers["FEN"]
                except:
                    pass
                board = game.board()
                if startingfen is not None:
                    chess.Board(chess960=True)
                else:
                    board = game.board()
                    board.reset()
                for node in game.mainline():
                    weval = node.eval()
                    timeleft = node.clock()
                    if weval is not None:
                        weval = weval.white().score(mate_score=2000)
                        if weval < -maxcpl:
                            weval = -maxcpl
                        if weval > maxcpl:
                            weval = maxcpl

                    phaselist.append(calcPhase(board.fen()))
                    evallist.append(weval)
                    if weval is not None:
                        wrl.append(calcWinrate(weval) * 100)
                    else:
                        wrl.append(None)
                    nummoveslist.append(board.legal_moves.count())
                    timeleftlist.append(timeleft)
                    if nummoveslist[-1] == 0:
                        print(board.fen())

                    board.push(node.move)
            except Exception as e:
                try:
                    print(e)
                    print(f"Skipped Game {X + 1} because some nonsense happened. {game.headers['Site']}")
                    continue
                except:
                    print(f"Skipped a game that didn't have a header. {file}")
                    continue
            # end

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
            # 12 = half move ply (game)
            # 13 = evaluation (player, %)
            # 14 = acpl (player, %)

            # we want to analyze players, which means we can only look at moves where it is their turn
            # this means look at positions where the opponent has last moved

            # figure out where to start analyzing only pov player
            # first 10 moves are excluded
            if pov:
                start = 20
            else:
                start = 21
            for X in range(start, len(timeleftlist) - 1, singleordouble):
                if X > 61:
                    break
                results[12].append(X)
                if wrl[X] is not None:
                    if X % 2 == 1:
                        results[13].append(wrl[X])
                    else:
                        results[13].append(100 - wrl[X])
                else:
                    results[13].append(None)
                if wrl[X] is not None and wrl[X + 1] is not None:
                    results[14].append(calcWinrateChange(wrl[X], wrl[X + 1], X + 1))
                else:
                    results[14].append(None)
                if timeleftlist[X - 1] is not None and timeleftlist[X + 1] is not None:
                    results[4].append(int(timeleftlist[X - 1] - timeleftlist[X + 1] + inctccolor[(X + 1) % 2]))
                    results[2].append(int(timeleftlist[X - 1]))
                else:
                    results[4].append(None)
                    results[2].append(None)

                results[6].append(int(nummoveslist[X]))
                results[7].append(int(phaselist[X]))

    return results

# end of file
