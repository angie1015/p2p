import time

from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'the random string'
db = SQLAlchemy(app)


#################### All the databases ################################
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    credentials = db.Column(db.String(50))
    image = db.Column(db.String(50))
    about = db.Column(db.String(50))
    skills = db.Column(db.String(50))
    github = db.Column(db.String(50))
    linkedin = db.Column(db.String(50))
    score = db.Column(db.Integer, default=500)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(50))
    shortdescription = db.Column(db.String(200))
    detaileddescription = db.Column(db.String(200))
    pay = db.Column(db.Integer)
    tags=db.Column(db.String(50))
    status = db.Column(db.Integer, default='Pending')
    askedby_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    askedby_name = db.Column(db.String(200))
    askedby_img = db.Column(db.String(200))


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    image = db.Column(db.String(50))
    description = db.Column(db.String(200))
    pay = db.Column(db.Integer)
    questionID = db.Column(db.Integer, db.ForeignKey('question.id'))


class Assigned(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    createdbyId = db.Column(db.Integer, db.ForeignKey('user.id'))
    questionID = db.Column(db.Integer, db.ForeignKey('question.id'))
    assignedto_ID = db.Column(db.Integer, db.ForeignKey('user.id'))
    # To display the name of user and question in history section
    questionName = db.Column(db.String(200))
    assignedName = db.Column(db.String(200))

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer)
    time = db.Column(db.Integer)
    fromuser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    touser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # To display the name of user and question in history section
    from_username = db.Column(db.String(50))
    to_username = db.Column(db.String(50))


class Footsteps(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    url = db.Column(db.String(50))

################################  REGISTER  LOGIN  LOGOUT ROUTES ###################################

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        data = User.query.filter_by(username=username,
                                    password=password).first()

        if data is not None:
            session['user'] = data.id
            print(session['user'])
            return redirect(url_for('index'))

        return render_template('incorrectLogin.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(username=request.form['username'],
                        password=request.form['password'],

                        skills=request.form['skills'], image=request.form['image'], about=request.form['about'],
                        github=request.form['github'], linkedin=request.form['linkedin'])

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))




######################################### CRUD Model ####################################

@app.route('/index')
def index():
    user_id = session['user']
    username = User.query.get(session['user']).username
    print('*' * 30)
    print('YOU ARE LOGGINED IN AS', username)  # All those print statments are for testing purpose. Ignore them
    print('*' * 30)
    flash("welcome {}".format(username))
    today = time.strftime("%m/%d/%Y")
    showQuestion = Question.query.order_by(desc(Question.id))
    meeting =  Meeting.query.all()
    print('meeting',meeting)
    return render_template('index.html', showQuestion=showQuestion, meeting=meeting, interview={},
                           today=today)


# Route to add a new question
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        user_id = session['user']
        getTagsArrays=request.form.getlist('tags')
        t=''
        for eachTag in getTagsArrays:
            t += "      "
            t += eachTag
            t += "   |   "
        print('request.form',request.form)
        print(user_id)
        new_question = Question(question=request.form['question'],
                                shortdescription=request.form['shortdescription'],
                                detaileddescription=request.form['detaileddescription'],
                                pay=request.form['rangeInput'], tags=t, askedby_id=user_id,
                                askedby_name=User.query.get(user_id).username,
                                askedby_img=User.query.get(user_id).image)
        flash("New question has been succesfully added")
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('index'))

    else:
        return render_template('AddQuestion.html')


# In the index.html file, the entire question db will be displayed
# When the user clicks on view more btn, they would be redirected to the ParticularQuestion url
@app.route('/ParticularQuestion', methods=['GET', 'POST'])
def ParticularQuestion():
    if request.method == 'POST':
        id = request.args['questionid']
        username = User.query.get(session['user']).username
        image=User.query.get(session['user']).image
        print('question id is', id)
        new_response = Response(username=username,
                                description=request.form['description'],
                                pay=request.form['pay'], questionID=id, image=image)
        db.session.add(new_response)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        args = request.args
        print('args in q url is', args)
        questionid = Question.query.get(args['questionid'])
        # To check whether the user view the q is same as the user who raised that question. If True, then display assign tag

        isSamePerson =False
        if args['user']==User.query.get(session['user']).username:
            isSamePerson = True
        print(isSamePerson)
        user = questionid.askedby_id
        img = User.query.get(user).image
        username = User.query.get(user).username
        response = Response.query.filter_by(questionID=questionid.id).all()
        print("response is", response)
        return render_template('ParticularQuestion.html', question=questionid, username=username, img=img,
                               response=response,
                               isSamePerson=isSamePerson)


