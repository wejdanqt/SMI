import flask
from flask import Flask, redirect, render_template, request, session, abort, url_for, flash, redirect, session,jsonify , make_response ,\
    render_template_string , send_from_directory
from flaskext.mysql import MySQL
from forms import RegistrationForm, LoginForm, forgotPassForm, bankProfileForm, clientForm, oldCommentForm, newCommentForm, dbSetupForm , manageBankDataForm ,\
    SearchForm , ViewProfileForm , ViewCasesForm , reportCase , uploadForm , uploadKeywords , bankP_form
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
from flask_socketio import SocketIO
from flask_socketio import send, emit
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
import functools
import collections
import flask






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

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'smi.ksu2019@gmail.com'
app.config['MAIL_PASSWORD'] = '$MI7320KSU2019'
app.config['MAIL_DEFAULT_SENDER'] = 'smi.ksu2019@gmail.com'

socketio = SocketIO(app)


# Initialize Flask-Breadcrumbs
Breadcrumbs(app=app)


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



#breadcrumbs



#............
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
            query = "INSERT INTO AMLOfficer (userName, email, fullname, password , bankName) VALUES(%s,%s,%s,%s,%s)"
            val = (form.username.data, form.email.data, form.fullName.data, form.password.data , form.bankName.data)
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
@register_breadcrumb(app, '.', 'Profile')
def bankP():

    if session.get('username') == None:
        return redirect(url_for('home'))
    username = session.get('username')


    cur, db, engine = connection2()
    form2 = bankP_form()
    form = SearchForm()

    query = "SELECT * FROM AMLOfficer WHERE userName = '" + username + "'"
    cur.execute(query)
    data1 = cur.fetchall()

    for column in data1:
        form2.bnak_name.data = column[5]
        form2.username.data =  column[0]
        form2.AML_name.data =  column[2]
        form2.Email.data =  column[1]



    cur, db, engine = connection2()
    query2 = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query2)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})


    if form.validate_on_submit():
        return redirect((url_for('searchResult', id= form.search.data)))  # or what you want
    return render_template("bankProfile.html", form = form, form2 = form2 , alert = totalAlert , data = data1)



@app.route("/searchResult/<id>" , methods=['GET', 'POST'])
@register_breadcrumb(app, '.searchResult', 'Search result')
def searchResult(id):

    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:
        cur, db , engine = connection2()
        query = "SELECT * FROM SMI_DB.Client WHERE clientID  =  '" + id + "'  OR clientName  = '" + id + "'"
        cur.execute(query)
        data = cur.fetchall()
        print(len(data))
        form = ViewProfileForm()
        search_form = SearchForm()

        query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
        cur.execute(query)
        totalAlert = cur.fetchall()
        totalAlert = len(totalAlert)
        print(totalAlert)
        socketio.emit('count-update', {'count': totalAlert})

        if form.view_submit.data and form.validate_on_submit():
            return redirect((url_for('clientProfile', id = id  , form = form )))

        if search_form.search_submit.data and search_form.validate_on_submit():
            return redirect((url_for('searchResult', id=search_form.search.data , form2 = search_form ,
                                     alert = totalAlert , NoResult = len(data) )))

        return render_template("searchResult.html", data=data, form=form , form2 = search_form ,
                               alert = totalAlert , NoResult = len(data) )



