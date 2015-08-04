from diagnostics.common import utils


class KeystoneDiagnostics:
    """Main keystone diagnostics class"""
    def __init__(self, lab):
        self.executors = [
            KeystoneHostPing(lab),
            KeystoneHostAccess(lab),
            KeystoneURLAccess(lab),
            KeystoneDatabaseCheck(lab),
            KeystoneServiceRunningCheck(lab)
        ]

    def execute(self):
        for e in self.executors:
            e.execute()

    def diagnosis(self):
        for e in self.executors:
            for d in e.diagnosis:
                yield (e.__class__.__name__, d)


class KeystoneDiagnosticsUtil(utils.Diagnosis):
    def __init__(self, lab):
        super(KeystoneDiagnosticsUtil, self).__init__()
        self.lab = lab
        self.keystone_server = filter(lambda s: 'keystone'
                                      in s['services'],
                                      self.lab['servers'])[0]


class KeystoneHostPing(KeystoneDiagnosticsUtil,
                       utils.PingValidator):
    def __init__(self, lab):
        super(KeystoneHostPing, self).__init__(lab)

    def execute(self):
        utils.host_access_check(self.keystone_server['ip_address'],
                                self.validate)


class KeystoneHostAccess(KeystoneDiagnosticsUtil):
    def __init__(self, lab):
        super(KeystoneHostAccess, self).__init__(lab)

    def execute(self):
        utils.ssh_access_check(self.keystone_server['ip_address'],
                               self.keystone_server['username'],
                               self.keystone_server['password'],
                               [],
                               self.validator)

    def validator(self, output, error):
        if len(error) > 0:
            self.set_fail_status('SSH error to Keystone host')
        else:
            self.set_ok_status('SSH connected to Keystone host')


class KeystoneURLAccess(KeystoneDiagnosticsUtil):
    def __init__(self, lab):
        super(KeystoneURLAccess, self).__init__(lab)

    def execute(self):
        url = 'http://%s:5000/v2.0/' % self.lab['vip']
        utils.url_access_check(url, 'get', self.validator)

        url = 'http://%s:35357/v2.0/' % self.lab['vip']
        utils.url_access_check(url, 'get', self.validator)

    def validator(self, request):
        if request.status_code != 200:
            self.set_fail_status('Unable to access %s. Status code = %d' % (
                request.url, request.status_code))
        else:
            self.set_ok_status('Connected to %s Keystone URL' % request.url)


class KeystoneDatabaseCheck(KeystoneDiagnosticsUtil):
    def __init__(self, lab):
        super(KeystoneDatabaseCheck, self).__init__(lab)

    def execute(self):
        utils.db_connection_check(self.keystone_server['ip_address'],
                                  self.keystone_server['username'],
                                  self.keystone_server['password'],
                                  self.lab['keystone_db']['username'],
                                  self.lab['keystone_db']['password'],
                                  'keystone',
                                  'select * from project limit 1',
                                  'mariadb_v1',
                                  self.validator)

    def validator(self, output, error):
        if len(error) > 0:
            self.set_fail_status(error)
        else:
            if "error" in output.lower():
                self.set_fail_status("MySQL access error : " + repr(output))
            else:
                self.set_ok_status("Connected to Keystone database")


class KeystoneServiceRunningCheck(KeystoneDiagnosticsUtil):
    def __init__(self, lab):
        super(KeystoneServiceRunningCheck, self).__init__(lab)

    def execute(self):
        utils.ssh_access_check(self.keystone_server['ip_address'],
                               self.keystone_server['username'],
                               self.keystone_server['password'],
                               ['ps -ef | grep keystone'],
                               self.validator)

    def validator(self, output, error):
        if len(error) > 0:
            self.set_failed_status(error)
        else:
            processes = output.split('\n')
            process_found = False

            for proc in processes:
                if 'keystone-all' in proc:
                    process_found = True
                    break

            if process_found:
                self.set_ok_status('Keystone process found')
            else:
                self.set_fail_status('No Keystone process found')