################################ My Questions Section ###################################

@app.route('/DoubtSolved')
def DoubtSolved():
    id = request.args
    print(id)
    q = Question.query.get(id)
    print(q.status)
    q.status = 'Solved'
    print(q.status)
    db.session.commit()
    return render_template('DoubtSolved.html', q=q)


@app.route('/Delete')
def Delete():
    id = int(request.args['id'])
    print('to be deleted ', id)
    obj = Question.query.filter_by(id=id).one()
    db.session.delete(obj)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/assign')
def assign():
    qid = int(request.args['qid'])
    assignedto_ID = int(request.args['userid'])
    createdbyId = session['user']
    print('to be assign ', assignedto_ID)
    obj = Question.query.filter_by(id=qid).one()
    print('obj is', obj)
    print(obj.question)
    obj.status = 'Assigned'
    assign = Assigned(createdbyId=createdbyId, questionID=qid, assignedto_ID=assignedto_ID,
                      assignedName=request.args['assignedName'], questionName=request.args['questionName'])


    u = User.query.get(createdbyId)
    topay = User.query.get(assignedto_ID-1)
    print('mentor is  ', topay,u)
    if u.score > 0:
        flash("Payment successully made")
        print(u.score)
        u.score = u.score - int(obj.pay)
        topay.score += int(obj.pay)

    db.session.add(assign)
    db.session.commit()
    print('************* STATUS CHANGED TO ASSIGNED **************')
    return redirect(url_for('index'))

####################################  OTHER ROUTES  #########################################


@app.route('/payment')
def payment():
    details = request.args
    print(details)
    mentor = str(details['doubt'])
    print('m is', mentor)
    amt = details['amount']
    user_id = session['user']
    u = User.query.get(user_id)
    mentor = User.query.filter_by(username=mentor).first()
    topay = User.query.get(mentor.id)
    print('mentor is  ', topay)
    if u.score > 0:
        flash("Payment successully made")
        print(u.score)
        u.score = u.score - int(amt)
        topay.score += int(amt)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('4o4.html', display_content="Transcation unsuccessul due to lack of credits")


######################################### Routes to display ####################################

@app.route('/scoreBoard')
def scoreBoard():
    rank_user = User.query.order_by(desc(User.score))
    t=time.strftime("%d")
    print(t)
    diff=int(30-int(t))
    return render_template('scoreBoard.html', rank_user=rank_user,days=diff)


# Shows the user profile of the user who is currently logged in
@app.route('/profile')
def profile():
    userid = session['user']
    print('userid is', userid)
    Profile = User.query.filter_by(id=userid).one()
    return render_template('profile.html', i=Profile)


# Shows the list of tasks assigned to and by a particular user
@app.route('/history', methods=['GET', 'POST'])
def history():
    user_id = session['user']
    if request.method == 'POST':
        print('request.form123', request.form)
        date = request.form['date']
        time = request.form['time']
        fromuser_id = user_id
        qid=request.form['qid']

        a=Assigned.query.filter_by(questionID=qid).all()[0]

        touser_id=a.assignedto_ID-1
        print('aaaa', touser_id)
        from_username=User.query.get(fromuser_id).username
        to_username = User.query.get(touser_id).username

        new_response = Meeting(date=date, time=time,fromuser_id=fromuser_id,touser_id=touser_id,
                                 to_username=to_username, from_username=from_username)
        print('new_response')
        print('new_response',new_response)
        db.session.add(new_response)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        askedByme = Assigned.query.filter_by(createdbyId=user_id).all()
        toBeDoneByMe = Assigned.query.filter_by(assignedto_ID=user_id).all()
        myQuestion = Question.query.filter_by(askedby_id=user_id).all()
        print(myQuestion)
        return render_template('history.html', askedByme=askedByme, toBeDoneByMe=toBeDoneByMe, myQuestion=myQuestion,
                               user_id=user_id)


# To display all the questions asked by the particular user
'''
@app.route('/myQuestion')
def myQuestion():
    user_id = session['user']
    myQuestion = Question.query.filter_by(askedby_id=user_id).all()
    print(myQuestion)
    return render_template('myQuestion.html', myQuestion=myQuestion, user_id=user_id)
'''
@app.route('/footsteps',methods=['GET', 'POST'])
def footsteps():
    if request.method == 'POST':

        new_question = Footsteps(name=request.form['name'],
                                url=request.form['url'] )
        flash("New roadmap has been succesfully added")
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('index'))

    else:
        footsteps = Footsteps.query.all()
        return render_template('footsteps.html',footsteps=footsteps)



######################################### MAIN ####################################


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
