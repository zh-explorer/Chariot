import json
import yaml
import jsonschema
from functools import partial
from ..util import Context, DictWrapper, log_reinit
from .config_schema import schema as schema_data


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
            self.weight = conf.weigth
            self.active = conf.active
            self.type = conf.type
            self.port = conf.port

            # we do not deal with this ip here, this will be do when db init
            self.ip_range = conf.ip_range
            self.ip_mask = conf.ip_mask
        else:
            self.name = conf
            self.weight = 10
            self.active = True
            self.type = "unknown"
            self.port = None
            self.ip_range = None
            self.ip_mask = None


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

    if "log_file" in conf:
        Context.log_file = conf.log_file
    Context.log_level = conf.log_level
    log_reinit()
    # init log when get log config from config file

    Context.round_time = conf.rount_time

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
