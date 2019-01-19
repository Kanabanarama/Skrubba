import os
from functools import wraps
from flask import Flask, request, send_from_directory, render_template, json # pylint: disable=import-error
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, # pylint: disable=import-error
                          BadSignature, SignatureExpired) # pylint: disable=import-error

from skrubba.db import DB
from config.environment import DEBUG
from main import APP

TOKEN_EXPIRATION = 7200

################################################################################
# Authentication
################################################################################

def requires_auth(func):
    """
    Decorator for endpoints that require authentication
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        if not is_login_required():
            return func(*args, **kwargs)

        header_auth_token = request.headers.get('authentication')
        if not header_auth_token or not check_auth_token(header_auth_token):
            return deny_access_token()
        return func(*args, **kwargs)

    return decorated

def is_login_required():
    """
    Checks if user credentials are required
    """
    store = DB()
    login_required = False
    for line in store.get_system_settings():
        if line['setting_name'] == 'username':
            login_required = True
            break

    return login_required

def generate_auth_token(credentials, expiration=TOKEN_EXPIRATION):
    """
    Generates the auth token
    """
    serializer = Serializer(APP.config['SECRET_KEY'], expires_in=expiration)

    return serializer.dumps({'username': credentials['username']})

def check_auth_token(auth_token):
    """
    Checks if the auth token is valid and has not expired
    """
    serializer = Serializer(APP.config['SECRET_KEY'])
    try:
        serializer.loads(auth_token)
    except SignatureExpired:
        return False # valid token, but expired
    except BadSignature:
        return False # invalid token

    return True

def deny_access_token():
    """
    Returns an invalid token message
    """
    return json.dumps({'success': 'false', 'message': 'Authentication failed.'})

def localhost_only(func):
    """
    Decorator for allowing requests from localhost
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        request_ip = request.remote_addr
        if DEBUG:
            allowed = True
        else:
            allowed = (request_ip == '127.0.0.1')
        if not allowed:
            print('return denyIp()' + request_ip)
            return deny_request_ip()
        return func(*args, **kwargs)
    return decorated

def deny_request_ip():
    """
    Returns an access denied message
    """
    return json.dumps({'success': 'false',
                       'message': 'Requests from remote hosts are not allowed.'
                      })

