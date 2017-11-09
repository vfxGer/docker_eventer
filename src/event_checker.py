import sys
import time
from collections import Counter
from pprint import pprint, pformat
import datetime

import arrow

from notifier import notify
import docker


def run():
    client = docker.from_env()
    until = datetime.datetime.utcnow()
    since = until - datetime.timedelta(hours=1)
    event_data = []
    for event in client.events(since=since, until=until, decode=True):
        event_data.append(event)
        event_data[-1]['human_time'] = arrow.get(event_data[-1]['time']).humanize()
        pprint(event_data[-1])
        print("-" * 5)
    if event_data:
        message = ""
        message += "\n%d events\n" % len(event_data)
        message += pformat(Counter(row['Action'] for row in event_data))
        message += "\n"
        message += pformat(event_data)
        subject = "[ISSUEI] %d docker events\n" % len(event_data)
        notify(message, subject)
        print("e-mail sent")


def main():
    while True:
        run()
        print("Now sleeping for an hour")
        time.sleep(60*60)


if __name__=="__main__":
    main()
