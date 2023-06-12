from flask import Flask, request, Response
from flask_cors import CORS
import os
import dotenv
from slack import WebClient
from slack.errors import SlackApiError
import json
import time
import threading
from datetime import datetime
import pytz
from calendar import day_name

# Flask app configuration
app = Flask(__name__)
CORS(app)

# Loading environment variables from .env by default
dotenv.load_dotenv()

# Initializing the Slack app client
client = WebClient(token=os.environ['SLACK_TOKEN'])


def ratelimit_breaker(f):
    """Decorator function to handle the rate limit error"""

    def wrapper(*args, **kwargs):
        while True:
            try:
                response = f(*args, **kwargs)
                break
            except SlackApiError as e:
                if e.response["error"] == "ratelimited":
                    # The `Retry-After` header will tell you how long to wait before retrying
                    delay = int(e.response.headers['Retry-After'])
                    print(f"Rate limited. Retrying in {delay} seconds")
                    time.sleep(delay)
                else:
                    # other errors
                    raise e
        return response

    return wrapper


@ratelimit_breaker
def channel_users(channel: str):
    return client.conversations_members(channel=channel)


@ratelimit_breaker
def send_chat_message(channel: str, text: str, thread_ts: str | None = None):
    """Function to send a message to a channel

    Keyword arguments:
    channel -- Id of the channel in which the message is to be sent
    text -- Message to be sent
    thread_ts -- Thread id of the message to which the message is to be sent

    Returns: SlackResponse object
    """

    # sending the message to the channel
    if thread_ts:
        return client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts
        )

    return client.chat_postMessage(
        channel=channel,
        text=text
    )


@ratelimit_breaker
def send_chat_message_ephemeral(channel: str, user: str, text: str):
    """Function to send a message to a channel

    Keyword arguments:
    channel -- Id of the channel in which the message is to be sent
    user -- Id of the user to whom the message is to be sent
    text -- Message to be sent

    Returns: SlackResponse object
    """

    # sending the message to the channel
    return client.chat_postEphemeral(
        channel=channel,
        user=user,
        text=text
    )


def tag_group(user: str, channel: str, positions: list[str], message: str):
    """Function to tag a specific group

    Keyword arguments:
    user -- Id of the person invoking the /tag command
    channel -- Id of the channel in which the /tag command was invoked
    position -- Name of the group in the data.json file -> ctm, exec, advisor
    message -- Message to be sent to each individual of the group
    """

    # get the list of users in the channel
    channel_members_ids = channel_users(channel)['members']

    # Load the data of group members from data.json
    with open('data.json') as f:
        data = json.load(f)

    real_names = []  # keep track of real names of tagged people
    user_not_in_channel = []  # keep track of errors
    tags = ""  # keep track of tags

    for position in positions:
        members = []  # keep track of members in the channel
        if position not in data:
            send_chat_message_ephemeral(
                channel, user,
                f"Hey <@{user}>!\nLooks like there is no one in {position}s in this channel")
            return
        for member in data[position]:
            if member["id"] in channel_members_ids:
                members.append(member)
            else:
                user_not_in_channel.append(member["real_name"])

        for member in members:
            tags += f"<@{member['id']}> "
            real_names.append(member["real_name"])

        if len(tags) == 0:
            send_chat_message_ephemeral(
                channel, user,
                f"Hey <@{user}>!\nLooks like there is no one in {position}s in this channel")

    # configuring the message to be sent to the channel
    response = send_chat_message(
        channel,
        message
    )
    message_ts = response['ts']
    send_chat_message(
        channel,
        f"{tags}\n\ntagged by: <@{user}>",
        thread_ts=message_ts
    )

    # configuring the stats message for the /tag user
    stats = f"Hey <@{user}>!\n"
    if len(real_names):
        stats += f"I tagged {', '.join(real_names)} for you!"
    else:
        stats += "No one was tagged!!"
    if len(user_not_in_channel):
        stats += f"```Not in channel:\n{', '.join(user_not_in_channel)}```"
    stats += f"\nYou Sent:\n{message}"

    # sending the stats message to the /tag user
    send_chat_message_ephemeral(
        channel, user, stats
    )
    return


