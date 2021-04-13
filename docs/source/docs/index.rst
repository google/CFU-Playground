Writing Documentation
=====================

Documentation is hosted at `cfu-playground.readthedocs.io`__. It is built with 
Sphinx__, which is a Python based document generator.

__ https://cfu-playground.readthedocs.io/
__ https://www.sphinx-doc.org/


Development Setup
-----------------

#. cd to the docs/source directory.

#. run ``pip3 install -r requirements.txt`` to install Sphinx and the components 
   used by the CFU-Playground's documentation.

#. run ``make html`` to build the documentation.

Built documentation is in the docs/sourc/build/html directory. Use a web browser 
to view it.



Markdown or ReStructured Text
------------------------------

Documentation may be written in either Markdown_ or `ReStructured Text`_. Either is 
acceptable, although ReStructuredText is Sphinx's native format and you may 
find it slightly more flexible.

This document is written in ReStructuredText. There is also a 
:doc:`example Markdown document <md_example>` in this folder.

.. _Markdown: https://www.sphinx-doc.org/en/master/usage/markdown.html
.. _ReStructured Text: https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html



Diagrams
--------

We use Google Drawings for diagrams. Store diagrams in the
cfu-playground-media_ Google Drive folder. It is publically readable, and if
you're working on diagrams, ask someone to put your diagram into this folder
(you will still have write access).

To get a link to a png image, use ``File > Publish To the Web`` and select size
"Large". You can use the resulting link in Restructured Text or Markdown image
tags.

.. _cfu-playground-media: https://drive.google.com/drive/folders/1fAKv1StCrLiQi0PrUR2Et0NMQCLtffYa



Sub-pages
---------

.. toctree::
   :maxdepth: 1
   :caption: Sub-pages:

   md_example
