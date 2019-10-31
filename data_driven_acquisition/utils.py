import re


def apply_properties(data, properties):
    """
        Apply the provided properties to a data string following one of these
        formats:

        1. "{{ Property Name }}" : The entire string will be replaces with the value. 
        2. <!--PROPERTY:property_name-->VALUE<!--/PROPERTY:property_name--> The
            value will replace the string between the comments. Leaving the comments
            in place for later update.
    """

    for prop in properties.keys():
        # {{ Var }} format
        data = data.replace(f"{{{{  {prop}  }}}}", properties[prop])

        # <!--PROPERTY:var-->VALUE<!--/PROPERTY:var--> format
        re_str = re.compile(f"<!--PROPERTY:{prop}-->.+?<!--/PROPERTY:{prop}-->")

        if re.search(re_str, data):
            new_str = f"<!--PROPERTY:{prop}-->{properties[prop]}<!--/PROPERTY:{prop}-->"
            data = re.sub(re_str, new_str, data)

    return data
