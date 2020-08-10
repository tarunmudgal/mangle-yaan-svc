"""
In this file you may place miscellaneous utility functions/classes that
don't really belong anywhere, or should be shared all over systest.
"""

import collections
import contextlib
import datetime
import errno
import fcntl
import functools
import heapq
import itertools
import logging
import multiprocessing.pool
import operator
import os
import pipes
import random
import re
import socket
import string
import struct
import subprocess
import sys
import threading
import time
import types
import uuid
import zipfile

from lib.common import logger

try:
    import copy_reg as copyreg
except ImportError:  # py3
    import copyreg
try:
    import Queue as queue
except ImportError:  # py3
    import queue


try:
    basestring
except NameError:  # py3
    basestring = unicode = str

log = logging.getLogger(__name__)
Interface = collections.namedtuple("Interface", "network names mac id")

# Make instance methods pickleable
copyreg.pickle(types.MethodType, lambda m: (getattr, (m.__self__, m.__func__.__name__)))

# global variable! bad code! with that aside we would like to have access to
# the current pytest test directory from our framework, so that we can write
# setup details there and have them automatically attached to bugs when using
# the bugzilla autofiling feature provided by the pytest-traditions plugin.
# This variable is set using the autouse, function-scoped fixture set_testdir
# in vmware/spark/topology/fixture.py.
testdir = None

# NOTE: Update this value after a branch has been cut for the systest repo.
CURRENT_UPSTREAM_BRANCH = "master"


@contextlib.contextmanager
def custom_sys_path(*paths):
    """
    Temporarily patch sys.path for custom package imports in a with-statement.

    Example:

    with custom_sys_path('/build/toolchain/noarch/pyvpx-6.0.0-2559267'):
        import pyVim
    """
    old_sys_path = list(sys.path)
    for path in paths:
        sys.path.insert(0, path)

    try:
        yield
    finally:
        # Restore old sys path even if an exception is raised in the context
        sys.path = old_sys_path


@contextlib.contextmanager
def conditional(cond, ctx):
    """
    Conditional context manager, only enters <ctx> if cond is truthy.
    """
    if cond:
        with ctx as value:
            yield value
    else:
        yield None


# Ping output regex, put together from nsx-qe/mh/tools/pingparser.py
ping_re = re.compile(
    r"(?P<transmitted>[0-9]+) packets transmitted, "
    r"(?P<received>[0-9]+) received, "
    r"(?:\+(?P<duplicates>[0-9]+) duplicates, )?"
    r"(?:\+(?P<errors>[0-9]+) errors, )?"
    r"(?P<pct_loss>[0-9]+)\% packet loss, "
    r"time (?P<duration>[0-9]+)ms"
    r"(?:\n, pipe (?P<ignored>[0-9]+))?"
    r"(?:\s*?rtt min/avg/max/mdev = "
    r"(?P<rtt_min>[0-9]+\.[0-9]+)/"
    r"(?P<rtt_avg>[0-9]+\.[0-9]+)/"
    r"(?P<rtt_max>[0-9]+\.[0-9]+)/"
    r"(?P<rtt_mdev>[0-9]+\.[0-9]+) ms)?"
)

PingResult = collections.namedtuple(
    "PingResult",
    (
        "transmitted received duplicates errors pct_loss duration "
        "ignored rtt_min rtt_avg rtt_max rtt_mdev"
    ),
)

fping_re = re.compile(
    r"(?P<host>\S+)\s+: xmt/rcv/%(?P<type>loss|return) = "
    r"(?P<transmitted>\d+)/(?P<received>\d+)/(?P<loss>\d+)%"
    r"(?:, min/avg/max = "
    r"(?P<min>[.0-9]+)/(?P<avg>[.0-9]+)/(?P<max>[.0-9]+))?"
)


def get_git_email():
    """Get the current git user's email address"""
    return subprocess.check_output(["git", "config", "user.email"]).rstrip().decode("utf-8")


def get_git_username():
    """Get the current git user's username"""
    return get_git_email().split("@")[0]


def get_last_upstream_changeset(branch=CURRENT_UPSTREAM_BRANCH):
    """Get the most recent changeset hash also present in the origin"""
    cmd = ["git", "merge-base", "HEAD", "origin/%s" % branch]
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).rstrip().decode()
    except (OSError, subprocess.CalledProcessError):
        return None


def get_git_root():
    """Return the absolute path to the nsx-qe git dir"""
    cmd = "git rev-parse --show-toplevel".split()
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).rstrip().decode()
    except (OSError, subprocess.CalledProcessError):
        # We might be running from pytest in a temporary folder
        pytest_root = get_pytest_root()
        try:
            return (
                subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=pytest_root)
                .rstrip()
                .decode()
            )
        except (OSError, subprocess.CalledProcessError):
            # Maybe not, let's hope the user hasn't changed the current path
            up = os.path.dirname
            return up(up(up(up(up(os.path.abspath(__file__))))))


