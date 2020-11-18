schema = {
    "description": "Chariot config file",
    "required": [
        "database",
        "round_time",
        "teams",
        "challenges",
        "log_path",
        "exp_path"
    ],
    "oneof": [
        {"required": ["ip_range"]},
        {"required": ["addr_map"]}
    ],
    "title": "config",
    "type": "object",
    "properties": {
        "database": {
            "$id": "#/properties/database",
            "examples": [
                "mysql+pymysql://<username>:<password>@<host>/<dbname>[?<options>]"
            ],
            "title": "Database address",
            "type": "string"
        },
        "max_workers": {
            "$id": "#/properties/max_workers",
            "title": "The workers count",
            "type": "integer"
        },
        "log_level": {
            "$id": "#/properties/log_level",
            "default": "INFO",
            "description": "one of log levels: [DEBUG|INFO|WARNING|ERROR|CRITICAL]",
            "pattern": "(DEBUG|INFO|WARNING|ERROR|CRITICAL)",
            "title": "Log level",
            "type": "string"
        },
        "log_path": {
            "$id": "#/properties/log_path",
            "type": "string",
            "default": "/tmp/chariot",
            "title": "The log_path schema",
        },
        "exp_path": {
            "$id": "#/properties/exp_path",
            "type": "string",
            "default": "./exp",
            "title": "The exp_path schema",
            "description": "The path store exp",
        },
        "flag_pattern": {
            "$id": "#/properties/flag_pattern",
            "description": "the pattern to search flag",
            "title": "The flag_pattern schema",
            "type": "string"
        },
        "round_time": {
            "$id": "#/properties/round_time",
            "title": "The round time",
            "type": "integer"
        },
        "start_time": {
            "$id": "#/properties/start_time",
            "title": "The start_time schema",
            "type": "string"
        },
        "ip_range": {
            "$id": "#/properties/ip_range",
            "description": "the first ip of range used to map range to teams",
            "title": "The ip_range schema",
            "type": "string"
        },
        "ip_mask": {
            "$id": "#/properties/ip_mask",
            "default": 32,
            "description": "Ip mask to point out witch bits will be increase",
            "title": "The ip_mask schema",
            "type": "integer"
        },
        "teams": {
            "$id": "#/properties/teams",
            "type": "array",
            "title": "The teams schema",
            "additionalItems": True,
            "items": {
                "$id": "#/properties/teams/items",
                "anyOf": [
                    {
                        "$id": "#/properties/teams/items/anyOf/1",
                        "title": "The second anyOf schema",
                        "$schema": "team name of a team",
                        "type": "string"
                    },
                    {
                        "$ref": "#/definitions/team"
                    }
                ]
            }
        },
        "challenges": {
            "$id": "#/properties/challenges",
            "type": "array",
            "title": "The challenges schema",
            "additionalItems": True,
            "items": {
                "$id": "#/properties/challenges/items",
                "anyOf": [
                    {
                        "$id": "#/properties/challenges/items/anyOf/0",
                        "type": "string",
                        "title": "The first anyOf schema",
                        "description": "Name of challenge"
                    },
                    {
                        "$ref": "#/definitions/challenge"
                    }
                ]
            }
        },
        "addr_map": {
            "$id": "#/properties/addr_map",
            "title": "The addr_map schema",
            "type": "array",
            "additionalItems": True,
            "items": {
                "$id": "#/properties/addr_map/items",
                "anyOf": [
                    {
                        "$id": "#/properties/addr_map/items/anyOf/0",
                        "$ref": "#/definitions/map"
                    }
                ]
            }
        }
    },
    "additionalProperties": True,
    "definitions": {
        "team": {
            "$id": "#/definitions/team",
            "required": [
                "name"
            ],
            "title": "The team schema",
            "type": "object",
            "properties": {
                "name": {
                    "$id": "#/properties/teams/items/anyOf/2/properties/name",
                    "title": "The name schema",
                    "type": "string"
                },
                "weight": {
                    "$id": "#/properties/teams/items/anyOf/2/properties/weight",
                    "default": 10,
                    "description": "flag will first be submit if weight is less",
                    "title": "The weight schema",
                    "type": "integer"
                },
                "comment": {
                    "$id": "#/properties/teams/items/anyOf/2/properties/comment",
                    "title": "The comment schema",
                    "type": "string"
                },
                "ip": {
                    "$id": "#/properties/teams/items/anyOf/2/properties/ip",
                    "description": "ip of a team, overwrite ip range config",
                    "title": "The ip schema",
                    "type": "string"
                },
                "active": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/active",
                    "default": True,
                    "title": "The active schema",
                    "type": "boolean"
                }
            },
            "additionalProperties": True
        },
        "challenge": {
            "$id": "#/definitions/challenge",
            "required": [
                "name"
            ],
            "type": "object",
            "properties": {
                "name": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/name",
                    "title": "The name schema",
                    "type": "string"
                },
                "weight": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/weight",
                    "default": 10,
                    "title": "The weight schema",
                    "type": "integer"
                },
                "active": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/active",
                    "default": True,
                    "title": "The active schema",
                    "type": "boolean"
                },
                "type": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/type",
                    "default": "unknown",
                    "title": "The type schema",
                    "pattern": "(unknown|web|pwn)",
                    "type": "string"
                },
                "port": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/port",
                    "title": "The port schema",
                    "maximum": 65535,
                    "minimum": 1,
                    "type": "integer"
                },
                "ip_range": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/ip_range",
                    "description": "the first ip of range used to map range to teams",
                    "title": "The ip_range schema",
                    "type": "string"
                },
                "flag_path": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/flag_path",
                    "title": "The flag_path schema",
                    "default": "flag",
                    "type": "string"
                },
                "ip_mask": {
                    "$id": "#/properties/challenge/items/anyOf/1/properties/ip_mask",
                    "default": 32,
                    "description": "Ip mask to point out witch bits will be increase",
                    "title": "The ip_mask schema",
                    "type": "integer"
                }
            },
            "additionalProperties": True
        },
        "map": {
            "$id": "#/definitions/map",
            "required": [
                "ip",
                "port",
                "team",
                "challenge"
            ],
            "title": "The map",
            "type": "object",
            "properties": {
                "ip": {
                    "$id": "#/properties/addr_map/items/anyOf/0/properties/ip",
                    "title": "The ip schema",
                    "type": "string"
                },
                "port": {
                    "$id": "#/properties/addr_map/items/anyOf/0/properties/port",
                    "title": "The port schema",
                    "type": "integer"
                },
                "team": {
                    "$id": "#/properties/addr_map/items/anyOf/0/properties/team",
                    "title": "The team name schema",
                    "type": "string"
                },
                "challenge": {
                    "$id": "#/properties/addr_map/items/anyOf/0/properties/challenge",
                    "title": "The challenge name schema",
                    "type": "string"
                }
            }
        }
    }
}
