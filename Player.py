class Player:


    def __init__(self, name: str) -> None:
        """
        Initializer for creating a new instance of the class.

        This method sets the initial values for the attributes `name` and `score`,
        and calls the `add_score` method to process the provided score.

        :param name: Name of an individual
        :type name: str
        :param score: Initial score of the individual
        :type score: int
        """

        if type(name) != str:
            raise ValueError("name must be a string")
        if name.strip() == "":
            raise ValueError("name must not be empty")

        self.name = name
        self.score = 0
        self.get_score()



    def add_score(self, new_score: int) -> None:
        """
        Adds a new score to the current score if the provided score is positive.

        :param new_score: The new score to be added to the existing score
        :type new_score: int
        :return: None
        """
        if type(new_score) != int:
            raise ValueError("score must be an int")
        if not new_score  >= 0:
            raise ValueError("score must be >= to 0")
        self.score += new_score




    def get_score(self) -> int:
        """
        Gets the value of the score attribute.

        This method retrieves and returns the current value of the `score` attribute.

        :return: The current value of the `score` attribute.
        :rtype: int
        """
        return self.score

    def __str__(self) -> str:
        return f"Player {self.name} |  Score: {self.score}"

