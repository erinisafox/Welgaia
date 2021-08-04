# Welgaia
Looking at distributions of chess player behavior

Welgaia, The Holy City (神聖都市ヴィルガイア Shinsei Toshi Virugaia?) the Holy City, is a city populated entirely by angels and serves as the main base of Cruxis in Tales of Symphonia. The only way to enter the city is through the Tower of Salvation. It is filled with high technology and computers that serve as archives. (Source: Aselia Wiki).

How to use:
1. Download a PGN that has all the required headers and evals and clock times in their moves. Usually this means downloading games from the Lichess API, for example https://lichess.org/api/games/user/erinyu?perfType=blitz&rated=true&max=1000&evals=true&clocks=true. Not every game needs to have evals or clock times attached to its moves; those games will just be skipped.
2. Rename the file according to the convention player_variant_numberofgames.pgn (for analyzing only a single player's moves) or event_numberofgames.pgn (to analyze all moves from all games). Save to the pgn folder.
3. Run main.py. Select (1) to choose the PGN from the pgn folder. Select (2) to process the games that have evals and clock times. Select (3) to generate plots, which are saved in the plot folder. Select (0) to exit the program.

How to install:
I have no idea.

Requirements:
- python-chess
- tqdm
- matplotlib
- numpy and other packages (eventually)
