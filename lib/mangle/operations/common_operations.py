from lib.common import logger, utilities

log = logger.setup_logging(__name__)


class CommonOps(object):
    """
    common operations
    """

    @staticmethod
    def poll_fault_status(session_obj, fault_id, expected_status="COMPLETED", timeout=120):
        """
        # TODO:
        """

        mylog.debug("%s *** fault id :: %s ***", logger.plugin_name, fault_id)

        def get_task_status():
            """
            # TODO:
            """
            # build prefix to get the status of task
            prefix = "/tasks/%s" % fault_id
            ret_val, fault_status = session_obj.make_call("GET", prefix)
            mylog.debug("%s *** fault_status ***:: %s", logger.plugin_name, fault_status)
            status = fault_status["mangleTaskInfo"]["taskStatus"]
            return status == expected_status

        utilities.poll(
            get_task_status,
            "Expected status to become %s.." % expected_status,
            sleep=10,
            timeout=timeout,
        )
