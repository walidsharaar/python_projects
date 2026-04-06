import random

class PasswordGenerator:
    """Handles the algorithmic generation of credentials."""
    def __init__(self):
        self.letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 
                        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        self.numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

    def generate(self, l_min=8, l_max=10, s_min=2, s_max=4, n_min=2, n_max=4):
        """Generates a randomized password string based on complexity parameters."""
        nr_letters = random.randint(l_min, l_max)
        nr_symbols = random.randint(s_min, s_max)
        nr_numbers = random.randint(n_min, n_max)

        password_list = []
        password_list += [random.choice(self.letters) for _ in range(nr_letters)]
        password_list += [random.choice(self.symbols) for _ in range(nr_symbols)]
        password_list += [random.choice(self.numbers) for _ in range(nr_numbers)]

        random.shuffle(password_list)
        return "".join(password_list)