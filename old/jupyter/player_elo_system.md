# Player ELO system



Iterate through series of games, from oldest to newest.
Name a game $G$. From game $G$, there will be players, $P_1, P_2 ...$.
If there is no ELO for a certain player, then we initialise based on this standard
1. If more than half of his team members' elo is undefined, we define his elo based on his market value of that time. More specifically, we find out where he locates based on a normal distribution of market value of players of that time.
2. If more than half of his team members' elo is defined, we define his elo to be an average of his team member's elo. (Or, if the player is young, less than 20 yo or sth, we init his elo a bit lower than team's avg but put $K$ value bigger)
3. Change player's elo same as formula?
4. 