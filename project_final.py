# -*- coding: utf-8 -*-

import subprocess

def install(package):
    subprocess.check_call([f"pip install {package}"], shell=True)

required_libraries = ["flask", "flask_table", "twilio"]

for library in required_libraries:
    try:
        __import__(library)
    except ImportError:
        install(library)

from flask import Flask, request, render_template
from flask_table import Table, Col
from twilio.rest import Client
import random
import string


app = Flask(__name__)

class ItemTable(Table):
    name = Col('Name')
    num = Col('Queue Number')


class customer:
    def __init__(self, phone, name, domain, branch, num= -1):
        self.phone = phone  
        self.name = name  
        self.domain = domain  
        self.branch = branch
        self.num = self.get_queue_num(num) # str

    def get_queue_num(self,num):
        if self.domain == "business":
            return("B{}".format(num))
        elif self.domain == "personal":
            return("P{}".format(num))
        elif self.domain == "priority":
            return("VIP{}".format(num))


class Counter:
    def __init__(self, id, domain, branch):
        self.id = id  
        self.domain = domain  
        self.finishedlist = []
        self.branch = branch  
        self.emptyflag = True
        self.inprogress = None # None or the inprogress customer object
        self.stopFlag = False
        self.all_branch = []

    def send_sms(self):
        #  will not send if there is no money le
        account_sid = 'AC61765409abfcb8b673ac0c2c98913722'
        auth_token = '8c19f9f6d5cdec5e8d1a991eb8fc01e6'

        # send sms to next three customers in each queue
        for i in range(3):
            try:
                client = Client(account_sid, auth_token)

                message = client.messages \
                    .create(
                    body="Dear customer number{}, thanks for your patience. There is only {} people before you queueing. Please get ready.".format(
                        all_branch_queue[self.branch][self.domain].list[i].num, i),
                    from_='+19135131406',
                    to='+65{}'.format(all_branch_queue[self.branch][self.domain].list[i].phone)
                )

                print(message.sid)
            except:
                print(i,"Locked sms sent function because no money in account, sorry.")

    def next(self):
        belong_queue = all_branch_queue[self.branch][self.domain]
        if self.inprogress is not None:
            self.finishedlist.append(self.inprogress)
        # pass the first customer to the counter and marked inprogress and removed him/her from queue

        if len(all_branch_queue[self.branch][self.domain].list) != 0:
            self.inprogress = all_branch_queue[self.branch][self.domain].dequeue()
            #self.send_sms() #no money le
            print([value.name for value in all_branch_queue[self.branch][self.domain].list])
            print(self.inprogress.num)
            return {#"output":output,
                    "counterid":self.id
                    ,"branch":self.branch
                    ,"branch_list":branch_list
                    ,"domain":self.domain
                    ,"inprogress":self.inprogress.num
                    ,"holdlist":[customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]}
        else:
            self.inprogress = None
            return {"counterid":self.id
                    ,"branch":self.branch
                    ,"branch_list":branch_list
                    ,"domain":self.domain
                    ,"inprogress":None
                    ,"holdlist":[customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]}


    def hold(self):
        # add to hold list
        all_branch_queue[self.branch][self.domain].holdlist.append(self.inprogress)
        return {"counterid":self.id
                ,"branch":self.branch
                ,"branch_list":branch_list
                ,"domain":self.domain
                ,"inprogress":self.inprogress.num
                ,"holdlist":[customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]}

    def reschedule(self, num):
        # insert to 3rd
        domain_mapping = {"p":"personal","P":"personal",
                          "v":"priority","V":"priority",
                          "b":"business","B":"business"}
        customer_domain = domain_mapping[num[0]]
        for customer in all_branch_queue[self.branch][customer_domain].holdlist:
            if customer.num == num.upper():
                reschedule_customer = customer
                all_branch_queue[self.branch][customer_domain].holdlist.remove(customer)
                all_branch_queue[self.branch][customer_domain].insert(reschedule_customer, 2)
                return {"counterid": self.id
                    , "branch": self.branch
                    , "branch_list": branch_list
                    , "domain": self.domain
                    , "inprogress": self.inprogress.num
                    , "holdlist": [customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]
                    , "noti": "Customer {} found! Successfully rescheduled!".format(num)}
            else:
                print("not found")

        return {"counterid": self.id
                    , "branch": self.branch
                    , "branch_list": branch_list
                    , "domain": self.domain
                    , "inprogress": self.inprogress.num
                    , "holdlist": [customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]
                    , "noti": "Customer not found in hold list!"}


    def return_info(self):
        try:
            return {"counterid":self.id
                    ,"branch":self.branch
                    ,"branch_list":branch_list
                    ,"domain":self.domain
                    ,"inprogress":self.inprogress.num
                    ,"holdlist":[customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]}
        except:
            return {"counterid":self.id
                    ,"branch":self.branch
                    ,"branch_list":branch_list
                    ,"domain":self.domain
                    ,"inprogress":None
                    ,"holdlist":[customer.num for customer in all_branch_queue[self.branch][self.domain].holdlist]}


