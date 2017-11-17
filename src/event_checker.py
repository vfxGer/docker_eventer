#!/usr/bin/env python3
import time
from collections import Counter
from pprint import pformat
import datetime

import docker

import notifier

MAX_NOTIFY_TIME = 60


def notify(events):
    message = ""
    message += "\n%d events\n" % len(events)
    message += pformat(Counter(row['Action'] for row in events))
    message += "\n"
    message += pformat(events)
    subject = "[DOCKER_EVNETS] %d docker events\n" % len(events)
    print("Sending e-mail %s", subject)
    notifier.notify(message, subject)


def run():
    client = docker.from_env()
    while True:
        for event in client.events(decode=True):
            notify([event])
            break
        since = datetime.datetime.now()
        # Do not want to bombard the e-mailer with messages so sleeping
        print("Sleeping for %d seconds" % MAX_NOTIFY_TIME)
        time.sleep(MAX_NOTIFY_TIME)
        print("Woke")
        until = datetime.datetime.now()
        notify([event for event in client.events(since=since, until=until, decode=True)])


def main():
    run()


if __name__=="__main__":
    main()
