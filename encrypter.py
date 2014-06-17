
import string

def encrypt_letter(letter):

    lowercase_alphabet = string.ascii_lowercase
    uppercase_alphabet = string.ascii_uppercase
    index_lowercase = lowercase_alphabet.find(letter)
    index_uppercase = uppercase_alphabet.find(letter)

    if (index_lowercase == -1):
        if (index_uppercase == -1): #om det inte finns i ngt av alfabeten
            return letter
        else: #om det finns i STORA alfabetet
            new_index = index_uppercase + 13
            if new_index > 25:
                new_index = new_index - 26
            return uppercase_alphabet[new_index]
    else:    #om det finns i lilla alfabetet
        new_index = index_lowercase + 13
        if new_index > 25:
            new_index = new_index - 26
        return lowercase_alphabet[new_index]

#symbols and letters not in the (english) alphabet will not be encrypted
def encrypt_text(s):
    if s:
        encrypted_string = ''
        for c in s:
            encrypted_string = encrypted_string + encrypt_letter(c)
        return encrypted_string