@app.route("/clientProfile/<id>", methods=['GET', 'POST'])
@register_breadcrumb(app, '.clientProfile', 'Client profile')
def clientProfile(id):
    client_form = clientForm()
    new_comment = newCommentForm()
    old_comment = oldCommentForm()
    search_form = SearchForm()
    cur, db , engine = connection2()

    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    else:

        # alert code

        query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
        cur.execute(query)
        totalAlert = cur.fetchall()
        totalAlert = len(totalAlert)
        print(totalAlert)
        socketio.emit('count-update', {'count': totalAlert})

        #Retrive client Info from database:
        query = "SELECT * FROM SMI_DB.Client WHERE clientID  =  '" + id + "'  OR clientName  = '" + id + "'"

        cur.execute(query)
        record1 = cur.fetchall()
        result=[]
        profileLabel = ''

        for column in record1:
            client_form.clientID.data = column[0] #clientID
            client_form.clientName.data = column[1] #clientName


            if column[2] == 'Medium':  # Meduim
                profileLabel = 'label label-warning'
            elif column[2] == 'High':  # High
                profileLabel = 'label label-danger'
            else: # Low
                profileLabel = 'label label-primary'


        #Retreive old comments
        if type(id) == str:
            query1 = "SELECT * FROM SMI_DB.Client WHERE clientName = '" + id + "'"
            cur.execute(query1)
            data = cur.fetchall()
            for each in data:
                id = each[0]

            print(id)
            print(type(id))

        cur, db , engine= connection2()
        query = "SELECT * FROM SMI_DB.Comment WHERE clientID  = '" + str(id) + "'"
        cur.execute(query)
        record = cur.fetchall()


        if  new_comment.add_submit.data and new_comment.validate_on_submit():
            print("works")
            cur, db, engine = connection2()
            date_now = datetime.now()
            formatted_date = date_now.strftime('%Y-%m-%d %H:%M:%S')

            if type(id) == str:
                query1 = "SELECT * FROM SMI_DB.Client WHERE clientName = '" + id + "'"
                cur.execute(query1)
                data = cur.fetchall()
                for each in data:
                    id = each[0]


            query = "INSERT INTO SMI_DB.Comment (commentBody, commentDate, clientID, officerName ) VALUES(%s,%s,%s,%s)"
            val = (new_comment.commentBody.data, formatted_date, id, session['username'])
            print(new_comment.commentBody.data)
            cur.execute(query, val)
            db.commit()
            cur.close()
            db.close()
            return redirect(url_for('clientProfile', commentForm=new_comment, id=id))


        print(old_comment.delete.data)

        if search_form.search_submit.data and search_form.validate_on_submit():
            return redirect((url_for('searchResult', id=search_form.search.data, form2=search_form)))


        if  old_comment.validate_on_submit():
            print('the delete works')
            cur, db , engine = connection2()
            id1 = request.form['Delete_comment']
            print(id)
            print(id1)
            query = "DELETE FROM SMI_DB.Comment WHERE commentID = '" + id1 + "'"
            cur.execute(query)
            return redirect(url_for('clientProfile' , oldCommentForm=old_comment , id1 = id1 , id = id))


        return render_template("clientProfile.html", clientForm = client_form, commentForm = new_comment , record = record ,
                               record1 = record1,label = profileLabel , oldCommentForm=old_comment , form2=search_form , alert = totalAlert)



