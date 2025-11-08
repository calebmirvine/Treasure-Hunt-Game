import random


class Board:

    def __init__(self, n: int = 10, t: str = '4') -> None:
        """
        Initialize the board, validating n and t, raising ValueErrors if invalid.
        Creates a board as a 2D list with all tiles initially set to '_' (underscore).
        Default (no args) is a 10 x 10 board with 4 treasures.
        :param n: Board size - creates an n x n square grid of tiles. Must be >= 2
        :param t: Number of treasure types (as string). Creates treasure chains from t down to 1.
                  Each treasure type has a value equal to its number.
                  For example, if t='4', creates treasures labeled 4, 3, 2, and 1.
        :raises ValueError: if n is not an int, n < 2, t is not a digit, t <= 0, or t > n
        :return: None
        """
        if type(n) != int: raise ValueError("n must be an int")
        if n < 2: raise ValueError("n must not be less than 2")
        if not t.isdigit() or int(t) <= 0: raise ValueError("t must be digit greater 0")
        if int(t) <= 0 or int(t) > n: raise ValueError("Treasure t length cant be greater than n board length")

        self.n = n
        self.t = int(t)
        self.board = [['_' for _ in range(n)] for _ in range(self.n)]
        self.place_treasure()

    def place_treasure(self) -> None:
        """
        Places treasure chains on the board when the board is initialized.
        For each treasure type from self.t down to 1:
        Randomly selects a starting position and direction (up/down/left/right)
        Places a chain of tiles with length equal to the treasure value
        Each tile in the chain is labeled with the treasure value (I.e a 4-treasure (t) is 4 tiles labeled '4')
        Wraparound board edges
        Ensures no overlap with existing treasures by retrying if collision detected
        :return: None
        """
        t_count = int(self.t)

        directions = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}

        while t_count > 0:
            placed = False
            while not placed:
                row = random.randint(0, self.n - 1)
                col = random.randint(0, self.n - 1)
                direction = random.choice(list(directions.values()))

                temp_row, temp_col = row, col

                positions = []
                for _ in range(t_count):
                    temp_row = temp_row % self.n
                    temp_col = temp_col % self.n

                    if self.board[temp_row][temp_col] != '_': break
                    positions.append((temp_row, temp_col))
                    temp_row += direction[0]
                    temp_col += direction[1]

                if len(positions) == t_count:
                    for pos_row, pos_col in positions:
                        self.board[pos_row][pos_col] = str(t_count)
                    placed = True
                    t_count -= 1

    def pick(self, row: int, col: int) -> int:
        """
        Picks a tile from the board at the specified position and returns its value.
        The tile is then replaced with ' ' showings its been picked.
        If the tile contains a treasure digit, returns that treasure value.
        If the tile is empty ('_'), returns 0 points.

        :param row: Row index (0 to n-1) of the tile to pick
        :param col: Column index (0 to n-1) of the tile to pick
        :return: Int value of the treasure at that position: 0 if empty.
        :raises ValueError: if row or col is not an int
        :raises ValueError: if row or col is out of bounds (< 0 or >= n)
        """
        if type(row) != int or type(col) != int: raise ValueError("Row and Column must be digits")
        if row < 0 or row >= self.n or col < 0 or col >= self.n: raise ValueError(
            "Row and Column must be between 0 and n-1")

        value = self.board[row][col]
        self.board[row][col] = ' '
        if value == '_' or value == ' ':
            return 0
        return int(value)

    def __str__(self) -> str:
        """
        Returns a string representation of the board for display.
        Each row is space-separated, rows are newline-separated.
        :return: String representation of the board with tiles separated by spaces and rows by newlines
        """
        return '\n'.join([' '.join(row) for row in self.board])

    def mask_board(self) -> str:
        """
        Returns a simplified string representation for client transmission.
        Shows only picked tiles (space) vs unpicked tiles (underscore), hiding treasure values.
        This prevents clients from seeing where treasures are located before picking.
        Each tile is followed by a space (including the last tile in each row).

        :return: String with ' ' for picked tiles, '_' for unpicked tiles, each followed by a space
        """
        result = []
        for row in self.board:
            row_str = ''
            for tile in row:
                if tile == ' ':
                    row_str += '  '
                else:
                    row_str += '_ '
            result.append(row_str)
        return '\n'.join(result)
