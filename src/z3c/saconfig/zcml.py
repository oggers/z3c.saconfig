import zope.interface
import zope.schema
import zope.component.zcml
from zope.configuration.name import resolve

import utility
import interfaces
from z3c.saconfig import scopedsession

class IEngineDirective(zope.interface.Interface):
    """Registers a database engine factory."""

    url = zope.schema.URI(
        title=u"Database URL",
        description=u"e.g. 'sqlite:///:memory:'.",
        required=True)

    name = zope.schema.Text(
        title=u"Engine name",
        description=u"Empty if this is the default engine.",
        required=False,
        default=u"")

    echo = zope.schema.Bool(
        title=u'Echo SQL statements',
        description=u'Enable logging statements for debugging.',
        required=False,
        default=False)

    pool_size = zope.schema.Int(
        title=u"Pool size",
        description=u"Number of connections to keep open inside the connection pool.",
        required=False,
        default=5)
        
    pool_recycle = zope.schema.Int(
        title=u"Pool recycle",
        description=u"Recycle connections after the given number of seconds have passed.",
        required=False,
        default=-1)

    pool_timeout = zope.schema.Int(
        title=u"Pool timeout",
        description=u"Number of seconds to wait before giving up on getting a connection from the pool.",
        required=False,
        default=30)
    
    setup = zope.schema.BytesLine(
        title=u'After engine creation hook',
        description=u'Callback for creating mappers etc. One argument is passed, the engine',
        required=False,
        default=None)
    

class ISessionDirective(zope.interface.Interface):
    """Registers a database scoped session"""

    name = zope.schema.Text(
        title=u"Scoped session name",
        description=u"Empty if this is the default session.",
        required=False,
        default=u"")

    twophase = zope.schema.Bool(
        title=u'Use two-phase commit',
        description=u'Session should use two-phase commit',
        required=False,
        default=False)

    engine = zope.schema.Text(
        title=u"Engine name",
        description=u"Empty if this is to use the default engine.",
        required=False,
        default=u"")

    factory = zope.schema.DottedName(
        title=u'Scoped Session utility factory',
        description=u'GloballyScopedSession by default',
        required=False,
        default="z3c.saconfig.utility.GloballyScopedSession")


def engine(_context, url, name=u"", echo=False, setup=None, twophase=False,
           pool_size=5, pool_recycle=-1, pool_timeout=30):
    factory = utility.EngineFactory(
        url, echo=echo, pool_size=pool_size,
        pool_recycle=pool_recycle, pool_timeout=pool_timeout)
    
    zope.component.zcml.utility(
        _context,
        provides=interfaces.IEngineFactory,
        component=factory,
        permission=zope.component.zcml.PublicPermission,
        name=name)
    
    if setup:
        if _context.package is None:
            callback = resolve(setup)
        else:
            callback = resolve(setup, package=_context.package.__name__)
        callback(factory())

def session(_context, name=u"", engine=u"", twophase=False,
            factory="z3c.saconfig.utility.GloballyScopedSession"):
    if _context.package is None:
        ScopedSession = resolve(factory)
    else:
        ScopedSession = resolve(factory, package=_context.package.__name__)
    scoped_session = ScopedSession(engine=engine, twophase=twophase)

    zope.component.zcml.utility(
        _context,
        provides=interfaces.IScopedSession,
        component=scoped_session,
        permission=zope.component.zcml.PublicPermission,
        name=name)

def install_sessions(_context):
    _context.action(discriminator=('installSessions'),
                    callable=scopedsession.install_sessions)