@app.route("/ManageProfile", methods=['GET', 'POST'])
@register_breadcrumb(app, '.manageProfile', 'Edit Profile')
def manageProfile():
    form = bankProfileForm()
    search_form = SearchForm()
    username = session.get('username')
    if session.get('username') == None:
        return redirect(url_for('home'))

     # alert code
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})

    if form.profile_submit.data and form.validate_on_submit():
        cursor.execute("SELECT * FROM AMLOfficer WHERE email = '" + form.email.data + "'")
        data2 = cursor.fetchone()
        if not ((data2 is None)) and (data2[0] != username):
            flash('This Email is already exists please try another email', 'danger')
            return render_template('ManageProfile.html', form=form , form2 = search_form , alert = totalAlert)
        else:
            cur, db , engine = connection2()
            cur.execute("UPDATE SMI_DB.AMLOfficer SET fullname = '" + form.fullName.data + "' , email = '" + form.email.data + "' , password = '" + form.password.data + "' WHERE userName = '" + username + "'" )
            db.commit()
            flash('Profile Successfully updated', 'success')
            return redirect(url_for('bankP'))




    # bring info from database
    cur1, db1, engine1 = connection2()
    cur1.execute("SELECT * FROM SMI_DB.AMLOfficer WHERE userName = '" + username + "'")
    data = cur1.fetchall()


    for each in data:
        form.fullName.data = each[2]
        form.email.data = each[1]


    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id= search_form.search.data , form2 = search_form  , alert = totalAlert)))

    return render_template("ManageProfile.html", form=form , form2 = search_form , alert = totalAlert )


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
@register_breadcrumb(app, '.manageBankData', 'Business rules setup')
def manageBankData():
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    form = manageBankDataForm()
    search_form = SearchForm()
    form3 = uploadForm()

    #alert code
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})


    status, cur, db, engine = BankConnection()
    operands = ['==', 'not', 'or', 'in', 'and', '<', '>', '<=', '>=']

    if status == 1:  # If upload BR and didn't set DB redirect to database setup
        flash(Markup('To upload your rules you need to setup your database connection first, please click <a href="/DatabaseSetup" class="alert-link">here</a>'),
              'danger')
        return render_template("ManageBankData.html", form=form, form2=search_form,
                               form3=form3 , alert = totalAlert)

    fb = firebase.database()
    isFB_Connected = fb.child().get().val()



    FB_flag = 0

    if not (isFB_Connected is None):
        FB_flag = 1
    print('isFB_Connected', FB_flag)

    print(form.bank_submit.data)
    print(form.validate_on_submit())

    if form.bank_submit.data and form.validate_on_submit():

        ## check if there's prevoius BR and confirm to update it
        #print()
        target = os.path.join(APP_ROOT, 'br_file/')
        #print(target)
        if not os.path.isdir(target):
            os.mkdir(target)

        file = request.files.get('file_br')
        #print(file)
        filename = file.filename
        print(filename)

        if filename.split(".", 1)[1] != 'txt':
            flash('File extention should be txt', 'danger')
            return render_template("ManageBankData.html", form=form, form2=search_form,
                                   form3=form3 , alert = totalAlert)

        else:
            dest = "/".join([target, filename])
            print(dest)
            file.save(dest)
        try:

            # businessRules_file = businessRules_file.data
            sanction_list = open("Br_file/" + filename, "r")
            risk_countries = form.risk_countries.data
            exceed_avg_tran = form.exceed_avg_tran.data
            # type1 = form.type.data
            amount = form.amount.data
            fb.child('Rule1').child('highRiskCountries').set(risk_countries)
            fb.child('Rule2').child('exceedingAvgTransaction').set(exceed_avg_tran)
            # db.child('Rule3').child('suspiciousTransaction').child('Type').set(type1)
            fb.child('Rule3').child('suspiciousTransaction').child('amount').set(amount)
            fb.child('Rule4').child('blackList').set(sanction_list.read().splitlines())

        except Exception as e:
            flash('Please connect to the Internet..', 'danger')
            print(e)
            return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                   FB_flag=FB_flag , alert = totalAlert)
        #treger code
        if status == 0:
            task = Analysis.delay(0)
            form2 = SearchForm()
            flash('Successfully uploaded your business rules..', 'success')
            return render_template('analysisView.html', JOBID=task.id, form2=form2 , alert = totalAlert)

        return redirect((url_for('manageBankData', form=form, form2=search_form, form3=form3,
                                 FB_flag=FB_flag , alert = totalAlert)))


    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id=search_form.search.data, form2=search_form , form3=form3) ))


    # upload BR
    if form3.submitRule.data and form3.validate_on_submit():
        print('iam in manage data')
        target = os.path.join(APP_ROOT, 'Br_User/')
        print(target)
        if not os.path.isdir(target):
            os.mkdir(target)

        file1 = request.files.get('file_br')
        print(file1)
        if file1 is None:
            return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                   FB_flag=FB_flag,
                                   is_Br_submitted=1 , alert = totalAlert)
        filename = file1.filename
        print(filename)

        if filename.split(".", 1)[1] != 'json':
            file_exttintion_json = 1
            return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                   FB_flag=FB_flag,
                                   file_exttintion_json=file_exttintion_json , alert = totalAlert)

        else:
            dest = "/".join([target, filename])
            print(dest)
            file1.save(dest)
            cur.execute("SELECT * FROM Bank_DB.transaction LIMIT 1")
            try:
                with open(dest) as f:
                    data = json.load(f)

                print(data)
            except Exception as e:
                flash('Sorry...your file is not well structured... please follow the file format in the sample',
                      'danger')
                return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                       FB_flag=FB_flag, alert=totalAlert)

            i = 1

            ## 1- check file structure ##
            if 'Rules' not in data:
                print('Sorry...your file is not well structured... please follow the file format in the sample')
                flash('Sorry...your file is not well structured... please follow the file format in the sample',
                      'danger')
                return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                       FB_flag=FB_flag , alert = totalAlert)
            try:
                fb = firebase.database()
                for each in data['Rules']:

              ### 2-check Key words structure #####
                    if 'Rule{}'.format(i) not in data['Rules']:
                        print('ERROR in your file structure in Rule{} please follow the format'.format(i))
                        flash('ERROR in your file structure in Rule{} please follow the format'.format(i),'danger')
                        return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                               FB_flag=FB_flag , alert = totalAlert)
                     ### 3- check if all attriubtes in dataset ###
                    if data['Rules']['Rule' + str(i)][0] not in cur.column_names:
                        print('Rule{} attribute {} not found in the dataset'.format(i,data['Rules']['Rule{}'.format(i)][0]))
                        flash('Rule{} attribute {} not found in the dataset'.format(i,data['Rules']['Rule{}'.format(i)][0]),'danger')
                        return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                               FB_flag=FB_flag , alert = totalAlert)
                     ### 4- check if theres illegal operand ####

                    if data['Rules']['Rule' + str(i)][1] not in operands:
                        print('Illegal operand ({})in Rule{}'.format(data['Rules']['Rule{}'.format(i)][1], i))
                        flash('Illegal operand ({})in Rule{}'.format(data['Rules']['Rule{}'.format(i)][1], i),'danger')
                        return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                               FB_flag=FB_flag , alert = totalAlert)
                    #### 5- If there's rule for sanction, check if names are uploaded and get the names ####
                    if data['Rules']['Rule' + str(i)][2] == 'sanctionList':
                        print('Rule for sanction list')
                        if ('sanctionList' not in data):
                            print('for Rule{} Please  upload the sanction list section to the file'.format(i))
                            flash('for Rule{} Please  upload the sanction list section to the file'.format(i), 'danger')
                            return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                                   FB_flag=FB_flag , alert = totalAlert)
                        else:
                            print('Sanction list is uploaded:')
                            if len(data['sanctionList']) == 0:
                                print('Sanction List is empty please upload the names')
                                flash('Sanction List is empty please upload the names', 'danger')
                                return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                                       FB_flag=FB_flag , alert = totalAlert)
                            else:
                                print(data['sanctionList'])
                                fb.child('sanctionList').set(data['sanctionList'])

                    #### 6- If there's rule for risk countries, check if countries are uploaded and get the countries ####
                    if data['Rules']['Rule' + str(i)][2] == 'HighRiskCountries':
                        print('Rule for Risk countries')
                        if ('HighRiskCountries' not in data):
                            print('for Rule{} Please  upload the HighRiskCountries list section to the file'.format(i))
                            flash('for Rule{} Please  upload the HighRiskCountries list section to the file'.format(i), 'danger')
                            return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                                   FB_flag=FB_flag , alert = totalAlert)
                        else:
                            print('HighRiskCountries list is uploaded:')
                            if len(data['HighRiskCountries']) == 0:
                                print('HighRiskCountries is empty please upload the names')
                                flash('HighRiskCountries is empty please upload the names','danger')
                                return render_template("ManageBankData.html", form=form, form2=search_form, form3=form3,
                                                       FB_flag=FB_flag , alert = totalAlert)
                            else:
                                print(data['HighRiskCountries'])
                                fb.child('HighRiskCountries').set(data['HighRiskCountries'])


                    fb.child('Rules').child('Rule' + str(i)).set(data['Rules']['Rule' + str(i)])
                    i=i+1

                    # treger code
                    if status == 0:
                        task = Analysis.delay(1)
                        form2 = SearchForm()
                        flash('Successfully uploaded your business rules..', 'success')
                        return render_template('analysisView.html', JOBID=task.id, form2=form2, alert=totalAlert)




            except Exception as e :
                print(e)

    #retrive from firbase
    amount = fb.child('Rule3').child('suspiciousTransaction').child('amount').get().val()
    avg = fb.child('Rule2').child('exceedingAvgTransaction').get().val()
    form.amount.data = amount
    form.exceed_avg_tran.data = avg


    # treger code



    return render_template("ManageBankData.html", form=form, form2=search_form, FB_flag=FB_flag ,
                           form3=form3 , alert = totalAlert)