def get_pytest_root():
    """Return the pytest root dir or None"""
    import pytest  # generally we want to limit pytest imports to the tests

    try:
        return str(pytest.config.rootdir)
    except AttributeError:
        return None


def get_runner_ip():
    """
    Return the VMware 10-network/local ip address of the current machine.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        address = s.getsockname()[0]
    except socket.error:
        address = None
    finally:
        s.close()

    if address is None or not address.startswith("10."):
        raise RuntimeError("unable to detect local ip")
    return address


def get_runner_private_ip():
    """
    Return the scale private ip address of the current machine. Currently
    hardcoding eth1.
    (TODO): Find better solution to avoid hardcoding eth1
    """
    ifname = "eth1"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        address = socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", ifname[:15]))[20:24]  # SIOCGIFADDR
        )
    except IOError:
        address = None
    finally:
        s.close()

    if address is None or not address.startswith("20."):
        raise RuntimeError("unable to detect private ip")
    return address


# from vmware.pxelib.utils
def can_connect(hostname, port):
    """
    Check if a host accepts connections.

    Parameters
    ----------
    hostname : str
        Address of host.
    port : int
        Port number.

    Returns
    -------
    bool
        ``True`` if we can connect to `hostname`:`port`, ``False`` otherwise.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        return s.connect_ex((hostname, port)) == 0
    finally:
        s.close()


def get_ecdsa_fingerprint():
    """Return the ECDSA fingerprint of this host"""
    cmd = "ssh-keygen -lf /etc/ssh/ssh_host_ecdsa_key.pub".split()
    return subprocess.check_output(cmd).split()[1].replace(":", "").decode()


def get_ecdsa_sha256_base64_fingerprint():
    """Return ECDSA SHA256 base64 fingerprint of this host"""
    cmd = (
        "awk '{print $2}' /etc/ssh/ssh_host_ecdsa_key.pub | base64 -d | "
        "sha256sum -b | sed 's/ .*$//' | xxd -r -p | base64 | sed 's/.//44g'"
    )
    output = subprocess.check_output(cmd, shell=True).rstrip().decode()
    mylog.debug("%s *** ECDSA SHA256 base64 fingerprint on host: %s ***", logger.plugin_name, output)
    return output


def get_https_fingerprint(host, algorithm="sha1", port=443):
    """
    Return the https certificate SHA1/SHA256/... fingerprint on <host>

    algorithm: one of md5, sha1, sha256, sha512, ...

    See 'openssl dgst -h' for more algorithm options
    """
    cmd = "|".join(
        [
            "openssl s_client -connect {}:{} < /dev/null 2> /dev/null",
            "openssl x509 -fingerprint -{} -noout",
        ]
    ).format(host, port, algorithm)
    output = subprocess.check_output(cmd, shell=True).rstrip().decode()
    assert "Fingerprint" in output, output
    return output.split("=", 1)[1]


def iso8601_timestamp():
    """Return a UTC timestamp like '2016-02-24T14:36:41.123456Z'"""
    return datetime.datetime.utcnow().isoformat() + "Z"


def flatten(iterable):
    """
    Flattens nested lists/tuples objects into a list

    >>> flatten([[1], [2], [3, 4]])
    [1, 2, 3, 4]
    >>> flatten([1, 2, 3, [4, 5, 6, [7, 8, 9], 10], 11, 12])
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    """
    result = []
    for item in list(iterable):
        if isinstance(item, (list, tuple)):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def get_random_string(length=6, prefix="", suffix="", chars=None):
    """
    Return a random string

    Parameters
    ----------
    length: int
        The length of the random string, excluding any prefix/suffix
    prefix: str
        Optional, a prefix to prepend to the random string
    suffix: str
        Optional, a suffix to append to the random string
    chars: iterable of str
        Optional, may select which characters to limit the random string to
    """
    if chars is None:
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    res = "".join(random.choice(chars) for _ in range(length))
    return prefix + res + suffix


def is_uuid(value):
    """Return True if value is a valid, string-represented UUID, else False"""
    if not isinstance(value, basestring):
        return False
    try:
        res = str(uuid.UUID(value))
    except ValueError:
        return False
    else:
        return res.lower() == value.lower()


def shellquote(cmd):
    """
    Quotes a list of command line arguments into a copy-pastable string

    >>> print shellquote(["ls", "filename with spaces"])
    ls 'filename with spaces'
    """
    return " ".join(map(pipes.quote, cmd))


def strip_ansi(s):
    """
    Strip ANSI escape codes from the string <s>

    See https://stackoverflow.com/a/38662876

    >>> print strip_ansi("\x1b[JLoading Linux 2.6.32-5-686 ...\n\x1b[9;30]\x1b[14;30]Skipping")
    'Loading Linux 2.6.32-5-686 ...\nSkipping'
    """
    return re.sub(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]", "", s)


