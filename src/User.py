'''
Created on Jan 23, 2014

@author: Keith
'''

class UserData(object):
    '''
    classdocs
    '''


    def __init__(self, username):
        self.subredditsSubmittedTo = {}
        self.subredditsCommentedIn = {}
        self.name = username;
        
    def __repr__(self):
        return "UserData:{0}".format(self.name)
    def __eq__(self, other):
        if isinstance(other, UserData):
            return (self.name == other.name)
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other))
    def __hash__(self):
        return hash(self.__repr__())