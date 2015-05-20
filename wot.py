import collections
import json
import urllib
import urllib2
from concurrent.futures import ThreadPoolExecutor

__author__ = 'Dmitry Spikhalskiy <dmitry@spikhalskiy.com>'

API_VERSION = 0.4
REPUTATION_ENDPOINT = "http://api.mywot.com/" + str(API_VERSION) + "/public_link_json2"
CHUNK_SIZE = 100
RETRY_COUNT = 5


def wot_reports_for_domains(domains, key, threads_count=1):
    assert isinstance(domains, collections.Iterable)

    if isinstance(domains, str):
        return __get_report_for_one_domain(domains, key)
    elif isinstance(domains, collections.Iterable):
        return __get_reports_for_domains_collection(domains, key, threads_count)


def __get_report_for_one_domain(domain, key):
    assert isinstance(domain, str)
    report_dict = __get_for_domains([domain], key, RETRY_COUNT)
    return report_dict.values()[0]


def __get_reports_for_domains_collection(domains, key, threads_count=1):
    executor = ThreadPoolExecutor(threads_count)
    reports_lists_iterator = executor.map(lambda chunk: __get_for_domains(chunk, key, RETRY_COUNT),
                                          __split(domains, CHUNK_SIZE))

    maps_list = list(reports_lists_iterator)

    return __merge_dicts(*maps_list)


def __get_for_domains(domains_for_one_request, key, max_tries):
    """
    Portion for one request
    """
    assert isinstance(domains_for_one_request, (collections.Iterable, collections.Sized))

    params = {"key": key, "hosts": "".join(map(lambda domain: domain + "/", domains_for_one_request))}
    reputation_query_string = urllib.urlencode(params)
    request_string = REPUTATION_ENDPOINT + '?' + reputation_query_string
    reputation_request = urllib2.Request(request_string)

    try:
        response = urllib2.urlopen(reputation_request).read()
        try:
            parsed_response = json.loads(response)
            assert isinstance(parsed_response, dict)
            if len(parsed_response) == 0:
                print "Got empty response for request %s with length %s. Maybe it's too long" \
                      % (request_string, len(request_string))
        except ValueError as e:
            print "Non parsable response:%s for request:%s" % (response, request_string)
            print e
            return dict()
        return parsed_response
    except urllib2.HTTPError as e:
        print e
        if max_tries > 1:
            return __get_for_domains(domains_for_one_request, key, max_tries - 1)
        else:
            raise e
    except urllib2.URLError as e:
        print "URL error %s during request %s" % (e, request_string)
        if max_tries > 0:
            return __get_for_domains(domains_for_one_request, key, max_tries - 1)
        else:
            raise e


def __split(domains, chunk_size):
    assert chunk_size > 0
    result = []
    part = []
    for domain in iter(domains):
        part.append(domain)
        assert len(part) <= chunk_size
        if len(part) == chunk_size:
            result.append(part)
            part = []
    if len(part) > 0:
        result.append(part)

    return result


def __merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
