try:
    import basestring
except NameError:  # py3
    basestring = unicode = str


class Namespace(object):
    """
    Converts a dictionary into an object so that its key-values can be
    be accessed as regular attributes. Recursively traverses the given
    dictionary so that nested dictionaries also gets converted into
    namespaces.

    To access the dictionary keys as regular attributes they must follow
    normal naming conventions, i.e. something like [_a-zA-Z][_a-zA-Z0-9]+

    Keys not following normal naming conventions are not lost, and can
    be accessed via the getattr and setattr methods.

    Attributes can be added, edited, or deleted (via 'del').

    The Namespace can be converted back into a dictionary with to_dict(),
    and Namespace(dct).to_dict() == dct should always hold true.

    Example:
    >>> data = {'foo': 'one', 'bar': {'baz': 'two'}}
    >>> ns = Namespace(data)
    >>> ns
    Namespace(bar=Namespace(baz='two'), foo='one')
    >>> ns.bar.baz
    'two'
    >>> ns.bar.xxx = 3
    >>> del ns.foo
    >>> ns.foo
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    AttributeError: 'Namespace' object has no attribute 'foo'
    >>> ns.to_dict()
    {'bar': {'xxx': 3, 'baz': 'two'}}
    """

    def __init__(self, dct):
        if not isinstance(dct, dict):
            raise TypeError("Namespace argument is not a dict")
        if not all(isinstance(key, basestring) for key in dct.keys()):
            raise TypeError("Namespaces only support dicts with string keys")

        for key, value in dct.items():
            setattr(self, key, self._to_namespace(value))

    def __repr__(self):
        """String representation of this Namespace"""
        content = ("%s=%r" % kv for kv in sorted(vars(self).items()))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(content))

    def __eq__(self, other):
        """Support '==' comparision"""
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Support '!=' comparision"""
        return not self.__eq__(other)

    def __contains__(self, key):
        """Support 'key in Namespace()' checks"""
        return hasattr(self, key)

    def __getstate__(self):
        """Support pickling of Namespaces"""
        return self.to_dict()

    def __setstate__(self, dct):
        """Support unpickling of Namespaces"""
        self.__init__(dct)

    @classmethod
    def _to_namespace(cls, value):
        """Return the Namespace representation of <value>"""
        if isinstance(value, dict):
            return cls(value)
        elif isinstance(value, list):
            return list(cls._to_namespace(v) for v in value)
        elif isinstance(value, tuple):
            return tuple(cls._to_namespace(v) for v in value)
        else:
            return value

    @classmethod
    def _from_namespace(cls, value):
        """Return the inverse Namespace representation of <value>"""
        if isinstance(value, cls):
            return value.to_dict()
        elif isinstance(value, list):
            return list(cls._from_namespace(v) for v in value)
        elif isinstance(value, tuple):
            return tuple(cls._from_namespace(v) for v in value)
        else:
            return value

    def to_dict(self):
        """Return the original dict representation of this Namespace"""
        dct = {}
        for key, value in vars(self).items():
            dct[key] = self._from_namespace(value)
        return dct


class ResponseObject(Namespace):
    """
    Data wrapper for NSXT json objects returned by the manager API.

    For example, wrapping a TransportZone object could look like this:
    >>> r = requests.get('https://.../api/v1/transport-zones/<uuid>', ...)
    >>> pprint.pprint(r.json())
    {u'_create_time': 1475576935683,
     u'_create_user': u'admin',
     u'_last_modified_time': 1475576935683,
     u'_last_modified_user': u'admin',
     u'_revision': 0,
     u'_schema': u'/v1/schema/TransportZone',
     u'_system_owned': False,
     u'description': u'overlay transport zone',
     u'display_name': u'TZ_0',
     u'host_switch_name': u'nsx-vswitch',
     u'id': u'919ab8d4-5ad2-4c3b-b1fa-344578d3dee8',
     u'resource_type': u'TransportZone',
     u'transport_type': u'OVERLAY',
     u'transport_zone_profile_ids': [
        {u'profile_id': u'52035bb3-ab02-4a08-9884-18631312e50a',
         u'resource_type': u'BfdHealthMonitoringProfile'}]
    }
    >>> tz = ResponseObject(r.json())
    >>> tz
    <TransportZone: 919ab8d4-5ad2-4c3b-b1fa-344578d3dee8>
    >>> tz.host_switch_name
    u'nsx-vswitch'
    >>> tz._create_time
    1475576935683
    >>> tz.transport_zone_profile_ids
    [<BfdHealthMonitoringProfile: (profile_id=u'52035bb3-ab02-4a08-9884-18631312e50a', resource_type=u'BfdHealthMonitoringProfile')>]
    >>> tz.to_dict() == r.json()
    True
    """

    def __repr__(self):
        """Pretty string representation of ResponseObjects"""
        if hasattr(self, "id"):
            info = self.id  # pylint: disable=no-member
        else:
            content = ("%s=%r" % kv for kv in sorted(vars(self).items()))
            info = "(%s)" % ", ".join(content)
        type = getattr(self, "resource_type", "ResponseObject")
        return "<%s: %s>" % (type, info)
