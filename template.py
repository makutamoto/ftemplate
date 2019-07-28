#!/usr/bin/env python3
import sys
import re
import subprocess

VERSION = '0.1.0'

ERROR_NO_TEMPLATE = -1
ERROR_FILE_NOT_FOUND = -2
ERROR_NO_HEADER = -3
ERROR_UNDEFINED_VARIABLE = -4
ERROR_INVALID_DATA = -5
ERROR_INVALID_ARGUMENT = -6
ERROR_INVALID_PARAMETER = -7

parameterRegex = re.compile(r'(?:[^$]\$|^\$):\((.+)\)', re.MULTILINE)
commandRegex = re.compile(r'(?:[^$]\$|^\$):{\s*\"((?:\\\"|[^\"])*?[^\\])\"\s*}', re.MULTILINE)

propertyRegex = re.compile(r'^\s*(.+?)\s*:\s*(.+?)\s*$', re.MULTILINE)
arrayDetectRegex = re.compile(r'^\[(?:\s*\"(?:\\\"|[^\"])*?\"\s*,\s*)*(?:\s*\"(?:\\\"|[^\"])*?\")?\s*\](?:\s*;\s*(.+?)\s*)?$')
textDataRegex = re.compile(r'^\"((?:\\\"|[^\"])*?)\"(?:\s*;\s*(.+?)\s*)?$', re.MULTILINE)
arrayTextDataRegex = re.compile(r'\"((?:\\\"|[^\"])*?)\"')


class Object:
    pass


def error(message, status):
    sys.stderr.write(message + '\n')
    sys.exit(status)


def parseHeader(rawHeader):
    description = textDataRegex.search(rawHeader)
    description = "" if description is None else description.group(1)
    parameters = {}
    for matched in propertyRegex.finditer(rawHeader):
        name = matched.group(1)
        rawData = matched.group(2)
        arrayDetect = arrayDetectRegex.match(rawData)
        if arrayDetect is None:
            textMatched = textDataRegex.match(rawData)
            if textMatched is None:
                error("Invalid data.", ERROR_INVALID_DATA)
            else:
                data = textMatched.group(1)
                comment = textMatched.group(2)
        else:
            data = []
            comment = arrayDetect.group(1)
            for item in arrayTextDataRegex.finditer(rawData):
                data.append(item.group(1))
        parameters[name] = Object()
        parameters[name].data = data
        parameters[name].comment = comment
    header = Object()
    header.description = description
    header.parameters = parameters
    return header


def print_program_version_and_exit(command):
    print("%s %s" % (command, VERSION))
    sys.exit(0)


def print_program_help_and_exit(command):
    print("Usage: %s [--help/-h] [--version/-v] <template> [--help/-h] [<parameter>...]")
    sys.exit(0)


def print_template_help_and_exit(filename, header):
    print("%s: %s" % (filename, header.description))
    print()
    print("Parameters:")

    parameters = header.parameters
    for parameter in parameters:
        print("\t%s:" % parameter, end='')
        if type(parameters[parameter].data) is list:
            print(' {', end='')
            for i, selection in enumerate(parameters[parameter].data):
                print(" %d: \"%s\"" % (i, selection), end='')
                if i < len(parameters[parameter].data) - 1:
                    print(',', end='')
            print(' }')
        else:
            print(" %s" % parameters[parameter].data)
        if not (parameters[parameter].comment is None):
            print("\t\t%s" % parameters[parameter].comment)
    sys.exit(0)


def parse_preargs(args):
    command = args[0]
    for i, arg in enumerate(args[1:]):
        if arg[0] == '-':
            if arg[1:] == '-version' or arg[1] == 'v':
                print_program_version_and_exit(command)
            elif arg[1:] == '-help' or arg[1] == 'h':
                print_program_help_and_exit(command)
            else:
                error("Invalid argument: %s" % arg, ERROR_INVALID_ARGUMENT)
        else:
            return (arg, args[i+2:])
    error("Template name must be specified.", ERROR_INVALID_ARGUMENT)


def check_parameter(header, name, value):
    if name in header.parameters:
        if type(header.parameters[name].data) is list:
            if value.isdecimal():
                if int(value) >= len(header.parameters[name].data):
                    error("\"%s\" index out of range: %s" % (name, value), ERROR_INVALID_ARGUMENT)
            else:
                error("The value of \"%s\", \"%s\", is not a decimal." % (name, value), ERROR_INVALID_ARGUMENT)
    else:
        error("Parameter \"%s\" does not exist." % name, ERROR_INVALID_PARAMETER)
    return value


def parse_postargs(template, options, header):
    current_parameter = None
    parameters = {}
    for option in options:
        if option == '--help' or option == '-h':
            print_template_help_and_exit(template, header)
        else:
            if option[-1] == ':':
                current_parameter = option[:-1]
            else:
                if current_parameter is None:
                    parameter = propertyRegex.match(option)
                    if parameter is None:
                        error("Parameter name is not specified for \"%s\"." % (option), ERROR_INVALID_ARGUMENT)
                    else:
                        name = parameter.group(1)
                        parameters[name] = check_parameter(header, name, parameter.group(2))
                else:
                    parameters[current_parameter] = check_parameter(header, current_parameter, option)
                    current_parameter = None
    return parameters


def replace_reference(replaced, match, data):
    if match.group(0)[0] == '$':
        former = replaced[:match.start()]
    else:
        former = replaced[:match.start() + 1]
    latter = replaced[match.end():]
    return former + data + latter


def main():
    (template, options) = parse_preargs(sys.argv)
    try:
        file = open('./templates/%s.template' % template)
        data = file.read()
        file.close()
    except OSError:
        error("Failed to open specified template file.", ERROR_FILE_NOT_FOUND)
    headerMatched = re.search(r'-+\n', data)
    if headerMatched is None:
        error("This templete does not contain a header.", ERROR_NO_HEADER)
    header = parseHeader(data[:headerMatched.start()])
    data = data[headerMatched.end():]
    parameters = parse_postargs(template, options, header)
    while True:
        matched = parameterRegex.search(data)
        if matched is None:
            break
        name = matched.group(1)
        if name in header.parameters:
            if name in parameters:
                if type(header.parameters[name].data) is list:
                    value = header.parameters[name].data[int(parameters[name])]
                else:
                    value = parameters[name]
            else:
                if type(header.parameters[name].data) is list:
                    if len(header.parameters[name].data) > 0:
                        value = header.parameters[name].data[0]
                    else:
                        value = ""
                else:
                    value = header.parameters[name].data
            data = replace_reference(data, matched, value)
        else:
            error("Undefined parameter \"%s\" is referenced." % matched.group(1), ERROR_UNDEFINED_VARIABLE)
    while True:
        matched = commandRegex.search(data)
        if matched is None:
            break
        command = matched.group(1)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        data = replace_reference(data, matched, result.stdout)
    sys.stdout.write(data)


if __name__ == '__main__':
    main()
