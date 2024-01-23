""" Check ports and allocate a new docker instance"""

import configparser
import json
import logging
import string

from collections import abc

from logger import g_logger

class DockerPorts():
    ''' this is a global object that keeps track of the free ports
    when requested, it allocates a new docker instance and returns it '''

    CONFIG_PROFILEPREFIX = "profile:"
    CONFIG_DOCKEROPTIONSPREFIX = "dockeroptions:"

    def __init__(self):
        self.instances_by_name = {}
        self.image_params = {}

    def _get_profiles_list(self, config):
        out = []
        for n in config.sections():
            if n.startswith(self.CONFIG_PROFILEPREFIX):
                out += [n[len(self.CONFIG_PROFILEPREFIX):]]
        return out

    def _read_profile_config(self, config, profilename):
        fullprofilename = f"{self.CONFIG_PROFILEPREFIX}{profilename}"
        innerport = self._parse_int(config[fullprofilename]["innerport"])
        checkupport = innerport
        limit = 0
        reuse = False

        if "checkupport" in config[fullprofilename]:
            checkupport = self._parse_int(config[fullprofilename]["checkupport"])
        if "limit" in config[fullprofilename]:
            limit = self._parse_int(config[fullprofilename]["limit"])
        if "reuse" in config[fullprofilename]:
            reuse = self._parse_truthy(config[fullprofilename]["reuse"])

        return {
            "outerport": int(config[fullprofilename]["outerport"]),
            "innerport": innerport,
            "containername": config[fullprofilename]["container"],
            "checkupport": checkupport,
            "limit": limit,
            "reuse": reuse,
            "dockeroptions": self._get_docker_options(
                config, profilename, innerport, checkupport)
        }

    def _add_docker_options_from_config_section(self, config, sectionname, base):
        """ read options from config file """
        def update(d, u):
            for k, v in u.items():
                if isinstance(v, abc.Mapping):
                    r = update(d.get(k, {}), v)
                    d[k] = r
                else:
                    d[k] = u[k]
            return d

        def guessvalue(v):
            """ we may need to read json values """
            if v in ["True", "False"] or all(c in string.digits for c in v) or \
                v.startswith("[") or v.startswith("{"):
                return json.loads(v)
            return v

        # if sectionname doesn't exist, return base
        # otherwise, read keywords and values, add them to base
        if sectionname in config.sections():
            newvals = dict(config[sectionname])
            fixedvals = {}
            for (k,v) in newvals.items():
                fixedvals[k] = guessvalue(v)
            base = update(base, fixedvals)

        return base

    def _get_docker_options(self, config, profilename, innerport, checkupport):
        """ Get docker options form config """
        out = {}
        out = self._add_docker_options_from_config_section(
            config, "dockeroptions", {})
        out = self._add_docker_options_from_config_section(
            config, f"{self.CONFIG_DOCKEROPTIONSPREFIX}{profilename}", out)

        out["detach"] = True
        if "ports" not in out:
            out["ports"] = {}
        out["ports"][innerport] = None
        out["ports"][checkupport] = None
        # cannot use detach and remove together
        # See https://github.com/docker/docker-py/issues/1477
        #out["remove"] = True
        #out["auto_remove"] = True
        return out

    def read_config(self, fn):
        """ read the configfile. """
        config = configparser.ConfigParser()
        g_logger.debug("Reading configfile from %s", fn)
        config.read(fn)

        # set log file
        if "global" in config.sections() and "logfile" in config["global"]:
            if "global" in config.sections() and "rotatelogfileat" in config["global"]:
                handler = logging.handlers.TimedRotatingFileHandler(
                    config["global"]["logfile"],
                    when=config["global"]["rotatelogfileat"])
            else:
                handler = logging.FileHandler(config["global"]["logfile"])
            handler.setFormatter(CustomFormatter())
            g_logger.addHandler(handler)

        # Log to the screen, too
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())
        g_logger.addHandler(handler)

        # set log level
        if "global" in config.sections() and "loglevel" in config["global"]:
            # global logger
            g_logger.setLevel(logging.getLevelName(config["global"]["loglevel"]))

        # if there is a configdir directory, reread everything
        if "global" in config.sections() and "splitconfigfiles" in config["global"]:
            fnlist = [fn] + [f for f in glob.glob(config["global"]["splitconfigfiles"])]
            g_logger.debug("Detected configdir directive. Reading configfiles from %s", fnlist)
            config = configparser.ConfigParser()
            config.read(fnlist)

        if len(self._get_profiles_list(config)) == 0:
            g_logger.error("invalid configfile. No docker images")
            sys.exit(1)

        for profilename in self._get_profiles_list(config):
            conf = self._read_profile_config(config, profilename)
            g_logger.debug("Read config for profile %s", profilename)

            self.register_proxy(profilename, conf)

        params = {}
        for key, value in self.image_params.items():
            params[key] = value["outerport"]
        return params

    def _parse_int(self, x):
        """ converts to integer """
        return int(x)

    def _parse_truthy(self, x):
        """ converts to boolean """
        if x.lower() in ["0", "false", "no"]:
            return False
        if x.lower() in ["1", "true", "yes"]:
            return True

        raise f"Unknown truthy value {x}"

    def register_proxy(self, profilename, conf):
        """ store copy of config for this profile """
        self.image_params[profilename] = copy.deepcopy(conf)

    def create(self, profilename):
        """ create docker instance """
        containername = self.image_params[profilename]["containername"]
        dockeroptions = self.image_params[profilename]["dockeroptions"]
        imagelimit = self.image_params[profilename]["limit"]
        reuse = self.image_params[profilename]["reuse"]
        innerport = self.image_params[profilename]["innerport"]
        checkupport = self.image_params[profilename]["checkupport"]

        icount = 0
        if profilename in self.instances_by_name:
            icount = len(self.instances_by_name[profilename])

        if icount >= imagelimit > 0:
            g_logger.warning(
                "Reached max count of %d (currently %d) for image %s",
                imagelimit, icount, profilename)
            return None

        instance = None

        if reuse and icount > 0:
            g_logger.debug("Reusing existing instance for image %s", profilename)
            instance = self.instances_by_name[profilename][0]
        else:
            instance = DockerInstance(
                profilename, containername, innerport, checkupport, dockeroptions)
            instance.start()

        if profilename not in self.instances_by_name:
            self.instances_by_name[profilename] = []

        # in case of reuse, the list will have duplicates
        self.instances_by_name[profilename] += [instance]

        # Send the information of the recent created docker instance to rabbitmq
        try:
            rabbit.send(instance.get_instance_info())
        except pika.exceptions.AMQPConnectionError:
            g_logger.warning(
                "Cannot connect to rabbitmq. Are you sure it is running?")
        else:
            g_logger.info(
                "Docker instance [%s] info sent to rabbitmq server",
                instance.get_instance_id())

        return instance

    def destroy(self, instance):
        """ destroy docker instance """
        profilename = instance.get_profile_name()
        reuse = self.image_params[profilename]["reuse"]

        # in case of reuse, the list will have duplicates, but remove() does not care
        self.instances_by_name[profilename].remove(instance)

        # stop the instance if there is no reuse, or if this is the last instance for a reused image
        if not reuse or len(self.instances_by_name[profilename]) == 0:
            instance.stop()