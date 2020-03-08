class QuickPuTTYEncryption:
    def __init__(self, key_one: int, key_two: str):
        self.ASCII_SIZE = 1114120
        self.key_one = key_one
        self.key_two = key_two

    def convert_base(self, num, to_base: int = 10, from_base: int = 10):
        if isinstance(num, str):
            n = int(num, from_base)
        else:
            n = int(num)
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if n < to_base:
            return alphabet[n]
        return self.convert_base(n // to_base, to_base) + alphabet[n % to_base]

    def encrypt(self, string):
        use_key_two = 0
        for i in range(len(self.key_two)):
            use_key_two = (use_key_two + ord(self.key_two[i]) * (self.ASCII_SIZE ** i)) % self.key_one

        result = 0
        for i in range(len(string)):
            result += (ord(string[i]) + self.key_one) * ((self.ASCII_SIZE + self.key_one + use_key_two) ** i)
        return self.convert_base(result, from_base=10, to_base=36)

    def decrypt(self, string):
        use_key_two = 0
        for i in range(len(self.key_two)):
            use_key_two = (use_key_two + ord(self.key_two[i]) * (self.ASCII_SIZE ** i)) % self.key_one

        string = int(self.convert_base(string, from_base=36, to_base=10))
        result = []
        while string > 0:
            string, letter = divmod(string, (self.ASCII_SIZE + self.key_one + use_key_two))
            result.append(chr(letter - self.key_one))
        return ''.join(result)


key_one = 42
key_two = "my_key"

encryption = QuickPuTTYEncryption(key_one, key_two)

string = "You can't read this string"

encrypted = encryption.encrypt(string)
print(encrypted)

decrypted = encryption.decrypt(encrypted)
print(decrypted)
