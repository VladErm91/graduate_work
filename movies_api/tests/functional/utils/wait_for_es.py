import logging
import time

import backoff
from elastic_transport import ConnectionError
from elasticsearch import Elasticsearch
from functional.settings import test_settings


@backoff.on_exception(
    backoff.expo, (ConnectionError, ConnectionRefusedError), max_tries=100
)
def ping_elastic(es_client):
    logging.info("Pinging Elastic")
    while not es_client.ping(error_trace=False):
        print("ES not connected, retry in 5 seconds...")
        time.sleep(5)
    else:
        print("ES connected.")


if __name__ == "__main__":
    es_client = Elasticsearch(
        hosts=test_settings.es_dsl,
        verify_certs=False,
        request_timeout=1000,
        retry_on_timeout=True,
        max_retries=100,
    )
    ping_elastic(es_client)
