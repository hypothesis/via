from checkmatelib import CheckmateClient

from via.checkmate import checkmate


def test_it(pyramid_request):
    assert isinstance(checkmate(pyramid_request), CheckmateClient)