def subscribe(req, unsubscribe=False):
    """Function to handle the /subscribe command"""
    # adding the user to the subscribed list
    with open('./subscriptions.json') as f:
        subscribed = json.load(f)

    subscriptions = [k for k in subscribed.keys()]
    channel_id = req.form['channel_id']
    user_id = req.form['user_id']

    if len(req.form['text'].strip().split()) != 1:
        send_chat_message_ephemeral(channel_id, user_id, "```Usage: \n/subscribe <name>\n/unsubscribe <name>\n"
                                                         f"Current subscriptions are: {', '.join(subscriptions)}```")
        return Response(), 200

    if req.form['text'].strip() not in subscriptions:
        send_chat_message_ephemeral(channel_id, user_id, "```Invalid subscription name. Current subscriptions are:\n"
                                                         f"{', '.join(subscriptions)}```")
        return Response(), 200
    sub_name = req.form['text'].strip()
    if unsubscribe:
        if user_id not in subscribed[sub_name]['subscribers']:
            send_chat_message_ephemeral(channel_id, user_id, f"You did not subscribe to `{sub_name}`")
            return Response(), 200

        subscribed[sub_name]['subscribers'].remove(user_id)
        with open('./subscriptions.json', 'w') as f:
            json.dump(subscribed, f, indent=4)
        send_chat_message_ephemeral(channel_id, user_id, f"Unsubscribed from `{sub_name}` successfully!")
        return Response(), 200

    if user_id in subscribed[sub_name]['subscribers']:
        send_chat_message_ephemeral(channel_id, user_id, f"Already subscribed to `{sub_name}`")
        return Response(), 200

    ping_time = subscribed[sub_name]['ping_time']
    ping_channel = subscribed[sub_name]['ping_channel_id']

    ping_days = list(map(int, subscribed[sub_name]['ping_days'].split(",")))
    days = ""
    for day in ping_days:
        days += f"{day_name[day]}, " if day != ping_days[-1] else f"{day_name[day]}"

    subscribed[sub_name]["subscribers"].append(user_id)
    with open('./subscriptions.json', 'w') as f:
        json.dump(subscribed, f, indent=4)

    # sending the success message
    send_chat_message_ephemeral(
        channel_id, user_id,
        f"Subscribed to Bhattu successfully! Event: `{sub_name}`. Status: `{subscribed[sub_name]['status']}`\n"
        f"You will be pinged in <#{ping_channel}> at `{ping_time} H`,  on `{days}`."
    )
    return Response(), 200


def ping_scheduler():
    """Function to ping the subscribed users at the scheduled time"""
    print("Scheduler started")
    with open('./subscriptions.json') as f:
        subscriptions = json.load(f)
    while True:
        datetime_now = datetime.now(tz=pytz.timezone('Asia/Kolkata'))
        if datetime_now.hour == 0 and datetime_now.minute == 0:
            with open('./subscriptions.json') as f:
                subscriptions = json.load(f)

        for name, sub in subscriptions.items():
            if sub['status'] == 'off':
                continue
            message = sub['ping_message']
            ping_time = sub['ping_time']
            hour, minute = map(int, ping_time.split(':'))
            ping_days = list(map(int, sub['ping_days'].split(',')))
            channel = sub['ping_channel_id']
            subscribers = sub['subscribers']
            tags = ' '.join([f"<@{member}>" for member in subscribers])
            if datetime_now.hour == hour and datetime_now.minute == minute and datetime_now.weekday() in ping_days:
                response = send_chat_message(
                    channel,
                    message
                )
                message_ts = response['ts']
                send_chat_message(
                    channel,
                    f"Reminder for {name}: {tags}",
                    thread_ts=message_ts
                )
        time.sleep(60)


def bhattu_mod_help():
    return ("```Usage:\n"
            "/bhattu_mod <command> <keyword arguments> [optional keyword arguments]\n\n"
            "Commands:\n"
            "- help\n"
            "- /subscribe | /unsubscribe\n"
            "- /tag\nCurrently supported:\n"
            "/subscribe create <event_name> status=<on|off> ping_channel_id=<#channel id> ping_time=<hh:mm> "
            "ping_days=<0-6, comma separated> ping_message=<message, can include spaces>\n"
            "/subscribe update <event_name> ping_channel_id=[#channel_id] status=[on|off] "
            "ping_time=[hh:mm] ping_days=[0-6, comma separated] ping_message=[message, can include spaces]\n"
            "/subscribe delete <event_name>\n"
            "/subscribe list```")


def bhattu_arg_parser(plain: str, delim="="):
    """Function to parse the arguments passed to the command"""
    scramble = plain.split(delim)  # splitting the arguments
    # will be of the type ['arg1', 'val1 arg2', 'val2 val2 ... arg3', ...]
    prev_arg = None
    args = {}
    for i, text in enumerate(scramble):
        if i == 0:
            prev_arg = text.strip()
            continue
        if i == len(scramble) - 1:
            args[prev_arg] = text.strip()
            break
        current_arg = text.strip().split()[-1]
        args[prev_arg] = text[:len(text.strip()) - len(current_arg) - 1]
        prev_arg = current_arg
    return args


