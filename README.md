
ACWX wx-App Library
=======================

This is a set of utilities, widgets, and base classes used by APCI, LLC and
CMM, Inc. in the development of their software. At this point, Its primary
interest to others will be as a source of examples and inspiration as the
code is young (thus incompatible changes are likely) and can have specific
expectations in places (we're working on those).



Dependencies
============

The base app objects are meant to be usable without depending on GUI
libraries, thus wx, for instance, is not listed in the package dependencies
(the Debian package only "Suggests" it). For full features, this package
suggests:

  * SQLAlchemy
  * ScientificPython
  * matplotlib
  * numpy
  * passlib
  * scipy
  * wxPython
  * wxmplot



LICENSE
=======

This program is free software: you can redistribute it and/or modify it
under the terms of the MIT (Expat) license.
