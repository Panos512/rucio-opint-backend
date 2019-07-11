from __future__ import division
from json import dumps, loads
import datetime
import models
import difflib

session = models.getsess('sqlite:///robi.db')


# a function to calculate string similarity
def quick_match(str1, str2):
    d = difflib.SequenceMatcher(None, str1, str2)
    return d.ratio()


# small function to turn table object into dicts, which can then be dumped to json.
def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d


def add_error_category(regexp, issue_id=None):
    error_category = models.Error_category(regular_expression=regexp)
    if issue_id is not None and session.query(models.Issue).filter_by(id=issue_id).scalar():
        error_category.issue_id = issue_id
    session.add(error_category)
    session.commit()
    return dumps(row2dict(error_category))


def get_error_categories():
    rows = session.query(models.Error_category).all()
    response = []
    for row in rows:
        response.append(row2dict(row))
    return dumps(response)


# this function needs reimplementation so that it can remap to already existing errors
def add_error(message, dst_site, src_site, failure_type, amount, category_id=None):
    error = models.Error(message=message, dst_site=dst_site, src_site=src_site, amount=amount, category_id=category_id)
    if failure_type in ['transfer-failure', 'deletion-failure']:
        error.failure_type = failure_type
    else:
        raise Exception('The given failure type: %s, is not a valid failure type, valid types are "deletion-failure" and "transfer_failure"' % failure_type)
    if not isinstance(amount, int):
        raise Exception('the value for the amount column must be an integer, the value given was: %s' % amount)
    if category_id is not None and session.query(models.Error_category).filter_by(id=category_id).scalar() is None:
        raise Exception('The given category ID: %i, does not match any error_category row.' % category_id)

    if category_id is None:
        rows = session.query(models.Error_category).all()
        matching_ratio = 0.0
        category_id = 0
        matched = False

        for index, row in enumerate(rows):
            ratio = quick_match(message, row.regular_expression)
            if ratio > 0.95 and ratio > matching_ratio:
                matching_ratio = ratio
                category_id = row.id
                print('a match was found with match ratio: %f' % matching_ratio)
                print(message + '\n' + row.regular_expression)

                if index == len(rows) - 1 and matching_ratio > 0.95:
                    if row.total_amount is None:
                        row.total_amount = amount
                    else:
                        row.total_amount += amount

                error.category_id = category_id
                matched = True

        if matched is False:
            print('new error_category being added')
            ec = loads(add_error_category(message))
            error.category_id = ec['id']

    session.add(error)
    session.commit()
    return dumps(row2dict(error))


def update_error(ID, key, value):
    if key in ['message', 'dst_site', 'src_site', 'failure_type', 'amount', 'category_id', 'status']:
        if key == 'category_id' and session.query(models.Error_category).filter_by(id=value).scalar() is None:
            raise Exception('The category id: %i is not a valid existing id' % value)
        if key == 'failure_type' and value not in ['transfer-failure', 'deletion-failure']:
            raise Exception('the failure type: %s, does not match any of the 2 available types, transfer-failure and deletion-failure' % value)
        if key == 'status' and value not in ['new', 'ongoing', 'resolved']:
            raise Exception('the status given: %s, is not an available option, valid options are: "new", "ongoing", and "resolved"' % value)
        if key == 'amount' and not isinstance(value, int):
            raise Exception('the value for the amount column must be an integer, the value given was: %s' % value)
        error = session.query(models.Error).get(ID)
        setattr(error, key, value)
        session.commit()
    else:
        raise Exception('The given key: %s, does not match any column in the error table' % key)

    return dumps(row2dict(error))


def get_errors(last_hours):
    rows = session.query(models.Error).filter(models.Error.created_at >= (datetime.datetime.now() - datetime.timedelta(hours=last_hours))).all()
    text = ''
    response = []
    for row in rows:
        response.append(row2dict(row))
        text += 'id: %i | %s | dst_site:%s | src_site:%s | failure_type:%s | amount:%i | created_at:%s \n' % (row.id, row.message, row.dst_site, row.src_site, row.failure_type, row.amount, row.created_at)
    print(text)
    return dumps(response)


def add_issue(text):
    issue = models.Issue(text=text)
    session.add(issue)
    session.commit()
    return dumps(row2dict(issue))


def get_issue(ID):
    return dumps(row2dict(session.query(models.Issue).get(ID)))


def get_issues():
    rows = session.query(models.Issue).all()
    response = []
    for row in rows:
        response.append(row2dict(row))
    return dumps(response)


def update_issue(ID, text):
    issue = session.query(models.Issue).get(ID)
    issue.text = text
    session.commit()
    return dumps(row2dict(issue))


