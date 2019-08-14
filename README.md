FTemplate
=====
A template engine to make configuration file qucikly.

Getting Started
-----
To get started, what you need to do is only cloning or downloading this repository.
Then run *template.py* as shown in below.

`template.py desktop --help`  

This command shows what *desktop* template does.  
(desktop is a sample template that generates Desktop Entry file.)

Usage
-----
### Displaying version
`template.py --version` displays FTemplate's version.
### Displaying help
`template.py --help` displays FTemplate's help.

`template.py <template> --help` displays templates' help.

### Using templates
`template.py <template> name: "John Smith" gender:Male`

You can pass some data to templates with key and data pairs.
See the template's help if you want to know what keys exist.

If you want to save the generated result, rewrite your command like:

`template.py <template> key:data > result.txt`


Making original templates
-----
Making original templates is easy, what you need to do are:
1. Make a text file with a *.template* extension.
2. Declare a header and write some information.
3. Write a template text.
4. Place your template under *templates* directory.

### Example template
```
"Template description (optional)"
name: "John"               ; This declares key and set default value.
gender: ["Male", "Female"] ; You can provide selections.
-----
name=$:(name)           <- $:(key) is replaced its key value.
gender=$:(gender)       <- The leftmost value is treated as default.
date=$:{echo -n `date`} <- $:{command} is replaced its command result.
```

License
-----
FTemplate is released under MIT License.
