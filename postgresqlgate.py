from basegate import BaseGate
from basegate import GateException
from roller import Roller

import sys
import os
import time


class PgSQLGate(BaseGate):
    """
    Gate for PostgreSQL database tools.
    """
    NAME = "postgresql"


    def __init__(self, config):
        self.config = config or {}
        self._get_sysconfig()
        self._get_pg_home()
        if self._get_db_status():
            self._get_pg_config()


    # Utils
    def check(self):
        """
        Check system requirements for this gate.
        """
        msg = None
        if not os.path.exists("/usr/bin/psql"):
            msg = 'operations'
        elif not os.path.exists("/usr/bin/postmaster"):
            msg = 'core'
        elif not os.path.exists("/usr/bin/pg_ctl"):
            msg = 'control'
        
        if msg:
            raise GateException("Cannot find %s sub-component, required for the gate." % msg)

        return True


    def _get_sysconfig(self):
        """
        Read the system config for the postgresql.
        """
        for line in filter(None, map(lambda line:line.strip(), open('/etc/sysconfig/postgresql').readlines())):
            if line.startswith('#'):
                continue
            try:
                k, v = line.split("=", 1)
                self.config['sysconfig_' + k] = v
            except:
                print >> sys.stderr, "Cannot parse line", line, "from sysconfig."


    def _get_db_status(self):
        """
        Return True if DB is running, False otherwise.
        """
        status = False
        pid_file = self.config.get('pcnf_pg_home', '') + '/data/postmaster.pid'
        if os.path.exists(pid_file):
            if os.path.exists('/proc/' + open(pid_file).readline().strip()):
                status = True

        return status


    def _get_pg_home(self):
        """
        PostgreSQL home is where is 'postgres' user is.
        """
        stdout, stderr = self.syscall("sudo", None, None, "-i", "-u", "postgres", "env")
        if stdout:
            for line in stdout.strip().split("\n"):
                try:
                    k, v = line.split("=", 1)
                except:
                    print "cannot parse", line
                if k == 'HOME':
                    self.config['pcnf_pg_home'] = v
                    return
                

    def _get_pg_config(self):
        """
        Get entire PostgreSQL configuration.
        """
        stdout, stderr = self.syscall("sudo", self.get_scenario_template(target='psql').replace('@scenario', 'show all'),
                                      None, "-u", "postgres", "/bin/bash")
        if stdout:
            for line in stdout.strip().split("\n")[2:]:
                try:
                    k, v = map(lambda line:line.strip(), line.split('|')[:2])
                    self.config['pcnf_' + k] = v
                except:
                    print >> sys.stdout, "Cannot parse line:", line
        else:
            print >> sys.stderr, stderr
            raise Exception("Underlying error: unable get backend configuration.")


#    def get_scenario_template(self, target=None):
#        """
#        Convenience stub to make sure we are focused on PostgreSQL always.
#        """
#        return BaseGate.get_scenario_template(self, target='psql')


    def _cleanup_pids(self):
        """
        Cleanup PostgreSQL garbage in /tmp
        """
        for f in os.listdir('/tmp'):
            if f.startswith('.s.PGSQL.'):
                os.unlink('/tmp/' + f)


    # Commands        
    def do_start(self):
        """
        Start the SUSE Manager Database.
        """
        print >> sys.stdout, "Starting core...\t",
        sys.stdout.flush()
        #roller = Roller()
        #roller.start()

        if self._get_db_status():
            print >> sys.stdout, "failed"
            #roller.stop('failed')
            time.sleep(1)
            return

        # Cleanup first
        self._cleanup_pids()

        # Start the db
        if not os.system("sudo -u postgres /usr/bin/pg_ctl start -s -w -p /usr/bin/postmaster -D %s -o %s" 
                         % (self.config['pcnf_pg_home'] + "/data", self.config.get('sysconfig_POSTGRES_OPTIONS', ''))):
            print >> sys.stdout,  "done"
        else:
            print >> sys.stderr, "failed"

        #roller.stop('done')
        time.sleep(1)


    def do_stop(self):
        """
        Stop the SUSE Manager Database.
        """
        print >> sys.stdout, "Stopping core...\t",
        sys.stdout.flush()

        if not self._get_db_status():
            print >> sys.stdout, "failed"
            #roller.stop('failed')
            time.sleep(1)
            return

        # Stop the db
        if not self.config.get('pcnf_data_directory'):
            raise GateException("Cannot find data directory.")

        if not os.system("sudo -u postgres /usr/bin/pg_ctl stop -s -D %s -m fast" % self.config.get('pcnf_data_directory', '')):
            print >> sys.stdout, "done"
        else:
            print >> sys.stderr, "failed"

        # Cleanup
        self._cleanup_pids()


    def do_status(self):
        """
        Show database status.
        """
        print 'Database is', self._get_db_status() and 'online' or 'offline'


    def do_space_tables(self):
        """
        Show space report for each table.
        """
        stdout, stderr = self.call_scenario('pg-tablesizes.scn', target='psql')

        if stdout:
            t_index = []
            t_ref = {}
            t_total = 0
            longest = 0
            for line in stdout.strip().split("\n")[2:]:
                line = filter(None, map(lambda el:el.strip(), line.split('|')))
                if len(line) == 3:
                    t_name, t_size_pretty, t_size = line[0], line[1], int(line[2])
                    t_ref[t_name] = t_size_pretty
                    t_total += t_size
                    t_index.append(t_name)

                    longest = len(t_name) > longest and len(t_name) or longest

            t_index.sort()

            print >> sys.stdout, "Table" + (" " * (longest - 5)) + "\tSize"
            for t_name in t_index:
                print >> sys.stdout, t_name + (" " * (longest - len(t_name))) + "\t", t_ref[t_name]
            print >> sys.stdout, "\nTotal" + (" " * (longest - 5)) + "\t" + ('%.2f' % round(t_total / 1024. / 1024)) + "M\n"

        if stderr:
            print >> sys.stderr, stderr
            raise GateException("Unhandled underlying error occurred, see above.")

    def _do_system_check(self):
        """
        Common backend healthcheck.
        """
        # Check enough space

        return True


def getGate(config):
    """
    Get gate to the database engine.
    """
    return PgSQLGate(config)
