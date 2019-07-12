import json
import initial
from flask import Flask, request, Response
from flask.views import MethodView

import core

app = Flask(__name__)


class Error(MethodView):

    def get(self, hours):
        """ list all errors causing a inefficiency within the last hours

        :param hours: the amount of hours back you want to look for
        """
        h = int(hours)
        return Response(core.get_errors(h), content_type="application/json")

    def post(self):
        """ create an error

        :<json string message: the error message
        :<json string dst_site: the destination site
        :<json string src_site: the source site
        :<json integer amount: the amount of times the error occured
        :<json string failure_type: the failure_type, can either be transfer_failure or deletion_failure
        """

        json_data = request.data
        print(json_data)

        try:
            parameter = json.loads(json_data)
        except Exception as e:
            print('couldnt load json_data')
            print(e)
        print(parameter)

        core.add_error(message=parameter['message'], dst_site=parameter['dst_site'], src_site=parameter['src_site'], amount=parameter['amount'], failure_type=parameter['failure_type'])
        rows = session.execute('SELECT * FROM error')
        text = ''
        for row in rows:
            text += '%s %s %s %i %s \n' % (row.message, row.dst_site, row.src_site, row.amount, row.created_at)
        return text

    def put(self, error_id):
        """ update an error

        :param error_id: the id of the error you want to update
        :<json string message: the error message
        :<json string dst_site: the destination site
        :<json string src_site: the source site
        :<json integer amount: the amount of times the error occured
        :<json string failure_type: the failure_type, can either be transfer_failure or deletion_failure
        """

        json_data = request.data
        resp = ''
        parameter = json.loads(json_data)
        for key, value in parameter.items():
            try:
                resp += core.update_error(error_id, key, value)
            except Exception as e:
                return Response(e.args)
        return Response(resp, content_type="application/json")


class Action(MethodView):

    def post(self):
        """ create an action

        :<json string text: the text of the action to be taken
        """

        json_data = request.data
        parameter = json.loads(json_data)
        if "text" in parameter:
            return Response(core.add_action(parameter["text"]), content_type="application/json")
        else:
            return Response('no "text" key found, could not add account')

    def put(self, action_id):
        """ update an action

        :param action_id: the id of the action you want to update
        :<json string text: the text that you want an action to be updated to
        """

        json_data = request.data
        parameter = json.loads(json_data)
        if "text" in parameter:
            return Response(core.update_action(action_id, parameter["text"]), content_type="application/json")
        else:
            return Response('no "text" key found, could not update account')

    def get(self, action_id):
        """get the text of an action

        :param action_id: the id of the action you want the text from
        """

        if action_id is None:
            return Response(core.get_actions(), content_type="application/json")
        else:
            return Response(core.get_action(action_id), content_type="application/json")


class Issue(MethodView):

    def get(self, issue_id):
        """get the text of an issue

        :param issue_id: the id of the issue you want text from
        """

        if issue_id is None:
            return Response(core.get_issues(), content_type="application/json")
        else:
            return Response(core.get_issue(issue_id), content_type="application/json")

    def post(self):
        """create an issue

        :<json string text: the text of the issue you want to create
        """

        json_data = request.data
        parameter = json.loads(json_data)
        if "text" in parameter:
            return Response(core.add_issue(parameter["text"]), content_type="application/json")
        else:
            return Response('no "text" key found, could not add issue')

    def put(self, issue_id):
        """update an issue

        :param issue_id: the id of the issue you want to update
        :<json string text: the text that you want an issue to be updated to
        """

        json_data = request.data
        parameter = json.loads(json_data)
        if "text" in parameter:
            return Response(core.update_issue(issue_id, parameter["text"]), content_type="application/json")
        else:
            return Response('no "text" key found, could not update issue')


class Error_reason_solution(MethodView):

    def get(self, category_id):
        """get an Error_reason_solution by category_id

        :param category_id: the id of a category that you want to extract an Error_reason_solution from
        """

        if category_id is None:
            try:
                return Response(core.get_all_ers(), content_type="application/json")
            except Exception as e:
                return Response(e.args)
        else:
            return Response(core.get_ers_by_cid(category_id), content_type="application/json")

    def post(self):
        """create an Error_reason_solution

        :<json string category_id: the category_id the Error_reason_solution should be attached to
        :<json string issue_id: the issue_id that the Error_reason_solution should be attached to
        :<json string proposed_action_id: the action_id the Error_reason_solution should be attached to
        :<json boolean score: the boolean score on whether this Error_reason_solution is a valid solution or not
        :<json string affected_site: whether the affected site was the destination, source or unknown (dst_site, src_site, site_unknown)
        """

        json_data = request.data
        param = json.loads(json_data)
        if all(k in param for k in ('category_id', 'issue_id', 'proposed_action_id')):
            try:
                return Response(core.add_ers(**param), content_type="application/json")
            except Exception as e:
                return Response(e.args)

    def put(self, error_reason_solution_id):
        """update an Error_reason_solution

        :param error_reason_solution_id: the id of the Error_reason_solution you want to update

        :<json string category_id: the category_id the Error_reason_solution should be attached to
        :<json string issue_id: the issue_id that the Error_reason_solution should be attached to
        :<json string proposed_action_id: the action_id the Error_reason_solution should be attached to
        :<json boolean score: the boolean score on whether this Error_reason_solution is a valid solution or not
        :<json string affected_site: whether the affected site was the destination, source or unknown (dst_site, src_site, site_unknown)
        """

        json_data = request.data
        param = json.loads(json_data)
        try:
            return Response(core.update_ers(error_reason_solution_id, **param), content_type="application/json")
        except Exception as e:
            return Response(e.args)


errorview = Error.as_view('errorview')
app.add_url_rule('/error', methods=['POST'], view_func=errorview)
app.add_url_rule('/error/<hours>', methods=['get'], view_func=errorview)
app.add_url_rule('/error/<error_id>', methods=['put'], view_func=errorview)

actionview = Action.as_view('actionview')
app.add_url_rule('/action', methods=['POST'], view_func=actionview)
app.add_url_rule('/action/<action_id>', methods=['PUT', 'GET'], view_func=actionview)
app.add_url_rule('/action', defaults={'action_id': None}, methods=['GET'], view_func=actionview)

issueview = Issue.as_view('issueview')
app.add_url_rule('/issue', methods=['POST'], view_func=issueview)
app.add_url_rule('/issue/<issue_id>', methods=['PUT', 'GET'], view_func=issueview)
app.add_url_rule('/issue', defaults={'issue_id': None}, methods=['GET'], view_func=issueview)

ersview = Error_reason_solution.as_view('ersview')
app.add_url_rule('/error_reason_solution/<category_id>', methods=['GET'], view_func=ersview)
app.add_url_rule('/error_reason_solution', methods=['POST'], view_func=ersview)
app.add_url_rule('/error_reason_solution/<error_reason_solution_id>', methods=['PUT'], view_func=ersview)
app.add_url_rule('/error_reason_solution', defaults={'category_id': None}, methods=['GET'], view_func=ersview)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

