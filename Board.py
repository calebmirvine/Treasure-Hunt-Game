import random


class Board:
    def __init__(self, n: int, t: str):
        """
        initialize the board, validating n and t raising ValueErrors if invalid

        intialize the board in a 2d list comprehension. for _ in range. Creating our square

        :param n: Our board size. n*n in square tiles. Must be > 0
        :param t: Each treasure label must be between 1 and t, inclusive.
        """
        if n <= 0:
            raise ValueError("Invalid board dimensions")
        elif int(t) <= 0 or int(t) > n * n:
            raise ValueError("Invalid treasure input")
        self.n = n
        self.t = t
        self.board = [['-' for _ in range(n)] for _ in range(self.n)]
        self.place_treasure()

    def place_treasure(self):
        """
        Called when the board is __init___
        Will place the t label (if allowed) in the n*n space given.
        T may wrap around the board, but cannot overlay any other t labels

        :return: void
        """

        treasurecount = int(self.t)

        # random direction the treasure will be placed
        directions = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}

        while treasurecount > 0:
            placed = False

            # Avoid infinite loop by counting till 100 to determine if there is any valid placements
            attempts = 0
            max_attempts = 100

            # Keep running till placement is found or we reach max attempts
            while not placed and attempts < max_attempts:
                row = random.randint(0, self.n - 1)
                col = random.randint(0, self.n - 1)
                direction = random.choice(list(directions.values()))

                # Placeholder row and col
                temp_row, temp_col = row, col

                # Temp list that tracks all positions to be filled
                positions = []

                for _ in range(treasurecount):
                    # """
                    # Avoid going out of bounds by wrapping around
                    # e.g., going left from column 0 wraps to the last column
                    # example: if temp_row = -1 and n = 5, then temp_row becomes 4
                    #
                    # n is the count of rows/columns
                    # """
                    if temp_row < 0:
                        temp_row = self.n - 1
                    elif temp_row >= self.n:
                        temp_row = 0

                    if temp_col < 0:
                        temp_col = self.n - 1
                    elif temp_col >= self.n:
                        temp_col = 0

                    # If board position is already occupied, break
                    # Avoiding collisions
                    if self.board[temp_row][temp_col] != '-':
                        # Clear positions list and break
                        break

                    # else, add position to list
                    positions.append((temp_row, temp_col))
                    # Move to the next position in the chosen direction
                    temp_row += direction[0]
                    temp_col += direction[1]

                # If we collected all positions equal to label, place the treasure
                if len(positions) == treasurecount:
                    # for each position in the list, set the board position to the treasurecount
                    for pos_row, pos_col in positions:
                        self.board[pos_row][pos_col] = str(treasurecount)
                        # Take us out of while loop
                    placed = True

                # Else Attempt count ++
                attempts += 1

            # If we exit the loop without placing, print a warning, but still continue with the rest
            if not placed:
                print(f"Warning: Could not place treasure of size {treasurecount}")

            # Decrement treasurecount and proceed with next treasure t label
            treasurecount -= 1

    def pick(self, row: int, col: int) -> str:
        """
        :param row: Chosen row int value
        :param col: Chosen col int value
        :return: Applicable value of treasure (if treasure not blank).
        Value equivalent to treasure label
        """
        if not (0 <= row < self.n and 0 <= col < self.n):
            return '-'
        value = self.board[row][col]
        self.board[row][col] = '-'
        return value

    def __str__(self):
        """
        :return: Spaced out tiles joined with a newline for proper board appearance
        """
        return '\n'.join([' '.join(row) for row in self.board])
