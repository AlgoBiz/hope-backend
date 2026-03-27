from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import random

SUCCESS_CODE = 6000
ERROR_CODE = 6001



def success_response(data=None, message="Success.", status_code=200, extra=None):
    payload = {"code": SUCCESS_CODE, "message": message}
    if data is not None:
        payload["data"] = data
    if extra:
        payload.update(extra)
    return Response(payload, status=status_code)


def error_response(errors=None, message="An error occurred.", status_code=400):
    payload = {"code": ERROR_CODE, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)


class StandardResultsPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "code": SUCCESS_CODE,
                "message": "Data retrieved successfully.",
                "data": {
                    "count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )


def generate_otp():
    return str(random.randint(100000, 999999))