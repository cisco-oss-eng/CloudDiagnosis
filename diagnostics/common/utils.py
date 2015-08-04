import paramiko
import requests
import sh


class Diagnosis(object):
    def __init__(self):
        self.status = 'SKIPPED'
        self.diagnosis = []
        self.msgs = ''

    def set_fail_status(self, msg):
        self.diagnosis.append(('FAILED', msg))

    def set_ok_status(self, msg):
        self.diagnosis.append(('OK', msg))


class PingValidator(object):
    def validate(self, result):
        res_ping = result.split('\n')
        result_line = res_ping[len(res_ping) - 3].split(',')
        sent_packets = result_line[0].strip()[0]
        received_packets = result_line[0].strip()[0]
        if sent_packets != received_packets:
            self.set_fail_status('')
        else:
            self.set_ok_status('')


def host_access_check(host, validator):
    res_ping = sh.ping(host, '-c', 3)
    validator(res_ping)


def ssh_access_check(host, host_username, host_password, cmds, validator):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_client.connect(host, username=host_username,
                           password=host_password)
        for cmd in cmds:
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            validator(stdout.read(), stderr.read())

        ssh_client.close()
    except:
        validator('', 'SSH exception')


def url_access_check(url, action, validator):
    if action == 'get':
        result = requests.get(url)
    elif action == 'post':
        result = requests.post(url)
    validator(result)


def db_connection_check(host, host_username, host_password,
                        mysql_username, mysql_password,
                        database_name,
                        sql, docker_container_name, validator):

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(host, username=host_username, password=host_password)

    cmd = "mysql -u %s -p%s -D %s -e \'%s\'" % (mysql_username, mysql_password,
                                                database_name, sql)

    if docker_container_name:
        cmd = 'docker exec -t %s %s' % (docker_container_name, cmd)

    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    validator(stdout.read(), stderr.read())
    ssh_client.close()
