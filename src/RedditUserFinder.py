'''
Created on Jan 22, 2014

@author: Keith
'''
import praw
import time
import datetime
import signal
import sys
from pprint import pprint


class RedditUserFinder:

    def __init__(self):
        # CONFIGURABLE DATA PARAMETERS
        self.subredditsToCheck = []
        self.gatherDataThingLimit = 5
        self.commentExpandingLimit = 5
        self.commentExpandingThreshold = 2
        # ===
        
        self.knownUsersFile = None
        self.examinedSubmissionsFile = None
        self.targetSubredditsFile = None
        self.botInfoFilename = 'bot_info.txt'
        self.botInfoFile = None
        self.userAgentString = 'ScannerBot beta'
        
        self.botname = ''
        self.botpass = ''

        self.r = praw.Reddit(user_agent=self.userAgentString);


    def getMyKarmaBreakdown(self) :
        username = ''
        user = self.r.get_redditor(username)
        
        thingLimit = 0;
        genSub = user.get_submitted(limit=thingLimit)
        genCom = user.get_comments(limit=thingLimit)
        
        karmaBySubreddit = {}
        
        for thing in genSub:
            subreddit = thing.subreddit.display_name
            karmaBySubreddit[subreddit] = (karmaBySubreddit.get(subreddit, 0) + thing.score)
        for thing in genCom:
            subreddit = thing.subreddit.display_name
            karmaBySubreddit[subreddit] = (karmaBySubreddit.get(subreddit, 0) + thing.score)

        print("Karma breakdown by subreddit for user: {0}".format(username))    
        for thing in karmaBySubreddit:
            print('{0} : {1}'.format(thing, karmaBySubreddit.get(thing)))


    def botLogin(self):
        #read in the bot's login info
        try:
            self.botInfoFile = open(self.botInfoFilename, 'r')
            self.botInfoFile.seek(0, 0)
            
            line = self.botInfoFile.readline()
            self.botname = line.rstrip('\n')
            line = self.botInfoFile.readline()
            self.botpass = line.rstrip('\n')
                                     
        except FileNotFoundError:
            print("Bot info file: " + self.botInfoFilename +  " not found! Abort Abort!  Code Red!  Abandon ship!")
            sys.exit(1)

        self.r.login(self.botname, self.botpass);
        print('logged in');



    def clearUsersAndSubmissionFiles(self):
        #clear
        self.knownUsersFile.seek(0)
        self.knownUsersFile.truncate()
        self.examinedSubmissionsFile.seek(0)
        self.examinedSubmissionsFile.truncate()
        

    #Writes out the users and submissions for a single subreddit
    def writeSingleUsersAndSubmissionsToFile(self, subreddit, users, submissions):
        subredditSpecificUserFile = open(str(subreddit + "_users.txt"), "w")
        subredditSpecificSubmissionsFile = open(str(subreddit + "_submissions.txt"), "w")

        #print("r/" + subreddit)
        subredditSpecificUserFile.write("r/" + subreddit + "\n")
        for user in users:
            #print("u/" + user)
            subredditSpecificUserFile.write("u/" + user + "\n")

        #print("r/" + subreddit)
        subredditSpecificSubmissionsFile.write("r/" + subreddit + "\n")
        for id in submissions:
            #print("id/" + id)
            subredditSpecificSubmissionsFile.write("id/" + id + "\n")        


    #Write's out all users and submissions to the master file
    def writeAllUsersAndSubmissionsToFile(self, usersBySubreddit, submissionsBySubreddit):
        self.clearUsersAndSubmissionFiles()
        
        for sub in usersBySubreddit:
            #print("r/" + sub)
            self.knownUsersFile.write("r/" + sub + "\n")
            for user in usersBySubreddit[sub]:
                #print("u/" + user)
                self.knownUsersFile.write("u/" + user + "\n")
        for sub in submissionsBySubreddit:
            #print("r/" + sub)
            self.examinedSubmissionsFile.write("r/" + sub + "\n")
            for id in submissionsBySubreddit[sub]:
                #print("id/" + id)
                self.examinedSubmissionsFile.write("id/" + id + "\n")        


    def gatherData(self):
        startTime = time.time()    
        print("Hello World")


        #read in the bot's login info
        self.botLogin()
        
        #Open file of existing authors and already scanned submissions
        alreadyExaminedSubmissionIDs = {}  #needs to map sub name to set of already examined IDs
        allAuthorsBySubreddit = {} #needs to map string(sub name) to a set(users)
     
        #read in the subreddits to scan from file
        print("Reading in subreddits to scan...")
        try:
            self.targetSubredditsFile = open('target_subreddits.txt', 'r+')
            self.targetSubredditsFile.seek(0, 2)
            fileLength = self.targetSubredditsFile.tell()
            self.targetSubredditsFile.seek(0, 0)
            
            print(fileLength)

            #for i in range(0, fileLength):
            for line in self.targetSubredditsFile:
                #line = self.targetSubredditsFile.readline()
                if not line.startswith('r/'):
                    print("Line not r/ formatted: " + line)
                    continue
                print("Adding {0} to scan list".format(line))
                currentSubreddit = line.rstrip('\n').split("/")[1]  #get just the nanem of the subreddit
                self.subredditsToCheck.append(currentSubreddit);
                                     
        except FileNotFoundError:
            print("target_subreddits.txt not found!  Creating file...")
            self.targetSubredditsFile = open('target_subreddits.txt', 'a')
            self.subredditsToCheck = ["losangeles", "usc"]


        #setup subreddits to scan
        for s in self.subredditsToCheck:
            alreadyExaminedSubmissionIDs[s] = set()
            allAuthorsBySubreddit[s] = set()
        
        #Known Users
        print("Reading in known users...")
        try:
            self.knownUsersFile = open('known_users.txt', 'r+')
            self.knownUsersFile.seek(0, 2)
            fileLength = self.knownUsersFile.tell()
            self.knownUsersFile.seek(0, 0)
            print("known_users.txt read at length " + str(fileLength))
            
            currentSubreddit = ''
            #for i in range(0, fileLength):
            for line in self.knownUsersFile:
                #line = self.knownUsersFile.readline()
                if(line.find('/') == -1):
                    break
                name = line.split('/')[1]   #name of sub or user
                if line.startswith('r'):
                    currentSubreddit = name.rstrip('\n')
                else:
                    if currentSubreddit not in allAuthorsBySubreddit:
                        allAuthorsBySubreddit[currentSubreddit] = set()  #adds the name to known names
                    allAuthorsBySubreddit[currentSubreddit].add(name.rstrip('\n'))
                    #print("read in previous username: " + name.rstrip('\n'))
                
        except FileNotFoundError:
            print("known_users.txt not found!  Creating file...")
            self.knownUsersFile = open('known_users.txt', 'a')
            
        #print("INITIAL AUTHOR DATA")
        #print(allAuthorsBySubreddit)
        #print("---")
        
        #Examined Submissions
        try:
            self.examinedSubmissionsFile = open('examined_submissions.txt', 'r+')
            self.examinedSubmissionsFile.seek(0, 2)
            fileLength = self.examinedSubmissionsFile.tell()
            self.examinedSubmissionsFile.seek(0, 0)
            print("examined_submissions.txt read at length " + str(fileLength))
            
            currentSubreddit = ''
            #for i in range(0, fileLength):
            for line in self.examinedSubmissionsFile:
                #line = self.examinedSubmissionsFile.readline()
                if(line.find('/') == -1):
                    break
                name = line.split('/')[1]   #name of sub or user
                if line.startswith('r'):
                    currentSubreddit = name.rstrip('\n')
                else:
                    if currentSubreddit not in alreadyExaminedSubmissionIDs:
                        alreadyExaminedSubmissionIDs[currentSubreddit] = set()
                    alreadyExaminedSubmissionIDs[currentSubreddit].add(name.rstrip('\n'))    #adds the id to known subs
                    
        except FileNotFoundError:
            print("examined_submissions.txt not found!  Creating file...")
            self.examinedSubmissionsFile = open('examined_submissions.txt', 'a')    
        #============ end data reading
        
        
        for subreddit in self.subredditsToCheck:
            print("Checking subreddit r/{0}".format(subreddit))
            
            #allSubmissions = self.r.get_subreddit(subreddit).get_top(limit=self.gatherDataThingLimit)
            allSubmissions = self.r.get_subreddit(subreddit).get_hot(limit=self.gatherDataThingLimit)
            allAuthors = set()
            numSubmissions = 0
            
            for submission in allSubmissions:
                #increment numSubmissions
                numSubmissions += 1

                pprint(vars(submission))

                #Get title
                title = submission.title
                try:
                    title.encode('ascii')
                except UnicodeError:
                    print("Title was not an ascii-encoded unicode string...")
                else:        
                    print("({1}) Scanning submission: {0}".format(title, numSubmissions))
                    
                #check if we already know this submission            
                if submission.id in alreadyExaminedSubmissionIDs[subreddit]:
                    #we've already seen this submission, move on
                    print("Submission already recorded, moving on...")
                    continue
                else:
                    alreadyExaminedSubmissionIDs[subreddit].add(submission.id)
                    
                #Get Author
                if not submission.author:
                    name = '[deleted]'
                else:
                    name = submission.author.name 
                if(name not in allAuthorsBySubreddit[subreddit] and name not in allAuthors):
                    allAuthors.add(submission.author.name)
                    print("Found new Redditor in r/{0}: {1}".format(subreddit, submission.author.name))
                
                #Scan Comments
                
                submission.replace_more_comments(limit=self.commentExpandingLimit, threshold=self.commentExpandingThreshold)
                print ('sdfghjkllkhgfd')

                flatComments = praw.helpers.flatten_tree(submission.comments)
                for c in flatComments:
                    if not isinstance(c, praw.objects.Comment):
                        continue
                    if not c.author:
                        name = '[deleted]'
                    else:
                        if not hasattr(c.author, 'name'):
                            continue
                        else:
                            name = c.author.name 
                    
                    
                    if(name not in allAuthorsBySubreddit[subreddit] and name not in allAuthors):
                        allAuthors.add(name)
                        print("Found new Redditor in r/{0}: {1}".format(subreddit, name))

                
                
            print("Received {0} Submissions".format(numSubmissions))
            allAuthorsBySubreddit[subreddit] = set.union(allAuthors, allAuthorsBySubreddit[subreddit]) #Add in all the newly found authors to the set of authors in this subreddit
            #end check for this subreddit

        #get intersection results
        intersectionOfAuthorship = set.intersection(*allAuthorsBySubreddit.values())    

        #Check runtime and print results
        endTime = time.time()
        elapsedTime = endTime - startTime
        elapsedTimeStr = "{0} minutes and {1} seconds".format((int)(elapsedTime/60), (int)(elapsedTime % 60))
        numFound = len(intersectionOfAuthorship)
        countingGrammarString = 's'
        if numFound == 1:
            countingGrammarString = ''
        print("Mission Accomplished: {0} user{1} found in {2}".format(numFound, countingGrammarString, elapsedTimeStr))
        
        # print all authors
        for author in intersectionOfAuthorship:
            print(author)

        #Write to file
        self.writeAllUsersAndSubmissionsToFile(allAuthorsBySubreddit, alreadyExaminedSubmissionIDs)
        

##########################

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    #writeUsersAndSubmissionsToFile(allAuthorsBySebreddit, alreadyExaminedSubmissionIDs, self.knownUsersFile, self.examinedSubmissionsFile)
    sys.exit(0)


if __name__ == '__main__':
    '''
    #add support for commandline arguemnts TODO
    parser = argparse.ArgumentParser(description='Scan Subreddits for common users', version='%(prog)s 1.0')
    parser.add_argument('program', type=str, help='Program name')
    parser.add_argument('infiles', nargs='+', type=str, help='Input text files')
    parser.add_argument('--out', type=str, default='temp.txt', help='name of output file')
    args = parser.parse_args()
    '''
    #main(**vars(args))    
    signal.signal(signal.SIGINT, signal_handler)

    userFinder = RedditUserFinder()
    userFinder.gatherData()

