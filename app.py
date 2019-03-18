from flask import Flask, redirect, render_template, request, session, abort, url_for, flash, redirect, session,jsonify , make_response , render_template_string
from flaskext.mysql import MySQL
from forms import RegistrationForm, LoginForm, forgotPassForm, bankProfileForm, clientForm, oldCommentForm, newCommentForm, dbSetupForm , manageBankDataForm , SearchForm , ViewProfileForm , ViewCasesForm , reportCase
from DBconnection import connection2, BankConnection , firebaseConnection
from passwordRecovery import passwordRecovery
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import configparser
from flask import Markup
from flask_paginate import Pagination, get_page_parameter
from flask_sqlalchemy import SQLAlchemy
import pyrebase
import random
import time
from celery import Celery , task
from MachineLearningLayer.Detect import Detection
import pdfkit
from flask_mail import Mail, Message
from celery.result import AsyncResult
import json





app = Flask(__name__)




APP_ROOT = os.path.dirname(os.path.abspath(__file__))


app.config['SECRET_KEY'] = 'af6695d867da3c7d125a99f5c17ea79a'
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'SMIhmwn19*'
app.config['MYSQL_DATABASE_DB'] = 'SMI_DB'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
app.config['Upload_folder'] = 'Br_file/'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tiger@localhost/SMI_DB'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#dbA = SQLAlchemy(app)


conn = mysql.connect()
cursor = conn.cursor()

# Initialize extensions
mail = Mail(app)


celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

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
        cur, db , engine = connection2()
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
    #task = long_task.apply_async()
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
        if not (data2 is None):
            flash('This Email is already registered please try another email', 'danger')
            return render_template('Register.html', form=form)
        else:
            cur, db , engine = connection2()
            query = "INSERT INTO AMLOfficer (userName, email, fullname, password) VALUES(%s,%s,%s,%s)"
            val = (form.username.data, form.email.data, form.fullName.data, form.password.data)
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
        cur, db , engine = connection2()
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
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    form = SearchForm()
    if form.validate_on_submit():
        return redirect((url_for('searchResult', id= form.search.data)))  # or what you want
    return render_template("bankProfile.html", form = form, alert = totalAlert)



@app.route("/searchResult/<id>" , methods=['GET', 'POST'])
def searchResult(id):

    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:
        cur, db , engine = connection2()
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
    cur, db , engine = connection2()

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

        cur, db , engine= connection2()
        query = "SELECT * FROM SMI_DB.Comment WHERE clientID = '" + id + "'"
        cur.execute(query)
        record = cur.fetchall()

    #if not (record is None) :
        #for column in record:
            #old_comment.PrecommentDate.data = column[2] #comment date
            #old_comment.PrecommentContent.data = column[1] #comment body
        #return render_template("clientProfile.html", clientForm=client_form, commentForm=new_comment,oldCommentForm=old_comment)

        if  new_comment.add_submit.data and new_comment.validate_on_submit():
            print("works")
            cur, db, engine = connection2()
            date_now = datetime.now()
            formatted_date = date_now.strftime('%Y-%m-%d %H:%M:%S')
            query = "INSERT INTO SMI_DB.Comment (commentBody, commentDate, clientID, officerName ) VALUES(%s,%s,%s,%s)"
            val = (new_comment.commentBody.data, formatted_date, id, session['username'])
            print(new_comment.commentBody.data)
            cur.execute(query, val)
            db.commit()
            cur.close()
            db.close()
            return redirect(url_for('clientProfile', commentForm=new_comment, id=id))


        print(old_comment.delete.data)


        if  old_comment.validate_on_submit():
            print('the delete works')
            cur, db , engine = connection2()
            id1 = request.form['Delete_comment']
            print(id)
            print(id1)
            query = "DELETE FROM SMI_DB.Comment WHERE commentID = '" + id1 + "'"
            cur.execute(query)
            return redirect(url_for('clientProfile' , oldCommentForm=old_comment , id1 = id1 , id = id))


        return render_template("clientProfile.html", clientForm = client_form, commentForm = new_comment , record = record , oldCommentForm=old_comment)



