from django.core.exceptions import ValidationError


def validate_results_request(data):
    """
    Validates that a result request dictionary has all needed parameters
    and their type is correct.

    Throws ValidationError on error.
    """
    mandatory_data = [
        'env',
        'proj',
        'branch',
        'exe',
        'ben',
    ]

    for key in mandatory_data:
        if key not in data:
            raise ValidationError('Key "' + key +
                                  '" missing from GET request!')
        elif data[key] == '':
            raise ValidationError('Value for key "' + key +
                                  '" empty in GET request!')

    integer_data = [
            'revs',
            'width',
            'height'
    ]

    """
    Check that the items in integer_data are the correct format,
    if they exist
    """
    for key in integer_data:
        if key in data:
            try:
                rev_value = int(data[key])
            except ValueError:
                raise ValidationError('Value for "' + key +
                                      '" is not an integer!')
            if rev_value <= 0:
                raise ValidationError('Value for "' + key + '" should be a'
                                      ' strictly positive integer!')
