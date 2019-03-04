from flask import Flask, redirect, render_template, request, session, abort, url_for, flash, redirect, session
from flaskext.mysql import MySQL
from forms import RegistrationForm, LoginForm, forgotPassForm, bankProfileForm, clientForm, oldCommentForm, newCommentForm, dbSetupForm , manageBankDataForm , SearchForm , ViewProfileForm , ViewCasesForm
from DBconnection import connection2, BankConnection , firebaseConnection
from passwordRecovery import passwordRecovery
from datetime import datetime
import pyrebase



app = Flask(__name__)
app.config['SECRET_KEY'] = 'af6695d867da3c7d125a99f5c17ea79a'
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'SMIhmwn19*'
app.config['MYSQL_DATABASE_DB'] = 'SMI_DB'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

#Firebase connection

firebase = firebaseConnection()
#....................



@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        # Check id user exisit in the database
        cur, db = connection2()
        '''query = "SELECT * FROM AMLOfficer WHERE userName = '" + form.username.data + "' AND password = '" + form.password.data + "' "
        cur.execute(query)
        data1 = cur.fetchone()
        if data1 is None:
            flash('Invalid username or password please try again', 'danger')
            return render_template('login.html', form=form)
        else:
            query = "SELECT email FROM AMLOfficer WHERE userName = '" + form.username.data + "'"
            cur.execute(query)
            useremail = cur.fetchone()
            session["username"] = form.username.data
            session["email"] = useremail
            flash(f'Welcome back {form.username.data}', 'success')
            return redirect(url_for('bankP'))
        db.commit()
        cur.close()
        db.close()'''
        cur.execute("SELECT COUNT(1) FROM AMLOfficer WHERE userName = %s;", [form.username.data])  # CHECKS IF USERNAME EXSIST
        if cur.fetchone()[0]:
            cur.execute("SELECT password FROM AMLOfficer WHERE userName = %s;", [form.username.data])  # FETCH THE HASHED PASSWORD
            for row in cur.fetchall():
                if form.password.data == row[0]:
                    session['username'] = form.username.data
                    query2 = "SELECT email FROM AMLOfficer WHERE userName = '" + form.username.data + "'"
                    cur.execute(query2)
                    useremail = cur.fetchone()
                    session["email"] = useremail
                    cur.execute("UPDATE SMI_DB.AMLOfficer SET numOfFailedLogin=%s WHERE userName='%s' " % (0, form.username.data)) #SUCCESSFUL LOGIN SET #ofTries to zero
                    db.commit()
                    flash(f'Welcome back {form.username.data}', 'success')
                    return redirect(url_for('bankP'))


                else:
                    cur.execute("SELECT numOfFailedLogin FROM AMLOfficer WHERE userName = %s;",[form.username.data])  # FETCH THE HASHED PASSWORD
                    for row in cur.fetchall():
                        if row[0]== 3:
                            flash('Sorry You have entered your password 3 times wrong.. Enter your email for validation to reset your password', 'danger')
                            return redirect(url_for('forgotPass'))



                        else:
                            cur.execute("UPDATE SMI_DB.AMLOfficer SET numOfFailedLogin= numOfFailedLogin+1 WHERE userName='%s' " % (form.username.data))  # SUCCESSFUL LOGIN SET #ofTries to zero
                            db.commit()
                            flash('Wrong Password try again!', 'danger')

        else:
            flash('Invalid Username try again!', 'danger')
            db.commit()
            cur.close()
            db.close()
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    # remove the username and email from the session if it is there
    session.pop('username', None)
    session.pop('email', None)
    return redirect(url_for('home'))