def check_mod_args(args: dict, all_reqired=False, required_args=None, debug=False):
    """Function to check if the arguments passed to the command are valid"""
    # if dict is empty, return False
    if not args:
        return False
    if 'status' in args:
        if args['status'] not in ['on', 'off']:
            if debug:
                print('status')
            return False
    if 'ping_time' in args:
        if debug:
            print(args['ping_time'].split(':'))
        if int(args['ping_time'].split(':')[0]) not in [i for i in range(24)]:  # checking if the hour is valid
            if debug:
                print('ping_time')
            return False
        if int(args['ping_time'].split(':')[1]) not in [i for i in range(60)]:  # checking if the minute is valid
            if debug:
                print('ping_time')
            return False
    if 'ping_days' in args:
        for day in args['ping_days'].split(','):
            if day not in [str(i) for i in range(7)]:
                if debug:
                    print('ping_days')
                return False
    if 'ping_channel_id' in args:
        if args['ping_channel_id'].islower() or not args['ping_channel_id'].isalnum():
            if debug:
                print('ping_channel_id')
                print(args['ping_channel_id'])
                print(args['ping_channel_id'].isalnum())
                print(args['ping_channel_id'].islower())
            return False

    # checking if all the required arguments are present
    if required_args is None and all_reqired:
        required_args = ['status', 'ping_channel_id', 'ping_time', 'ping_days', 'ping_message']
    if required_args is not None:
        for arg in required_args:
            if arg not in args:
                return False
    return True


@app.route('/tag', methods=['POST'])
def tag():
    """Function to handle the /tag command"""

    response = Response()  # creating a response object

    # extracting the data from the request
    data = request.form
    user = data['user_id']
    channel = data['channel_id']
    text = data['text'].split()
    groups = text[0]
    message = "Tagged you"
    if len(text) > 1:
        message = data['text'][len(groups) + 1:].strip()

    # extracting the group name from the request
    positions = []
    undefined = []
    for group in groups.split(','):
        if group in ['ctm', 'ctms', 'fresher', 'freshers']:
            positions.append('ctm')
        elif group in ['exec', 'execs', 'executive', 'executives']:
            positions.append('exec')
        elif group in ['adv', 'advisor', 'advisors']:
            # position = 'advisor'
            positions.append('advisor')
        else:
            undefined.append(group)

    # sending the error message if the group name is not valid
    if undefined:
        client.chat_postEphemeral(
            channel=channel,
            user=user,
            text=f"Hey <@{user}>!\n"
                 f"I don't know what you mean by {', '.join(undefined)}\n"
                 "```Usage:\n"
                 "/tag <groups, (comma seperated. !! do not give spaces)> <message>\n"
                 "/tag <groups, (comma seperated. !! do not give spaces)> (In this case, message will be 'Tagged "
                 "you')\n\n"
                 "Groups:\n"
                 "- ctm | ctms | fresher | freshers\n"
                 "- exec | execs | executive | executives\n"
                 "- adv | advisor | advisors```"
        )
    else:
        tag_group(user, channel, list(set(positions)), message)  # tagging the group

    return response, 200


@app.route('/subscribe', methods=['POST'])
def subscribe_bhattu():
    return subscribe(request, unsubscribe=False)


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_bhattu():
    return subscribe(request, unsubscribe=True)


