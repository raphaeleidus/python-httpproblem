import json
import traceback
import sys

if sys.version_info[0] > 2:
    import http.client as httplib
else:
    import httplib

SERIALIZE_METHOD = json.dumps
WITH_TRACEBACK = False


def set_serialize_function(method):
    """
    Set the method to use to serialize a dict into a json string
    :param method: the method to use
    :type method: func
    """
    global SERIALIZE_METHOD
    SERIALIZE_METHOD = method


def activate_traceback():
    global WITH_TRACEBACK
    WITH_TRACEBACK = True


def deactivate_traceback():
    global WITH_TRACEBACK
    WITH_TRACEBACK = False


class Problem(Exception):
    def __init__(self, status=None, title=None, detail=None, type=None, instance=None, **kwargs):
        """
        Problem exception

        :param status: The HTTP status code generated by the origin server for this occurrence of the problem.
        :type status: int
        :param title: A short, human-readable summary of the problem type.  It SHOULD NOT change from occurrence to
                      occurrence of the problem, except for purposes of localisation.
        :type title: str
        :param detail: An human readable explanation specific to this occurrence of the problem.
        :type detail: str
        :param type: An absolute URI that identifies the problem type.  When dereferenced, it SHOULD provide
                     human-readable documentation for the problem type (e.g., using HTML).  When this member is not
                     present its value is assumed to be "about:blank".
        :type: type: str
        :param instance: An absolute URI that identifies the specific occurrence of the problem.  It may or may not
                         yield further information if dereferenced.
        :type instance: str
        """
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type
        self.instance = instance
        self.kwargs = kwargs

    def to_dict(self, with_traceback=None):
        """
        Transforms the Problem exception into a dict

        :param with_traceback: if True, the last exception traceback will be included
        :type with_traceback: bool
        :return the problem in dict form
        :rtype dict
        """
        if with_traceback is None:
            with_traceback = WITH_TRACEBACK
        if with_traceback:
            return problem(self.status, self.title, self.detail, self.type, self.instance,
                           traceback=traceback.format_exc(), **self.kwargs)
        else:
            return problem(self.status, self.title, self.detail, self.type, self.instance,
                           **self.kwargs)

    def to_http_response(self, with_traceback=None):
        """
        Transforms the Problem exception into an http response with a json body

        :param with_traceback: if True, the last exception traceback will be included
        :type with_traceback: bool
        :return the problem in an AWS lambda compatible http representation with json body
        :rtype dict
        """
        if with_traceback is None:
            with_traceback = WITH_TRACEBACK
        if with_traceback:
            return problem_http_response(self.status, self.title, self.detail, self.type, self.instance,
                                         traceback=traceback.format_exc(), **self.kwargs)
        else:
            return problem_http_response(self.status, self.title, self.detail, self.type, self.instance,
                                         **self.kwargs)

    def __str__(self):
        return str(self.to_dict(with_traceback=False))

    def __repr__(self):
        return str(self)


def problem(status=None, title=None, detail=None, type=None, instance=None, **kwargs):
    """
    Returns a dict with the problem fields sanitized

    :param status: The HTTP status code generated by the origin server for this occurrence of the problem.
    :type status: int
    :param title: A short, human-readable summary of the problem type.  It SHOULD NOT change from occurrence to
                  occurrence of the problem, except for purposes of localisation.
    :type title: str
    :param detail: An human readable explanation specific to this occurrence of the problem.
    :type detail: str
    :param type: An absolute URI that identifies the problem type.  When dereferenced, it SHOULD provide
                 human-readable documentation for the problem type (e.g., using HTML).  When this member is not
                 present its value is assumed to be "about:blank".
    :type: type: str
    :param instance: An absolute URI that identifies the specific occurrence of the problem.  It may or may not
                     yield further information if dereferenced.
    :type instance: str
    :return the problem in dict form
    :rtype dict
    """
    problem_dict = {}
    if status:
        problem_dict['status'] = int(status)
        if (not title or title == 'about:blank') and status in httplib.responses:
            problem_dict['title'] = httplib.responses[status]
    if title:
        problem_dict['title'] = str(title)
    if detail:
        problem_dict['detail'] = str(detail)
    if type:
        problem_dict['type'] = str(type)
    if instance:
        problem_dict['instance'] = str(instance)
    problem_dict.update(kwargs)
    return problem_dict


def problem_http_response(status=None, title=None, detail=None, type=None, instance=None,
                          headers=None, **kwargs):
    """
    Returns the problem as a dict in an AWS lambda compatible http representation with a json body

    :param status: The HTTP status code generated by the origin server for this occurrence of the problem.
    :type status: int
    :param title: A short, human-readable summary of the problem type.  It SHOULD NOT change from occurrence to
                  occurrence of the problem, except for purposes of localisation.
    :type title: str
    :param detail: An human readable explanation specific to this occurrence of the problem.
    :type detail: str
    :param type: An absolute URI that identifies the problem type.  When dereferenced, it SHOULD provide
                 human-readable documentation for the problem type (e.g., using HTML).  When this member is not
                 present its value is assumed to be "about:blank".
    :type: type: str
    :param instance: An absolute URI that identifies the specific occurrence of the problem.  It may or may not
                     yield further information if dereferenced.
    :type instance: str
    :param headers: Dict of headers that needs o be added to the response. If no Content-Type is present,
                    application/problem+json is added
    :type headers: dict
    :return the problem in an AWS lambda compatible http representation with a json body
    :rtype dict
    """
    body = problem(status, title, detail, type, instance, **kwargs)
    if not headers:
        headers = {}
    has_content_type = False
    for header in headers:
        if header.lower() == 'content-type':
            has_content_type = True
    if not has_content_type:
        headers['Content-Type'] = 'application/problem+json'

    return {
        'statusCode': status,
        'body': SERIALIZE_METHOD(body),
        'headers': headers
    }