def unload_flask():
    """
    Flask cleanup
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

    return True

#def postServerOffRequest():
#    response = APP.test_client().post('/serveroff')
#    return response'''

################################################################################
# Routes
################################################################################

@APP.route("/test", methods=['GET'])
def test():
    """
    Output test
    """
    #return 'It works.'
    return render_template('test.html')

# Serve favicon from static folder
@APP.route('/favicon.ico')
def favicon():
    """
    Serve favicon
    """
    favicon_path = os.path.join(APP.root_path, 'static')
    return send_from_directory(favicon_path, 'gfx/favicon.ico', mimetype='image/vnd.microsoft.icon')

# Serve index page
@APP.route("/", methods=['GET', 'POST'])
def index():
    """
    Serve the backend
    """
    return render_template('index.html')

def setup_backend_user_tracking():
    """
    Show IP's on tft display when users are using the backend
    """
    def track_active_backend_users():
        """
        Use keepalive info holding the client IP's
        """
        for client_ip, counter in KEEPALIVE_COUNTERS.items():
            KEEPALIVE_COUNTERS[client_ip] -= 10
            if KEEPALIVE_COUNTERS[client_ip] > 0:
                TFT.display_message(client_ip + ' is logged in.', 'backend_user')
            else:
                TFT.clear_message('backend_user')
    SCHEDULER.add_job(track_active_backend_users, 'interval', seconds=10)

KEEPALIVE_COUNTERS = {}

#@APP.before_request
@APP.route("/keepalive", methods=['GET'])
def refresh_keepalive():
    """
    Refresh keepalive
    """
    KEEPALIVE_COUNTERS[request.remote_addr] = 11
    return json.dumps({'success': 'true'})


@APP.route("/action/login", methods=['GET', 'POST'])
def action_login():
    """
    Handles login requests and checks against the credentials stored in database
    """
    if request.method == 'POST':
        params = request.get_json()
        request_username = params['username']
        request_password = params['password']

        system_credentials = {}
        store = DB()

        for line in store.get_system_settings():
            if line['setting_name'] == 'username':
                system_credentials['username'] = line['setting_value']
            if line['setting_name'] == 'password':
                system_credentials['password'] = line['setting_value']
        if len(system_credentials) == 2 \
                and request_username == system_credentials['username'] \
                and request_password == system_credentials['password']:
            print('Login successful')
            token = generate_auth_token(system_credentials, 600)
            response = json.dumps({'success': 'true', 'token': token})
        else:
            print('Login failed')
            response = json.dumps({'success': 'false', 'message': 'Invalid login.'})

    return response

################################################################################
# Flask CRUD routes
################################################################################

@APP.route("/data/plant.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def plant():
    """
    Handles all request actions for a plant entry
    """
    store = DB()
    action = request.args.get('action')

    if action == 'read':
        valve_configs = store.load_valve_configs()
        response = json.dumps({'plant': valve_configs})

    elif action == 'create':
        json_valve_configs_from_request = request.form['plant']
        valve_configs = json.loads(json_valve_configs_from_request)
        # check if valves can be added (system_settings.valve_amount)
        max_valves = store.get_max_valve_count_setting()
        actual_valves = store.get_valve_count()
        if not max_valves or actual_valves < max_valves:
            try:
                new_entry = store.add_valve_config(valve_configs)
            except:
                print('Error adding config')
            if new_entry:
                restart_job_manager()
                response_obj = {'success': 'true', 'plant': new_entry}
            else:
                response_obj = {'success': 'false'}
        else:
            response_obj = {'success': 'false',
                            'message': 'No more entrys to add, maximum entries '\
                            'can be configured in settings.'}
        response = json.dumps(response_obj)

    elif action == 'update':
        json_valve_configs_from_request = request.form['plant']
        valve_configs = json.loads(json_valve_configs_from_request)
        success = store.update_valve_config(valve_configs)
        if success:
            restart_job_manager()
            response_obj = {'success': 'true'}
        else:
            response_obj = {'success': 'false',
                            'message': 'Valve already used by another entry.'}
        response = json.dumps(response_obj)
        #{'success': 'false', 'message': }#, 500
        #'metaData': { 'messageProperty': 'msg', 'successProperty': 'success' }

    elif action == 'destroy':
        json_valve_configs_from_request = request.form['plant']
        valve_configs = json.loads(json_valve_configs_from_request)
        # print('DELETED VALVE CONFIG:')
        # print(valve_configs)
        success = store.delete_valve_config(valve_configs['id'])
        restart_job_manager()
        response = json.dumps({'success': str(success).lower()})

    return response

@APP.route("/data/log.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def log():
    """
    Read the logs stored in the database
    """
    store = DB()
    action = request.args.get('action')
    if action == 'read':
        logs = store.load_logs()
        # print('READ LOGS:')
        # print(logs)
        response = json.dumps({'log': logs})

    return response

@APP.route("/data/setting.json", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def setting():
    """
    Handle the settings requests
    """
    action = request.args.get('action')
    if action == 'read':
        response = setting_read()
    elif action == 'update' and request.method == 'POST':
        response = setting_update()
    elif action == 'destroy' and request.method == 'POST':
        response = setting_delete()

    return response

def setting_read():
    """
    Read settings stored in the database
    """
    store = DB()
    settings = {}
    # print('READ SYSTEM CONF:')
    for line in store.get_system_settings():
        if line['setting_name'] == 'password':
            continue
        settings.update({line['setting_name']: line['setting_value']})

    return json.dumps({'setting': [settings]})

def setting_update():
    """
    Update settings stored in the database
    """
    store = DB()
    json_credentials = request.form['setting']
    params = json.loads(json_credentials)
    response = json.dumps({'success': 'false'})
    if 'username' in params:
        credential_username = params['username']
        store.update_system_settings('username', credential_username)
        response = json.dumps({'success': 'true'})
    if 'password' in params:
        credential_password = params['password']
        store.update_system_settings('password', credential_password)
        response = json.dumps({'success': 'true'})
    if 'valve_amount' in params:
        valve_amount = int(params['valve_amount'])
        actual_valves = store.get_valve_count()
        if actual_valves <= valve_amount:
            store.update_system_settings('valve_amount', valve_amount)
            response = json.dumps({'success': 'true'})
        else:
            response = json.dumps({'success': 'false',
                                   'message': 'There are more valves '\
                                   'set up than you want to allow.'\
                                   'Please remove some of them first.'})

    return response

def setting_delete():
    """
    Delete settings stored in the database
    """
    store = DB()
    json_credentials = request.form['setting']
    params = json.loads(json_credentials)
    #print(params)
    #for setting in params:
    for key, value in params.items():
        #print('checking: %s / %s' % (key, value))
        if value == '-DELETE-':
            store.delete_system_setting(key)
    response = json.dumps({'success': 'true'})

    return response

################################################################################
# Flask action routes
################################################################################

@APP.route("/actions/manualwatering", methods=['GET', 'POST'])
@requires_auth
@localhost_only
def action_manualwatering():
    """
    Manually open a valve (but not the pump) by request for testing
    """
    if request.method == 'POST':
        params = request.get_json()
        valve_no = params['valve']
        VALVES.output_decimal(valve_no)
        VALVES.enable()
        time.sleep(3)
        VALVES.disable()
        VALVES.reset()
    response = json.dumps({'success': 'true'})

    return response


@APP.route('/action/serveroff', methods=['POST'])
@requires_auth
@localhost_only
def serveroff():
    """
    Exit flask only
    """
    print('SERVER SHUTTING DOWN')
    TFT.display_message('SHUTDOWN SERVER')
    #unload_scheduler()
    unload_flask()
    return json.dumps({'success': 'true'})

@APP.route('/action/reboot', methods=['POST'])
@requires_auth
@localhost_only
def reboot():
    """
    Call cleanup and reboot system
    """
    print('SYSTEM REBOOTING')
    TFT.display_message('REBOOTING')
    #unload_scheduler()
    unload_flask()
    os.system("reboot")

    return json.dumps({'success': 'true'})

@APP.route('/action/shutdown', methods=['POST'])
@requires_auth
@localhost_only
def shutdown():
    """
    Call cleanup and shutdown system
    """
    print('SYSTEM SHUTDOWN')
    TFT.display_message('SHUTDOWN SYSTEM')
    #unload_scheduler()
    unload_flask()
    os.system("poweroff")

    return json.dumps({'success': 'true'})