@app.route("/ManageProfile", methods=['GET', 'POST'])
def manageProfile():
    form = bankProfileForm()
    search_form = SearchForm()
    username = session.get('username')
    if session.get('username') == None:
        return redirect(url_for('home'))


    if form.profile_submit.data and form.validate_on_submit():
        cursor.execute("SELECT * FROM AMLOfficer WHERE email = '" + form.email.data + "'")
        data2 = cursor.fetchone()
        if not (data2 is None):
            flash('This Email is already exists please try another email', 'danger')
            return render_template('ManageProfile.html', form=form , form2 = search_form )
        else:
            cur, db , engine = connection2()
            cur.execute("UPDATE SMI_DB.AMLOfficer SET fullname = '" + form.fullName.data + "' , email = '" + form.email.data + "' , password = '" + form.password.data + "' WHERE userName = '" + username + "'" )
            db.commit()

    # bring info from database
    cur1, db1, engine1 = connection2()
    cur1.execute("SELECT * FROM SMI_DB.AMLOfficer WHERE userName = '" + username + "'")
    data = cur1.fetchall()


    for each in data:
        form.fullName.data = each[2]
        form.email.data = each[1]


    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id= search_form.search.data , form2 = search_form )))

    return render_template("ManageProfile.html", form=form , form2 = search_form )


@app.route('/deleteProfile', methods=['GET','POST'])
def deleteProfile():
    username = session.get('username')
    cur, db, engine = connection2()
    query = "DELETE FROM Comment WHERE officerName = '" + username + "'"
    cur.execute(query)

    query = "DELETE FROM AMLOfficer WHERE userName = '" + username + "'"
    cur.execute(query)
    return redirect(url_for('home'))


@app.route("/ManageBankData" , methods=['GET', 'POST'])
def manageBankData():
    form = manageBankDataForm()
    search_form = SearchForm()
    status, cur, db, engine = BankConnection()
    if  form.validate_on_submit():
        ## check if there's prevoius BR and confirm to update it

        print()
        target = os.path.join(APP_ROOT , 'Br_file/')
        print(target)
        if not os.path.isdir(target):
            os.mkdir(target)
        file  =  request.files.get('file_br')
        print(file)
        filename = file.filename
        print(filename)

        if filename.split(".", 1)[1] != 'txt':
            flash('File extention should be txt', 'danger')
            return render_template("ManageBankData.html", form=form)

        else:
            dest = "/".join([target, filename])
            print(dest)
            file.save(dest)

        db = firebase.database()
        #businessRules_file = businessRules_file.data
        sanction_list = open("Br_file/" + filename , "r")
        risk_countries = form.risk_countries.data
        exceed_avg_tran = form.exceed_avg_tran.data
        #type1 = form.type.data
        amount = form.amount.data
        db.child('Rule1').child('highRiskCountries').set(risk_countries)
        db.child('Rule2').child('exceedingAvgTransaction').set(exceed_avg_tran)
        #db.child('Rule3').child('suspiciousTransaction').child('Type').set(type1)
        db.child('Rule3').child('suspiciousTransaction').child('amount').set(amount)
        db.child('Rule4').child('blackList').set(sanction_list.read().splitlines())

        if status == 1:
            flash(Markup('You didn''t setup you''r database, please click <a href="/DatabaseSetup" class="alert-link">here</a> to setup ') , 'danger')
        return redirect((url_for('manageBankData',  form = form)))


    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id= search_form.search.data , form2 = search_form )))



    if session.get('username') == None:
        return redirect(url_for('home'))
    return render_template("ManageBankData.html" , form = form , form2 =search_form )

#cases page



