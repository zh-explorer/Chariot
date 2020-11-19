import json
import yaml
import jsonschema
import os, time, datetime
from functools import partial
import re
from ..util import Context, DictWrapper, log_reinit
from .config_schema import schema as schema_data
from .config_schema import exp_schema


class Team:
    def __init__(self, conf):
        if isinstance(conf, DictWrapper):
            self.name = conf.name
            self.weight = conf.weight
            self.comment = conf.comment
            self.ip = conf.ip
            self.active = conf.active
        else:
            self.name = conf
            self.weight = 10
            self.comment = ''
            self.ip = None
            self.active = True


class Challenge:
    def __init__(self, conf):
        if isinstance(conf, DictWrapper):
            self.name = conf.name
            self.weight = conf.weight
            self.active = conf.active
            self.type = conf.type
            self.port = conf.port

            # we do not deal with this ip here, this will be do when db init
            self.ip_range = conf.ip_range
            self.ip_mask = conf.ip_mask
            self.flag_path = conf.flag_path
        else:
            self.name = conf
            self.weight = 10
            self.active = True
            self.type = "unknown"
            self.port = None
            self.ip_range = None
            self.ip_mask = None
            self.flag_path = "flag"

        # we build exp dir for every challenge
        os.makedirs(os.path.join(Context.exp_path, self.name), exist_ok=True)


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
                validator, properties, instance, schema,
        ):
            yield error

    return jsonschema.validators.extend(
        validator_class, {"properties": set_defaults},
    )


def load_yaml(fp):
    data = yaml.load(fp)
    return data


def load_json(file_name):
    with open(file_name, 'r') as fp:
        data = fp.read()
    return json.loads(data)


def make_validator():
    top_schema = schema_data
    default_validating = extend_with_default(jsonschema.Draft4Validator)
    top_validator = default_validating(top_schema, format_checker=jsonschema.FormatChecker())
    return top_validator


def load_conf(conf):
    validator = make_validator()
    validator.validate(conf)
    conf = DictWrapper(conf)
    Context.conf = conf

    Context.log_path = conf.log_path
    # make log dir
    os.makedirs(Context.log_path, exist_ok=True)

    Context.exp_path = conf.exp_path
    os.makedirs(Context.exp_path, exist_ok=True)

    Context.log_level = conf.log_level
    log_reinit()
    # init log when get log config from config file

    Context.max_workers = conf.max_workers
    Context.max_submitters = conf.max_submitters

    start_time = conf.start_time
    start_time_ary = time.strptime(start_time, "%Y/%m/%d %H:%M")
    Context.start_time = int(time.mktime(start_time_ary))

    Context.round_time = conf.round_time
    # we need a byte pattern
    Context.flag_pattern = re.compile(conf.flag_pattern.encode(), re.M)

    for team in conf.teams:
        Context.teams.append(Team(team))

    for challenge in conf.challenges:
        Context.challenges.append(Challenge(challenge))

    return conf


def load_conf_dict(data):
    conf = load_conf(data)
    Context.conf = conf
    return conf


def load_conf_file(fp):
    conf = load_yaml(fp)
    conf = load_conf(conf)
    Context.conf = conf
    return conf


def load_exp_config(fp):
    conf = load_yaml(fp)
    top_schema = exp_schema
    default_validating = extend_with_default(jsonschema.Draft4Validator)
    top_validator = default_validating(top_schema, format_checker=jsonschema.FormatChecker())
    top_validator.validate(conf)
    return conf
