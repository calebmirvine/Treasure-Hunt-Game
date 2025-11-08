class Player:

    def __init__(self, name: str) -> None:
        """
        Initialize a Player object with a name and score of 0.
        :param name: Player's name (must be a non-empty string)
        :raises ValueError: if name is not a string
        :raises ValueError: if name is empty or contains only whitespace
        """
        if type(name) != str: raise ValueError("name must be a string")
        if name.strip() == "": raise ValueError("name must not be empty")

        self.name = name
        self.score = 0
        self.get_score()

    def add_score(self, new_score: int) -> None:
        """
        Add points to the player's current score.
        :param new_score: Points to add (must be a non-negative integer)
        :return: None
        :raises ValueError: if new_score is not an int
        :raises ValueError: if new_score is negative
        """
        if type(new_score) != int: raise ValueError("score must be an int")
        if not new_score >= 0: raise ValueError("score must be >= to 0")
        self.score += new_score

    def get_score(self) -> int:
        """
        Get the player's current score.
        :return: Current score as an integer
        """
        return self.score

    def __str__(self) -> str:
        """
        Return a string representation of the player with their name and score.
        :return: String in format "Player {name} | Score: {score}"
        """
        return f"Player {self.name} |  Score: {self.score}"
