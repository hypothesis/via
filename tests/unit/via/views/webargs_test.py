import pytest
from marshmallow.exceptions import ValidationError as MarshmallowValidationError

from via.views.webargs import handle_error


def test_handle_error():
    validation_error = MarshmallowValidationError("Test error")

    with pytest.raises(MarshmallowValidationError) as exc_info:
        handle_error(validation_error)

    assert exc_info.value.status_int == 400
    assert exc_info.value == validation_error