class Queue:
    def __init__(self, branch, domain):
        self.list = []
        self.count = -1
        self.domain = domain  # business, priority, personal
        self.branch = branch
        self.stopFlag = False
        self.holdlist = []

    def enqueue(self, customer):
        self.list.append(customer)
        self.count += 1
        customer.num = customer.get_queue_num(self.count)
        wait_num = all_branch_queue[self.branch][self.domain].list.index(customer)
        wait_time = wait_num*5
        return {"queuenum": customer.num,
                "wait_num": wait_num,
                "wait_time": wait_time,
                "name": customer.name,
                "phone": customer.phone,
                "domain": customer.domain,
                "branch": customer.branch
                }  # customer number

    def dequeue(self):
        return self.list.pop(0)

    def insert(self, customer, index):
        self.list.insert(index, customer)

    def check_position_queue(self, queuenum):
        for customer in all_branch_queue[self.branch][self.domain].list:
            if customer.num == queuenum:
                index = all_branch_queue[self.branch][self.domain].list.index(customer)
                wait_time = index*5
                return {"index":index,
                        'wait_time': wait_time,
                        "name": customer.name,
                        "phone": customer.phone,
                        "domain":self.domain,
                        "branch":self.branch}


def check_position_phone(branch,phonenum):
    for domain in ['business','priority','personal']:
        for customer in all_branch_queue[branch][domain].list:
            if customer.phone == phonenum:
                index = all_branch_queue[branch][domain].list.index(customer)
                wait_time = index * 5
                return {"index":index,
                         "wait_time":wait_time,
                         "name": customer.name,
                         "phone": customer.phone,
                        "domain":customer.domain,
                        "branch":branch}


