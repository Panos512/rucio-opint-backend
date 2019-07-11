from models import getsess
from models import Issue, Error_category, Action, Error_reason_solution
session = getsess('sqlite:///robi.db')

lissu = []
acts = []
mylist = []


# This with open clause is a generalized txt file with proper format to sql database parser,
# can be used in the future to create a database with same formatting as knowledged_db.txt
with open('initialdata.txt') as f:
    for cnt, line in enumerate(f):
        s = line.split(';')
        s[2] = s[2].replace("\n", "")
        if s[1] not in lissu:
            lissu.append(s[1])
            session.add(Issue(text=s[1]))
        if s[2] not in acts:
            acts.append(s[2])
            session.add(Action(text=s[2]))
        session.commit()
        myres = session.query(Issue).all()
        for row in myres:
            if s[1] == row.text:
                session.add(Error_category(issue_id=row.id, total_amount=0, regular_expression=s[0]))
        session.commit()
        issresult = session.query(Issue).all()
        errresult = session.query(Error_category).all()
        actresult = session.query(Action).all()
        for err in errresult:
            for iss in issresult:
                for act in actresult:
                    if [s[0], s[1], s[2]] not in mylist and s[0] == err.regular_expression and s[1] == iss.text and s[2] == act.text:
                        mylist.append([s[0], s[1], s[2]])
                        session.add(Error_reason_solution(category_id=err.id, proposed_action_id=act.id, issue_id=iss.id, probability=80, score=1))
session.commit()
result = session.query(Issue).all()
for row in result:
    print(row.text, row.id)
result = session.query(Error_category).all()
for row in result:
    print(row.regular_expression, row.id)
result = session.query(Action).all()
for row in result:
    print(row.text, row.id)
result = session.query(Error_reason_solution).all()
for row in result:
    print(vars(row))
