from ..util import Context
from .metadata import Database, Team, Challenge, ChallengeType, ChallengeInst
import sqlalchemy
from sqlalchemy.orm import exc as sql_exc
import struct
import socket


def update_teams(session, teams):
    name_set = set()
    for team in teams:
        name_set.add(team.name)
    if len(teams) != len(name_set):
        Context.logger.error("Team name should not duplicate")
        assert len(teams) == len(name_set)

    db_name_set = set()
    for team in session.query(Team).all():
        db_name_set.add(team.name)

    # del
    del_set = db_name_set.difference(name_set)
    if del_set:
        session.query(Team).filter(Team.name.in_(del_set)).delete(synchronize_session=False)
    session.commit()

    for team in teams:
        t = session.query(Team).filter(Team.name == team.name).first()
        if t is None:
            t = Team()
            session.add(t)
        t.name = team.name
        t.comment = team.comment
        t.weight = team.weight
        t.active = team.active
    session.commit()
    # change the order of team id
    team_count = len(db_name_set) + len(name_set)
    for team in session.query(Team).all():
        team.id += team_count
    session.commit()
    i = 0
    for team in teams:
        session.query(Team).filter(Team.name == team.name).one().id = i
        i += 1

    session.commit()


def update_challenges(session, challenges):
    name_set = set()
    for challenge in challenges:
        name_set.add(challenge.name)
    if len(challenges) != len(name_set):
        Context.logger.error("challenge name should not duplicate")
        assert len(challenges) == len(name_set)

    db_name_set = set()
    for challenge in session.query(Challenge).all():
        db_name_set.add(challenge.name)

    # del
    del_set = db_name_set.difference(name_set)
    if del_set:
        session.query(Challenge).filter(Challenge.name.in_(del_set)).delete(synchronize_session=False)
    session.commit()

    for challenge in challenges:
        t = session.query(Challenge).filter(Challenge.name == challenge.name).first()
        if t is None:
            t = Challenge()
            session.add(t)
        t.name = challenge.name
        t.weight = challenge.weight
        t.active = challenge.active
        t.challenge_type = ChallengeType[challenge.type]
        t.flag_path = challenge.flag_path
    session.commit()
    # change the order of challenge id
    challenge_count = len(db_name_set) + len(name_set)
    for challenge in session.query(Challenge).all():
        challenge.id += challenge_count
    session.commit()
    i = 0
    for challenge in challenges:
        session.query(Challenge).filter(Challenge.name == challenge.name).one().id = i
        i += 1
    session.commit()


# init database or marge new config with old db
def build_database():
    conf = Context.conf
    Context.db = Database(conf.database)

    session = Context.db.get_session()

    # first update teams
    update_teams(session, Context.teams)

    # than update challenges
    update_challenges(session, Context.challenges)

    # finally, build challenge inst

    # if config have address map. ignore all others
    if "addr_map" in conf:
        try:
            for m in conf.addr_map:
                try:
                    t = session.query(Team).filter(Team.name == m.team).one()
                except sql_exc.NoResultFound:
                    Context.logger.warning("Find a team in addr map but not in team list, something maybe wrong")
                    continue
                try:
                    c = session.query(Challenge).filter(Challenge.name == m.challenge).one()
                except sql_exc.NoResultFound:
                    Context.logger.warning(
                        "Find a challenge in addr map but not in challenge list, something maybe wrong")
                    continue
                challenge_inst = session.query(ChallengeInst).filter(ChallengeInst.team_id == t.id,
                                                                     ChallengeInst.challenge_id == c.id).first()
                if challenge_inst is None:
                    challenge_inst = ChallengeInst()
                    session.add(challenge_inst)
                challenge_inst.challenge_id = c.id
                challenge_inst.team_id = t.id
                challenge_inst.weight = t.weight * c.weight
                challenge_inst.address = m.ip
                challenge_inst.port = m.port
        except sql_exc.MultipleResultsFound as e:
            Context.logger.critical("This bug should not happen")
            raise e
        session.commit()
        # build other inst that not in addr map
        for t in session.query(Team).all():
            for c in session.query(Challenge).all():
                try:
                    m = session.query(ChallengeInst).filter(ChallengeInst.team_id == t.id,
                                                            ChallengeInst.challenge_id == c.id).one()
                except sql_exc.NoResultFound:
                    m = ChallengeInst()
                    m.challenge_id = c.id
                    m.team_id = t.id
                    m.weight = t.weight * c.weight
                    session.add(m)
                except sql_exc.MultipleResultsFound as e:
                    Context.logger.error("duplicate addr map find")
                    raise e
        session.commit()

    # if address map is not define, try build challenge inst by ip range
    else:
        # ip_range in global has lowest level
        # this should always be true
        assert "ip_range" in conf
        if "ip_range" in conf:
            ip = conf.ip_range
            mask = conf.ip_mask
            for t in session.query(Team).all():
                for c in Context.challenges:
                    db_c = session.query(Challenge).filter(Challenge.name == c.name).one()  # should not error
                    inst = session.query(ChallengeInst).filter(ChallengeInst.team_id == t.id,
                                                               ChallengeInst.challenge_id == db_c.id).first()
                    if inst is None:
                        inst = ChallengeInst()
                        session.add(inst)
                    inst.challenge_id = db_c.id
                    inst.team_id = t.id
                    inst.weight = t.weight * db_c.weight
                    inst.address = ip
                    inst.port = c.port
                ip = ip_inc(ip, mask)
        session.commit()
        # overwrite ip in team
        for team in Context.teams:
            if team.ip is not None:
                for inst in session.query(Team).filter(Team.name == team.name).one().challenge_inst:
                    inst.address = team.ip

        # overwrite ip in challenge
        for challenge in Context.challenges:
            if challenge.ip_range is not None:
                ip = challenge.ip_range
                mask = challenge.ip_mask
                c = session.query(Challenge).filter(Challenge.name == challenge.name).one()
                for inst in session.query(ChallengeInst).filter(ChallengeInst.challenge_id == c.id).order_by(
                        ChallengeInst.team_id):
                    inst.address = ip
                    ip = ip_inc(ip, mask)
        session.commit()
    session.close()


def ip_inc(ip, mask):
    ip_byte = socket.inet_aton(ip)
    ip_num = struct.unpack(">I", ip_byte)[0]
    ip_num += 1 << (32 - mask)

    ip_byte = struct.pack(">I", ip_num)
    ip = socket.inet_ntoa(ip_byte)
    return ip