def crostop(branch, domain):
    stoppedList = {}
    print(branch, domain)
    flagall = False
    flagallsingle = False
    flagsingleall = False
    flagsinglesingle = False
    if branch == 'all':
        if domain == 'all':  # all branch all domain
            for i in branch_list:
                for j in queue_type:
                    all_branch_queue[i][j].stopFlag = False if all_branch_queue[i][j].stopFlag else True
                    flagall = all_branch_queue[i][j].stopFlag
                # for k in range(counter_number[i]):
                #     all_branch_counter[i][str(k+1)].stopFlag = True
            if flagall == True:
                ret = 'Now all queues in all branches stop queuing!'
            else:
                ret = 'Now all queues in all branches continue queuing!'
            print(all_branch_queue['jurong']['personal'].stopFlag)
            return ret
        else:  # all branch single domain
            for i in branch_list:
                stoppedList[i] = {}
                all_branch_queue[i][domain].stopFlag = False if all_branch_queue[i][domain].stopFlag else True
                flagallsingle = all_branch_queue[i][domain].stopFlag
                # for k in range(counter_number[i]):
                #     if all_branch_counter[i][str(k+1)].domain == domain:
                #         all_branch_counter[i][str(k+1)].stopFlag = True

            # print(all_branch_queue['jurong']['business'].stopFlag)
            # print(all_branch_queue['jurong']['priority'].stopFlag)
            # print(all_branch_queue['jurong']['personal'].stopFlag)
            if flagallsingle == True:
                ret = 'Queue ' + domain + 'in all branches now stops queuing!'
            else:
                ret = 'Queue ' + domain + 'in all branches now starts queuing!'
            return ret
    else:
        if domain == 'all':  # single branch all domain
            stoppedList[branch] = {}
            for i in queue_type:
                all_branch_queue[branch][i].stopFlag = False if all_branch_queue[branch][i].stopFlag else True
                flagsingleall = all_branch_queue[branch][i].stopFlag
                # for k in range(counter_number[branch]):
                #     if all_branch_counter[branch][str(k+1)].domain == i:
                #         all_branch_counter[branch][str(k+1)].stopFlag = True

            # print(all_branch_queue['jurong']['business'].stopFlag)
            # print(all_branch_queue['jurong']['priority'].stopFlag)
            # print(all_branch_queue['jurong']['personal'].stopFlag)
            # print(all_branch_queue['ntu']['personal'].stopFlag)
            if flagsingleall == True:
                ret = 'All queues in ' + branch + ' branch now stops queuing!'
            else:
                ret = 'All queues in ' + branch + ' branch now starts queuing!'
            return ret
        else:  # single branch single domain
            stoppedList[branch] = {}
            print("stopflag:",all_branch_queue[branch][domain].stopFlag)
            all_branch_queue[branch][domain].stopFlag = False if all_branch_queue[branch][domain].stopFlag else True
            print(all_branch_queue[branch][domain].stopFlag)

            # for k in range(counter_number[branch]):
            #     if all_branch_counter[branch][str(k+1)].domain == domain:
            #         all_branch_counter[branch][str(k+1)].stopFlag = True
            #         stoppedList[branch].setdefault(domain,[]).append(str(k+1))
            # print(all_branch_queue['jurong']['business'].stopFlag)
            # print(all_branch_queue['jurong']['priority'].stopFlag)
            # print(all_branch_queue['jurong']['personal'].stopFlag)
            flagsinglesingle = all_branch_queue[branch][domain].stopFlag
            if flagsinglesingle == True:
                ret = 'Queue ' + domain + ' in ' + branch + ' branch now stops queuing!'
            else:
                ret = 'Queue ' + domain + ' in ' + branch + ' branch now starts queuing!'
            return ret


def croreinitiate(branch,domain):
    print(branch, domain)
    if branch == 'all':
        if domain == 'all':      # all branch all domain
            for i in branch_list:
                for j in queue_type:
                    all_branch_queue[i][j] = Queue(i,j)
                n_counter = counter_number[i]
                for k in range(n_counter):
                    all_branch_counter[i][str(k+1)].inprogress = None
            # test
            for i in branch_list:
                print('Branch: '+ i)
                for j in queue_type:
                    print(j)
                    print(all_branch_queue[i][j].list)
            output = 'Now all queues in all branches have been reinitiated!'
            return output
        else:                   # all branch single domain
            for i in branch_list:
                all_branch_queue[i][domain] = Queue(i,domain)
                for k in range(counter_number[i]):
                    if all_branch_counter[i][str(k+1)].domain == domain:
                        all_branch_counter[i][str(k+1)].inprogress = None
            # test
            for i in branch_list:
                print('Branch: '+ i)
                for j in queue_type:
                    print(j)
                    print(all_branch_queue[i][j].list)
            return 'Queue '+ domain + 'in all branches have been reinitiated!'
    else:
        if domain == 'all':     # single branch all domain
            for i in queue_type:
                all_branch_queue[branch][i] = Queue(branch,i)
                for k in range(counter_number[branch]):
                    all_branch_counter[branch][str(k+1)].inprogress = None
            # test
            for i in branch_list:
                print('Branch: '+ i)
                for j in queue_type:
                    print(j)
                    print(all_branch_queue[i][j].list)
            return 'All queues in ' + branch +' branch have been reinitiated!'
        else:                  # single branch single domain
            all_branch_queue[branch][domain] = Queue(branch,domain)
            for k in range(counter_number[branch]):
                if all_branch_counter[branch][str(k+1)].domain == domain:
                    all_branch_counter[branch][str(k+1)].inprogress = None
            # test
            for i in branch_list:
                print('Branch: '+ i)
                for j in queue_type:
                    print(j)
                    print(all_branch_queue[i][j].list)
            return 'Queue '+ domain + ' in ' + branch + ' branch has been reinitiated!'