#cases page



@app.route("/Cases" , methods=['GET', 'POST'])
@register_breadcrumb(app, '.cases', 'Cases')
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


        #alert code

        query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
        cur.execute(query)
        totalAlert = cur.fetchall()
        totalAlert = len(totalAlert)
        print(totalAlert)
        socketio.emit('count-update', {'count': totalAlert})


        #.................

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

        return render_template("cases.html", cases = cases, numOfcase = len(cases) , form=form ,form2 = search_form  , pagination=pagination ,css_framework='foundation', caseId = 0 ,alert = totalAlert)

#case page

@app.route("/case/<id>", methods=['GET', 'POST'])
@register_breadcrumb(app, '.cases.case', 'Case')
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
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})


    cur, db, engine = connection2()
    cur.execute("SELECT * FROM SMI_DB.ClientCase WHERE caseID=%s " % (id))
    data = cur.fetchall()
    client_ID = data[0][3]

    profileLabel=''
    if data[0][1] == 'Medium':#Meduim
        profileLabel ='label label-warning'
    else:#High
        profileLabel = 'label label-danger'

    cur.execute("SELECT * FROM SMI_DB.Client WHERE clientID=%s " % ( client_ID))
    data2 = cur.fetchall()

    client_BR = data2[0][5]
    client_custom_BR = data2[0][6]
    print('client_custom_BR',client_custom_BR)
    Br_flag = True
    Custom_BR_flag =True
    print('Br', client_BR)
    Br_dic = {}
    Custom_BR=[]
    if client_BR == '0000':
        Br_flag = False

    else:
        if client_BR[0] == '1':
            Br_dic['1'] = 'Client Name is in sanction list'
        if client_BR[1] == '1':
            Br_dic['2'] = 'Client location in risk contries'
        if client_BR[2] == '1':
            Br_dic['3'] = 'Client exceeded avg amount of transactions'
        if client_BR[3] == '1':
            Br_dic['4'] = 'Client exceeded max amount of transaction'

    if client_custom_BR is None:
        Custom_BR_flag = False

    else:
        i = 1
        for each in client_custom_BR:
            # print(each)
            if each == '1':
                print('found', i)
                Custom_BR.append('Rule{}'.format(i))
            i = i + 1

    cur.execute("SELECT * FROM SuspiciousTransaction WHERE clientID=%s " % (client_ID))
    transaction = cur.fetchall()

    return render_template("case.html",data= data, data2= data2, label= profileLabel, clientId = client_ID
                           ,caseId = id ,transaction=transaction, form2=search_form ,alert = totalAlert, Br_flag=Br_flag ,Br_dic=Br_dic,Custom_BR_flag=Custom_BR_flag,Custom_BR=Custom_BR)


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

    client_BR = record2[0][5]
    client_custom_BR = record2[0][6]
    Br_flag = True
    Custom_BR_flag = True
    print('Br', client_BR)
    Br_dic = {}
    Custom_BR = []
    if client_BR == '0000':
        Br_flag = False
    else:
        if client_BR[0] == '1':
            Br_dic['1'] = 'Client Name is in sanction list'
        if client_BR[1] == '1':
            Br_dic['2'] = 'Client location in risk contries'
        if client_BR[2] == '1':
            Br_dic['3'] = 'Client exceeded avg amount of transactions'
        if client_BR[3] == '1':
            Br_dic['4'] = 'Client exceeded max amount of transaction'



    if client_custom_BR is None:
        Custom_BR_flag = False

    else:
        i = 1
        for each in client_custom_BR:
            # print(each)
            if each == '1':
                print('found', i)
                Custom_BR.append('Rule{}'.format(i))
            i = i + 1

    rendered = render_template('CaseToPrint.html' , clientName = clientName , caseNumber = caseNumber
                               ,caseDate = caseDate,label = profileLabel ,label_name = label_name ,
                               transaction = transaction ,Br_flag=Br_flag ,Br_dic=Br_dic  ,Custom_BR_flag=Custom_BR_flag,
                               Custom_BR=Custom_BR )

    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=case.pdf'
    return response


