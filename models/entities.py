import datetime
from uuid import UUID

from pony.orm import Database, PrimaryKey, Optional, Required, Set

db = Database()


class Availability(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    notes = Optional(str)
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    time_of_day = Required('TimeOfDay')
    employee_plan_period = Required('EmployeePlanPeriod')


class TimeOfDay(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 40, unique=True)
    start = Required(datetime.time)
    delta = Required(datetime.timedelta)
    notes = Optional(str)
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    availabilities = Set(Availability)
    person = Required('Person')


class PlanPeriod(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    start = Required(datetime.date)
    end = Required(datetime.date)
    deadline = Required(datetime.date)
    notes = Optional(str)
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    employee_plan_periods = Set('EmployeePlanPeriod')
    team = Required('Team')


class Person(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    f_name = Required(str, 50)
    l_name = Optional(str, 50)
    artist_name = Optional(str, 50)
    email = Required(str, 50)
    username = Required(str, 50, unique=True)
    password = Required(str)
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    employee_plan_periods = Set('EmployeePlanPeriod')
    team = Required('Team', reverse='persons')
    time_of_days = Set(TimeOfDay)
    teams_of_dispatcher = Set('Team', reverse='dispatcher')
    project_of_admin = Optional('Project')


class Project(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 50, unique=True)
    active = Required(bool, default='true')
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    teams = Set('Team')
    admin = Required(Person)


class Team(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 50, unique=True)
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    persons = Set(Person, reverse='team')
    plan_periods = Set(PlanPeriod)
    dispatcher = Required(Person, reverse='teams_of_dispatcher')
    project = Required(Project)


class EmployeePlanPeriod(db.Entity):
    id = PrimaryKey(UUID, auto=True)
    notes = Optional(str)
    created_at = Required(datetime.datetime)
    latest_change = Required(datetime.datetime)
    prep_delete = Optional(datetime.datetime)
    availabilities = Set(Availability)
    plan_period = Required(PlanPeriod)
    person = Required(Person)