def croview(branch,domain):
    print(branch,domain)
    items = []
    for i in all_branch_queue[branch][domain].list:
        items.append(dict(name = i.name, num = i.num))
    table = ItemTable(items)
    return table,len(items)


@app.route("/bigbank/customer/<branch>/", methods=['POST', "GET"])
def Customer(branch):
    result = {"branch": branch}
    print("--------------",branch)

    if branch in branch_list:

        if request.method == 'POST':
            output1 = ""
            if request.form.get("getqueue") == "GET QUEUE":
                phone = request.form.get('phone')
                name = request.form.get('name')
                domain = request.form.get('domain')
                if all_branch_queue[branch][domain].stopFlag == False:
                    customer_new = customer(phone, name, domain, branch)
                    result_get = all_branch_queue[branch][domain].enqueue(customer_new)
                    nl = '\n'
                    output = f"Hello {result_get['name']}, your queue number is {result_get['queuenum']} for {result_get['domain']} service in {result_get['branch']} branch."
                    output1 = f"There are {result_get['wait_num']} before you, estimated waiting time is {result_get['wait_time']} minutes."
                else:
                    output = f"Sorry, the {domain} service is stopped."
                return render_template('customer.html', output=output, output1=output1, result=result)

            elif request.form.get("checkqueue") == "Check Queue".upper():
                queuenum = request.form.get('queuenum').upper()
                phonenum = request.form.get('phonenum')
                if queuenum != "":
                    try:
                        if queuenum[0].lower() == "b":
                            domain = 'business'
                        elif queuenum[0].lower() == 'p':
                            domain = 'personal'
                        elif queuenum[0].lower() == 'v':
                            domain = 'priority'
                        result_check = all_branch_queue[branch][domain].check_position_queue(queuenum)
                        output = f"Hello {result_check['name']}, there are {result_check['index']} people before you for {result_check['domain']} service in {result_check['branch']} branch."
                        output1 = f"Your estimated waiting time is {result_check['wait_time']} minutes."
                    except:
                        output = "Invalid search, please check the information!"
                elif phonenum != "":
                    try:
                        result_check = check_position_phone(branch, phonenum)
                        output = f"Hello {result_check['name']}, there are {result_check['index']} people before you for {result_check['domain']} service in {result_check['branch']} branch."
                        output1 = f"Your estimated waiting time is {result_check['wait_time']}."
                    except:
                        output = "Invalid search, please check the information!"
                else:
                    output = "Please input your phone number or queue number!"
                return render_template('customer.html', output=output, output1=output1, result=result)

            elif request.form.get("cancelqueue") == "Cancel Queue".upper():
                queuenum = request.form.get('queuenum').upper()
                phonenum = request.form.get('phonenum')
                if queuenum != "":
                    try:
                        if queuenum[0].lower() == "b":
                            domain = 'business'
                        elif queuenum[0].lower() == 'p':
                            domain = 'personal'
                        elif queuenum[0].lower() == 'v':
                            domain = 'priority'
                        result_cancel = all_branch_queue[branch][domain].check_position_queue(queuenum)
                        del all_branch_queue[branch][domain].list[result_cancel['index']]
                        output = f"Hello {result_cancel['name']}, your queue for {result_cancel['domain']} service in {result_cancel['branch']} branch is cancelled."
                    except:
                        output = "Invalid search, please check the information!"
                elif phonenum != "":
                    try:
                        result_cancel = all_branch_queue[branch][domain].check_position_queue(queuenum)
                        del all_branch_queue[branch][domain].list[result_cancel['index']]
                        output = f"Hello {result_cancel['name']}, your queue for {result_cancel['domain']} service in {result_cancel['branch']} branch is cancelled."
                    except:
                        output = "Invalid search, please check the information!"
                else:
                    output = "Please input your phone number or queue number!"
                return render_template('customer.html', output=output, result=result)

        elif request.method == 'GET':
            return render_template('customer.html', result=result)

        return render_template("customer.html")

    else:
        return "Cannot find the branch you entered, please check again!"


