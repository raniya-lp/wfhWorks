'''
520. Detect Capital

We define the usage of capitals in a word to be right when one of the following cases holds:

All letters in this word are capitals, like "USA".
All letters in this word are not capitals, like "leetcode".
Only the first letter in this word is capital, like "Google".
Given a string word, return true if the usage of capitals in it is right.
'''


class Solution(object):
    def detectCapitalUse(self, word):
        if word==word.upper():
            return True
        elif word==word.lower():
            return True
        else:
            if(word[0]==word[0].upper()):
                nw_word=word[1:]
                if(nw_word==nw_word.lower()):
                    return True
                else:
                    return False