@app.route('/bhattu_mod', methods=['POST'])
def bhattu_mod():
    """Function to handle the /bhattu_mod command"""
    # extracting the data from the request
    with open('data.json') as f:
        koss_members = json.load(f)
    ctms = list(map(lambda x: x["id"], koss_members['ctm']))

    if request.form['user_id'] in ctms:
        send_chat_message_ephemeral(
            request.form['channel_id'],
            request.form['user_id'],
            f"Hey <@{request.form['user_id']}>!\n"
            f"You don't have the permissions to use this command."
        )
        return Response(), 200

    text = request.form['text'].strip()

    if len(text.split()) < 2:
        send_chat_message_ephemeral(
            request.form['channel_id'],
            request.form['user_id'],
            f"Hey <@{request.form['user_id']}>!\n" + bhattu_mod_help()
        )
        return Response(), 200

    command = text.split()[0]
    text = text[len(command) + 1:].strip()

    # TODO: add support for /tag command
    if command not in ['/subscribe', '/unsubscribe'] or command == 'help':
        # sending the error message if the command is not valid
        send_chat_message_ephemeral(
            request.form['channel_id'],
            request.form['user_id'],
            f"Hey <@{request.form['user_id']}>!\nI don't Know what you mean by {command}\n" + bhattu_mod_help()
        )
        return Response(), 200

    if command == '/subscribe':
        with open('./subscriptions.json') as f:
            subscribed = json.load(f)
        sub_command = text.split()[0]
        if sub_command == 'list':
            send_chat_message_ephemeral(
                request.form['channel_id'],
                request.form['user_id'],
                f"Hey <@{request.form['user_id']}>!\n"
                f"Here are your subscriptions:\n"
                f"```{', '.join(subscribed.keys())}```"
            )
            return Response(), 200

        if sub_command not in ['update', 'create', 'delete'] or sub_command == 'help' or len(text.split()) < 2:
            send_chat_message_ephemeral(
                request.form['channel_id'],
                request.form['user_id'],
                f"Hey <@{request.form['user_id']}>!\n" + bhattu_mod_help()
            )
            return Response(), 200

        sub_name = text.split()[1]

        if sub_command == 'delete':
            if sub_name not in subscribed:
                send_chat_message_ephemeral(
                    request.form['channel_id'],
                    request.form['user_id'],
                    f"Hey <@{request.form['user_id']}>!\n"
                    f"Event `{sub_name}` is not in subscriptions!"
                )
                return Response(), 200
            del subscribed[sub_name]
            with open('./subscriptions.json', 'w') as f:
                json.dump(subscribed, f, indent=4)
            send_chat_message_ephemeral(
                request.form['channel_id'],
                request.form['user_id'],
                f"Hey <@{request.form['user_id']}>!\n"
                f"Event `{sub_name}` deleted!"
            )
            return Response(), 200

        # of the form
        # status=<on|off> ping_time=<hh:mm> ping_days=<0,1...6> ping_channel_id=<channel_id> ping_message=<message>
        keyword_args_plain = text[len(sub_command) + 1:].strip()[len(sub_name) + 1:].strip()
        keyword_args = bhattu_arg_parser(keyword_args_plain)

        if not check_mod_args(keyword_args):
            send_chat_message_ephemeral(
                request.form['channel_id'],
                request.form['user_id'],
                f"Hey <@{request.form['user_id']}>!\n"
                f"Invalid arguments!\n" + bhattu_mod_help()
            )
            return Response(), 200

        if sub_command == 'create':
            if sub_name in subscribed:
                send_chat_message_ephemeral(
                    request.form['channel_id'],
                    request.form['user_id'],
                    f"Hey <@{request.form['user_id']}>!\n"
                    f"Event `{sub_name}` already exists!"
                )
                return Response(), 200

            if not check_mod_args(keyword_args, all_reqired=True):
                send_chat_message_ephemeral(
                    request.form['channel_id'],
                    request.form['user_id'],
                    f"Hey <@{request.form['user_id']}>!\n"
                    f"Invalid arguments! All are required\n" + bhattu_mod_help()
                )
                return Response(), 200

            subscribed[sub_name] = {}
            for k, v in keyword_args.items():
                subscribed[sub_name][k] = v
            subscribed[sub_name]['subscribers'] = []

            with open('./subscriptions.json', 'w') as f:
                json.dump(subscribed, f, indent=4)
            send_chat_message_ephemeral(
                request.form['channel_id'],
                request.form['user_id'],
                f"Hey <@{request.form['user_id']}>!\n"
                f"Event `{sub_name}` created!"
            )
            return Response(), 200

        if sub_command == 'update':
            if sub_name not in subscribed:
                send_chat_message_ephemeral(
                    request.form['channel_id'],
                    request.form['user_id'],
                    f"Hey <@{request.form['user_id']}>!\n"
                    f"Event `{sub_name}` is not in subscriptions!"
                )
                return Response(), 200

            for k, v in keyword_args.items():
                subscribed[sub_name][k] = v

            with open('./subscriptions.json', 'w') as f:
                json.dump(subscribed, f, indent=4)
            send_chat_message_ephemeral(
                request.form['channel_id'],
                request.form['user_id'],
                f"Hey <@{request.form['user_id']}>!\n"
                f"Event `{sub_name}` updated!"
            )
            return Response(), 200

        subscribed[sub_name]['status'] = text.split()[1].split('=')[1]
        with open('./subscriptions.json', 'w') as f:
            json.dump(subscribed, f, indent=4)

        send_chat_message_ephemeral(
            request.form['channel_id'],
            request.form['user_id'],
            f"Hey <@{request.form['user_id']}>!\n"
            f"Event `{sub_name}` is now set to {subscribed[sub_name]['status']}"
        )

    return Response(), 200


if __name__ == '__main__':
    while True:
        try:
            scheduler = threading.Thread(target=ping_scheduler)
            scheduler.start()
            app.run(host="0.0.0.0", port=8080)
        except Exception as e:
            print(e)
