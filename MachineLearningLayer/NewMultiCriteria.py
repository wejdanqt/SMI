from DBconnection import firebaseConnection, connection2
import pandas as pd
from pandas import DataFrame

class NewMultiCriteria:


    def __init__(self):
        self.cur, self.db,self.engine = connection2()
        self.clientIDs = []
        self.query = "SELECT * FROM bank_db.transaction"
        self.cur.execute(self.query)
        recored = self.cur.fetchall()
        self.df = DataFrame(recored)
        self.df.columns =  self.cur.column_names
        self.numOfRules = 0
        self.sumOfFlags = 0
        self.saving_transaction = pd.DataFrame() #for saving client suspsious transactions
        self.transaction_IDs=[]
        self.allRules=''



        for each in recored:
            self.clientIDs.append(each[7])





    def getRules(self,Rules,sanctionList,highRiskCountries,MultiLevelRules,clientID):

        self.cur.execute("SELECT * FROM SMI_DB.SuspiciousTransaction WHERE clientID=%s " % (clientID))

        self.client_suspious_transaction = self.cur.fetchall()

        self.data = Rules
        i =1
        self.clientID = clientID
        self.client_df = self.df[self.df['clientID']== self.clientID].drop_duplicates(keep='first')
        self.sanctionList = sanctionList
        self.highRiskCountries = highRiskCountries


        for each in self.data:
            print('Rule statement',self.data['Rule{}'.format(i)])
            flag = self.checkRule(self.data['Rule{}'.format(i)],self.client_df,clientID)
            self.allRules = self.allRules + str(flag)
            print('Rule flag',flag)
            print('******************')
            self.sumOfFlags = self.sumOfFlags + flag
            i =i+1



        #### sanction List rule #####
        if not(self.sanctionList is None):
            if (self.client_df['clientName'].iloc[0] in self.sanctionList):
                    print('client name in sanction List',self.client_df['clientName'].iloc[0])
                    self.sumOfFlags = self.sumOfFlags + 1

        #### high risk countries rule #####
        if not( self.highRiskCountries is None):
            if (self.client_df['location'].iloc[0] in self.highRiskCountries):
                print('client location in high risk countries',self.client_df['location'].iloc[0])
                self.sumOfFlags = self.sumOfFlags + 1

        #### saving suspicious transaction to the database ####


        #### calculting Multicartiria score ####

        self.numOfRules = len(self.data)
        print('Sum of flags',self.sumOfFlags)
        print('Number of rules', self.numOfRules)

        MultiCriteriaScore =0
        try:
            MultiCriteriaScore = self.sumOfFlags / self.numOfRules
        except ZeroDivisionError:
            MultiCriteriaScore =0

        print('MultiCriteria Score: ',MultiCriteriaScore)
        print('*************')
        print(self.saving_transaction)


        if self.sumOfFlags > 0:
            self.cur.execute("UPDATE SMI_DB.Client SET custom_BR='%s' where clientID='%s'" % (self.allRules, self.clientID))
            self.db.commit()

        return MultiCriteriaScore



    def checkRule(self,rule, client_transaction,clientID):

        operands = ['==', 'not', 'or', 'in', 'and', '<', '>', '<=', '>=']
        self.rule = rule
        self.client_transaction = client_transaction
        self.cur.execute("SELECT * FROM SMI_DB.SuspiciousTransaction WHERE clientID=%s " % (clientID))
        self.client_suspious_transaction = self.cur.fetchall()
        for row in self.client_suspious_transaction:
            self.transaction_IDs.append(row[15])
        #print('Transactions ID', self.transaction_IDs)
        flag =0


        ##### opreands mapping ######
        if self.rule[1] == operands[0]: #==#
            #print("Inside == operand")
            if (self.client_transaction[self.rule[0]] == self.rule[2]).any():

                ### Saving suspicious transaction ###
                self.saving_transaction = pd.DataFrame(self.client_transaction[self.client_transaction[self.rule[0]] > self.rule[2]])
                #print('Before checking Database', self.saving_transaction)
                for index, row in self.saving_transaction.iterrows():
                    #print('transactions ID', row["transactionID"])
                    if (row["transactionID"] in self.transaction_IDs):
                        #print(row["transactionID"], 'Found in database')
                        self.saving_transaction = self.saving_transaction[self.saving_transaction.transactionID != row["transactionID"]]
                self.saving_transaction.to_sql(name='suspicioustransaction', con=self.engine,if_exists='append', index=False)


                #print('After checking Database')
                #print(self.saving_transaction)
                flag = 1



        if self.rule[1] == operands[5]:#<#
            if (self.client_transaction[self.rule[0]] < self.rule[2]).any():
                ### Saving suspicious transaction ###
                self.saving_transaction = pd.DataFrame(self.client_transaction[self.client_transaction[self.rule[0]] > self.rule[2]])
                #print('Before checking Database', self.saving_transaction)
                for index, row in self.saving_transaction.iterrows():
                    #print('transactions ID', row["transactionID"])
                    if (row["transactionID"] in self.transaction_IDs):
                        #print(row["transactionID"], 'Found in database')
                        self.saving_transaction = self.saving_transaction[self.saving_transaction.transactionID != row["transactionID"]]
                self.saving_transaction.to_sql(name='suspicioustransaction', con=self.engine,if_exists='append', index=False)


                #print('After checking Database')
                #print(self.saving_transaction)
                flag = 1



        if self.rule[1] == operands[6]:#>#
             if (self.client_transaction[self.rule[0]] > self.rule[2]).any():
                ### Saving suspicious transaction ###
                self.saving_transaction = pd.DataFrame(self.client_transaction[self.client_transaction[self.rule[0]] > self.rule[2]])
                #print('Before checking Database', self.saving_transaction)
                for index, row in self.saving_transaction.iterrows():
                    #print('transactions ID', row["transactionID"])
                    if (row["transactionID"] in self.transaction_IDs):
                        #print(row["transactionID"], 'Found in database')
                        self.saving_transaction = self.saving_transaction[self.saving_transaction.transactionID != row["transactionID"]]
                self.saving_transaction.to_sql(name='suspicioustransaction', con=self.engine,if_exists='append', index=False)


                #print('After checking Database')
                #print(self.saving_transaction)
                flag = 1


        if self.rule[1] == operands[7]:#<=#
            if (self.client_transaction[self.rule[0]] <= self.rule[2]).any():
                ### Saving suspicious transaction ###
                self.saving_transaction = pd.DataFrame(self.client_transaction[self.client_transaction[self.rule[0]] > self.rule[2]])
                #print('Before checking Database', self.saving_transaction)
                for index, row in self.saving_transaction.iterrows():
                    #print('transactions ID', row["transactionID"])
                    if (row["transactionID"] in self.transaction_IDs):
                        #print(row["transactionID"], 'Found in database')
                        self.saving_transaction = self.saving_transaction[self.saving_transaction.transactionID != row["transactionID"]]
                self.saving_transaction.to_sql(name='suspicioustransaction', con=self.engine,if_exists='append', index=False)


                #print('After checking Database')
                #print(self.saving_transaction)
                flag = 1


        if self.rule[1] == operands[8]:  # >=#
            if (self.client_transaction[self.rule[0]] >= self.rule[2]).any():
                ### Saving suspicious transaction ###
                self.saving_transaction = pd.DataFrame(
                    self.client_transaction[self.client_transaction[self.rule[0]] > self.rule[2]])
                #print('Before checking Database', self.saving_transaction)
                for index, row in self.saving_transaction.iterrows():
                    #print('transactions ID', row["transactionID"])
                    if (row["transactionID"] in self.transaction_IDs):
                        #print(row["transactionID"], 'Found in database')
                        self.saving_transaction = self.saving_transaction[
                            self.saving_transaction.transactionID != row["transactionID"]]
                self.saving_transaction.to_sql(name='suspicioustransaction', con=self.engine, if_exists='append',
                                               index=False)

                #print('After checking Database')
                #print(self.saving_transaction)
                flag = 1



        return flag







###### Calling ########
'''firebase = firebaseConnection()
fb = firebase.database()
Rules = fb.child('Rules').get().val()
sanctionList = fb.child('sanctionList').get().val()
highRiskCountries = fb.child('highRiskCountries').get().val()
MultiLevelRules = fb.child('MultiLevelRules').get().val()

a = NewMultiCriteria()
mc_score, rules = a.getRules(Rules,sanctionList,highRiskCountries,MultiLevelRules,1966002811)

print(rules)'''
