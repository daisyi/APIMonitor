#!/usr/bin/env python
# encoding: utf-8
import logging

class ApiException(Exception):
    def __init__(self, apiResponse, previous=None):
        self.__apiResponse = apiResponse

        message = previous.message if previous else 'Unknown error'
        status = 0  # previous.status if previous else 0

        if apiResponse:
            if apiResponse.error():
                message = apiResponse.error()

            if apiResponse.response() and apiResponse.response().status_code:
                status = apiResponse.response().status_code

        logging.error(apiResponse.response().status_code)
        logging.error(message)
        logging.error(apiResponse.json_dict())

        Exception.__init__(self, status, message)

    def api_response(self):
        return self.__apiResponse