@app.route("/DatabaseSetup", methods=['GET', 'POST'])
@register_breadcrumb(app, '.DatabaseSetup', 'Database setup')
def DatabaseSetup():
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))
    form = dbSetupForm()
    form3 = uploadForm()
    search_form = SearchForm()
    status, cur, db, engine = BankConnection()

    #alert code
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})

    #search code

    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id=search_form.search.data,
                                 form2=search_form, form3=form3 , alert = totalAlert)))



    try:
     fb = firebase.database() # if nothing is uploaded == None
     isFB_Connected = fb.child().get().val()
    except Exception as e:
        flash('Please connect to the Internet..', 'danger')
        return render_template("databaseSetup.html", form=form, status=status ,
                               form2=search_form, form3=form3 , alert = totalAlert )


    if form.validate_on_submit():
        if status == 0: # If the user tried to connect to already connected DB
            config = configparser.ConfigParser()
            config.read('credentials.ini')

            if form.db_host.data==config['DB_credentials']['host']\
                    and form.db_name.data == config['DB_credentials']['db']\
                    and form.db_pass.data == config['DB_credentials']['passwd']\
                    and form.db_user.data == config['DB_credentials']['user']:

                flash('You are already connected to this database..', 'success')
                return render_template("databaseSetup.html", form=form, status = status ,
                                       form2=search_form, form3=form3 , alert = totalAlert)

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
            return render_template("databaseSetup.html", form=form, status = status ,
                                   form2=search_form, form3=form3 , alert = totalAlert)
        else:
            if isFB_Connected == None :
                flash('Successfully connected to the database..Upload your business rules to start the analysis', 'success')
                form = manageBankDataForm()
                return render_template("ManageBankData.html", form=form, form2=search_form,
                                       form3= form3 , alert = totalAlert)

                # Check if bussinse rule is uploaded
            flash('Successfully connected to the database..', 'success')
            return render_template("databaseSetup.html", form=form, status = status , form2=search_form,
                                   form3=form3 , alert = totalAlert)
    if status == 0:  # If DB is already set bring the form.
        config = configparser.ConfigParser()
        config.read('credentials.ini')
        form.db_host.data = config['DB_credentials']['host']
        form.db_name.data = config['DB_credentials']['db']
        form.db_pass.data = config['DB_credentials']['passwd']
        form.db_user.data = config['DB_credentials']['user']


    return render_template("databaseSetup.html", form = form, status = status , alert = totalAlert , form2=search_form, form3=form3)



