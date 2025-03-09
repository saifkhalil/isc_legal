class BaseCommonException(Exception):
    """
    Base exception for the common app.
    """


class ResolverError(Exception):
    """
    The resolver class was not able to resolve the requested attribute.
    This is a not fatal exception and just makes the resolver pipeline
    try the next resolver class in the list.
    """


class ResolverPipelineError(Exception):
    """
    Raised when the resolver pipeline exhausted the list of resolvers
    and nothing new was returned. This means that the requested
    attribute does not exists.
    """


class NonUniqueError(BaseCommonException):
    """
    Raised when attempting to add duplicate values to a type that expects
    them to be unique.
    """
class APIError(Exception):
    """
    Base exception for the API app.
    """


class APIResourcePatternError(APIError):
    """
    Raised when an app tries to override an existing URL regular expression
    pattern.
    """

class BaseViewsException(Exception):
    """
    Base exception for the views app.
    """


class ActionError(BaseViewsException):
    """
    Raise by the MultiActionConfirmView to announce when the object action
    failed for one or more items.  This exception doesn't stop the iteration,
    it is used to announce that one item in the queryset failed to process.
    """