@app.route("/Cases" , methods=['GET', 'POST'])
def cases():

    search = False
    q = request.args.get('q')
    if q:
        search = True


    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:
        cur, db, engine = connection2()
        form = ViewCasesForm()
        search_form = SearchForm()
        per_page = 4
        page = request.args.get(get_page_parameter(), type=int, default=1)
        offset = (page - 1) * per_page
        query = "SELECT * FROM SMI_DB.ClientCase "
        cur.execute(query)
        total = cur.fetchall()
        cur.execute("SELECT * FROM SMI_DB.ClientCase ORDER BY caseID DESC LIMIT %s OFFSET %s", (per_page, offset))
        cases = cur.fetchall()

        if search_form.search_submit.data and search_form.validate_on_submit():
            return redirect((url_for('searchResult', id=search_form.search.data, form2=search_form)))


        if  form.validate_on_submit():
            #id = form.hidden.data
            #id = request.form.get('case_submit')
            id = request.form['caseView']
            #id2 = request.form['caseDownload']
            print(id)
            return redirect((url_for('case' , id = id)))

        pagination = Pagination(page=page,per_page = per_page, total= len(total) ,offset = offset , search=search, record_name='cases' , css_framework='bootstrap3')
        # 'page' is the default name of the page parameter, it can be customized
        # e.g. Pagination(page_parameter='p', ...)
        # or set PAGE_PARAMETER in config file
        # also likes page_parameter, you can customize for per_page_parameter
        # you can set PER_PAGE_PARAMETER in config file
        # e.g. Pagination(per_page_parameter='pp')
        #, pagination=pagination

        return render_template("cases.html", cases = cases, form=form ,form2 = search_form  , pagination=pagination ,css_framework='foundation', caseId = 0)

#case page

@app.route("/case/<id>", methods=['GET', 'POST'])
def case(id):
    # Only logged in users can access bank profile

    if session.get('username') == None:
        return redirect(url_for('home'))
    search_form = SearchForm()


    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id=search_form.search.data, form2=search_form)))



    cur, db, engine = connection2()
    cur.execute("UPDATE ClientCase SET viewed = '0' WHERE caseID=%s " % (id))



    cur, db, engine = connection2()
    cur.execute("SELECT * FROM SMI_DB.ClientCase WHERE caseID=%s " % (id))
    data = cur.fetchall()
    client_ID = data[0][3]

    profileLabel=''
    if data[0][1] == 'Low':#Need to change it Meduim
        profileLabel ='label label-warning'
    else:#High
        profileLabel = 'label label-danger'

    cur.execute("SELECT * FROM SMI_DB.Client WHERE clientID=%s " % ( client_ID))
    data2 = cur.fetchall()

    cur.execute("SELECT * FROM SuspiciousTransaction WHERE clientID=%s " % (client_ID))
    transaction = cur.fetchall()

    return render_template("case.html",data= data, data2= data2, label= profileLabel, clientId = id, transaction=transaction)


