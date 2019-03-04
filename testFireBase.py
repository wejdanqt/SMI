import pyrebase

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

#db.child("names").push({'name':'noura'})
#db.child("names").child('name').update({'name':'noura'})

#users = db.child('names').remove()
#print(users.val())

countries = {'Iraq':2,'Yemen':5 ,'Iran': 7 ,'turkey': 5  }
suspiciousTransaction = {'amount':8000, 'Type':'CashIN'}
blackList = ['حجاج العجمي','عبدالملك الحوثي']





db.child('Rule1').child('highRiskCountries').set(countries)
db.child('Rule2').child('exceedingAvgTransaction').set(8)
#db.child('Rule3').child('suspiciousTransaction').set(suspiciousTransaction)
#db.child('Rule4').child('blackList').set(blackList)

