from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy
import enum
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ChallengeType(enum.Enum):
    unknown = 0
    pwn = 1
    web = 2


class Team(Base):
    __tablename__ = "team"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(256), unique=True)
    comment = sqlalchemy.Column(sqlalchemy.String(256))
    weight = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)


class Challenge(Base):
    __tablename__ = "challenge"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(256), unique=True)
    challenge_type = sqlalchemy.Column(sqlalchemy.Enum(ChallengeType), default=ChallengeType.unknown)
    weight = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    flag_path = sqlalchemy.Column(sqlalchemy.String(256), default="flag")


class ChallengeInst(Base):
    __tablename__ = "challenge_inst"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    challenge_id = sqlalchemy.Column(sqlalchemy.Integer,
                                     sqlalchemy.ForeignKey("challenge.id", ondelete="CASCADE", onupdate="CASCADE"))
    challenge = sqlalchemy.orm.relationship("Challenge", backref="challenge_inst")

    team_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("team.id", ondelete="CASCADE", onupdate="CASCADE"))
    team = sqlalchemy.orm.relationship("Team", backref="challenge_inst")
    weight = sqlalchemy.Column(sqlalchemy.Integer, default=100)

    address = sqlalchemy.Column(sqlalchemy.String(256))
    port = sqlalchemy.Column(sqlalchemy.Integer)


class FlagStatus(enum.Enum):
    wait_submit = 0
    submit_success = 1
    flag_error = 2
    flag_expire = 3
    flag_duplicate = 4
    internal_error = 5


class Flag(Base):
    __tablename__ = "flag"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    flag_data = sqlalchemy.Column(sqlalchemy.String(256))
    timestamp = sqlalchemy.Column(sqlalchemy.Integer)
    inst_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("challenge_inst.id", ondelete="SET NULL", onupdate="CASCADE"))
    inst = sqlalchemy.orm.relationship("ChallengeInst", backref="flag")
    weight = sqlalchemy.Column(sqlalchemy.Integer, default=100)
    submit_status = sqlalchemy.Column(sqlalchemy.Enum(FlagStatus), default=FlagStatus.wait_submit)
    comment = sqlalchemy.Column(sqlalchemy.String(256))


class ExpStatus(enum.Enum):
    process = 1
    attack_failed = 2
    flag_submitting = 3
    success = 4
    flag_error = 5


class ExpLog(Base):
    __tablename__ = "exp_log"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    timestamp = sqlalchemy.Column(sqlalchemy.Integer)
    inst_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("challenge_inst.id", ondelete="SET NULL", onupdate="CASCADE"))
    inst = sqlalchemy.orm.relationship("ChallengeInst", backref='exp_log')

    flag_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("flag.id", ondelete="SET NULL", onupdate="CASCADE"))
    flag = sqlalchemy.orm.relationship("Flag", backref="exp_log")

    log_path = sqlalchemy.Column(sqlalchemy.String(256))

    exp_name = sqlalchemy.Column(sqlalchemy.String(256))

    status = sqlalchemy.Column(sqlalchemy.Enum(ExpStatus), default=ExpStatus.process)


class Database(object):
    def __init__(self, db: str):
        self.engine = sqlalchemy.create_engine(db)
        Base.metadata.create_all(self.engine)
        self.session_maker = sessionmaker(bind=self.engine)

        # move this to build_database
        # session = self.session_maker()
        # session.query(ChallengeInst).delete()
        # session.query(Team).delete()
        # session.query(Challenge).delete()
        # session.commit()
        # session.close()

    def get_session(self):
        return self.session_maker()
