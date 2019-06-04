from request_builders.abstract_request_builder import AbstractRequestBuilder
from ask_sdk_model import LaunchRequest
import datetime


class LaunchRequestBuilder(AbstractRequestBuilder):
    """
    RequestBuilder for a LaunchRequest
    """

    def build_request(self):
        """
        Builds the request
        Returns: (LaunchRequest) the build LaunchRequest
        """
        return LaunchRequest(request_id=self.request_id,
                             timestamp=datetime.datetime.now(),
                             locale=self.skill_settings.locale)
