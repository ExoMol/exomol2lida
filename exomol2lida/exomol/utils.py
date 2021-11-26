import warnings


def parse_exomol_line(lines, n_orig, expected_comment=None):
    """Line parser for the ExoMol files (.all and .def).

    List of the file lines is passed as well as the original length of the list.
    The top line of lines is popped (lines gets changed as an externality) and the
    line value is extracted and returned.
    If the expected_comment is passed, the comment in the top line (after # symbol)
    is asserted to equal the expected_comment.
    If the comment does not match (possible inconsistency), AssertionError is
    raised with the line number of the original file.

    Parameters
    ----------
    lines : list[str]
        List at first containing all the lines of the file which are then being
        popped one by one.
    n_orig : int
        The number of lines of the full file
    expected_comment : str
        The comment after the # symbol on each line is expected to match the
        passed expected comment.

    Returns
    -------
    str
        Value belonging to the top line in lines passed.

    Raises
    ------
    AssertionError
        If the comment behind # symbol on the top line does not match the
        expected_comment, or if the top line in lines does not have any comment.

    Examples
    --------
    >>> lns = ['val1 # comment1', 'val2 # comment2', 'val3']
    >>> n = len(lns)
    >>> parse_exomol_line(lns, n, expected_comment='comment1')
    'val1'
    >>> lns
    ['val2 # comment2', 'val3']
    >>> parse_exomol_line(lns, n, expected_comment='foo')
    Traceback (most recent call last):
      ...
    AssertionError: Inconsistent comment detected on line 2!
    >>> parse_exomol_line(lns, n)
    Traceback (most recent call last):
      ...
    AssertionError: Inconsistency detected on line 3!
    >>> lns
    []
    """

    while True:
        line = lines.pop(0)
        line_num = n_orig - len(lines)
        if line:
            break
        else:
            warnings.warn(f'Empty line detected on line {line_num}!')
    try:
        val, comment = line.split('# ')
    except ValueError:
        raise AssertionError(f'Inconsistency detected on line {line_num}!')
    assert comment == expected_comment, \
        f'Inconsistent comment detected on line {line_num}!'
    return val.strip()
