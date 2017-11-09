#!/usr/bin/env python3
import requests


def notify(message, subject):
    mailer(subject, message)


def mailer(subject, message):
    return requests.post("https://api.mailgun.net/*******",
                         auth=("api", "*******"),
                         data={"from": "noreply@mexample.com",
                               "to": "******",
                               "subject": subject,
                               "text": message})
