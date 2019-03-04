import pyrebase

#Firebase cinnection
config = {
    "apiKey": "AIzaSyBdvcfSBiaMQjb0q9g04emiCFYksGMvJfo",
    "authDomain": "saudi-money-investigator.firebaseapp.com",
    "databaseURL": "https://saudi-money-investigator.firebaseio.com",
    "projectId": "saudi-money-investigator",
    "storageBucket": "saudi-money-investigator.appspot.com",
    "messagingSenderId": "1098052350164"
  }

firebase = pyrebase.initialize_app(config)

db = firebase.database()

'''file_string = ""
with f as open("filename.txt"):
  file_string = f.read().lower()

user_input = input().lower()
if file_string.find('IF') >= 0:
  print("Fruit")
else:
  print("Not fruit")'''

# Open the file with read only permit
f = open('bussinseRules.txt')
# use readline() to read the first line
line = f.readline()
# use the read line to read further.
# If the file is not empty keep reading one line
# at a time, till the file is empty
while line:
    # in python 2+
    # print line
    # in python 3 print is a builtin function, so
    print(line)
    # use realine() to read next line
    line = f.readline()
f.close()