@app.route("/Register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Checking If the account(user_name) is already registered.
        cursor.execute("SELECT * FROM AMLOfficer WHERE userName = '" + form.username.data + "'")
        data1 = cursor.fetchone()

        # Checking If the account(email) is already registered.
        cursor.execute("SELECT * FROM AMLOfficer WHERE email = '" + form.email.data + "'")
        data2 = cursor.fetchone()
        if not (data1 is None):
            flash('This Username is already registered please try another username', 'danger')
            return render_template('Register.html', form=form)
        elif not (data2 is None):
            flash('This Email is already registered please try another email', 'danger')
            return render_template('Register.html', form=form)
        else:
            cur, db = connection2()
            query = "INSERT INTO AMLOfficer (userName, email, fullname, password, bank_id ) VALUES(%s,%s,%s,%s,%s)"
            val = (form.username.data, form.email.data, form.fullName.data, form.password.data, 1)
            cur.execute(query, val)
            db.commit()
            cur.close()
            db.close()
            session["username"] = form.username.data
            session['email'] = form.email.data
            flash(f'Account created for {session["username"]} Successfully !', 'success')
        return redirect(url_for('bankP'))

    return render_template('Register.html', form=form)


@app.route("/forgotPassword", methods=['GET', 'POST'])
def forgotPass():
    form = forgotPassForm()
    if form.validate_on_submit():
        # Check id user exisit in the database
        cur, db = connection2()
        query = "SELECT * FROM SMI_DB.AMLOfficer WHERE email ='" + form.email.data + "'"
        cur.execute(query)
        data1 = cur.fetchone()
        if (data1 is None):
            flash('This email is not registered in our system ', 'danger')
            return render_template('forgotPassword.html', form=form)
        else:
            a = passwordRecovery(form.email.data)
            a.sendEmail()

            flash('A recovery password has been sent to your email', 'success')
            return render_template('forgotPassword.html', form=form)

    return render_template("forgotPassword.html", form=form)


@app.route("/bankProfile" , methods=['GET', 'POST'])
def bankP():

    if session.get('username') == None:
        return redirect(url_for('home'))
    form = SearchForm()
    if form.validate_on_submit():
        return redirect((url_for('searchResult', id= form.search.data)))  # or what you want
    return render_template("bankProfile.html", form = form)



@app.route("/searchResult/<id>" , methods=['GET', 'POST'])
def searchResult(id):

    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:
        cur, db = connection2()
        query = "SELECT * FROM SMI_DB.Client WHERE clientID = '" + id + "'"
        cur.execute(query)
        data = cur.fetchall()
        form = ViewProfileForm()
        search_form = SearchForm()

        if form.view_submit.data and form.validate_on_submit():
            return redirect((url_for('clientProfile', id = id  , form = form )))

        if search_form.search_submit.data and search_form.validate_on_submit():
            return redirect((url_for('searchResult', id=search_form.search.data , form2 = search_form)))

        return render_template("searchResult.html", data=data, form=form , form2 = search_form)




@app.route("/clientProfile/<id>", methods=['GET', 'POST'])
def clientProfile(id):
    client_form = clientForm()
    new_comment = newCommentForm()
    old_comment = oldCommentForm()
    cur, db = connection2()
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:
        #Retrive client Info from database:
        query = "SELECT * FROM SMI_DB.Client WHERE clientID = '" + id + "'"
        cur.execute(query)
        record = cur.fetchall()
        result=[]
        for column in record:
            client_form.clientID.data = column[0] #clientID
            client_form.clientName.data = column[1] #clientName
            client_form.clientSalary.data = column[2] #clientSalary
            client_form.clientClass.data = column[3]  #clientClass

    cur, db = connection2()
    query = "SELECT * FROM SMI_DB.Comment WHERE clientID = '" + id + "'"
    cur.execute(query)
    record = cur.fetchall()
    if not (record is None) :
        for column in record:
            old_comment.PrecommentDate.data = column[2] #comment date
            old_comment.PrecommentContent.data = column[1] #comment body
        return render_template("clientProfile.html", clientForm=client_form, commentForm=new_comment,
                               oldCommentForm=old_comment)
    if new_comment.validate_on_submit():
        date_now = datetime.now()
        formatted_date = date_now.strftime('%Y-%m-%d %H:%M:%S')
        query = "INSERT INTO SMI_DB.Comment (commentBody, commentDate, clientID, officerName ) VALUES(%s,%s,%s,%s)"
        val = (new_comment.commentBody.data, formatted_date, formatted_date, 1, session['username'])
        cur.execute(query, val)
        db.commit()
        cur.close()
        db.close()

    return render_template("clientProfile.html", clientForm = client_form, commentForm = new_comment)




@app.route("/ManageProfile", methods=['GET', 'POST'])
def manageProfile():
    form = bankProfileForm()
    search_form = SearchForm()
    username = session.get('username')
    if session.get('username') == None:
        return redirect(url_for('home'))

    if form.profile_submit.data and form.validate_on_submit():
        cur, db = connection2()
        cur.execute("UPDATE SMI_DB.AMLOfficer SET fullname = '" + form.fullName.data + "' , email = '" + form.email.data + "' , userName = '" + form.username.data + "', password = '" + form.password.data + "' WHERE userName = '" + username + "'" )
        db.commit()

    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id= search_form.search.data , form2 = search_form )))

    return render_template("ManageProfile.html", form=form , form2 = search_form )



@app.route("/ManageBankData" , methods=['GET', 'POST'])
def manageBankData():
    form = manageBankDataForm()
    if form.validate_on_submit():
        db = firebase.database()
        #businessRules_file = businessRules_file.data
        sanction_list = open(form.sanction_list.data , "r")
        risk_countries = form.risk_countries.data
        exceed_avg_tran = form.exceed_avg_tran.data
        #type1 = form.type.data
        amount = form.amount.data
        db.child('Rule1').child('highRiskCountries').set(risk_countries)
        db.child('Rule2').child('exceedingAvgTransaction').set(exceed_avg_tran)
        #db.child('Rule3').child('suspiciousTransaction').child('Type').set(type1)
        db.child('Rule3').child('suspiciousTransaction').child('amount').set(amount)
        db.child('Rule4').child('blackList').set(sanction_list.readlines())

    if session.get('username') == None:
        return redirect(url_for('home'))
    return render_template("ManageBankData.html" , form = form)


#cases page



@app.route("/Cases" , methods=['GET', 'POST'])
def cases():
    cur, db = connection2()
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:
        query = "SELECT * FROM SMI_DB.ClientCase "
        cur.execute(query)
        data = cur.fetchall()
        form = ViewCasesForm()
        if form.validate_on_submit():
            print(form.submit)
            id = request.form['submit'][-1]
            return redirect((url_for('case' , id = id)))
        return render_template("cases.html", data=data, form=form)

#case page

@app.route("/case/<id>", methods=['GET', 'POST'])
def case(id):
    # Only logged in users can access bank profile
    print(type(id))
    if session.get('username') == None:
        return redirect(url_for('home'))




    return render_template("case.html")


'''@app.route("/addComment")
def comment():
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))'''

@app.route("/DatabaseSetup", methods=['GET', 'POST'])
def DatabaseSetup():
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    form = dbSetupForm()
    if form.validate_on_submit():
        status, cur, db = BankConnection(form.db_host.data,form.db_user.data,form.db_pass.data,form.db_name.data)
        if status == 1 :
            flash('Unable to connect please try again..', 'danger')
            return render_template("databaseSetup.html", form=form)
        else :
            flash('Successfully connected to the database..', 'success')
            return render_template("databaseSetup.html", form=form)

    return render_template("databaseSetup.html", form = form)

@app.route("/Report", methods=['GET', 'POST'])
def Report():
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))


    return render_template("email.html")




if __name__ == "__main__":
    app.run(debug=True)