def readable_time(seconds):
    """
    Converts a number of seconds into a human-readable time

    e.g.:  123456 -> 1d 10h 17m 36s (123456 seconds)
           600    -> 10m (600 seconds)
           40     -> 40 seconds
           1      -> 1 second
           0      -> 0 seconds
    """
    t = int(seconds)
    parts = [
        ("d", t // 60 // 60 // 24),
        ("h", (t // 60 // 60) % 24),
        ("m", (t // 60) % 60),
        ("s", t % 60),
    ]
    times = ["%d%s" % (number, unit) for unit, number in parts if number]
    # Don't bother with parenthesis if there are only seconds
    if not times:
        return "0 seconds"
    elif len(times) == 1 and "s" in times[0]:
        return "%d second%s" % (t, "s" if t > 1 else "")

    times.append("(%d seconds)" % t)
    return " ".join(times)


def parse_ping(output):
    """
    Parse the output from a ping command into a namedtuple

    Note: The duration and rtt_* values are given in milliseconds.

    Parameters
    ----------
    output: str OR [str, ...]
        A string or list of strings containing output from a ping command

    Raises
    ------
    ValueError
        If the output cannot be parsed

    Returns
    -------
    A PingResult namedtuple
    """
    if isinstance(output, list):
        output = "\n".join(output)

    match = ping_re.search(output)
    if not match:
        raise ValueError("Cannot parse ping results from: %s" % output.strip())

    parsed = []
    for i, value in enumerate(match.groups()):
        # First 7 values should be ints, the rest floats
        fmt = int if i < 7 else float
        parsed.append(value if value is None else fmt(value))
    return PingResult(*parsed)


def parse_fping(output):
    """
    Parse the summarized output from a fping command

    Note: The rtt_* values are given in milliseconds.

    Parameters
    ----------
    output: str OR [str, ...]
        A string or list of strings containing output from a fping command

    Returns
    -------
    A list of (address, PingResult)-tuples
    """
    if isinstance(output, list):
        output = "\n".join(output)

    res = []
    for match in fping_re.findall(output):
        host, type, transmitted, received, loss, min, avg, max = match
        # https://github.com/schweikert/fping/blob/develop/src/fping.c#L1202-L1215
        if type == "return":
            # We got more than we asked for
            loss = 0
            duplicates = int(received) - int(transmitted)
        elif type == "loss":
            duplicates = None
        else:
            raise AssertionError("should never happen")

        res.append(
            (
                host,
                PingResult(
                    transmitted=int(transmitted),
                    received=int(received),
                    duplicates=duplicates,
                    errors=None,
                    pct_loss=int(loss),
                    duration=None,
                    ignored=None,
                    rtt_min=float(min) if min else None,
                    rtt_avg=float(avg) if avg else None,
                    rtt_max=float(max) if max else None,
                    rtt_mdev=None,
                ),
            )
        )

    return res


def parse_nuke_or_clean_options(options):
    """
    This method parses the command line options
    for clean and nuke
    >>> parse_nuke_or_clean_options(['esxs:version=6.7,name="foo"', 'kvmss:version=16.04,name="bar"'])
    [('esxs', {version=6.7, name='foo'}), ('kvms', {version=14.04, name='bar'})
    """
    options_list = []
    for var in options:
        filters = {}
        items = var.split(":")
        container = items[0]
        if len(items) > 1:
            filter_list = items[1].split(",")
            for s in filter_list:
                item = s.split("=")
                filters[item[0]] = item[1]
        options_list.append((container, filters))
    return options_list


def convert_to_flat_list(nested_list):
    """
    This method converts list of lists into flat list
    >>> convert_to_flat_list([[1,2,3],[4,5,6])
    [1,2,3,4,5,6]
    """
    if not nested_list:
        return None
    flat_list = [item for sublist in nested_list for item in sublist]
    return flat_list


def shuffled_pairs(iterable):
    """
    Return every 2-combination of the items in <iterable>. Flip every other
    element and shuffle the resulting list to balance/distribute them evenly.

    >>> shuffled_pairs('abcd')
    [('b', 'a'), ('c', 'd'), ('b', 'c'), ('a', 'c'), ('d', 'b'), ('d', 'a')]
    """
    pairs = [
        (a, b) if i % 2 else (b, a) for i, (a, b) in enumerate(itertools.combinations(iterable, 2))
    ]
    random.shuffle(pairs)
    return pairs


def download_support_bundle(target_filename, sourceobj, source_filename):
    """ Download the support bundle on runner machine.
    target_filename: Absolute path to the desired download location
    sourceobj: Host from where support bundle needs to be pulled
     Must contain sourceobj.ip, sourceobj.password
    source_filename: Absolute path to the support bundle file.
    """
    mylog.debug("%s *** Downloading support bundle for %s ***", logger.plugin_name, sourceobj.ip)
    command = """/usr/bin/sshpass -p %s
              scp %s:%s %s""" % (
        sourceobj.password,
        sourceobj.ip,
        source_filename,
        target_filename,
    )
    res = subprocess.Popen(command, shell=True).wait()
    if res != 0:
        mylog.error("%s *** Downloading the support bundle failed ***", logger.plugin_name)
    else:
        mylog.debug(
            "%s *** Successfully downloaded support bundle at %s ***",
            logger.plugin_name,
            target_filename,
        )


def scramble_string(word):
    word = list(word)
    random.shuffle(word)
    return "".join(word)


def multi_getattr(obj, attr, default=None):
    """
    Get a named attribute from an object; multi_getattr(x, 'a.b.c.d') is
    equivalent to x.a.b.c.d. When a default argument is given, it is
    returned when any attribute in the chain doesn't exist; without
    it, return None
    """
    try:
        return operator.attrgetter(attr)(obj)
    except AttributeError:
        return default


def poll(predicate, msg, timeout, sleep, *args, **kwargs):
    """
    Helper function to implement simple wait functions

    Poll <predicate> for maximum <timeout> s at <sleep> s intervals
    until it returns True, or raise a RuntimeError.

    If raise_ is False this function will return True/False instead of
    raising an error, indicating whether the wait was successful or not.

    Parameters
    ----------
    predicate: () -> Bool function
        The wait stops when the predicate function returns True
    msg: str
        A helpful message to display in the logs
    timeout: int
        How long before a RuntimeError is raised
    sleep: int
        How long to wait between calling predicate again
    raise_: bool
        If True, raise a RuntimeError on timeout. If False, return a bool
        indicating whether the predicate succeeded within the timeout
        (This argument is pulled from kwargs for backwards-compatibility)
    args: tuple
        Positional arguments passed to <predicate>
    kwargs: dict
        Keyword arguments passed to <predicate>
    """
    raise_ = kwargs.pop("raise_", True)
    mylog.debug("%s *** waiting maximum %d seconds for %s ***", logger.plugin_name, timeout, msg)
    start = time.time()
    while time.time() < start + timeout:
        if predicate(*args, **kwargs):
            mylog.debug(
                "%s *** Done waiting for %s after %d seconds ***",
                logger.plugin_name,
                msg,
                int(time.time() - start),
            )
            return None if raise_ else True
        time.sleep(sleep)

    if raise_:
        raise RuntimeError("%s timeout exceeded while waiting for %s", logger.plugin_name, msg)
    return False


def retry(exceptions, retries=None, timeout=None, sleep=0):
    """
    Catch <exceptions> and call the decorated function up to <retries> times,
    or until <timeout> seconds have passed.

    usage:
    >>>@retry(urllib.URLError, timeout=60, sleep=3)
    ...def my_func():
    ...    pass
    >>>@retry(urllib.URLError, retries=12, sleep=5)
    ...def my_func():
    ...    pass

    Parameters
    ----------
    exceptions: Exception OR (Exception1, Exception2, ...)
        The exceptions to catch, prefer not to include 'Exception'
    retries: (optional) int
        Number of retries, required if timeout is None.
    timeout: (optional) int
        max-elapsed seconds to wait, required if retries is None,
    sleep: int
        Number of seconds to sleep between retries
    """
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)
    if Exception in exceptions:
        mymylog.warning(
            "'%s Exception' as a catch-all in retry not" " recommended", logger.plugin_name
        )

    assert retries or timeout, "must set retries or timeout"
    assert not (retries and timeout), "cannot set both retries and timeout"
    assert all(issubclass(e, Exception) for e in exceptions)
    assert sleep >= 0

    unit = "attempt(s)" if retries else "second(s)"

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            remaining = retries if retries else timeout
            endtime = None if retries else time.time() + timeout
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if not retries:
                        remaining = endtime - time.time()
                    if remaining <= 0:
                        mylog.debug(
                            "%s *** caught exception in retry " "decorator, re-raising now. ***",
                            logger.plugin_name,
                        )
                        raise
                    mylog.warn(
                        "%s *** caught exception in retry "
                        "decorator, re-raising in %d %s. traceback: ***",
                        logger.plugin_name,
                        remaining,
                        unit,
                        exc_info=True,
                    )
                    if retries:
                        remaining -= 1
                    time.sleep(sleep)

        return wrapper

    return decorator


def simple_table(data, header=None, sep="\t"):
    """
    Helper function to display tabular data
    usage:
    >>> data = [
    ... ['longer item', '.', 'short'],
    ... [None, 12345, 'hello'],
    ... [(), 'some long var', 'bye']
    ... ]
    >>> print(simple_table(data))
    longer item .               short
    None        12345           hello
    ()          some long var   bye
    >>>
    >>> header = ['column #1', 'column #2', 'column #3']
    >>> print(simple_table(data, header, sep=' | '))
    column #1   | column #2     | column #3
    longer item | .             | short
    None        | 12345         | hello
    ()          | some long var | bye
    >>>
    """
    if not isinstance(data, list):
        data = list(data)
    if header:
        data = [header] + data
    data = [[str(r) for r in row] for row in data]
    max_widths = [max(len(c) for c in col) for col in zip(*data)]
    fmt = sep.join("{:<%d}" % width for width in max_widths)
    return "\n".join(fmt.format(*row).rstrip() for row in data)


def formatter_fields(template_string):
    """
    Given a template string like '{self.x} {foo.bar} {baz}' return
    a list of the root field names, e.g. here: ['self', 'foo', 'baz']
    """
    fields = []
    for _, field, _, _ in string.Formatter().parse(template_string):
        if field:
            fields.append(field.split(".", 1)[0])
    return fields


def function_call_string(func, *args, **kwargs):
    """
    Return a string of how the call would look in code

    Useful for debugging purposes in decorators/general wrappers
    """
    parameters = list(map(repr, args)) + ["%s=%r" % kv for kv in kwargs.items()]
    return "%s(%s)" % (func.__name__, ", ".join(parameters))


def drop_duplicates(iterable, key=None):
    """
    Return a generator that removes duplicates entries

    A custom comparison function may be specifed with <key>
    """
    if key is None:
        key = lambda item: item

    seen = set()
    for item in iterable:
        hash = key(item)
        if hash not in seen:
            seen.add(hash)
            yield item


def check_output(*args, **kwargs):
    """
    When invoking subprocess.check_output with piped commands the stderr
    output can (will) leak through to the pytest prompt. This wrapper
    behaves like subprocess.check_output but redirects stderr to /dev/null.

    NOTE: In python >= 3.3 there exists subprocess.DEVNULL for this purpose.
    """
    with open(os.devnull, "w") as devnull:
        kwargs.setdefault("stderr", devnull)
        return subprocess.check_output(*args, **kwargs)


def get_random_mac(standard_oui=False):
    """
    Return a random mac address as string
    if standard_oui is True return Nicira OUI (00:23:20:xx:xx:xx)
    https://www.wireshark.org/tools/oui-lookup.html
    """
    int_list = []
    if standard_oui:
        int_list = [00, 35, 32]

    while len(int_list) < 6:
        int_list.append(random.randint(0, 255))

    return "%02x:%02x:%02x:%02x:%02x:%02x" % tuple(int_list)


class Reclaimable(collections.Iterator):
    """
    An iterator you can pickle and add back generated (or other) stuff to:

    >>> def squares(start, stop):
    ...     for i in xrange(start, stop):
    ...         yield i ** 2
    ...
    >>> s1 = Reclaimable(squares, (4, 9))
    >>> next(s1)
    16
    >>> next(s1)
    25
    >>> s2 = pickle.loads(pickle.dumps(s1))
    >>> next(s2)
    36
    >>> s1.reclaim(-1)
    >>> s2 = pickle.loads(pickle.dumps(s1))
    >>> next(s1)
    -1
    >>> next(s2)
    -1
    >>> next(s1)
    36
    >>> next(s2)
    36
    """

    def __init__(self, func, args=None, kwargs=None, yielded=0, reclaimed=None):
        collections.Iterator.__init__(self)
        self.__iter = None
        self.__state = func, args or (), kwargs or {}
        self.__yielded = yielded
        self.__reclaimed = collections.deque(reclaimed or ())

    def reclaim(self, item):
        """Reclaim an item to be yielded"""
        self.__reclaimed.append(item)

    def __next__(self):
        """Iterator protocol"""
        if self.__reclaimed:
            return self.__reclaimed.popleft()

        if self.__iter is None:
            # NOTE: We cannot instantiate the iterator in __init__ since the
            # pickled function may depend on state yet to be restored.
            f, a, kw = self.__state
            self.__iter = f(*a, **kw)
            for _ in range(self.__yielded):
                next(self.__iter)

        self.__yielded += 1
        return next(self.__iter)

    next = __next__  # py2

    def __reduce__(self):
        """Pickle protocol"""
        return self.__class__, self.__state + (self.__yielded, self.__reclaimed)


class RepeatingBackgroundJob(object):
    """
    Run func(*args, **kwargs) continuously in the background at <sleep>
    intervals until you tell it to stop. Results can be polled while
    the job is running or after it has completed.

    Each function ouput is returned together with an ISO8601 (UTC) timestamp.

    >>> job = RepeatingBackgroundJob(random.randint, sleep=5, args=(0, 100))
    >>> job.start()
    >>> print "doesn't block!"
    doesn't block!
    >>> job.get_finished()  # Results can be checked while the job is running
    [('2017-03-08T20:35:36', 71),
     ('2017-03-08T20:35:42', 66),
     ('2017-03-08T20:35:47', 76)]
    >>> job.stop()
    >>> job.get_finished()  # And/or after the job has been stopped
    [('2017-03-08T20:35:52', 36),
     ('2017-03-08T20:35:57', 49)]
    >>> job.get_finished()  # Empty since finished jobs are returned only once
    []
    >>>
    """

    def __init__(self, func, args=None, kwargs=None, sleep=0):
        self._event = threading.Event()
        self._queue = queue.Queue()

        args = args or ()
        kwargs = kwargs or {}

        def worker():
            while not self._event.is_set():
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    mylog.warn(
                        "%s *** unexpected exception in background" " job %s: %s ***",
                        logger.plugin_name,
                        function_call_string(func, *args, **kwargs),
                        e,
                    )
                else:
                    self._queue.put((iso8601_timestamp(), result))

                # While sleeping, don't block .stop() calls longer than 1 sec
                for _ in range(sleep):
                    if self._event.is_set():
                        break
                    time.sleep(1)

        self._thread = threading.Thread(target=worker)
        # Exit with main process
        self._thread.daemon = True

    def start(self):
        """
        Start the background job
        """
        self._thread.start()

    def stop(self):
        """
        Stop the background job

        Will block for maximum 1 second if the job is in its
        sleep phase, else until the current job is finished.
        """
        self._event.set()
        self._thread.join()

    def get_finished(self):
        """
        Return a list of the completed job results

        Can be called:
        - Before the job has started
        - During the job is running
        - After the job has been stopped

        NOTE: A job result will only be returned once
        """
        if self._thread.is_alive():
            results = []
            while True:
                try:
                    r = self._queue.get_nowait()
                except queue.Empty:
                    return results
                else:
                    results.append(r)
        elif self._queue.queue:
            results = list(self._queue.queue)
            self._queue.queue.clear()
            return results
        else:
            return []


class JobGroup(object):
    """
    Lets you start and stop a group (set) of jobs simultaneously
    """

    def __init__(self, *jobs):
        self._jobs = set(jobs)

    def add(self, *jobs):
        self._jobs.update(jobs)

    def start(self):
        for job in self._jobs:
            job.start()

    def stop(self):
        pool = multiprocessing.pool.ThreadPool(processes=len(self._jobs))
        pool.map(lambda job: job.stop(), self._jobs)


class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


def group_similar(iterable, key):
    """
    Groups similar items in <iterable> by <key>, retaining the inital order

    I.e. similar items are "bubbled" up from the end of the list to below
    their first occurrence.

    >>> items = [
    ... ('A1', 'FOO'),
    ... ('A2', 'BAR'),
    ... ('A3', 'BAR'),
    ... ('A4', 'FOO'),
    ... ('A5', 'BAR'),
    ... ('A6', 'XYZ'),
    ... ('A7', 'XYZ')]
    >>> group_similar(items, key=lambda item: item[1])
    [('A1', 'FOO'),
     ('A4', 'FOO'),
     ('A2', 'BAR'),
     ('A3', 'BAR'),
     ('A5', 'BAR'),
     ('A6', 'XYZ'),
     ('A7', 'XYZ')]
    """
    index = 0
    grouped = []
    insert_indices = {}  # group: index
    to_be_inserted = {}  # group: [item, item, ...]

    for item in iterable:
        group = key(item)
        if group not in insert_indices:
            grouped.append(item)
            index += 1  # Next item in group should be inserted at index+1
            insert_indices[group] = index
        else:
            to_be_inserted.setdefault(group, []).append(item)

    for group, index in sorted(insert_indices.items(), key=lambda kv: -kv[1]):
        for item in reversed(to_be_inserted.get(group, [])):
            grouped.insert(index, item)

    return grouped


def get_matching_files(directory, patterns=None):
    """ Walk the dep tree (on disk) to find a match for all patterns.
    parameters:
    ----------
    directory: root-dir of a tree of files
    patterns: list of regex matches for desired resource (filename-matches).

    returns
    -------
    (maybe empty) list of abspaths to matching files.

    TODO: support posix-globbing, this is a legacy of using regex in url
    __path_regex call to buildweb
    """
    patterns_ = []
    if patterns is None:
        patterns = []
    for pattern in patterns:
        if isinstance(pattern, str):
            patterns_.append(re.compile(pattern))
        else:
            patterns_.append(pattern)
    return _get_matching_files(directory, patterns_)


def _get_matching_files(directory, patterns_):
    results = []
    for directory_, subdirs, files in os.walk(directory):
        _ = subdirs
        for filename in files:
            for pattern in patterns_:
                if re.match(pattern, filename):
                    path = os.path.join(directory_, filename)
                    assert os.path.exists(path)
                    results.append(path)
    return results


def log_duration(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start_time = time.time()
        ret = func(*args, **kwargs)
        duration = readable_time(time.time() - start_time)
        mylog.debug(
            '%s *** Done running "%s" in %s ***', logger.plugin_name, func.__name__, duration
        )
        return ret

    return inner


@log_duration
def zip_systest():
    """zips current systest dir. Only files returned by git ls-files are
    included in zip."""
    output = subprocess.check_output(["git", "ls-files"]).decode()
    files = output.split("\n")
    zip = zipfile.ZipFile("systest.zip", "w")
    for f in files:
        try:
            zip.write(f)
        except OSError as e:
            # Ignore no file exists errors
            if e.errno != errno.ENOENT:
                raise
    zip.close()


def zipdir(path, archname):
    """https://gist.github.com/felixSchl/d38b455df8bf83a78d3d"""
    archive = zipfile.ZipFile(archname, "w", zipfile.ZIP_DEFLATED)
    if os.path.isdir(path):
        _zippy(path, path, archive)
    else:
        _, name = os.path.split(path)
        archive.write(path, name)
    archive.close()


def _zippy(base_path, path, archive):
    paths = os.listdir(path)
    for p in paths:
        p = os.path.join(path, p)
        if os.path.isdir(p):
            _zippy(base_path, p, archive)
        else:
            archive.write(p, os.path.relpath(p, base_path))


def string_replace(in_filename, to_replace, new_string, out_filename=None, count=-1):
    """
    Replace the "count" occurences of  string "to_replace"
    by "new_string" in file "in_filename" to "out_filename"

    By default replace all occurences inplace
    """
    if out_filename is None:
        out_filename = in_filename

    with open(in_filename) as f:
        contents = f.read()

    contents = contents.replace(to_replace, new_string, count)

    with open(out_filename, "w") as f:
        f.write(contents)


def netmask_to_cidr(netmask):
    """
    Converts from dotted notation of netmask to cidr, for eg
    255.255.255.0 -> 24
    """
    return sum([bin(int(x)).count("1") for x in netmask.split(".")])


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    if hasattr(itertools, "izip_longest"):  # py2
        zip_longest = itertools.izip_longest
    else:
        zip_longest = itertools.zip_longest
    return zip_longest(fillvalue=fillvalue, *args)


def chunks(l, num):
    """
    Returns successive n-sized chunks from list l

    For Example:
        >>> chunks(range(10),4)
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]
    """
    return [l[i : i + num] for i in range(0, len(l), num)]


def eth_vnic(vnic, prefix="eth"):
    """return int vnic as eth#, or unchanged, to use something other than eth
    pass in a prefix. usage:
    >>>vnic = eth_vnic(1)
    eth1
    >>>vnic = eth_vnic(1, prefix='breth')
    breth1
    >>>vnic = eth_vnic('breth2')
    breth2
    """
    if vnic is None:
        return vnic
    try:
        index = int(vnic)
        vnic = "%s%d" % (prefix, index)
    except ValueError:
        pass
    return vnic


class ThreadSafeIter(object):
    """
    Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.it)

    next = __next__  # py2


def retry_if_false(retries, interval, raise_on_error=True):
    """Annotation object, calls decorated method repeatedly if it returns
    False. Throws  TimeoutError if decorated method does not succeed
    after given number of attempts

    usage:
    >>>@retry_if_false(3, 10)
    ...def my_func():
    ...    pass

    Parameters
    ----------
    retries: (required) int
        Number of retries.
    interval: (required) int
        max-elapsed seconds to wait before retry
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            count = 0
            while count <= retries:
                ret = func(*args, **kwargs)
                if not ret:
                    mylog.debug(
                        "%s *** %s failed; Retry after an interval of" " %s sec ***",
                        logger.plugin_name,
                        func.__name__,
                        interval,
                    )
                    time.sleep(interval)
                else:
                    return ret
                count += 1

    return decorator


def generate_private_key(pkey_type="rsa", pkey_bits=2048):
    if pkey_type == "rsa":
        pkey_type = crypto.TYPE_RSA
    else:
        pkey_type = crypto.TYPE_DSA

    key = crypto.PKey()
    key.generate_key(pkey_type, pkey_bits)
    return key


def generate_ca_certificate(
    pkey_type="rsa",
    pkey_bits=2048,
    version=2,
    ca_subj_dict=None,
    sign_digest="sha256",
    validity=10 * 365 * 24 * 60 * 60,
):
    """
    Generate a CA certificate and return the cer and key
    Input params:
    --------------
    pkey_type: The type of private key, defaults to rsa
    pkey_bits: The bits used to encrypt private key
    version: The version of certificate, 0,1,2
    ca_subj_dict: A dict of properties required to create CA, like commonName etc
                check help(ca_cert.get_subject()) for all keys. Has some defaults
                values if not provided
    sign_digest: The digest used to sign CA certificate
    validity: validity in seconds for which CA is valid. Defaults to 10 years
    Returns:
    ----------
    Returns the ca_cert and ca_key
    Also dumps them into a local file
    """
    ca_key = generate_private_key(pkey_type, pkey_bits)

    ca_cert = crypto.X509()
    ca_cert.set_version(version)
    ca_cert.set_serial_number(random.randint(50000000, 100000000))

    ca_subj = ca_cert.get_subject()
    default_ca_subj = {
        "commonName": "VMware India",
        "countryName": "IN",
        "stateOrProvinceName": "MH",
        "localityName": "Pune",
        "organizationName": "VMWare Inc",
    }

    if ca_subj_dict is None:
        ca_subj_dict = {}
    default_ca_subj.update(ca_subj_dict)

    for key, value in default_ca_subj.items():
        setattr(ca_subj, key, value)

    ca_cert.add_extensions(
        [crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=ca_cert),]
    )

    ca_cert.add_extensions(
        [crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always", issuer=ca_cert),]
    )

    ca_cert.add_extensions(
        [
            crypto.X509Extension(b"basicConstraints", False, b"CA:TRUE"),
            crypto.X509Extension(b"keyUsage", False, b"keyCertSign, cRLSign"),
        ]
    )

    ca_cert.set_issuer(ca_subj)
    ca_cert.set_pubkey(ca_key)
    ca_cert.sign(ca_key, sign_digest)

    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(validity)

    # Save certificate
    ca_cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert)
    ca_cert_pem = ca_cert_pem.decode("utf-8")
    with open("ca.crt", "wt") as f:
        f.write(ca_cert_pem)

    # Save private key
    ca_key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key)
    ca_key_pem = ca_key_pem.decode("utf-8")
    with open("ca.key", "wt") as f:
        f.write(ca_key_pem)

    return ca_cert, ca_key, ca_cert_pem, ca_key_pem


def generate_selfsigned_certificate(
    ca_cert,
    ca_key,
    pkey_type="rsa",
    pkey_bits=2048,
    version=2,
    client_subj_dict=None,
    sign_digest="sha256",
    validity=10 * 365 * 24 * 60 * 60,
):
    """
    Generate a self signed certificate and return the cer and key
    Input params:
    --------------
    ca_cert_pem and ca_key_pem: Certificate and key for CA. Can be obtained from
            function utilities.generate_ca_certificate
    pkey_type: The type of private key, defaults to rsa
    pkey_bits: The bits used to encrypt private key
    version: The version of certificate, 0,1,2
    ca_subj_dict: A dict of properties required to create CA, like commonName etc
                check help(ca_cert.get_subject()) for all keys. Has some defaults
                values if not provided
    sign_digest: The digest used to sign CA certificate
    validity: validity in seconds for which CA is valid. Defaults to 10 years
    Returns:
    ----------
    Returns the ca_cert and ca_key
    Also dumps them into a local file
    Usage:
    -----------
    ca_cert, ca_key, ca_cert_pem, ca_key_pem = generate_ca_certificate()
    client_cert, client_key, client_cert_pem, client_key_pem = \
        generate_selfsigned_certificate(ca_cert, ca_key)
    """
    client_key = generate_private_key(pkey_type, pkey_bits)
    client_cert = crypto.X509()
    client_cert.set_version(2)
    client_cert.set_serial_number(random.randint(50000000, 100000000))

    client_subj = client_cert.get_subject()
    default_client_subj = {
        "commonName": get_random_string(prefix="client_"),
        "countryName": "IN",
        "stateOrProvinceName": "MH",
        "localityName": "Pune",
        "organizationName": "VMWare Inc",
    }

    if client_subj_dict is None:
        client_subj_dict = {}
    default_client_subj.update(client_subj_dict)

    for key, value in default_client_subj.items():
        setattr(client_subj, key, value)

    client_cert.add_extensions(
        [
            crypto.X509Extension(b"basicConstraints", False, b"CA:FALSE"),
            crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=client_cert),
        ]
    )

    client_cert.add_extensions(
        [
            crypto.X509Extension(
                b"authorityKeyIdentifier", False, b"keyid:always", issuer=ca_cert
            ),
            crypto.X509Extension(b"extendedKeyUsage", False, b"clientAuth"),
            crypto.X509Extension(b"keyUsage", False, b"digitalSignature"),
        ]
    )

    client_cert.set_issuer(ca_cert.get_subject())
    client_cert.set_pubkey(client_key)

    client_cert.gmtime_adj_notBefore(0)
    client_cert.gmtime_adj_notAfter(validity)
    client_cert.sign(ca_key, sign_digest)

    # Save certificate
    client_cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert)
    client_cert_pem = client_cert_pem.decode("utf-8")
    with open("client.crt", "wt") as f:
        f.write(client_cert_pem)

    # Save private key
    client_key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key)
    client_key_pem = client_key_pem.decode("utf-8")
    with open("client.key", "wt") as f:
        f.write(client_key_pem)

    return client_cert, client_key, client_cert_pem, client_key_pem


def get_n_max_items_from_map_of_lists(data, n):
    """
    This function returns a list of n maximum items from the data.

    Parameters
    ----------
    data: defaultdict(list)
        This is the restriction right now.
    n: int
        The number of max elements to be returned.

    Returns
    ----------
    list:
        List of the n max elements.
    """
    return [k for k in heapq.nlargest(n, data, key=lambda k: len(data[k]))]


def str2bool(value):
    """Convert string to bool

    @value: string

    Returns
    -------
    bool
    """
    if not value:
        return None
    return value.lower() in ("yes", "true", "t", "1")


def generate_name(name, index):
    """Generate unique name based on current process group

    @name: string
    @index: int

    Returns:
    --------
    name + '_' + index + '_' + <curr process group>

    Sample:
    -------
    generate_name("datacenter", 1) => datacenter_1_1179 => unique to current
    process

    """
    return name + "_" + str(index) + "_" + str(os.getpgrp() % 2000)