@app.route("/bigbank/customeronline/", methods=['POST', "GET"])
def Customer_online():

    branch_return = {"branch":branch_list,"branch_selected":request.form.get('branch')}
    print(request.form.get('branch'))
    branch = request.form.get('branch')

    if request.method == 'POST':
        output1 = ""
        if request.form.get("getqueue") == "GET QUEUE":
            print("get queue ok")
            phone = request.form.get('phone')
            name = request.form.get('name')
            domain = request.form.get('domain')
            if all_branch_queue[branch][domain].stopFlag == False:
                customer_new = customer(phone, name, domain, branch)
                result_get = all_branch_queue[branch][domain].enqueue(customer_new)
                output = f"Hello {result_get['name']}, your queue number is {result_get['queuenum']} for {result_get['domain']} service in {branch_return['branch_selected']} branch."
                output1 = f"There are {result_get['wait_num']} before you, estimated waiting time is {result_get['wait_time']} minutes."
            else:
                output = f"Sorry, the {domain} service is stopped."
            return render_template('customer_online.html', output=output, output1=output1, branch_return=branch_return)

        elif request.form.get("checkqueue") == "Check Queue".upper():
            queuenum = request.form.get('queuenum').upper()
            phonenum = request.form.get('phonenum')
            branch_for_search = request.form.get('branch_for_search')
            if queuenum != "":
                try:
                    if queuenum[0].lower() == "b":
                        domain = 'business'
                    elif queuenum[0].lower() == 'p':
                        domain = 'personal'
                    elif queuenum[0].lower() == 'v':
                        domain = 'priority'
                    result_check = all_branch_queue[branch_for_search][domain].check_position_queue(queuenum)
                    output = f"Hello {result_check['name']}, there are {result_check['index']} people before you for {result_check['domain']} service in {branch_for_search} branch."
                    output1 = f"Your estimated waiting time is {result_check['wait_time']} minutes."
                except:
                    output = "Invalid search, please check the information!"
            elif phonenum != "":
                try:
                    result_check = check_position_phone(branch, phonenum)
                    output = f"Hello {result_check['name']}, there are {result_check['index']} people before you for {result_check['domain']} service in {branch_return['branch_selected']} branch."
                    output1 = f"Your estimated waiting time is {result_check['wait_time']} minutes."
                except:
                    output = "Invalid search, please check the information!"
            else:
                output = "Please input your phone number or queue number!"
            return render_template('customer_online.html', output=output,output1=output1, branch_return=branch_return)

        elif request.form.get("cancelqueue") == "Cancel Queue".upper():
            queuenum = request.form.get('queuenum').upper()
            phonenum = request.form.get('phonenum')
            if queuenum != "":
                try:
                    if queuenum[0].lower() == "b":
                        domain = 'business'
                    elif queuenum[0].lower() == 'p':
                        domain = 'personal'
                    elif queuenum[0].lower() == 'v':
                        domain = 'priority'
                    result_cancel = all_branch_queue[branch][domain].check_position_queue(queuenum)
                    del all_branch_queue[branch][domain].list[result_cancel['index']]
                    output = f"Hello {result_cancel['name']}, your queue for {result_cancel['domain']} service in {result_cancel['branch']} branch is cancelled."
                except:
                    output = "Invalid search, please check the information!"
            elif phonenum != "":
                try:
                    result_cancel = all_branch_queue[branch][domain].check_position_queue(queuenum)
                    del all_branch_queue[branch][domain].list[result_cancel['index']]
                    output = f"Hello {result_cancel['name']}, your queue for {result_cancel['domain']} service in {result_cancel['branch']} branch is cancelled."
                except:
                    output = "Invalid search, please check the information!"
            else:
                output = "Please input your phone number or queue number!"
            return render_template('customer_online.html', output=output, branch_return = branch_return)

    elif request.method == 'GET':
        return render_template('customer_online.html', branch_return = branch_return)

    return render_template("customer_online.html",branch_return = branch_return)


