# Fantasy Hockey Solver

Solving the optimal placement of players and rosters using Google's OR-Tools.

## Constraints

Based on the following input constraints, how should you place players to optimize your fantasy team? Goal is to maximize the point categories

* 3 LW/C/RW, 5 D, 1 Util (rookie), 3 on the Bench, and 1 IR
* Each player can only be in 1 position
* Each player can only hold the positions defined by their position category

By assigning each players possible positions as a boolean variable, the goal is to maximize the placement of players and their stats.

## Model

Based on the placed positions, the BoolVar will take on a 1 or a 0. By multiplying this by the players stats, we can maximize the sum of the categories.

To account for an abnormally skewed category (Hits), the data is normalized between 0 and 100, and cast to an Int.

Un-attainable positions for a player (a players possible positions is a C but the category is a LW) gets an IntVar between 0 and 0. This forces the value to be excluded (0*0=0).

## Usage

To access the Yahoo API, you must get the client ID and secret from the Yahoo Developer Network.

Then deploy to your platform, i chose Deta. Add requirments of the .detaenv to deta deploy

Update the appropriate environment variables in a .env file.  

Run `main.py` to run the program.
Results will print and be saved to Deta Drive.