def add_action(text):
    action = models.Action(text=text)
    session.add(action)
    session.commit()
    return dumps(row2dict(action))


def get_action(ID):
    return dumps(row2dict(session.query(models.Action).get(ID)))


def get_actions():
    rows = session.query(models.Action).all()
    response = []
    for row in rows:
        response.append(row2dict(row))
    return dumps(response)


def update_action(ID, text):
    action = session.query(models.Action).get(ID)
    action.text = text
    session.commit()
    return dumps(row2dict(action))


def get_all_ers():
    rows = session.query(models.Error_reason_solution).all()
    response = []
    for row in rows:
        response.append(row2dict(row))
    return dumps(response)


def get_ers(ID):
    return dumps(row2dict(session.query(models.Error_reason_solution).get(ID)))


def get_ers_by_cid(category_id):
    dis = session.query(models.Error_reason_solution).filter(models.Error_reason_solution.category_id == category_id).group_by(models.Error_reason_solution.proposed_action_id).all()
    for row in dis:
        temp = session.query(models.Error_reason_solution).filter(models.Error_reason_solution.category_id == category_id).filter(models.Error_reason_solution.proposed_action_id == row.proposed_action_id)
        total = 0
        successes = 0
        for obj in temp:
            total += 1
            if obj.score is True:
                successes += 1
        row.probability = 100 * (successes / total)

    session.commit()

    response = []
    for row in dis:
        response.append(row2dict(row))
    return dumps(response)


def add_ers(category_id, issue_id, proposed_action_id, score=False, affected_site='site_unknown'):
    ers = models.Error_reason_solution()
    if session.query(models.Error_category).filter_by(id=category_id).scalar() is not None:
        ers.category_id = category_id
    else:
        raise Exception('The category id: %i is not a valid existing id' % category_id)
    if session.query(models.Issue).filter_by(id=issue_id).scalar() is not None:
        ers.issue_id = issue_id
    else:
        raise Exception('the issue id: %i is not a valid existing id' % issue_id)
    if session.query(models.Action).filter_by(id=proposed_action_id).scalar() is not None:
        ers.proposed_action_id = proposed_action_id
    else:
        raise Exception('the proposed_action_id: %i is not a valid existing id' % proposed_action_id)
    if score is True or score is False:
        ers.score = score
    else:
        raise Exception('the given score: %s is not a valid boolean value, use True or False' % score)
    if affected_site in ['site_unknown', 'dst_site', 'src_site']:
        ers.affected_site = affected_site
    else:
        raise Exception('the given affected_site: %s, is not a valid value, only these options are valid: ["site_unknown", "dst_site", "src_site"]' % affected_site)

    # calculate the probability
    successes = session.query(models.Error_reason_solution).filter(models.Error_reason_solution.category_id == category_id).filter(models.Error_reason_solution.score is True).count()
    total = session.query(models.Error_reason_solution).filter(models.Error_reason_solution.category_id == category_id).count()
    probability = (successes / total) * 100
    ers.probability = probability

    session.add(ers)
    session.commit()
    return dumps(row2dict(ers))


def update_ers(ID, **kwargs):
    ers = session.query(models.Error_reason_solution).get(ID)
    for key, value in kwargs.items():
        if key in ['proposed_action_id', 'real_solution_id']:
            if session.query(models.Action).filter_by(id=value).scalar() is not None:
                setattr(ers, key, value)
            else:
                raise Exception('The %s column does not contain the id: %i' % (key, value))
        elif key == 'category_id':
            if session.query(models.Error_category).filter_by(id=value).scalar() is not None:
                setattr(ers, key, value)
            else:
                raise Exception('The %s column does not contain the id: %i' % (key, value))
        elif key == 'issue_id':
            if session.query(models.Issue).filter_by(id=value).scalar() is not None:
                setattr(ers, key, value)
            else:
                raise Exception('The %s column does not contain the id: %i' % (key, value))
        elif key == 'score':
            if value is True or value is False:
                setattr(ers, key, value)
            else:
                raise Exception('the score key is a boolean type, the given value: %s, is not boolean, use True or False' % (value))
        elif key == 'probability':
            if value <= 100 and value >= 0:
                setattr(ers, key, value)
            else:
                raise Exception('the given probability: %f is not a valid percentage' % (value))
        elif key == 'affected_site':
            if value in ['dst_site', 'src_site', 'site_unknown']:
                setattr(ers, key, value)
            else:
                raise Exception('the given value: %s for the affected site is not one of the acceptable values of ["dst_site", "src_site", "site_unknown"]' % (value))
        else:
            raise Exception('the given key: %s does not match any column' % (key))
    session.commit()
    return dumps(row2dict(ers))