@app.route('/bigbank/counter/<branch>/<counter>/', methods=["GET","POST"])
def counter(branch, counter):
    print(counter)
    print(branch)
    counterid = counter #str
    branch = branch

    if branch in branch_list and eval(counterid) <= counter_number[branch]:

        if request.method == 'POST':

            if request.form.get('next') == 'NEXT':
                result = all_branch_counter[branch][counterid].next()
                return render_template("counter_new.html", result=result, noti="Next customer called!")

            elif request.form.get('hold') == 'HOLD':
                result = all_branch_counter[branch][counterid].hold()
                return render_template("counter_new.html", result=result, noti="Customer Successfully hold!")

            elif request.form.get('Reschedule') == 'Reschedule'.upper():
                num = request.form.get('queue_num')  # str
                result = all_branch_counter[branch][counterid].reschedule(num)
                return render_template("counter_new.html", result=result, noti="Customer {} found! Successfully rescheduled!".format(num))

            elif request.form.get('change_domain') == 'change'.upper():
                domain = request.form.get('domain')
                all_branch_counter[branch][counterid].domain = domain
                result = all_branch_counter[branch][counterid].return_info()
                return render_template("counter_new.html", result=result, noti="Domain changed successfully!")

        elif request.method == 'GET':
            result = all_branch_counter[branch][counterid].return_info()
            return render_template("counter_new.html", result=result, noti='Welcome!')

        result = all_branch_counter[branch][counterid].return_info()
        return render_template("counter_new.html", result=result)

    else:
        return "Cannot find the branch or counterid you entered, please check again!"


@app.route("/bigbank/cro/", methods=['GET', 'POST'])
def cro():
    branch_return = {"branch":branch_list,"branch_selected":request.form.get('branch')}
    if request.method == 'POST':
        branch = request.form.get('branch')
        if branch != "no_select":
            domain = request.form.get('domain')
            if request.form.get('action1') == 'STOP/CONTINUE':
                output = crostop(branch, domain)
                return render_template('cro.html', output = output,branch_return = branch_return,domain_return = domain)
            if  request.form.get('action2') == 'REINITIATE':
                output = croreinitiate(branch, domain)
                return render_template('cro.html', output = output,branch_return = branch_return,domain_return = domain)
            if request.form.get('action3') == 'VIEW':
               output,length = croview(branch, domain)
               if length != 0:
                    return render_template('cro.html', data=output, column1='Name', column2='Queue Number',branch_return = branch_return,domain_return = domain)
               else:
                    return render_template('cro.html', output='No people in this queue!',branch_return = branch_return,domain_return = domain)
        elif branch == "no_select":
            return render_template('cro.html', branch_return=branch_return, output="Please select a branch",domain_return = domain)
    elif request.method == 'GET':
        return render_template('cro.html',branch_return = branch_return,domain_return = "personal")
    return render_template("cro.html",branch_return = branch_return,domain_return = domain)


@app.route("/bigbank/display/<branch>/",methods=["GET","POST"])
def screen(branch):
    if branch in branch_list:
        inprogress={}
        for counterid, counter in all_branch_counter[branch].items():
            if counter.inprogress != None:
                inprogress[counterid]= counter.inprogress.num


        waiting_Id = {}
        for key,value in all_branch_queue[branch].items():
            for customer_info in value.list:
                get_item = waiting_Id.get(key,[])
                get_item.append(customer_info.num)
                waiting_Id[key] = get_item[:3]

        missing_id = {}
        for key,value in all_branch_queue[branch].items():
            for customer_info in value.holdlist:
                get_item = missing_id.get(key,[])
                get_item.append(customer_info.num)
                missing_id[key] = get_item

        return render_template("Screen3.html", branch=branch,inprogress = inprogress, waiting_Id = waiting_Id, missing_id=missing_id)
    else:
        return "Cannot find the branch you entered, please check again!"






