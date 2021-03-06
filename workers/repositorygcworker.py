import logging

from app import repository_gc_queue, all_queues
from data import model, database
from workers.queueworker import QueueWorker
from util.log import logfile_path

logger = logging.getLogger(__name__)


POLL_PERIOD_SECONDS = 60
REPOSITORY_GC_TIMEOUT = 60 * 15  # 15 minutes


class RepositoryGCWorker(QueueWorker):
    """
    Worker which cleans up repositories enqueued to be GCed.
    """

    def process_queue_item(self, job_details):
        logger.debug("Got repository GC queue item: %s", job_details)
        marker_id = job_details["marker_id"]

        try:
            marker = database.DeletedRepository.get(id=marker_id)
        except database.DeletedRepository.DoesNotExist:
            logger.debug("Found no matching delete repo marker: %s", job_details)
            return

        logger.debug("Purging repository %s", marker.repository)
        model.gc.purge_repository(marker.repository)


if __name__ == "__main__":
    logging.config.fileConfig(logfile_path(debug=False), disable_existing_loggers=False)

    logger.debug("Starting repository GC worker")
    worker = RepositoryGCWorker(
        repository_gc_queue,
        poll_period_seconds=POLL_PERIOD_SECONDS,
        reservation_seconds=REPOSITORY_GC_TIMEOUT,
    )
    worker.start()