@app.route('/download/<id>', methods=['GET','POST'])
def download(id):
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE caseID = '" + id + "'"
    cur.execute(query)
    record = cur.fetchall()
    client_ID = record[0][3]
    caseNumber = ''
    caseDate = ''

    for each1 in record:
        caseNumber = each1[0]
        caseDate = each1[2]



    profileLabel = ''
    if record[0][1] == 'Low':  # Need to change it Meduim
        profileLabel = 'label label-warning'
    else:  # High
        profileLabel = 'label label-danger'
    label_name = record[0][1]




    #--------------------#----------------------#--------------------------#-------------#

    query1 = "SELECT * FROM SMI_DB.SuspiciousTransaction WHERE clientID=%s " % (client_ID)
    cur.execute(query1)
    transaction = cur.fetchall()


    # --------------------#----------------------#--------------------------#-------------#

    query2 = "SELECT * FROM SMI_DB.Client WHERE clientID=%s " % (client_ID)
    cur.execute(query2)
    record2 = cur.fetchall()
    clientName = ''
    for each in record2:
     clientName = each[1]


    rendered = render_template('CaseToPrint.html' , clientName = clientName , caseNumber = caseNumber ,caseDate = caseDate,label = profileLabel ,label_name = label_name , transaction = transaction)

    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=case.pdf'
    return response

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
    form2 = SearchForm()
    status, cur, db, engine = BankConnection()
    db = firebase.database()
    isFB_Connected = db.child('Rule3').child('suspiciousTransaction').child('amount').get().val()



    if form2.search_submit.data and form2.validate_on_submit():
        return redirect((url_for('searchResult', id=form2.search.data, form2=form2)))


    if form.validate_on_submit():
        if status == 0: # If the user tried to connect to already connected DB
            config = configparser.ConfigParser()
            config.read('credentials.ini')

            if form.db_host.data==config['DB_credentials']['host']\
                    and form.db_name.data == config['DB_credentials']['db']\
                    and form.db_pass.data == config['DB_credentials']['passwd']\
                    and form.db_user.data == config['DB_credentials']['user']:

                flash('You are already connected to this database..', 'success')
                return render_template("databaseSetup.html", form=form ,form2=form2 )

        config = configparser.ConfigParser()
        config['DB_credentials'] = {'host': form.db_host.data,
                                    'user': form.db_user.data,
                                    'passwd': form.db_pass.data,
                                     'db': form.db_name.data}
        with open('credentials.ini', 'w') as configfile:
            config.write(configfile)
        status, cur, db, engine= BankConnection()
        if status == 1:
            flash('Unable to connect please try again..', 'danger')
            return render_template("databaseSetup.html", form=form , form2=form2)
        else:
            if isFB_Connected != 'false':
                flash('Successfully connected to the database..Upload your business rules to start the analysis', 'success')
                search_form = SearchForm()
                form = manageBankDataForm()
                return render_template("ManageBankData.html", form=form, form2=form2)

            # Check if bussinse rule is uploaded
            flash('Successfully connected to the database..', 'success')
            return render_template("databaseSetup.html", form=form , form2=form2)



    if status == 0: #If DB is already set bring the form.
        config = configparser.ConfigParser()
        config.read('credentials.ini')
        form.db_host.data = config['DB_credentials']['host']
        form.db_name.data = config['DB_credentials']['db']
        form.db_pass.data = config['DB_credentials']['passwd']
        form.db_user.data = config['DB_credentials']['user']


    return render_template("databaseSetup.html", form = form , form2=form2)



@app.route("/Report/<id>", methods=['GET', 'POST'])
def Report(id):
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))

    form = reportCase()
    print('Inside Report')
    print(form.reciver.data)
    if form.validate_on_submit():
        #print('Calling sendReport')
        #return redirect((url_for('sendReport', form=form)))
        print('Inside sendReport')
        print(form.reciver.data)
        recipient = form.reciver.data
        msg = Message(form.subject.data, recipient.split())
        msg.body = form.email_body.data
        print(msg)
        mail.send(msg)

        flash('Email has been sent Successfully..', 'success')
    return render_template("email.html", form = form, clientID= id)


######CELERY PART #########

@app.route('/startAnalysis')
def startAnalysis():
    return render_template_string('''<a href="{{ url_for('enqueue') }}">start</a>''')

@app.route('/enqueue')
def enqueue():
    task = Analysis.delay()
    form2 = SearchForm()
    return render_template('analysisView.html', JOBID=task.id, form2=form2)


@app.route('/analysisView')
def analysisView():
    form2 =SearchForm()
    return render_template("analysisView.html",form2= form2)


@app.route('/progress')
def progress():
    jobid = request.values.get('jobid')
    if jobid:
        # GOTCHA: if you don't pass app=celery here,
        # you get "NotImplementedError: No result backend configured"
        job = AsyncResult(jobid, app=celery)
        print (job.state)
        print (job.result)
        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state=job.state,
                progress=job.result['current']*1.0/job.result['total'],
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
    return '{}'

@celery.task
def Analysis():
    d = Detection()
    d.Detect()

if __name__ == "__main__":
    app.run(debug =True)