@app.route("/Report/<id>", methods=['GET', 'POST'])
@register_breadcrumb(app, '.cases.case.Report', 'Report')
def Report(id):
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))

    form = reportCase()
    search_form = SearchForm()


    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id=search_form.search.data, form2=search_form)))


    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})

    cur, db, engine = connection2()
    cur.execute("SELECT * FROM SMI_DB.ClientCase WHERE caseID=%s " % (id))
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

    # --------------------#----------------------#--------------------------#-------------#

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

    client_BR = record2[0][5]
    client_custom_BR = record2[0][6]
    Br_flag = True
    Custom_BR_flag = True
    print('Br', client_BR)
    Br_dic = {}
    Custom_BR = []
    if client_BR == '0000':
        Br_flag = False
    else:
        if client_BR[0] == '1':
            Br_dic['1'] = 'Client Name is in sanction list'
        if client_BR[1] == '1':
            Br_dic['2'] = 'Client location in risk contries'
        if client_BR[2] == '1':
            Br_dic['3'] = 'Client exceeded avg amount of transactions'
        if client_BR[3] == '1':
            Br_dic['4'] = 'Client exceeded max amount of transaction'

    if client_custom_BR is None:
        Custom_BR_flag = False

    else:
        i = 1
        for each in client_custom_BR:
            # print(each)
            if each == '1':
                print('found', i)
                Custom_BR.append('Rule{}'.format(i))
            i = i + 1

    rendered = render_template('CaseToPrint.html', clientName=clientName, caseNumber=caseNumber
                               , caseDate=caseDate, label=profileLabel, label_name=label_name,
                               transaction=transaction , Br_flag=Br_flag ,Br_dic=Br_dic , Custom_BR_flag=Custom_BR_flag,
                               Custom_BR=Custom_BR)

    #######save case to working dierctory ##########
    pdfFile = pdfkit.from_string(rendered, 'case.pdf')

    form.subject.data = 'Case#{}_{}'.format(id,clientName)
    form.email_body.data = 'Fruad Report'

    if form.validate_on_submit():

        target = os.path.join(APP_ROOT, 'Case_file/')
        print('target',target)
        if not os.path.isdir(target):
            os.mkdir(target)
        file = request.files.get('file_case')
        try:
            filename = file.filename
            print('fileNAME',filename)
            dest = "/".join([target, filename])
            print(dest)
            file.save(dest)
            fileType= filename.split(".")[0]+"/"+filename.split(".")[1]
            filename = 'Case_file/'+filename
        except Exception as e:
            filename= "case.pdf"
            fileType = "case/pdf"




        recipient = form.reciver.data
        msg = Message(form.subject.data, recipient.split())
        msg.body = form.email_body.data
        with app.open_resource(filename) as fp:
            msg.attach(filename, fileType, fp.read())
        print(msg)
        mail.send(msg)

        flash('Email has been sent Successfully..', 'success')
    return render_template("email.html", form = form, clientID= id , alert = totalAlert , form2=search_form )