if __name__ == "__main__":

    # can change settings here
    all_branch_queue = {}
    all_branch_counter = {}
    branch_list = ["jurong", "ntu", "buonavista"]
    queue_type = ["business", "priority", "personal"]
    counter_number = {"jurong":6, "ntu":6, "buonavista":10}
    
    # create all the queues and counters according to branch list and queue type
    for branch in branch_list:
    
        # create all queues
        all_branch_queue[branch] = {}
        for queue in queue_type:
            all_branch_queue[branch][queue] = Queue(branch,queue)
    
        # create all counters
        # all counter ID should be str
        all_branch_counter[branch] = {}
        n_counter = counter_number[branch]
        for i in range(n_counter):
            all_branch_counter[branch][str(i+1)] = Counter(str(i+1), random.choice(queue_type), branch)
    
    # print(all_branch_counter)
    # print(all_branch_queue)
    for j in branch_list:
        print('Branch: '+ j)
        for i in range(counter_number[j]):
            print("----")
            print("counter:{}".format(i+1))
            print(all_branch_counter[j][str(i+1)].domain)

    random_phone = []
    for i in range(36):
        random_phone.append(random.randint(10000000, 99999999))


    # print(random_phone)

    def generate_random_name(length):
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))


    random_name = []
    for i in range(36):
        random_name.append(generate_random_name(3))
    # print(random_name)

    # insert customer
    for i in range(12):
        all_branch_queue['jurong']['personal'].enqueue(customer(random_phone[i], random_name[i],
                                                                'personal', 'jurong'))
    for j in range(12, 16):
        all_branch_queue['jurong']["priority"].enqueue(customer(random_phone[j], random_name[j],
                                                                "priority", 'jurong'))
    for k in range(16, 24):
        all_branch_queue['jurong']["business"].enqueue(customer(random_phone[k], random_name[k],
                                                                "business", 'jurong'))


    all_branch_counter['jurong']['1'].domain = "personal"
    all_branch_counter['jurong']['2'].domain = "personal"
    all_branch_counter['jurong']['3'].domain = "priority"
    all_branch_counter['jurong']['4'].domain = "priority"
    all_branch_counter['jurong']['5'].domain = "business"
    all_branch_counter['jurong']['6'].domain = "business"

    all_branch_counter['jurong']['1'].next()
    all_branch_counter['jurong']['2'].next()
    all_branch_counter['jurong']['3'].next()
    all_branch_counter['jurong']['4'].next()
    all_branch_counter['jurong']['5'].next()
    all_branch_counter['jurong']['6'].next()




    # # test for counter
    # all_branch_queue['jurong']['personal'].enqueue(customer('1','zyy','personal','jurong','1'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('2', 'zj', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('3', 'hkt', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('4', 'zyc', 'personal', 'jurong','4'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('5', 'zjy', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('6', 'zyq', 'business', 'jurong','2'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('7', 'zxy', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('8', 'lyq', 'business', 'jurong','2'))
    # all_branch_queue['jurong']['personal'].enqueue(customer('9', 'zycc', 'business', 'jurong','2'))
    # all_branch_queue['jurong']['business'].enqueue(customer('h', 'zyc1', 'business', 'jurong','2'))
    # all_branch_queue['jurong']['business'].enqueue(customer('g', 'zjy1', 'business', 'jurong','2'))
    # all_branch_queue['jurong']['business'].enqueue(customer('f', 'zyq1', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['business'].enqueue(customer('d', 'zxy1', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['business'].enqueue(customer('s', 'lyq1', 'personal', 'jurong','2'))
    # all_branch_queue['jurong']['business'].enqueue(customer('a', 'zycc1', 'personal', 'jurong','2'))
    #
    # print([customer.name for customer in all_branch_queue['jurong']['personal'].list])
    # all_branch_counter['jurong']['9'].domain = "personal"
    # all_branch_counter['jurong']['8'].domain = "personal"
    #
    # all_branch_counter['jurong']['9'].next()
    # all_branch_counter['jurong']['9'].next()
    # print(all_branch_counter['jurong']['9'].inprogress.num,all_branch_counter['jurong']['9'].inprogress.name)
    # print([customer.name for customer in all_branch_queue['jurong']['personal'].list])

    # all_branch_counter['jurong']['9'].hold()
    # #all_branch_counter['jurong']['9'].reschedule("12344321")
    # print(all_branch_counter['jurong']['9'].inprogress.name,all_branch_counter['jurong']['9'].finishedlist[-1].name)
    # print([customer.name for customer in all_branch_queue['jurong']['personal'].list])
    #
    # all_branch_counter['jurong']['8'].next()
    # print(all_branch_counter['jurong']['8'].inprogress.name,all_branch_counter['jurong']['8'].finishedlist[-1].name)
    # print([customer.name for customer in all_branch_queue['jurong']['personal'].list])
    #
    # all_branch_counter['jurong']['8'].next()
    # print(all_branch_counter['jurong']['8'].inprogress.name,all_branch_counter['jurong']['8'].finishedlist[-1].name)
    # print([customer.name for customer in all_branch_queue['jurong']['personal'].list])


    
    app.run(host = 'Localhost',port = 1219, debug = False)
                
    