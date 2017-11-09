#Docker Event
##The Problem
I had a problem recently. I had a couple Docker containers on one machine 
for a personal project which was a django web app called 
[issueinfinity.com](https://www.issueinfinity.com). 
One of the containers, that was doing some image manipulation, kept 
crashing and I did not know until I logged into the machine and looked at it
 using `docker ps`. So I wanted an e-mail notification if any of my 
 containers stopped or if anything happened to them. 
##The Command
I discovered a command `docker events`. This is a very handy command to see what has 
 happened to your docker containers.
 
To see what has happened to your containers in the last hour you can run:

    docker events --format {{json .}} --since "1h" --until "0s"
    
The `--since 1h` simply means get everything since an hour ago.

The `--until 0s` means until 0 seconds ago, without the `--until` the command
 will just continually stream docker events.
 
The `--format "{{json .}}"` argument outputs the events as 
[JSON lines](http://jsonlines.org) which basically means a JSON document for
 every event.

As well as the above you can add filters to the events like

    docker events --filter 'container=test' --filter 'event=stop'

This will output any stop event on the test container. For more about the 
filters and more details on the other the arguments see the 
[official docker docs](https://docs.docker.com/engine/reference/commandline/events)

##The Python Script
So now we have enough to create a Python script:
```python
import sys
import subprocess
import time
import json
from collections import Counter
from pprint import pprint, pformat

from notifier import notify


def run():
    proc = subprocess.Popen('docker events --format "{{json .}}" --since "1h" --until "0s"',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, shell=True)

    retcode = proc.poll()
    wait_time = 0.1
    while retcode is None:
        time.sleep(wait_time)
        retcode = proc.poll()
    res = proc.stdout.read()
    res = res.decode("utf-8")
    event_data = []
    for line in res.split("\n"):
        line = line.strip()
        if line:
            event_data.append(json.loads(line))
            pprint(event_data[-1])
            print("-"*5)
    if event_data:
        message = ""
        message += "\n%d events\n" % len(event_data)
        message += pformat(Counter(row['Action'] for row in event_data))
        message += "\n"
        message += pformat(event_data)
        subject = "[DOCKER_EVENTS] %d docker events\n" % len(event_data)
        notify(message, subject)
        print("e-mail sent")


def main(_):
    while True:
        run()
        print("Now sleeping for an hour")
        time.sleep(60*60)



if __name__=="__main__":
    main(sys.argv[1:])
```

Here I am simply running the docker event in a subprocess. 
I am the putting the stderr of the process into stdout and putting 
stdout into a temporary file. The temporary file avoids issues with 
buffer overflows. Then the script sends an e-mail(not shown) if there is 
any events 
and parses the json to create a summary of the work.

Although this works the subprocess adds overhead so to simplify the 
solution we can just use the docker python api.

##Using the Docker Python API
Simply run `pip install docker`
to install the python docker api.

Now the script becomes simpler:

```python
import sys
import time
from collections import Counter
from pprint import pprint, pformat
import datetime

from notifier import notify
import docker


def run():
    client = docker.from_env()
    until = datetime.datetime.utcnow()
    since = until - datetime.timedelta(hours=1)
    event_data = []
    for event in client.events(since=since, until=until, decode=True):
        event_data.append(event)
        pprint(event_data[-1])
        print("-" * 5)
    if event_data:
        message = ""
        message += "\n%d events\n" % len(event_data)
        message += pformat(Counter(row['Action'] for row in event_data))
        message += "\n"
        message += pformat(event_data)
        subject = "%d docker events\n" % len(event_data)
        notify(message, subject)
        print("e-mail sent")


def main(_):
    while True:
        run()
        print("Now sleeping for an hour")
        time.sleep(60*60)


if __name__=="__main__":
    main(sys.argv[1:])
```

The docker client is created from the environment with `docker.from_env`, 
which means it works like the command line would. 
The client.events function works very similar to the command line version. 
The `decode=True` means the output are python dictionaries.
##I Put Docker in your Docker
Now I could put this python script into supervisord and run on the docker 
machine but if we are using docker why not use docker. 
To get this working in a docker container we need to install the docker 
client inside the container. The simplest way to do this is to run  
`apt-get install docker.io` in the Dockerfile. 
Then to make it work we need to mount the docker socket into the container 
with `/var/run/docker.sock:/var/run/docker.sock`.
You can see this in the docker-compose.yml file.

And voila a docker event notifier. 

Still to do:
* make it more configurable
* make it send notification on the first event and not just once an hour