@app.route('/BussinseRuleGuide', methods=['GET','POST'])
def BR_GUIDE():

    if session.get('username') == None:
        return redirect(url_for('home'))

    search_form = SearchForm()
    # alert code
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})
    return render_template('BussinseRuleGuide.html',form2=search_form ,alert = totalAlert)



@app.route('/return-file/')
def return_file():
   ''' with open("BR_Sample/BussinseRulesSample.json") as fp:
         content = fp.read()
    response = make_response(content)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=BussinseRulesSample'
    return response'''

   return send_from_directory('BR_Sample/', 'BussinseRulesSample.json', as_attachment=True, mimetype='application/json',
                       attachment_filename='BussinseRulesSample.json')

@app.route("/keyword", methods=['GET', 'POST'])
@register_breadcrumb(app, '.keyword', 'Keywords')
def keyword():
    # Only logged in users can access bank profile
    if session.get('username') == None:
        return redirect(url_for('home'))

     # alert code
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})

    search_form = SearchForm()
    form3 = uploadKeywords()
    fileEx = 0

    # upload BR
    if form3.submit.data and form3.validate_on_submit():
        print('iam in keywords')


        target = os.path.join(APP_ROOT, 'key_words/')
        # print(target)
        if not os.path.isdir(target):
            os.mkdir(target)

        file = request.files.get('file_br')
        filename = file.filename
        print(filename)

        if filename.split(".", 1)[1] != 'txt':
            #flash('File extention should be txt', 'danger')
            fileEx = 1
            return render_template("keyword.html", form2=search_form,form3=form3, alert=totalAlert, fileEx=fileEx)

        else:
            dest = "/".join([target, filename])
            print(dest)
            file.save(dest)

            cur.execute('SELECT key_word FROM SMI_DB.KeyWord')
            data = cur.fetchall()
            db_word = []
            ### get old key words in database ###
            for each in data:
                db_word.append(each[0])

            ### get key words entered by user ###
            user_word = []
            f = open(dest, mode="r", encoding='utf-8')
            for line in f:
                user_word.append(line.rstrip('\n'))

            print('length of user words', len(user_word))

            #### If the is empty ####
            if len(user_word) ==0 :
                flash('The uploaded file is empty..', 'danger')
                return render_template("keyword.html", form2=search_form, form3=form3, alert=totalAlert, fileEx=fileEx)

            #### get unique words only ####
            new_words = set(user_word) - set(db_word)


            ### If there's any unique Key words add it
            if len(new_words) > 0:
                for each in new_words:
                    print(each)
                    cur.execute("""INSERT INTO  SMI_DB.KeyWord (key_word) VALUES (%s)""", (each,))
                flash('Keywords Uploaded Successfully ', 'success')
                return render_template("keyword.html", form2=search_form, form3=form3, alert=totalAlert, fileEx=fileEx)

            else :
                flash('Keywords in the file is already in the database  ', 'success')
                return render_template("keyword.html", form2=search_form, form3=form3, alert=totalAlert, fileEx=fileEx)



    if search_form.search_submit.data and search_form.validate_on_submit():
        return redirect((url_for('searchResult', id=search_form.search.data, form2=search_form , form3= form3 , alert = totalAlert)))

    return render_template("keyword.html" ,  form2=search_form , form3 = form3 , alert = totalAlert,fileEx=fileEx)


######CELERY PART #########

@app.route('/startAnalysis')
def startAnalysis():
    return render_template_string('''<a href="{{ url_for('enqueue') }}">start</a>''')

@app.route('/enqueue')
def enqueue():
    task = Analysis.delay()
    form2 = SearchForm()
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})
    return render_template('analysisView.html', JOBID=task.id, form2=form2 , alert = totalAlert)


@app.route('/analysisView')
#@register_breadcrumb(app, '.manageBankData.analysisView', 'Analysis')
def analysisView():
    form2 =SearchForm()
    cur, db, engine = connection2()
    query = "SELECT * FROM SMI_DB.ClientCase WHERE viewed ='1'"
    cur.execute(query)
    totalAlert = cur.fetchall()
    totalAlert = len(totalAlert)
    print(totalAlert)
    socketio.emit('count-update', {'count': totalAlert})
    return render_template("analysisView.html",form2= form2 , alert = totalAlert )



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
def Analysis(id):
    d = Detection()
    d.Detect(id)

if __name__ == "__main__":
    app.run(debug =True)
