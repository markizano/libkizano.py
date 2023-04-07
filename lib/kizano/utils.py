
import copy
import yaml

def literal_scalar(self, tag, value, style=None):
    '''
    Maintains for us the discontinuity of a multiline scalar string.
    '''
    if style is None:
        if any(c in value for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029"):
            style='|'
        else:
            style = self.default_style
    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node

def dump_yaml(data):
    '''
    Same as write yaml, but returns the result instead.
    Also use our representer to render multiline strings properly.
    '''
    yaml.representer.BaseRepresenter.represent_scalar = literal_scalar
    return yaml.dump(data, default_flow_style=False)

def read_yaml(f):
    '''
    Read a file and parse it as yaml.
    Return the data structure
    '''
    result = None
    with open(f, 'r') as fd:
        result = yaml.safe_load( fd.read() )
    return result

def write_yaml(f, data):
    '''
    Takes a data structure and writes it to file as yaml.
    Except, don't use the default options provided by the package.
    Use our custom decorators and whatnot to make it all purty <:
    '''
    with open(f, 'w') as fd:
        fd.write( dump_yaml(data) )
    return True

def dictmerge(target, *args):
    '''
    Merge multiple dictionaries.
    Usage:
    
        one = {'one': 1}
        two = {'two': 2}
        three = {'three': 3}
        sum = dictmerge(one, two, three)
        
        {one: 1, two: 2, three: 3}
    '''
    target = copy.deepcopy(target)
    if len(args) > 1:
        for obj in args:
            target = dictmerge(target, obj)
        return target
    obj = copy.deepcopy(args[0])

    # Try to combine basic algorithms we know will work for sure.
    try:
        if isinstance(target, (bool, int, float, str, list, tuple, set)) and isinstance(obj, (bool, int, float, str, list, tuple, set)):
            if isinstance(target, bool) and isinstance(obj, bool):
                return target and obj
            if isinstance(target, (int, float)) and isinstance(obj, (int, float)):
                return target + obj
            if isinstance(target, (list, tuple, set)) and isinstance(obj, (list, tuple, set)):
                return list(target + obj)
            raise ValueError('Invalid Argument')
        elif isinstance(target, dict) and isinstance(obj, dict):
            # Don't take action on dictionaries. We will execute on them in the following lines after the exception tracking.
            pass
        else:
            raise ValueError('Invalid Argument')
    except Exception as e:
        raise ValueError('\x1b[33mCould not merge\x1b[0m %s(%s) and %s(%s); Error=%s' % (type(target), target, type(obj), obj, e) )

    # Recursively merge dicts and set non-dict values
    for k, v in list(obj.items()):
        if k in target and isinstance(v, dict):
            target[k] = dictmerge(target[k], v)
        elif k in target and isinstance(v, (set, tuple, list)):
            oldtype = type(target[k])
            # Coerce to list so we can add the two reliably
            target[k] = oldtype( [*target[k]] + [*v] )
            # Convert back to its original type afterwards.
        else:
            target[k] = v
    return target

