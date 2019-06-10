import json
import re
import uuid

import responses
from ask_sdk_core.serialize import DefaultSerializer
from ask_sdk_model import ResponseEnvelope
from ask_sdk_model.context import Context

from classes import TestItem, ProfileInfo
from validators.audio_player_validator import AudioPlayerValidator
from validators.card_validator import CardValidator
from validators.dialog_validator import DialogValidator
from validators.end_session_validator import EndSessionValidator
from validators.question_mark_validator import QuestionMarkValidator
from validators.session_attribute_validator import SessionAttributeValidator
from validators.speech_validator import SpeechValidator
from validators.video_app_validator import VideoAppValidator


class AlexaTest:
    def __init__(self, handler):
        """
        Class for testing an alexa handler
        Args:
            handler(callable): the alexa handler
        """
        self.handler = handler
        self.validators = [
            SpeechValidator(),
            SessionAttributeValidator(),
            EndSessionValidator(),
            QuestionMarkValidator(),
            DialogValidator(),
            CardValidator(),
            AudioPlayerValidator(),
            VideoAppValidator()
        ]

    def test(self, test_items):
        """
        Test the sequence of TestItems against self.validators
        Args:
            test_items(list of TestItem): the sequence of TestItems
        """
        if len(test_items) == 0:
            raise AttributeError("test_items must not be empty")
        handler = self.handler
        session_attributes = {}
        session_id = test_items[0].request.session.session_id.format(uuid.uuid4())
        for i, item in enumerate(test_items):
            item.request.session.new = i == 0
            item.request.attributes = session_attributes
            item.request.session.session_id = session_id

            if item.session_attributes:
                for k, v in item.session_attributes.items():
                    item.request.session.attributes[k] = v

            context = item.request.context
            if item.user_access_token is not None:
                context.system.api_access_token = item.user_access_token

            if item.profile_info is not None:
                handler = responses.activate(self.handler)
                add_profile_mock(context, item.profile_info)

            response_dict = handler(request_to_dict(item.request), context)
            response = response_from_dict(response_dict)
            for validator in self.validators:
                validator.validate(item, response)


def request_to_dict(request):
    return DefaultSerializer().serialize(request)


def response_from_dict(response_dict):
    serializer = DefaultSerializer()
    response_json = json.dumps(serializer.serialize(response_dict))
    return serializer.deserialize(response_json, ResponseEnvelope)


def add_profile_mock(context: Context, profile_info: ProfileInfo):
    def request_callback(request):
        profile_info_type = re.search(r"Profile\.(\w+)", request.path_url).group(1)

        if profile_info is not None:
            info_dict = {"name": profile_info.name, "givenName": profile_info.given_name,
                         "email": profile_info.email, "mobileNumber": profile_info.mobile_number}
            if profile_info_type in info_dict and info_dict[profile_info_type] is not None:
                return 200, {}, json.dumps(info_dict[profile_info_type])
        return 401, {}, json.dumps({})

    # noinspection PyUnresolvedReferences
    responses.add_passthru('')
    # noinspection PyUnresolvedReferences
    responses.add_callback(
        responses.GET,
        re.compile(r"{}v2/accounts/~current/settings"
                   r"/Profile\.(name|givenName|email|mobileNumber)".format(context.system.api_endpoint)),
        callback=request_callback,
        content_type="application/json"
    )
