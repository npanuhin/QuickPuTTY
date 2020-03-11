class QuickPuTTYEncryption:
    def __init__(self, key_one: int, key_two: str):
        self.ASCII_SIZE = 1114120
        self.key_one = key_one
        self.alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.key_two = 0
        for i in range(len(key_two)):
            self.key_two = (self.key_two + ord(key_two[i]) * (self.ASCII_SIZE ** i)) % self.key_one

    def convert_to_36(self, num: int) -> str:
        '''Converts number to base 36'''
        return self.alphabet[num] if num < 36 else self.convert_to_36(num // 36) + self.alphabet[num % 36]

    def encrypt(self, string: str) -> str:
        '''Encrypts string'''
        res = sum([(ord(string[i]) + self.key_one) * ((self.ASCII_SIZE + self.key_one + self.key_two) ** i) for i in range(len(string))])
        return self.convert_to_36(res)

    def decrypt(self, string: str) -> str:
        '''Decrypts string'''
        string = int(string, 36)
        result = []
        while string > 0:
            string, letter = divmod(string, (self.ASCII_SIZE + self.key_one + self.key_two))
            result.append(chr(letter - self.key_one))
        return "".join(result)


# key_one = 42
# key_two = "my_key"

# encryption = QuickPuTTYEncryption(key_one, key_two)

# string = "You can't read this string"

# encrypted = encryption.encrypt(string)
# print(encrypted)

# decrypted = encryption.decrypt(encrypted)
# print(decrypted)
