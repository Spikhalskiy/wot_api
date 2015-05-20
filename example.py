from wot import *

__author__ = 'Dmitry Spikhalskiy <dmitry@spikhalskiy.com>'

KEY=""

report = wot_reports_for_domains("google.com", KEY)
print parse_attributes_for_report(report)

report = wot_reports_for_domains(["yahoo.com"], KEY)
print parse_attributes_for_report(report["yahoo.com"])
