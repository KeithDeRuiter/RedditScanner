'''
Created on Jan 22, 2014

@author: Keith
'''
import praw
import time
import datetime

def getMyKarmaBreakdown() :
    username = ''
    user = r.get_redditor(username)
    
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


def writeUsersAndSubmissionsToFile(usersBySubreddit, submissionsBySubreddit, userfile, submissionsfile) :
    userfile.seek(0)
    userfile.truncate()
    submissionsfile.seek(0)
    submissionsfile.truncate()
    
    for sub in usersBySubreddit:
        #print("r/" + sub)
        userfile.write("r/" + sub + "\n")
        for user in usersBySubreddit[sub]:
            #print("u/" + user)
            userfile.write("u/" + user + "\n")
    for sub in submissionsBySubreddit:
        #print("r/" + sub)
        submissionsfile.write("r/" + sub + "\n")
        for id in submissionsBySubreddit[sub]:
            #print("u/" + id)
            submissionsfile.write("id/" + id + "\n")        


def main():
    startTime = time.time()    
    print("Hello World")


    #read in the bot's login info
    try:
        botInfoFile = open('bot_info.txt', 'r')
        botInfoFile.seek(0, 0)
        
        line = botInfoFile.readline()
        botname = line.rstrip('\n')
        line = botInfoFile.readline()
        botpass = line.rstrip('\n')
                                 
    except FileNotFoundError:
        print("bot_info.txt not found! Abort Abort!  Code Red!  Abandon ship!")
        sys.exit(1)

    
    r = praw.Reddit(user_agent='ScannerBot alpha');
    r.login(botname, botpass);
    print('logged in');
    
    # CONFIGURABLE DATA PARAMETERS
    subredditsToCheck = []
    thingLimit = 1000
    commentExpandingLimit = 16
    commentExpandingThreshold = 10
    # ===
    
    #Open file of existing authors and already scanned submissions
    alreadyExaminedSubmissionIDs = {}  #needs to map sub name to set of already examined IDs
    allAuthorsBySubreddit = {} #needs ot map string(sub name) to a set(users)
 
    #read in the subreddits to scan from file
    try:
        targetSubredditsFile = open('target_subreddits.txt', 'r+')
        targetSubredditsFile.seek(0, 2)
        fileLength = targetSubredditsFile.tell()
        targetSubredditsFile.seek(0, 0)
        
        for i in range(0, fileLength):
            line = targetSubredditsFile.readline()
            currentSubreddit = line.rstrip('\n')
            subredditsToCheck.append(currentSubreddit);
                                 
    except FileNotFoundError:
        print("target_subreddits.txt not found!  Creating file...")
        targetSubredditsFile = open('target_subreddits.txt', 'a')
        subredditsToCheck = ["losangeles", "usc"]


    #setup subreddits to scan
    for s in subredditsToCheck:
        alreadyExaminedSubmissionIDs[s] = set()
        allAuthorsBySubreddit[s] = set()
    
    #Known Users
    try:
        knownUsersFile = open('known_users.txt', 'r+')
        knownUsersFile.seek(0, 2)
        fileLength = knownUsersFile.tell()
        knownUsersFile.seek(0, 0)
        
        currentSubreddit = ''
        for i in range(0, fileLength):
            line = knownUsersFile.readline()
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
        knownUsersFile = open('known_users.txt', 'a')
        
    #print("INITIAL AUTHOR DATA")
    #print(allAuthorsBySubreddit)
    #print("---")
        
    #Examined Submissions
    try:
        examinedSubmissionsFile = open('examined_submissions.txt', 'r+')
        examinedSubmissionsFile.seek(0, 2)
        fileLength = examinedSubmissionsFile.tell()
        examinedSubmissionsFile.seek(0, 0)
        
        currentSubreddit = ''
        for i in range(0, fileLength):
            line = examinedSubmissionsFile.readline()
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
        examinedSubmissionsFile = open('examined_submissions.txt', 'a')    
    #============ end data reading
    
    
    for subreddit in subredditsToCheck:
        print("Checking subreddit r/{0}".format(subreddit))
        
        #allSubmissions = r.get_subreddit(subreddit).get_top(limit=thingLimit)
        allSubmissions = r.get_subreddit(subreddit).get_hot(limit=thingLimit)
        allAuthors = set()
        numSubmissions = 0
        
        for submission in allSubmissions:
            #increment numSubmissions
            numSubmissions += 1
            
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
            submission.replace_more_comments(limit=commentExpandingLimit, threshold=commentExpandingThreshold)
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
        allAuthorsBySubreddit[subreddit] = set.union(allAuthors, allAuthorsBySubreddit[subreddit])
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
        
    #write to file
    #print("AUTHORS")
    #print(allAuthorsBySubreddit)
    #print("---")
    writeUsersAndSubmissionsToFile(allAuthorsBySubreddit, alreadyExaminedSubmissionIDs, knownUsersFile, examinedSubmissionsFile)
    

##########################

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
    main()
